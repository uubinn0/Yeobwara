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
        "kubectl", "exec", pod_name, "-n", "agent-env", "--", 
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