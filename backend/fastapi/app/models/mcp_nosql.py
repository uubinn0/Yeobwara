from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

# 사용자 모델
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: Optional[uuid.UUID] = None
    is_admin: bool = False
    selected_mcps: List[Dict[str, Any]] = []
    def model_dump(self):
        return {
            "id": str(self.id) if self.id else None, 
            "username": self.username, 
            "email": self.email, 
            "is_admin": self.is_admin,
            "selected_mcps":self.selected_mcps
        }

class UserInDB(UserBase):
    id: uuid.UUID
    is_admin: bool = False
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # 사용자가 선택한 MCP 목록 (기본 정보를 포함한 객체 저장)
    selected_mcps: List[Dict[str, Any]] = []
    # 사용자의 MCP별 환경 변수 설정 (MCP ID를 키로 사용)
    env_settings: Dict[str, Dict[str, str]] = {}

# MCP 모델
class MCPBase(BaseModel):
    name: str
    description: Optional[str] = None
    mcp_type: str  # MCP 타입 (예: "notion", "gitlab" 등)

class MCPCreate(MCPBase):
    required_env_vars: Optional[List[str]] = None  # 필요한 환경변수 이름 목록

class MCPUpdate(MCPBase):
    required_env_vars: Optional[List[str]] = None

class MCP(MCPBase):
    id: uuid.UUID
    public_id: str  # 공개용 식별자
    required_env_vars: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
# MCP 환경변수 업데이트를 위한 모델
class EnvUpdate(BaseModel):
    public_id: str  # public_id 사용
    env_vars: Dict[str, str]  # 키-값 쌍으로 여러 환경변수 지원

# 인증 토큰 모델
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 채팅 메시지 스키마
class ChatRequest(BaseModel):
    message: str

# 채팅 응답 스키마
class ChatResponse(BaseModel):
    response: str
    timestamp: datetime