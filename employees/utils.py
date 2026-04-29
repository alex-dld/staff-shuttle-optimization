import requests
from django.conf import settings

YANDEX_URL = 'https://geocode-maps.yandex.ru/v1/'


def geocode_address(address: str) -> dict:
    """
    Returns:
      {'ok': True,  'lat': float, 'lng': float, 'api_address': str}
      {'ok': False, 'reason': 'no_result'}
      {'ok': False, 'reason': 'api_error', 'detail': str}
    """
    try:
        resp = requests.get(YANDEX_URL, params={
            'apikey': settings.YANDEX_API_KEY,
            'geocode': address,
            'lang': 'tr_TR',
            'll': '29.06,40.19',
            'spn': '0.8,0.6',
            'results': 1,
            'format': 'json',
        }, timeout=10)
        resp.raise_for_status()
        members = resp.json()['response']['GeoObjectCollection']['featureMember']
        if not members:
            return {'ok': False, 'reason': 'no_result'}
        obj = members[0]['GeoObject']
        lng_str, lat_str = obj['Point']['pos'].split()
        return {
            'ok': True,
            'lat': float(lat_str),
            'lng': float(lng_str),
            'api_address': obj['metaDataProperty']['GeocoderMetaData']['text'],
        }
    except requests.RequestException as exc:
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
    except Exception as exc:
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
