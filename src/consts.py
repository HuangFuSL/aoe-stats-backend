from sqlalchemy import ForeignKey, Table, Column, Integer, MetaData, SmallInteger, Boolean, DateTime

# NETWORK

RETRY_COUNT = 3
STRING_URL = 'https://aoe2.net/api/strings?game=aoe2de&language=en'
ONGOING_MATCH_URL = 'https://aoe2.net/matches/aoe2de/ongoing'
MATCH_RESULT_URL = 'https://api.ageofempires.com/api/v2/AgeII/GetMPMatchDetail'

# FIELDS

UNUSED_MATCH_FIELDS = (
    'matchHtml', 'id', 'name', 'numPlayers', 'numSlots', 'status', 'full',
    'isLobby', 'gameType', 'leaderboard', 'ranked', 'numSpectators', 'opened',
    'appId', 'server'
)
UNUSED_PLAYER_FIELDS = (
    'slotType', 'avatarmedium', 'avatar', 'avatarfull', 'steamId', 'clan',
    'countryCode', 'civName', 'name'
)

# DATABASE

CONNECT_STR = 'postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>'

m = MetaData()
MATCH_TABLE = Table(
    'match',
    m,
    Column('matchId', Integer, primary_key=True, nullable=False),
    Column('averageRating', Integer, nullable=True),
    Column('gameTypeId', SmallInteger, nullable=True),
    Column('locationId', SmallInteger, nullable=True),
    Column('mapSizeId', SmallInteger, nullable=True),
    Column('ratingTypeId', SmallInteger, nullable=True),
    Column('resourcesId', SmallInteger, nullable=True),
    Column('startingAgeId', SmallInteger, nullable=True),
    Column('started', DateTime, nullable=True),
    Column('ended', Boolean, nullable=False),
    Column('solo', Boolean, nullable=False)
)
MATCH_PLAYER_TABLE = Table(
    'matchplayers',
    m,
    Column('matchId', ForeignKey('match.matchId'), primary_key=True, nullable=False),
    Column('profileId', Integer, primary_key=True, nullable=False),
    Column('slot', SmallInteger, nullable=True),
    Column('rating', Integer, nullable=True),
    Column('color', SmallInteger, nullable=True),
    Column('team', SmallInteger, nullable=True),
    Column('civ', SmallInteger, nullable=False),
    Column('result', Boolean, nullable=True)
)
