import logging
import re
import difflib
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

YANDEX_URL = 'https://geocode-maps.yandex.ru/v1/'
MAPBOX_GEOCODE_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json'


_ABBR = {
    'cd': 'cadde', 'cad': 'cadde', 'caddesi': 'cadde',
    'sk': 'sokak', 'sok': 'sokak', 'sokagi': 'sokak', 'sokak': 'sokak',
    'blv': 'bulvar', 'bulvari': 'bulvar',
    'mah': 'mahalle', 'mahallesi': 'mahalle',
    'blok': 'blok', 'apt': 'apartman',
}


def _normalize_addr(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans('ığşöüç', 'igsouc'))
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = [_ABBR.get(t, t) for t in text.split()]
    return ' '.join(tokens)


def address_match_score(address: str, api_address: str):
    if not address or not api_address:
        return None
    a = _normalize_addr(address)
    b = _normalize_addr(api_address)
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    token_score = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    str_score = difflib.SequenceMatcher(None, a, b).ratio()
    return round(0.7 * token_score + 0.3 * str_score, 2)


def _geocode_yandex(address: str) -> dict:
    if not settings.YANDEX_API_KEY:
        return {'ok': False, 'reason': 'api_error', 'detail': 'Yandex API key not configured'}

    resp = requests.get(YANDEX_URL, params={
        'apikey': settings.YANDEX_API_KEY,
        'geocode': address,
        'lang': 'tr_TR',
        'll': '29.06,40.19',
        'spn': '0.8,0.6',
        'results': 1,
        'format': 'json',
    }, timeout=10)

    logger.debug('yandex HTTP %s  (%.0f ms)', resp.status_code, resp.elapsed.total_seconds() * 1000)

    # 403 = limit doldu, 429 = rate limit — her ikisinde de fallback'e geç
    if resp.status_code in (403, 429):
        raise _YandexLimitError(f'Yandex HTTP {resp.status_code}')

    resp.raise_for_status()

    data = resp.json()
    members = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])

    if not members:
        return {'ok': False, 'reason': 'no_result'}

    obj = members[0]['GeoObject']
    lng_str, lat_str = obj['Point']['pos'].split()
    api_address = obj.get('metaDataProperty', {}).get('GeocoderMetaData', {}).get('text', '')

    return {
        'ok': True,
        'lat': float(lat_str),
        'lng': float(lng_str),
        'api_address': api_address,
        'provider': 'yandex',
    }


def _geocode_mapbox(address: str) -> dict:
    if not settings.MAPBOX_API_KEY:
        return {'ok': False, 'reason': 'api_error', 'detail': 'Mapbox API key not configured'}

    resp = requests.get(
        MAPBOX_GEOCODE_URL.format(query=requests.utils.quote(address)),
        params={
            'access_token': settings.MAPBOX_API_KEY,
            'language': 'tr',
            'proximity': '29.06,40.19',  # Bursa merkezi
            'limit': 1,
        },
        timeout=10,
    )

    logger.debug('mapbox HTTP %s  (%.0f ms)', resp.status_code, resp.elapsed.total_seconds() * 1000)
    resp.raise_for_status()

    data = resp.json()
    features = data.get('features', [])

    if not features:
        return {'ok': False, 'reason': 'no_result'}

    feat = features[0]
    lng, lat = feat['geometry']['coordinates']
    api_address = feat.get('place_name', '')

    return {
        'ok': True,
        'lat': lat,
        'lng': lng,
        'api_address': api_address,
        'provider': 'mapbox',
    }


class _YandexLimitError(Exception):
    pass


def geocode_address(address: str) -> dict:
    try:
        logger.debug('geocode → "%s"', address)
        result = _geocode_yandex(address)
        return result
    except _YandexLimitError as exc:
        logger.warning('geocode yandex_limit → "%s" (%s) — falling back to Mapbox', address, exc)
    except requests.RequestException as exc:
        logger.error('geocode yandex api_error → "%s"  %s — falling back to Mapbox', address, exc)
    except Exception as exc:
        logger.exception('geocode yandex unexpected error → "%s"', address)
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}

    try:
        result = _geocode_mapbox(address)
        if result['ok']:
            logger.debug('geocode mapbox OK → %s, %s  "%s"', result['lat'], result['lng'], result['api_address'])
        return result
    except requests.RequestException as exc:
        logger.error('geocode mapbox api_error → "%s"  %s', address, exc)
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
    except Exception as exc:
        logger.exception('geocode mapbox unexpected error → "%s"', address)
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
