import asyncio
import datetime
from typing import Any, Dict, List

import aiohttp
import requests

from . import consts, string


def get_string() -> Dict[str, List[Dict[str, str]]]:
    ret = requests.get(consts.STRING_URL).json()
    del ret['language']
    return ret

def with_retry(func):
    async def wrapper(*args, **kwargs):
        for _ in range(3):
            try:
                return await func(*args, **kwargs)
            except aiohttp.ClientError:
                await asyncio.sleep(10)
        raise Exception('Failed to connect to API')
    return wrapper

@with_retry
async def get_ongoing_matches() -> List[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(consts.ONGOING_MATCH_URL) as resp:
            ret = await resp.json(content_type='text/plain')

    ret['data'] = [_ for _ in ret['data'] if _.get('ranked', False)]
    for _ in ret['data']:
        for field in consts.UNUSED_MATCH_FIELDS:
            if field in _:
                del _[field]
        for player in _['players']:
            for field in consts.UNUSED_PLAYER_FIELDS:
                if field in player:
                    del player[field]
            if 'rating' not in player:
                player['rating'] = None

        for field in ('mapSize', 'startingAge', 'resources'):
            _[field + 'Id'] = None
            if field in _:
                _[field + 'Id'] = string.Strings().query(field, _[field])
                del _[field]
        try:
            _['locationId'] = string.Strings().query('map_type', _.get('location', None))
        except KeyError:
            if '#' in _['location']:
                _['locationId'] = int(_['location'].split('#')[1])
            else:
                assert False
        del _['location']
        _['solo'] = len(_['players']) == 2
        _['started'] = datetime.datetime.fromtimestamp(_['started'])
        if 'averageRating' not in _:
            _['averageRating'] = None

    return ret['data']

async def query_match_result(matchId: int, profileId: int) -> List[Dict[str, Any]]:
    data = {
        'game': 'age2',
        'gameId': str(matchId),
        'profileId': str(profileId)
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(consts.MATCH_RESULT_URL, json=data) as resp:
            result = (await resp.json(content_type=None))['playerList']
    ret = []
    for _ in result:
        ret.append({
            'matchId': matchId, 'profileId': int(_['userId']), 'result': _['winLoss'] == 'Win'
        })
    return ret
