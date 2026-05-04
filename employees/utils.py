import logging
import re
import difflib
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MAPBOX_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json'


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


def geocode_address(address: str) -> dict:
    try:
        logger.debug('geocode → "%s"', address)
        import urllib.parse
        url = MAPBOX_URL.format(query=urllib.parse.quote(address))
        resp = requests.get(url, params={
            'access_token': settings.MAPBOX_API_KEY,
            'language': 'tr',
            'country': 'TR',
            'proximity': '29.06,40.19',
            'limit': 1,
        }, timeout=10)
        logger.debug('geocode HTTP %s  (%.0f ms)', resp.status_code, resp.elapsed.total_seconds() * 1000)
        resp.raise_for_status()
        features = resp.json().get('features', [])
        if not features:
            logger.warning('geocode no_result → "%s"', address)
            return {'ok': False, 'reason': 'no_result'}
        feature = features[0]
        lng, lat = feature['center']
        api_address = feature.get('place_name', '')
        logger.debug('geocode OK → %s, %s  "%s"', lat, lng, api_address)
        return {
            'ok': True,
            'lat': float(lat),
            'lng': float(lng),
            'api_address': api_address,
        }
    except requests.RequestException as exc:
        logger.error('geocode api_error → "%s"  %s', address, exc)
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
    except Exception as exc:
        logger.exception('geocode unexpected error → "%s"', address)
        return {'ok': False, 'reason': 'api_error', 'detail': str(exc)}
