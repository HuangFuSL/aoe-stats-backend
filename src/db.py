from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, bindparam, insert, select, update
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import IntegrityError

from . import consts


class Database():

    @staticmethod
    def connect():
        """ Builds the enums for the API. """
        return create_async_engine(
            consts.CONNECT_STR, echo=False, future=True,
            pool_size=200, max_overflow=50
        )

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Database, cls).__new__(cls)
            cls._engine = None
            cls._conn = None
        return cls._instance
    
    async def conn(self):
        if self._conn is None:
            self._conn = await self.engine.connect()
        return self._conn

    @property
    def engine(self):
        if self._engine is None:
            self._engine = self.connect()
        return self._engine

    async def insert_new_matches(self, data: List[Dict[str, Any]]):
        conn = await self.conn()
        for row in data:
            row['ended'] = False
            try:
                await conn.execute(insert(consts.MATCH_TABLE).values(**row))
            except IntegrityError:
                await conn.rollback()
            else:
                await conn.commit()

    async def update_matches(self, *args: int):
        conn = await self.conn()
        for matchId in args:
            await conn.execute(
                update(consts.MATCH_TABLE) \
                .where(consts.MATCH_TABLE.c.matchId == matchId)
                .values(ended=True, length=None)
            )
        await conn.commit()

    async def complete_matches(self, *args: Tuple[int, Optional[int]]):
        conn = await self.conn()
        for matchId, length in args:
            await conn.execute(
                update(consts.MATCH_TABLE) \
                .where(consts.MATCH_TABLE.c.matchId == matchId)
                .values(ended=True, length=length)
            )
        await conn.commit()

    async def insert_new_players(self, data: List[Dict[str, Any]]):
        conn = await self.conn()
        for row in data:
            try:
                row['result'] = None
                await conn.execute(insert(consts.MATCH_PLAYER_TABLE).values(**row))
            except IntegrityError:
                await conn.rollback()
            else:
                await conn.commit()

    async def update_players(self, data: List[Dict[str, Any]]):
        conn = await self.conn()
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


    async def query_finished(self) -> List[int]:
        conn = await self.conn()
        result = (await conn.execute(
            select(consts.FINISHED_MATCH_TABLE.c.matchId).limit(30)
        )).all()
        return [_[0] for _ in result]

    async def query_players(self, *matchIds: int) -> List[Tuple[int, int]]:
        conn = await self.conn()
        result = (await conn.execute(
            select(
                consts.MATCH_PLAYER_TABLE.c.matchId.distinct(),
                consts.MATCH_PLAYER_TABLE.c.profileId
            )
            .where(consts.MATCH_PLAYER_TABLE.c.matchId.in_(matchIds))
        )).all()
        return result

    async def query_ongoing_match(self):
        conn = await self.conn()
        result = (await conn.execute(
            select(consts.ONGOING_MATCH_TABLE.c.matchId).limit(2000)
        )).all()
        return {_[0] for _ in result}

    async def close(self):
        if self._conn is not None:
            await self._conn.close()
        await self.engine.dispose()
