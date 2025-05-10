import api from './api';
import { McpServiceResponse } from '../types/mcp';
// import axios from 'axios';

// MCP 서비스 목록 조회 API
export const fetchMcpServices = async (): Promise<McpServiceResponse[]> => {
  try {
    const response = await api.get('/mcps');
    // const response = await axios.get('https://k12b107.p.ssafy.io/api/mcps');
    return response.data as McpServiceResponse[];
  } catch (error) {
    console.error('MCP 서비스 API 호출 실패:', error);
    return []; // 에러 발생 시 빈 배열 반환
  }
};

// 환경변수 조회 API
export const fetchEnvironmentVariables = async (): Promise<Record<string, Record<string, string>>> => {
  try {
    const response = await api.get('/env');
    // const response = await axios.get('https://k12b107.p.ssafy.io/api/env');
    console.log('환경변수 조회 성공:', response.data);
    return response.data as Record<string, Record<string, string>>; // 타입 단언
  } catch (error) {
    console.error('환경변수 조회 실패:', error);
    return {}; // 에러 발생 시 빈 객체 반환
  }
};

// MCP 서비스 설정 저장 API
export const saveMcpServiceSettings = async (services: any[]): Promise<void> => {
  try {
    // 활성화된 서비스만 필터링
    const activeServices = services.filter(service => service.active);
    
    // 서비스가 없으면 진행하지 않음
    if (activeServices.length === 0) {
      console.warn('저장할 활성화된 서비스가 없습니다.');
      return;
    }
    
    // API 문서 형식에 맞게 데이터 변환
    const payload: { 
      public_id: string; 
      env_vars: Record<string, string>; 
    } = {
      public_id: activeServices[0].id,
      env_vars: {}
    };
    
    // 환경변수 객체로 변환
    activeServices[0].required_env_vars.forEach((env: { key: string; value: string }) => {
      payload.env_vars[env.key] = env.value;
    });
    
    // 단일 객체로 POST 요청
    console.log('저장할 환경변수 데이터:', payload);
    await api.post('/env', payload);
    // await axios.post('https://k12b107.p.ssafy.io/api/env', payload);
  } catch (error) {
    console.error('MCP 서비스 환경변수 설정 저장 실패:', error);
    throw error; // 에러를 상위로 전파
  }
};

// MCP 서비스 선택 토글 API - 선택 또는 선택 취소를 자동으로 처리
export const toggleMcpSelection = async (public_id: string, isCurrentlySelected: boolean): Promise<boolean> => {
  try {
    let response;
    
    if (isCurrentlySelected) {
      // 이미 선택된 상태라면 선택 취소
      response = await api.delete(`/select/${public_id}`);
      // response = await axios.delete(`https://k12b107.p.ssafy.io/api/select/${public_id}`);
      console.log('MCP 선택 취소 성공:', response.data);
    } else {
      // 선택되지 않은 상태라면 선택
      response = await api.post(`/select/${public_id}`);
      // response = await axios.post(`https://k12b107.p.ssafy.io/api/select/${public_id}`);
      console.log('MCP 선택 성공:', response.data);
    }
    
    return !isCurrentlySelected; // 토글된 상태 반환
  } catch (error) {
    console.error('MCP 선택 상태 변경 실패:', error);
    throw error;
  }
};

// POD 생성 API - 설정된 MCP 서비스로 POD 생성
export const createPod = async (): Promise<any> => {
  try {
    const response = await api.post('/pod');
    // const response = await axios.post('https://k12b107.p.ssafy.io/api/pod');
    console.log('POD 생성 성공:', response.data);
    return response.data;
  } catch (error) {
    console.error('POD 생성 실패:', error);
    throw error;
  }
}; 