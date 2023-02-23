from typing import Any, Dict, List, Optional

from sqlalchemy import and_, bindparam, insert, select, update
from sqlalchemy.ext.asyncio import create_async_engine

from . import consts


class Database():

    @staticmethod
    def connect():
        """ Builds the enums for the API. """
        return create_async_engine(consts.CONNECT_STR, echo=False, future=True)

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Database, cls).__new__(cls)
            cls._engine = None
        return cls._instance

    @property
    def engine(self):
        if self._engine is None:
            self._engine = self.connect()
        return self._engine

    async def insert_new_matches(self, data: List[Dict[str, Any]]):
        for row in data:
            async with self.engine.connect() as conn:
                row['ended'] = False
                await conn.execute(insert(consts.MATCH_TABLE).values(**row))
                await conn.commit()

    async def update_matches(self, matchId: int, length: Optional[int] = None):
        async with self.engine.connect() as conn:
            await conn.execute(
                update(consts.MATCH_TABLE) \
                .where(consts.MATCH_TABLE.c.matchId == matchId)
                .values(ended=True, length=length)
            )
            await conn.commit()

    async def insert_new_players(self, data: List[Dict[str, Any]]):
        for row in data:
            async with self.engine.connect() as conn:
                row['result'] = None
                await conn.execute(insert(consts.MATCH_PLAYER_TABLE).values(**row))
                await conn.commit()

    async def update_players(self, data: List[Dict[str, Any]]):
        async with self.engine.connect() as conn:
            await conn.execute(
                update(consts.MATCH_PLAYER_TABLE) \
                .where(and_(
                    consts.MATCH_PLAYER_TABLE.c.matchId == bindparam('_matchId'),
                    consts.MATCH_PLAYER_TABLE.c.profileId == bindparam('_profileId'),
                ))
                .values(result=bindparam('_result')),
                data
            )
            await conn.commit()

    async def query_one_player(self, matchId: int):
        async with self.engine.connect() as conn:
            result = (await conn.execute(
                select(consts.MATCH_PLAYER_TABLE.c.profileId)
                .where(consts.MATCH_PLAYER_TABLE.c.matchId == matchId)
            )).fetchone()
            assert result is not None
            return result[0]

    async def query_ongoing_match(self):
        async with self.engine.connect() as conn:
            result = (await conn.execute(
                select(consts.ONGOING_MATCH_TABLE.c.matchId)
            )).all()
            return {_[0] for _ in result}

    async def close(self):
        await self.engine.dispose()