import re
from urllib.parse import unquote
import requests

_COORD_RE = re.compile(r'^(-?\d+\.\d+),(-?\d+\.\d+)$')


def parse_google_maps_url(url: str) -> list:
    # /dir/ segments give the route's literal endpoints; data= carries the
    # full shape (route-shaping via points plus resolved named places) in
    # route order, but never repeats a literal coordinate typed in /dir/.
    path_match = re.search(r'/dir/(.+?)(?:/@|$)', url)
    if not path_match:
        return []

    segments = [unquote(s).strip() for s in path_match.group(1).split('/') if s.strip()]
    if not segments:
        return []

    data_coords: list[dict] = []
    data_match = re.search(r'data=(.+?)(?:\?|$)', url)
    if data_match:
        for lon_str, lat_str in re.findall(r'1d(-?\d+\.\d+)!2d(-?\d+\.\d+)', data_match.group(1)):
            data_coords.append({'lat': float(lat_str), 'lng': float(lon_str)})

    def same_point(a: dict, b: dict) -> bool:
        return (round(a['lat'], 4), round(a['lng'], 4)) == (round(b['lat'], 4), round(b['lng'], 4))

    result: list[dict] = []

    start_match = _COORD_RE.match(segments[0])
    if start_match:
        result.append({'lat': float(start_match.group(1)), 'lng': float(start_match.group(2))})

    result.extend(data_coords)

    if len(segments) > 1:
        end_match = _COORD_RE.match(segments[-1])
        if end_match:
            end = {'lat': float(end_match.group(1)), 'lng': float(end_match.group(2))}
            if not result or not same_point(result[-1], end):
                result.append(end)

    return result


def get_isochrone_from_ors(lat: float, lng: float, meters: int, api_key: str) -> dict:
    """
    Call ORS Isochrones API for a walking isochrone (distance-based).
    Returns GeoJSON FeatureCollection with the polygon.
    """
    response = requests.post(
        'https://api.openrouteservice.org/v2/isochrones/foot-walking',
        json={
            'locations': [[lng, lat]],
            'range': [meters],
            'range_type': 'distance',
        },
        headers={
            'Authorization': api_key,
            'Content-Type': 'application/json',
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def get_walking_matrix_from_ors(locations: list, source_indices: list, destination_indices: list, api_key: str) -> list:
    """
    ORS Matrix API - foot-walking.
    locations: [[lng, lat], ...] combined list
    source_indices / destination_indices: indices into locations
    Returns: durations matrix[source][destination] in seconds (None = unreachable)
    """
    response = requests.post(
        'https://api.openrouteservice.org/v2/matrix/foot-walking',
        json={
            'locations': locations,
            'sources': source_indices,
            'destinations': destination_indices,
            'metrics': ['duration'],
        },
        headers={
            'Authorization': api_key,
            'Content-Type': 'application/json',
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()['durations']


def get_route_from_mapbox(waypoints: list, api_key: str) -> dict:
    coords = ';'.join(f"{wp['lng']},{wp['lat']}" for wp in waypoints)
    response = requests.get(
        f'https://api.mapbox.com/directions/v5/mapbox/driving/{coords}',
        params={
            'access_token': api_key,
            'geometries': 'geojson',
            'overview': 'full',
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    route = data['routes'][0]
    return {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'geometry': route['geometry'],
            'properties': {
                'segments': [{
                    'distance': route['distance'],
                    'duration': route['duration'],
                }],
            },
        }],
    }
