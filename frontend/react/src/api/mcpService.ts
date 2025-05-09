import api from './api';
import { McpServiceResponse } from '../types/mcp';

// MCP 서비스 목록 조회 API
export const fetchMcpServices = async (): Promise<McpServiceResponse[]> => {
  try {
    const response = await api.get('/mcps');
    return response.data as McpServiceResponse[];
  } catch (error) {
    console.error('MCP 서비스 API 호출 실패:', error);
    return []; // 에러 발생 시 빈 배열 반환
  }
};

// MCP 서비스 설정 저장 API
export const saveMcpServiceSettings = async (services: any[]): Promise<void> => {
  try {
    await api.put('/mcps', { services });
  } catch (error) {
    console.error('MCP 서비스 설정 저장 실패:', error);
    // 에러가 발생해도 계속 진행
  }
}; 