from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime
from routers.nosql_auth import get_current_user

from models.mcp_nosql import ChatRequest, ChatResponse

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
    bot_response = "안녕하세요! 어떻게 도와드릴까요?"  # 임시 응답
    
    return {
        "response": bot_response,
        "timestamp": datetime.utcnow()
    }