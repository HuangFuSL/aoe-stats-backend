import asyncio
import os

from . import api, db


async def one_step():
    ongoing_match_id = await db.Database().query_ongoing_match()
    current = await api.get_ongoing_matches()
    current_match_id = {_['matchId'] for _ in current}
    new_match = [
        _ for _ in current
        if _['matchId'] in current_match_id - ongoing_match_id
    ]
    end_match = list(ongoing_match_id - current_match_id)
    new_match_players = []
    for _ in new_match:
        new_match_players.extend([
            dict(matchId=_['matchId'], **player)
            for player in _['players']
        ])
        del _['players']

    await db.Database().insert_new_matches(new_match)
    await asyncio.sleep(5)
    print(f'Added {len(new_match)} matches')
    await db.Database().insert_new_players(new_match_players)
    await asyncio.sleep(5)
    print(f'Added {len(new_match_players)} players')
    await db.Database().update_matches(*end_match)
    print(f'Finished {len(end_match)} matches')

    print('Finished')
    await db.Database().close()

async def update():
    matchIds = (await db.Database().query_finished())
    result = await db.Database().query_players(*matchIds)
    r = {}
    for matchId, profileId in result:
        r[matchId] = profileId
    matches, records = [], []
    for matchId, profileId in r.items():
        if profileId is None:
            continue
        try:
            (length, result), _ = await asyncio.gather(api.query_match_result(matchId, profileId), asyncio.sleep(1))
            if length is None:
                length = -1
            matches.append((matchId, length))
            records.extend([{'_' + k: v for k, v in _.items()} for _ in result])
        except:
            matches.append((matchId, -1))

        print(len(matches), len(records))
    if matches:
        await db.Database().complete_matches(*matches)
    if records:
        await db.Database().update_players(records)

    await db.Database().close()

async def main():
    # Unused infinite loop
    while True:
        await asyncio.gather(one_step(), asyncio.sleep(120))

if __name__ == '__main__':
    if os.environ.get('ci', False):
        asyncio.run(one_step())
    if os.environ.get('fc', False):
        asyncio.run(update())
