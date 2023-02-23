import asyncio
from typing import Set

from . import api, db


async def query_and_update(matchId: int, profileId: int):
    result = await api.query_match_result(matchId, profileId)
    await db.Database().update_matches(matchId)
    await asyncio.sleep(0.5)
    await db.Database().update_players([{'_' + k: v for k, v in _.items()} for _ in result])

async def one_step(ongoing_match_id: Set[int]):
    while True:
        current = await api.get_ongoing_matches()
        current_match_id = {_['matchId'] for _ in current}
        new_match = [
            _ for _ in current
            if _['matchId'] in current_match_id - ongoing_match_id
        ]
        print(len(new_match))
        end_match = list(ongoing_match_id - current_match_id)
        new_match_players = []
        for _ in new_match:
            new_match_players.extend([
                dict(matchId=_['matchId'], **player)
                for player in _['players']
            ])
            del _['players']

        print(new_match_players[0])
        await db.Database().insert_new_matches(new_match)
        await asyncio.sleep(5)
        await db.Database().insert_new_players(new_match_players)
        await asyncio.sleep(5)
        print(f'Added {len(new_match)} matches')
        print(f'Added {len(new_match_players)} players')

        if ongoing_match_id:
            r = await asyncio.gather(*map(db.Database().query_one_player, end_match))
            for matchId, profileId in zip(end_match, r):
                try:
                    await query_and_update(matchId, profileId)
                    await asyncio.sleep(1 )
                except TypeError:
                    current_match_id.add(matchId)

        return current_match_id

async def main():
    ongoing_match_id = set()
    while True:
        result, _ = await asyncio.gather(one_step(ongoing_match_id), asyncio.sleep(120))
        ongoing_match_id = set(result)

if __name__ == '__main__':
    print(asyncio.run(main()))
