import subprocess,json
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime
from routers.nosql_auth import get_current_user
from models.mcp_nosql import ChatRequest, ChatResponse
from core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["챗봇"],
    responses={404: {"description": "Not found"}}
)

@router.post("/pod")
async def create_pod(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Pod 생성 함수 호출
    from core.create_pod import create_pod as c_create_pod
    try:
        # user_id만 전달하여 Pod 생성 함수 호출
        pod_result = await c_create_pod(user_id)
        
        if pod_result.get("success", False):
            logger.info(f"Pod 생성 성공 - 사용자: {user_id}, Pod: {pod_result.get('pod_name')}")
        else:
            logger.warning(f"Pod 생성 실패 - 사용자: {user_id}, 오류: {pod_result.get('message')}")
        
        # 중요: 결과 반환
        # return pod_result
        return {
            "success": True,
            "message": pod_result["message"]
        }
    
    except Exception as e:
        # Pod 생성 오류가 로그인을 방해하지 않도록 예외 처리
        logger.error(f"Pod 생성 중 예외 발생 - 사용자: {user_id}, 오류: {str(e)}")
        return {
            "success": False,
            "message": f"Pod 생성 중 오류 발생: {str(e)}",
            "pod_name": None
        }


@router.post("/chat", response_model=ChatResponse)
async def process_chat(chat_request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """사용자의 채팅 메시지를 처리하고 응답합니다."""
    
    user_id = str(current_user["_id"])
    # TODO
    # agent와 통신하는 부분

    from crud.nosql import get_user_by_id
    user = await get_user_by_id(user_id)
    pod_name = user["pod_name"]

    cmd = [
        "kubectl", "exec", pod_name, "-n", "agent-env", "-c", "agent","--", 
        "curl", "-X", "POST", settings.AGNET_URL, 
        "-H", "Content-Type: application/json", 
        "-d", f'{{"text": "{chat_request.message}"}}'
    ]

    result = subprocess.run(cmd,capture_output=True,text=True)
    logger.info(f"테스팅 {result}")

    bot_response = "안녕하세요! 어떻게 도와드릴까요?"  # 임시 응답
    
    return {
        "response": bot_response,
        "timestamp": datetime.utcnow()
    }

