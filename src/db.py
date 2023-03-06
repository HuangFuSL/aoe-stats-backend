import asyncio
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, bindparam, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

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
            cls._insert_pool = None
            cls._queue = None
        return cls._instance

    @property
    def queue(self):
        if self._queue is None:
            self._queue = asyncio.Queue()
        return self._queue

    @property
    def engine(self):
        if self._engine is None:
            self._engine = self.connect()
        return self._engine
    
    async def conn(self):
        if self._conn is None:
            self._conn = await self.engine.connect()
        self._insert_pool = asyncio.create_task(self.insert_pool(self.queue))
        return self._conn

    async def insert_pool(self, queue: asyncio.Queue):
        conn = await self.conn()
        while True:
            stmt = await queue.get()
            if stmt is None:
                break
            try:
                await conn.execute(*stmt)
            except IntegrityError:
                await conn.rollback()
            else:
                await conn.commit()

    async def execute(self, *stmt):
        await self.queue.put(stmt)

    async def insert_new_matches(self, data: List[Dict[str, Any]]):
        for row in data:
            row['ended'] = False
            await self.execute(insert(consts.MATCH_TABLE).values(**row))

    async def update_matches(self, *args: int):
        for matchId in args:
            await self.execute(
                update(consts.MATCH_TABLE)
                .where(consts.MATCH_TABLE.c.matchId == matchId)
                .values(ended=True, length=None)
            )

    async def complete_matches(self, *args: Tuple[int, Optional[int]]):
        for matchId, length in args:
            await self.execute(
                update(consts.MATCH_TABLE) \
                .where(consts.MATCH_TABLE.c.matchId == matchId)
                .values(ended=True, length=length)
            )

    async def insert_new_players(self, data: List[Dict[str, Any]]):
        for row in data:
            row['result'] = None
            await self.execute(insert(consts.MATCH_PLAYER_TABLE).values(**row))

    async def update_players(self, data: List[Dict[str, Any]]):
        await self.execute(
            update(consts.MATCH_PLAYER_TABLE) \
            .where(and_(
                consts.MATCH_PLAYER_TABLE.c.matchId == bindparam('_matchId'),
                consts.MATCH_PLAYER_TABLE.c.profileId == bindparam('_profileId'),
            ))
            .values(result=bindparam('_result')),
            data
        )

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
        if self._insert_pool is not None:
            await self.queue.put(None)
            await self._insert_pool
        if self._conn is not None:
            await self._conn.close()
        await self.engine.dispose()
