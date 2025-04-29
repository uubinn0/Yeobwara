from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

# 사용자 모델
class UserBase(BaseModel):
    username: str
    email: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: Optional[str] = None

    def model_dump(self):
        return {
            "id": self.id, 
            "username": self.username, 
            "email": self.email, 
            "is_admin": self.is_admin
        }

class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # 사용자가 선택한 MCP 목록 (기본 정보를 포함한 객체 저장)
    selected_mcps: List[Dict[str, Any]] = []
    # 사용자의 MCP별 환경 변수 설정 (MCP ID를 키로 사용)
    env_settings: Dict[str, Dict[str, str]] = {}

# MCP 모델 (매뉴얼과 스크립트를 내장)
class MCPBase(BaseModel):
    name: str
    description: Optional[str] = None

class MCPCreate(MCPBase):
    manual: Optional[str] = None
    script: Optional[Dict[str, Any]] = None

class MCPUpdate(MCPBase):
    manual: Optional[str] = None
    script: Optional[Dict[str, Any]] = None

class MCP(MCPBase):
    id: str
    manual: Optional[str] = None
    script: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
# MCP 환경변수 업데이트를 위한 모델
class EnvUpdate(BaseModel):
    mcp_id: str
    api_key: str

# 인증 토큰 모델
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
