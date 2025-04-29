from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from models.mcp_nosql import MCPCreate, MCPUpdate
from routers.nosql_auth import get_current_user, get_admin_user
import crud.nosql as nosql_crud

router = APIRouter(
    prefix="/mcps",
    tags=["MCP"],
    responses={404: {"description": "Not found"}}
)

@router.post("/", response_model=Dict[str, Any])
async def create_mcp(mcp: MCPCreate, _: dict = Depends(get_admin_user)):
    """새 MCP를 생성합니다. (관리자 권한 필요)"""
    mcp_data = await nosql_crud.create_mcp(mcp)
    if not mcp_data:
        raise HTTPException(status_code=400, detail="MCP 생성에 실패했습니다.")
    return {"success": True, "mcp_id": str(mcp_data["_id"])}

@router.get("/", response_model=List[Dict[str, Any]])
async def read_mcps():
    """모든 MCP를 조회합니다."""
    mcps = await nosql_crud.get_all_mcps()
    result = []
    for mcp in mcps:
        result.append({
            "id": str(mcp["_id"]),
            "name": mcp["name"],
            "description": mcp.get("description", ""),
            "has_manual": mcp.get("manual") is not None,
        })
    return result

@router.get("/{mcp_id}", response_model=Dict[str, Any])
async def read_mcp(mcp_id: str):
    """특정 MCP를 조회합니다."""
    mcp = await nosql_crud.get_mcp(mcp_id)
    if not mcp:
        raise HTTPException(status_code=404, detail="MCP를 찾을 수 없습니다.")
    
    return {
        "id": str(mcp["_id"]),
        "name": mcp["name"],
        "description": mcp.get("description", ""),
        "manual": mcp.get("manual"),
        "script": mcp.get("script"),
        "created_at": mcp.get("created_at", "").isoformat() if mcp.get("created_at") else None,
        "updated_at": mcp.get("updated_at", "").isoformat() if mcp.get("updated_at") else None
    }

@router.put("/{mcp_id}", response_model=Dict[str, Any])
async def update_mcp(mcp_id: str, mcp_data: MCPUpdate, _: dict = Depends(get_admin_user)):
    """MCP 정보를 업데이트합니다. (관리자 권한 필요)"""
    success = await nosql_crud.update_mcp(mcp_id, mcp_data)
    if not success:
        raise HTTPException(status_code=404, detail="MCP를 찾을 수 없습니다.")
    return {"success": True}

@router.delete("/{mcp_id}", response_model=Dict[str, Any])
async def delete_mcp(mcp_id: str, _: dict = Depends(get_admin_user)):
    """MCP를 삭제합니다. (관리자 권한 필요)"""
    success = await nosql_crud.delete_mcp(mcp_id)
    if not success:
        raise HTTPException(status_code=404, detail="MCP를 찾을 수 없습니다.")
    return {"success": True}
