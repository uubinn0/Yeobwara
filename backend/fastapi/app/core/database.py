from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

# MongoDB 연결 설정
MONGO_URI = settings.MONGODB_URL
DATABASE_NAME = settings.DATABASE_NAME

# 동기식 클라이언트
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# 비동기식 클라이언트
async_client = AsyncIOMotorClient(MONGO_URI)
async_db = async_client[DATABASE_NAME]

# 컬렉션 정의
users_collection = db["users"]
async_users_collection = async_db["users"]

# MCP 관련 컬렉션
mcps_collection = db["mcps"]
async_mcps_collection = async_db["mcps"]

mcp_manuals_collection = db["mcp_manuals"]
async_mcp_manuals_collection = async_db["mcp_manuals"]

mcp_scripts_collection = db["mcp_scripts"]
async_mcp_scripts_collection = async_db["mcp_scripts"]

envs_collection = db["envs"]
async_envs_collection = async_db["envs"]

select_mcps_collection = db["select_mcps"]
async_select_mcps_collection = async_db["select_mcps"]

# 인덱스 생성 함수
async def create_indexes():
    # mcp_manuals, mcp_scripts의 mcp_id에 유니크 인덱스 생성 (1:1 관계 강제)
    await async_mcp_manuals_collection.create_index("mcp_id", unique=True)
    await async_mcp_scripts_collection.create_index("mcp_id", unique=True)
    
    # envs의 user_id+mcp_id에 복합 인덱스 생성
    await async_envs_collection.create_index([("user_id", 1), ("mcp_id", 1)], unique=True)
    
    # select_mcps의 user_id+mcp_id에 복합 인덱스 생성
    await async_select_mcps_collection.create_index([("user_id", 1), ("mcp_id", 1)], unique=True)
