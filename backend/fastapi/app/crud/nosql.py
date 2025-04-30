from datetime import datetime
from bson import ObjectId
from typing import List, Dict, Any, Optional
from models.mcp_nosql import UserCreate, MCPCreate, MCPUpdate, EnvUpdate
from core.security import get_password_hash, verify_password
from core.database import async_db

# 컬렉션 정의
users = async_db["users_nosql"]
mcps = async_db["mcps_nosql"]

# MongoDB는 컬렉션이 없으면 자동으로 생성하므로 미리 만들 필요 없음

# 인덱스 생성 함수
async def create_nosql_indexes():
    # 사용자 인덱스
    await users.create_index("username", unique=True)
    await users.create_index("email", unique=True)
    
    # MCP 인덱스
    await mcps.create_index("name")

# ======== 사용자 관련 CRUD ========

async def get_user_by_username(username: str):
    """사용자 이름으로 사용자를 조회합니다."""
    return await users.find_one({"username": username})

async def get_user_by_email(email: str):
    """이메일로 사용자를 조회합니다."""
    return await users.find_one({"email": email})

async def get_user_by_id(user_id: str):
    """ID로 사용자를 조회합니다."""
    try:
        object_id = ObjectId(user_id)
        return await users.find_one({"_id": object_id})
    except:
        return None

async def create_user(user: UserCreate):
    """새 사용자를 생성합니다."""
    # 사용자 존재 여부 확인
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        return None
    
    # 이메일 중복 확인
    email_user = await get_user_by_email(user.email)
    if email_user:
        return None
    
    # 새 사용자 생성
    hashed_password = get_password_hash(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "selected_mcps": [],
        "env_settings": {}
    }
    
    result = await users.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return user_dict

async def authenticate_user(email: str, password: str):
    """사용자 인증을 수행합니다."""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

