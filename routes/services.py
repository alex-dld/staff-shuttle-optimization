import re
from urllib.parse import unquote, urlparse, parse_qs
import requests

_COORD_RE = re.compile(r'^(-?\d+\.\d+),(-?\d+\.\d+)$')


def parse_google_maps_url(url: str) -> list:

    # --- 1. All coordinates from data= in route order ---
    # data= contains the named-place coordinates AND all intermediate via points
    # that Google Maps uses to define the exact path.
    data_coords: list[dict] = []
    data_match = re.search(r'data=(.+?)(?:\?|$)', url)
    if data_match:
        for lon_str, lat_str in re.findall(r'1d(-?\d+\.\d+)!2d(-?\d+\.\d+)', data_match.group(1)):
            data_coords.append({'lat': float(lat_str), 'lng': float(lon_str)})

    # --- 2. Coordinate-based path segments (typically the destination) ---
    path_match = re.search(r'/dir/(.+?)(?:/@|$)', url)
    if not path_match:
        return []

    coord_segments: list[dict] = []
    for segment in path_match.group(1).split('/'):
        segment = unquote(segment).strip()
        if not segment:
            continue
        m = _COORD_RE.match(segment)
        if m:
            coord_segments.append({'lat': float(m.group(1)), 'lng': float(m.group(2))})

    # --- 3. Merge: data= coords first (already in route order), then any
    #         coordinate-based destinations not already covered ---
    seen: set[tuple] = set()
    result: list[dict] = []

    def add(wp: dict) -> None:
        key = (round(wp['lat'], 4), round(wp['lng'], 4))
        if key not in seen:
            seen.add(key)
            result.append(wp)

    for wp in data_coords:
        add(wp)
    for wp in coord_segments:
        add(wp)

    return result


def parse_yandex_maps_url(url: str) -> list:
    # rtext=lat,lng~lat,lng~... formatındaki waypoint'leri çeker
    params = parse_qs(urlparse(url).query)
    rtext = params.get('rtext', [''])[0]
    if not rtext:
        return []

    result = []
    seen: set[tuple] = set()
    for segment in rtext.split('~'):
        segment = segment.strip()
        if not segment:
            continue
        parts = segment.split(',')
        if len(parts) != 2:
            continue
        try:
            lat, lng = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        key = (round(lat, 4), round(lng, 4))
        if key not in seen:
            seen.add(key)
            result.append({'lat': lat, 'lng': lng})
    return result


def get_isochrone_from_ors(lat: float, lng: float, minutes: int, api_key: str) -> dict:
    """
    Call ORS Isochrones API for a walking isochrone.
    Returns GeoJSON FeatureCollection with the polygon.
    """
    response = requests.post(
        'https://api.openrouteservice.org/v2/isochrones/foot-walking',
        json={
            'locations': [[lng, lat]],
            'range': [minutes * 60],
            'range_type': 'time',
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


def get_route_from_ors(waypoints: list, api_key: str) -> dict:
    coordinates = [[wp['lng'], wp['lat']] for wp in waypoints]
    response = requests.post(
        'https://api.openrouteservice.org/v2/directions/driving-car/geojson',
        json={'coordinates': coordinates},
        headers={
            'Authorization': api_key,
            'Content-Type': 'application/json',
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def get_route_from_mapbox(waypoints: list, api_key: str) -> dict:
    # Mapbox accepts max 25 waypoints; coords are lng,lat separated by ;
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
    # Normalize to GeoJSON FeatureCollection (same shape as ORS response)
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
