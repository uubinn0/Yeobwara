from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict, Any
from models.mcp_nosql import UserCreate, User, Token
from routers.nosql_auth import get_current_user, get_admin_user
from core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
import crud.nosql as nosql_crud
import os
import httpx
import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["사용자"],
    responses={401: {"description": "인증되지 않음"}}
)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """로그인하고 액세스 토큰을 발급합니다."""
    # OAuth2PasswordRequestForm은 username 필드를 사용하지만 이메일로 간주함
    user = await nosql_crud.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, # username 대신 email 사용
        expires_delta=access_token_expires
    )

        ##################### Agent Operator 호출 #####################
    # 유저별 환경변수 예시 (필요 시 수정)
    settings = await nosql_crud.get_user_settings(user["_id"])  # 없으면 빈 dict
    env_list = [
        {"name": "USER_ID", "value": str(user["_id"])},
        {"name": "FEATURES", "value": ",".join(settings.get("features", []))},
        {"name": "API_KEY", "value": settings.get("api_key", "")},
    ]

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.post(
                "http://3.35.167.118:30082/deploy",
                json={"user_id": str(user["_id"]), "env": env_list},
            )
            resp.raise_for_status()
            service_url = resp.json().get("service_url")
            logger.info(f"Agent for {user['_id']} at {service_url}")
            # 필요하다면 DB나 세션에 service_url 저장
        except Exception as e:
            logger.warning(f"Agent deploy failed for {user['_id']}: {e}")
    ##################### Agent Operator 호출 #####################
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    """새로운 사용자를 등록합니다."""
    db_user = await nosql_crud.create_user(user)
    if db_user is None:
        raise HTTPException(
            status_code=400, 
            detail="이미 사용 중인 아이디 또는 이메일입니다"
        )
    
    return {
        "id": str(db_user["_id"]), 
        "username": db_user["username"], 
        "email": db_user["email"],
        "is_admin": db_user.get("is_admin", False)
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """현재 인증된 사용자의 정보를 조회합니다."""
    return {
        "id": str(current_user["_id"]), 
        "username": current_user["username"], 
        "email": current_user["email"],
        "is_admin": current_user.get("is_admin", False)
    }

@router.delete("/me", response_model=Dict[str, Any])
async def delete_current_user(current_user: dict = Depends(get_current_user)):
    """현재 인증된 사용자를 삭제합니다."""
    user_id = str(current_user["_id"])
    success = await nosql_crud.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제 중 오류가 발생했습니다"
        )
    
    return {"success": True, "message": "사용자가 성공적으로 삭제되었습니다"}

@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user_by_id(user_id: str, _: dict = Depends(get_admin_user)):
    """특정 사용자를 삭제합니다. (관리자 권한 필요)"""
    # 사용자 존재 확인
    user = await nosql_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    success = await nosql_crud.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제 중 오류가 발생했습니다"
        )
    
    return {"success": True, "message": "사용자가 성공적으로 삭제되었습니다"}