async def delete_user(user_id: str):
    """사용자를 삭제합니다."""
    try:
        object_id = ObjectId(user_id)
        result = await users.delete_one({"_id": object_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"사용자 삭제 중 오류 발생: {e}")
        return False

# ======== MCP 관련 CRUD ========

async def create_mcp(mcp: MCPCreate):
    """새 MCP를 생성합니다."""
    mcp_dict = {
        "name": mcp.name,
        "description": mcp.description,
        "manual": mcp.manual,
        "script": mcp.script,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await mcps.insert_one(mcp_dict)
    mcp_dict["_id"] = result.inserted_id
    return mcp_dict

async def get_mcp(mcp_id: str):
    """ID로 MCP를 조회합니다."""
    try:
        object_id = ObjectId(mcp_id)
        return await mcps.find_one({"_id": object_id})
    except:
        return None

async def get_all_mcps():
    """모든 MCP를 조회합니다."""
    return await mcps.find().to_list(length=100)

async def update_mcp(mcp_id: str, mcp_data: MCPUpdate):
    """MCP 정보를 업데이트합니다."""
    try:
        object_id = ObjectId(mcp_id)
        update_dict = {k: v for k, v in mcp_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        result = await mcps.update_one(
            {"_id": object_id},
            {"$set": update_dict}
        )
        return result.modified_count > 0
    except:
        return False

async def delete_mcp(mcp_id: str):
    """MCP를 삭제합니다."""
    try:
        object_id = ObjectId(mcp_id)
        
        # MCP 삭제
        mcp_result = await mcps.delete_one({"_id": object_id})
        
        # 사용자의 선택 목록과 환경 변수 설정에서 이 MCP 제거
        # $pull을 사용하여 선택 목록에서 제거
        await users.update_many(
            {"selected_mcps": str(object_id)},
            {"$pull": {"selected_mcps": str(object_id)}}
        )
        
        # unset을 사용하여 환경 변수 설정에서 제거
        await users.update_many(
            {f"env_settings.{str(object_id)}": {"$exists": True}},
            {"$unset": {f"env_settings.{str(object_id)}": ""}}
        )
        
        return mcp_result.deleted_count > 0
    except Exception as e:
        print(f"MCP 삭제 중 오류 발생: {e}")
        return False

# ======== MCP 선택 관련 ========

async def select_mcp_for_user(user_id: str, mcp_id: str):
    """사용자가 MCP를 선택합니다."""
    try:
        user_obj_id = ObjectId(user_id)
        
        # MCP가 존재하는지 확인
        mcp = await get_mcp(mcp_id)
        if not mcp:
            return {"success": False, "message": "MCP를 찾을 수 없습니다."}
        
        # MCP 정보를 객체로 구성 (id, name, script, script_metadata 포함)
        mcp_info = {
            "id": str(mcp["_id"]),
            "name": mcp["name"],
            "script": mcp.get("script"),
            "script_metadata": {
                "type": mcp.get("script", {}).get("type") if mcp.get("script") else None,
                "version": mcp.get("script", {}).get("version") if mcp.get("script") else None
            },
            "selected_at": datetime.utcnow()
        }
        
        # 동일한 ID의 MCP가 이미 있는지 확인하고, 있다면 제거
        await users.update_one(
            {"_id": user_obj_id},
            {"$pull": {"selected_mcps": {"id": mcp_id}}}
        )
        
        # 새 MCP 정보 추가
        result = await users.update_one(
            {"_id": user_obj_id},
            {"$push": {"selected_mcps": mcp_info}}
        )
        
        return {"success": True, "message": "MCP 선택이 완료되었습니다."}
    except Exception as e:
        print(f"MCP 선택 중 오류 발생: {e}")
        return {"success": False, "message": f"오류 발생: {str(e)}"}

async def deselect_mcp(user_id: str, mcp_id: str):
    """사용자의 MCP 선택을 취소합니다."""
    try:
        user_obj_id = ObjectId(user_id)
        
        # selected_mcps 배열에서 해당 ID를 가진 객체 제거
        result = await users.update_one(
            {"_id": user_obj_id},
            {"$pull": {"selected_mcps": {"id": mcp_id}}}
        )
        
        return result.modified_count > 0
    except Exception as e:
        print(f"MCP 선택 취소 중 오류 발생: {e}")
        return False

async def get_user_selected_mcps(user_id: str):
    """사용자가 선택한 모든 MCP를 조회합니다."""
    try:
        user = await get_user_by_id(user_id)
        if not user or "selected_mcps" not in user:
            return []
        
        # 저장된 MCP 정보 사용
        selected_mcps = user["selected_mcps"]
        if not selected_mcps:
            return []
        
        # 결과 반환 - 저장된 정보를 그대로 반환
        # 추가로 필요한 정보가 있다면 여기서 처리
        for mcp in selected_mcps:
            # 만약 추가 정보가 필요하다면 여기서 갱신 가능
            # 예: 현재 MCP의 최신 상태 정보를 붙이는 경우
            pass
        
        return selected_mcps
    except Exception as e:
        print(f"선택된 MCP 조회 중 오류 발생: {e}")
        return []

# ======== 환경 변수 관련 ========

async def update_env_var(user_id: str, env_update: EnvUpdate):
    """사용자의 MCP 환경 변수를 업데이트합니다."""
    try:
        user_obj_id = ObjectId(user_id)
        
        # MCP가 존재하는지 확인
        mcp = await get_mcp(env_update.mcp_id)
        if not mcp:
            return {"success": False, "message": "MCP를 찾을 수 없습니다."}
        
        # 환경 변수 설정 업데이트
        result = await users.update_one(
            {"_id": user_obj_id},
            {"$set": {f"env_settings.{env_update.mcp_id}": {"API_KEY": env_update.api_key}}}
        )
        
        return {"success": True, "message": "환경 변수가 업데이트되었습니다."}
    except Exception as e:
        print(f"환경 변수 업데이트 중 오류 발생: {e}")
        return {"success": False, "message": f"오류 발생: {str(e)}"}

async def get_env_vars(user_id: str, mcp_id: str = None):
    """사용자의 환경 변수를 조회합니다."""
    try:
        user = await get_user_by_id(user_id)
        if not user or "env_settings" not in user:
            return None if mcp_id else {}
        
        env_settings = user["env_settings"]
        
        # 특정 MCP에 대한 환경 변수 조회
        if mcp_id:
            return env_settings.get(mcp_id, None)
        
        # 모든 환경 변수 조회
        return env_settings
    except:
        return None if mcp_id else {}

async def delete_env_var(user_id: str, mcp_id: str):
    """사용자의 MCP 환경 변수를 삭제합니다."""
    try:
        user_obj_id = ObjectId(user_id)
        
        # 환경 변수 설정 삭제
        result = await users.update_one(
            {"_id": user_obj_id},
            {"$unset": {f"env_settings.{mcp_id}": ""}}
        )
        
        return result.modified_count > 0
    except:
        return False


#####################################################
# 정찬호 추가 crud
# crud/nosql.py ― 파일 맨 아래 “환경 변수 관련” 주석 위 or 원하는 위치
# ================================================================

async def get_user_settings(user_id: str) -> dict:
    """
    사용자가 저장해 둔 세팅(features, api_key 등)을 반환합니다.
    값이 없으면 빈 dict.
    """
    try:
        user = await get_user_by_id(user_id)
        # env_settings, selected_mcps 등 다른 키를 합치고 싶으면 여기서 병합
        return user.get("env_settings", {}) if user else {}
    except Exception as e:
        print(f"유저 세팅 조회 중 오류: {e}")
        return {}
