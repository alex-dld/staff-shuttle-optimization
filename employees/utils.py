import requests
from django.conf import settings

MAPBOX_GEOCODE_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json'


def geocode_address(address: str) -> dict:
    """
    Returns:
      {'ok': True,  'lat': float, 'lng': float, 'api_address': str}
      {'ok': False, 'reason': 'no_result'}
      {'ok': False, 'reason': 'api_error', 'detail': str}
    """
    try:
        resp = requests.get(
            MAPBOX_GEOCODE_URL.format(query=requests.utils.quote(address)),
            params={
                'access_token': settings.MAPBOX_API_KEY,
                'language': 'tr',
                'country': 'tr',
                'proximity': '28.8,40.0',  # Bursa merkezi
                'limit': 1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        features = resp.json().get('features', [])
        if not features:
            return {'ok': False, 'reason': 'no_result'}
        feature = features[0]
        lng, lat = feature['geometry']['coordinates']
        return {
            'ok': True,
            'lat': lat,
            'lng': lng,
            'api_address': feature.get('place_name', address),
        }
    except requests.RequestException as exc:
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
    except Exception as exc:
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
