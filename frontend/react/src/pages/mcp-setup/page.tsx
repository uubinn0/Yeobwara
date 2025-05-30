import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useNavigate } from "react-router-dom"
import { Save, X, ArrowLeft, Loader2, Info } from "lucide-react"
import "@/styles/globals.css"
import ServiceIcon from "@/components/ServiceIcon"
import { fetchMcpServices, saveMcpServiceSettings, toggleMcpSelection, createPod, fetchEnvironmentVariablesByService } from "@/api/mcpService"
import { McpService, McpServiceResponse } from "@/types/mcp"
import { showToast } from '../../utils/toast'

export default function McpSetupPage() {
  const navigate = useNavigate()
  const [selectedService, setSelectedService] = useState<McpService | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [podLoading, setPodLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dialogLoading, setDialogLoading] = useState(false)

  // MCP 서비스 목록
  const [services, setServices] = useState<McpService[]>([])

  // API에서 MCP 서비스 목록 가져오기
  useEffect(() => {
    const getMcpServices = async () => {
      try {
        setLoading(true)
        // API에서 서비스 목록 가져오기
        const servicesData = await fetchMcpServices()
        
        if (!servicesData || servicesData.length === 0) {
          throw new Error("서비스 데이터를 불러오지 못했습니다.")
        }
        
        // 로컬스토리지에서 저장된 사용자 설정 불러오기 (환경변수 제외)
        const savedUserSettings = localStorage.getItem("mcpServices")
        const userSettings = savedUserSettings ? JSON.parse(savedUserSettings) : []
        
        // API 응답을 McpService 형태로 변환
        const formattedServices: McpService[] = servicesData.map((service: McpServiceResponse) => {
          // 로컬스토리지에 저장된 활성화 상태만 불러오기
          const savedService = Array.isArray(userSettings) ? 
            userSettings.find((s: {id: string, active: boolean}) => s.id === service.public_id) : 
            undefined
          
          // 환경변수가 없는 경우 기본적으로 활성화 상태로 설정
          const hasNoEnvVars = service.required_env_vars.length === 0;
          
          return {
            id: service.public_id,
            name: service.name,
            icon: service.mcp_type, // mcp_type을 icon으로 사용
            description: service.description, // description 추가
            active: savedService ? savedService.active : hasNoEnvVars, // 환경변수가 없으면 기본 활성화
            is_selected: service.is_selected, // 서버에서 받아온 선택 상태 그대로 사용
            required_env_vars: service.required_env_vars.map((key: string) => ({
              key,
              value: "" // 초기값은 빈 문자열로 설정, DB에서 가져옴
            }))
          }
        })
        
        setServices(formattedServices)
      } catch (err) {
        // console.error("MCP 서비스 목록 가져오기 실패:", err)
        setError("서비스 목록을 불러오는 중 오류가 발생했습니다.")
        setServices([]) // 에러 시 빈 배열로 설정
      } finally {
        setLoading(false)
      }
    }

    getMcpServices()
  }, [])

  const openServiceDialog = async (service: McpService) => {
    // console.log("openServiceDialog 호출:", service.name);
    
    // 먼저 모달을 표시하고 로딩 상태 표시
    setSelectedService(service);
    setIsDialogOpen(true);
    setDialogLoading(true);
    
    try {
      // 모달 열기 전에 해당 서비스의 최신 환경변수만 조회
      const serverEnvVars = await fetchEnvironmentVariablesByService(service.id);
      // console.log(`${service.name} 서비스의 환경변수 조회 완료:`, serverEnvVars);
      
      // 서버에서 받은 환경변수로 서비스 정보 업데이트
      const updatedService = {
        ...service,
        required_env_vars: service.required_env_vars.map((env: { key: string; value: string }) => {
          const serverValue = serverEnvVars[env.key];
          // console.log(`환경변수 ${env.key}:`, serverValue || "값 없음");
          return {
            key: env.key,
            value: serverValue || env.value // 서버 값이 있으면 사용, 없으면 기존 값 유지
          };
        })
      };
      
      setSelectedService(updatedService);
    } catch (error) {
      // console.error(`${service.name} 서비스 환경변수 불러오기 실패:`, error);
      // 오류 발생 시 알림
      showToast.error("환경변수를 불러오는데 실패했습니다. \n다시 시도해주세요.");
    } finally {
      setDialogLoading(false);
    }
  };

  // 서비스 선택 상태 변경
  const handleToggleSelection = async (e: React.MouseEvent | null, service: McpService) => {
    // 이벤트 전파 중지 (openServiceDialog가 호출되지 않도록) - 이벤트가 있는 경우만
    if (e) {
      e.stopPropagation();
    }
    
    // console.log("handleToggleSelection 호출:", service.name);
    
    // 환경변수가 없는 경우 항상 선택 가능
    const hasNoEnvVars = service.required_env_vars.length === 0;
    
    // 현재 선택 상태 저장
    const currentSelected = service.is_selected;
    
    // 환경변수가 없는 경우 바로 토글
    if (hasNoEnvVars) {
      try {
        // 토글 API 호출 - 현재 선택 상태의 반대 값으로 변경
        const newSelectedState = await toggleMcpSelection(service.id, currentSelected);
        
        // 서비스 목록 업데이트
        const updatedServices = services.map(s => 
          s.id === service.id ? { ...s, is_selected: newSelectedState } : s
        );
        
        setServices(updatedServices);
        
        // 로컬 스토리지에는 환경변수를 제외한 필수 정보만 저장
        const simplifiedServices = updatedServices.map(s => ({
          id: s.id,
          active: s.active
        }));
        localStorage.setItem("mcpServices", JSON.stringify(simplifiedServices));
      } catch (err) {
        // console.error("MCP 선택 상태 변경 실패:", err);
        showToast.error("서비스 선택 상태 변경에 실패했습니다.");
      }
      return;
    }
    
    // 환경변수가 필요한 경우, 서버에서 최신 환경변수 조회
    try {
      // 서비스 선택 전에 최신 환경변수 다시 조회
      // console.log("환경변수 다시 조회 중...");
      const serverEnvVars = await fetchEnvironmentVariablesByService(service.id);
      
      // 조회된 환경변수로 서비스 정보 업데이트
      const updatedEnvVars = service.required_env_vars.map((env: { key: string; value: string }) => {
        const serverValue = serverEnvVars[env.key];
        return {
          key: env.key,
          value: serverValue || "" // 서버 값이 있으면 사용, 없으면 빈 문자열로 설정
        };
      });
      
      // 모든 환경변수가 입력되었는지 확인
      const hasAllEnvVars = updatedEnvVars.every((env: { key: string; value: string }) => env.value.trim() !== "");
      
      // 환경변수가 모두 입력된 경우 토글 가능
      if (hasAllEnvVars) {
        try {
          // 토글 API 호출
          const newSelectedState = await toggleMcpSelection(service.id, currentSelected);
          
          // 서비스 목록 업데이트 - 최신 환경변수와 선택 상태 반영
          const updatedServices = services.map(s => 
            s.id === service.id ? { 
              ...s, 
              is_selected: newSelectedState,
              required_env_vars: updatedEnvVars,
              active: true // 환경변수가 모두 있으므로 활성화 상태로 변경
            } : s
          );
          
          setServices(updatedServices);
          
          // 로컬 스토리지에는 환경변수를 제외한 필수 정보만 저장
          const simplifiedServices = updatedServices.map(s => ({
            id: s.id,
            active: s.active
          }));
          localStorage.setItem("mcpServices", JSON.stringify(simplifiedServices));
        } catch (err) {
          // console.error("MCP 선택 상태 변경 실패:", err);
          showToast.error("서비스 선택 상태 변경에 실패했습니다.");
        }
      } else {
        // 환경변수가 없거나 불완전한 경우 모달 열기
        showToast.error("서비스를 선택하기 전에 모든 환경변수를 입력해주세요.");
        
        // 최신 환경변수로 업데이트된 서비스 정보로 모달 열기
        const serviceWithUpdatedEnvVars = {
          ...service,
          required_env_vars: updatedEnvVars
        };
        
        setSelectedService(serviceWithUpdatedEnvVars);
        setIsDialogOpen(true);
      }
    } catch (error) {
      // console.error(`${service.name} 서비스 환경변수 불러오기 실패:`, error);
      showToast.error("환경변수를 불러오는데 실패했습니다. \n다시 시도해주세요.");
    }
  };

  const handleSaveEnvVars = async () => {
    if (!selectedService) return;

    // 모든 환경변수가 입력되었는지 확인
    const allEnvVarsComplete = selectedService.required_env_vars
      .every((ev: { key: string; value: string }) => ev.value.trim() !== "");

    // 서비스 활성화 상태 업데이트 - 모든 환경변수가 입력된 경우에만 활성화
    const updatedService = { 
      ...selectedService, 
      active: allEnvVarsComplete 
    };
    
    // 환경변수가 없는데 현재 is_selected가 true라면 false로 변경
    if (!allEnvVarsComplete && updatedService.is_selected) {
      try {
        // 선택 해제 API 호출
        await toggleMcpSelection(updatedService.id, true);
        updatedService.is_selected = false;
      } catch (err) {
        // console.error("서비스 선택 상태 해제 실패:", err);
      }
    }
    
    // 전체 서비스 목록 업데이트
    const updatedServices = services.map((service) => 
      service.id === updatedService.id ? updatedService : service
    );
    
    try {
      // API를 통해 환경변수 저장 (DB에만 저장됨)
      // 수정된 API에서는 active 상태와 관계없이 모든 환경변수를 저장함
      await saveMcpServiceSettings([updatedService]);
      
      // 로컬 스토리지에는 환경변수를 제외한 필수 정보만 저장
      const simplifiedServices = updatedServices.map(s => ({
        id: s.id,
        active: s.active
      }));
      localStorage.setItem("mcpServices", JSON.stringify(simplifiedServices));
      
      // 상태 업데이트
      setServices(updatedServices);
      
      showToast.success(`${updatedService.name} 서비스 설정이 저장되었습니다.`);
    } catch (err) {
      // console.error("환경변수 설정 저장 실패:", err);
      
      // API 저장 실패해도 UI에는 반영
      setServices(updatedServices);
      
      // 실패해도 로컬에는 활성화 상태만 저장
      const simplifiedServices = updatedServices.map(s => ({
        id: s.id,
        active: s.active
      }));
      localStorage.setItem("mcpServices", JSON.stringify(simplifiedServices));
      
      showToast.error(`서버 저장에 실패했지만 설정은 적용되었습니다.`);
    } finally {
      setLoading(false);
      setIsDialogOpen(false);
    }
  }

  const handleEnvVarChange = (index: number, value: string) => {
    if (!selectedService) return

    const updatedEnvVars = [...selectedService.required_env_vars]
    updatedEnvVars[index] = { ...updatedEnvVars[index], value }

    setSelectedService({
      ...selectedService,
      required_env_vars: updatedEnvVars,
    })
  }

  const handleCreatePod = async () => {
    try {
      setPodLoading(true); // Pod 생성 로딩 상태 시작
      
      // 선택된 서비스가 있는지 확인
      const selectedServices = services.filter(service => service.is_selected);
      
      // 선택된 서비스가 없어도 진행 가능 (0개 선택 가능하도록 수정)
      // console.log(`선택된 서비스 수: ${selectedServices.length}개`);
      
      // 선택된 서비스의 최신 환경변수 상태를 서버에서 다시 조회
      let updatedServices = [...services];
      let hasIncompleteEnvVars = false;
      let incompleteServiceNames: string[] = [];
      
      // 선택된 서비스만 검사
      for (const service of selectedServices) {
        // 환경변수가 없는 서비스는 검사하지 않음
        if (service.required_env_vars.length === 0) continue;
        
        try {
          // console.log(`${service.name} 서비스의 환경변수 다시 조회 중...`);
          const serverEnvVars = await fetchEnvironmentVariablesByService(service.id);
          
          // 환경변수 업데이트
          const updatedEnvVars = service.required_env_vars.map((env: { key: string; value: string }) => {
            // 서버에 저장된 값 사용
            const serverValue = serverEnvVars[env.key] || "";
            return {
              key: env.key, 
              value: serverValue
            };
          });
          
          // 모든 환경변수가 입력되었는지 확인
          const allEnvVarsComplete = updatedEnvVars.every((env: { key: string; value: string }) => 
            env.value.trim() !== ""
          );
          
          // 환경변수가 불완전하면 기록
          if (!allEnvVarsComplete) {
            hasIncompleteEnvVars = true;
            incompleteServiceNames.push(service.name);
          }
          
          // 서비스 업데이트
          updatedServices = updatedServices.map(s => 
            s.id === service.id ? {
              ...s,
              required_env_vars: updatedEnvVars,
              active: allEnvVarsComplete
            } : s
          );
        } catch (error) {
          // console.error(`${service.name} 서비스 환경변수 조회 실패:`, error);
          // 오류가 발생한 경우도 불완전한 것으로 처리
          hasIncompleteEnvVars = true;
          incompleteServiceNames.push(`${service.name} (조회 실패)`);
        }
      }
      
      // 상태 업데이트
      setServices(updatedServices);
      
      // 환경변수가 불완전한 서비스가 있는 경우
      if (hasIncompleteEnvVars) {
        const serviceNames = incompleteServiceNames.join(", ");
        showToast.error(`다음 서비스의 모든 환경변수를 입력해주세요: ${serviceNames}`);
        setPodLoading(false);
        return;
      }

      // POD 생성 API 호출 - 선택된 MCP 서비스로 POD 생성
      await createPod();
      
      // 로컬 스토리지에는 환경변수를 제외한 필수 정보만 저장
      const simplifiedServices = updatedServices.map(s => ({
        id: s.id,
        active: s.active
      }));
      localStorage.setItem("mcpServices", JSON.stringify(simplifiedServices));
      
      // 채팅 페이지로 이동
      navigate("/chat");
    } catch (err) {
      // console.error("POD 생성 실패:", err);
      
      // 오류 메시지 표시
      showToast.error("POD 생성에 실패했습니다. \n다시 시도해주세요.");
    } finally {
      setPodLoading(false); // Pod 생성 로딩 상태 종료
    }
  }

  return (
    <div className="min-h-screen bg-black flex flex-col items-center p-4 sm:p-6">
      {/* 별 배경 */}
      <div className="absolute inset-0 z-0">
        <div className="stars"></div>
        <div className="twinkling"></div>
      </div>

      {/* 스크롤바 스타일 */}
      <style dangerouslySetInnerHTML={{
        __html: `
          /* 스크롤바 스타일 */
          ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }
          
          ::-webkit-scrollbar-track {
            background: rgba(31, 31, 35, 0.5);
            border-radius: 10px;
          }
          
          ::-webkit-scrollbar-thumb {
            background: linear-gradient(to bottom, rgba(139, 92, 246, 0.6), rgba(124, 58, 237, 0.7));
            border-radius: 10px;
            border: 2px solid rgba(31, 31, 35, 0.1);
          }
          
          ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(to bottom, rgba(139, 92, 246, 0.8), rgba(124, 58, 237, 0.9));
          }

          /* Firefox에 대한 스크롤바 */
          * {
            scrollbar-width: thin;
            scrollbar-color: rgba(139, 92, 246, 0.6) rgba(31, 31, 35, 0.5);
          }
          
          /* 스크롤 가능한 요소에 오른쪽 패딩 추가 */
          .overflow-y-auto, .overflow-x-auto {
            padding-right: 8px;
          }
        `
      }} />

      {/* 채팅으로 돌아가기 버튼 */}
      <Button 
        variant="ghost" 
        className="fixed top-4 left-4 text-white hover:bg-gray-800 z-50 px-3 py-2 flex items-center"
        onClick={() => navigate("/chat")}
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        <span>채팅으로 돌아가기</span>
      </Button>

      <div className="w-full max-w-4xl z-10 pt-12">
        <Card className="bg-black/60 border border-gray-800 backdrop-blur-lg">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-white">MCP 서비스 설정</CardTitle>
            <CardDescription className="text-gray-400">
              사용할 서비스를 선택하고 필요한 환경변수를 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center items-center p-12">
                <Loader2 className="h-8 w-8 text-purple-500 animate-spin" />
                <span className="ml-3 text-white">MCP 서비스 목록을 불러오는 중...</span>
              </div>
            ) : podLoading ? (
              <div className="flex justify-center items-center p-12">
                <Loader2 className="h-8 w-8 text-purple-500 animate-spin" />
                <span className="ml-3 text-white">환경변수 저장 중...</span>
              </div>
            ) : error ? (
              <div className="text-center p-6 text-red-400">{error}</div>
            ) : (
              <div className="grid grid-cols-4 gap-4 mb-6 max-h-[50vh] overflow-y-auto pr-2">
                {services.map((service) => (
                  <div
                    key={service.id}
                    onClick={() => {
                      // console.log("서비스 카드 클릭:", service.name);
                      openServiceDialog(service);
                    }}
                    className={`
                      flex flex-col items-center justify-center p-4 rounded-lg border border-gray-700 
                      cursor-pointer transition-all duration-200 hover:border-gray-500 relative
                      ${service.is_selected 
                        ? "bg-gray-800/40 border-purple-500" 
                        : (service.active || service.required_env_vars.length === 0)
                          ? "bg-gray-800/40" 
                          : "bg-gray-900/30"}
                    `}
                  >
                    {/* 선택 토글 스위치 */}
                    <div 
                      className="absolute top-2 right-2 cursor-pointer"
                      onClick={(e) => {
                        // 이벤트 전파 중지 - 부모의 onClick이 실행되지 않도록 함
                        e.stopPropagation();
                        // console.log("토글 스위치 클릭");
                        handleToggleSelection(e, service);
                      }}
                    >
                      <div className={`
                        w-10 h-5 rounded-full transition-all duration-200 flex items-center px-0.5
                        ${service.is_selected 
                          ? "bg-gradient-to-r from-indigo-500 to-purple-600" 
                          : "bg-gray-600"}
                      `}>
                        <div className={`
                          w-4 h-4 bg-white rounded-full shadow-md transform transition-transform duration-200
                          ${service.is_selected ? "translate-x-5" : ""}
                        `}></div>
                      </div>
                    </div>
                    
                    <div
                      className={`w-16 h-16 flex items-center justify-center rounded-full mb-3 ${
                        service.is_selected 
                          ? "bg-gradient-to-r from-indigo-500 to-purple-600" 
                          : (service.active || service.required_env_vars.length === 0)
                            ? "bg-gray-700" 
                            : "bg-gray-800"
                      }`}
                    >
                      <ServiceIcon name={service.icon} active={service.is_selected || service.active || service.required_env_vars.length === 0} />
                    </div>
                    <span className={`text-sm font-medium ${
                      service.is_selected 
                        ? "text-white" 
                        : (service.active || service.required_env_vars.length === 0)
                          ? "text-gray-200" 
                          : "text-gray-400"
                    }`}>
                      {service.name}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {!loading && !podLoading && !error && (
              <div className="flex justify-end">
                <Button
                  onClick={handleCreatePod}
                  className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
                  disabled={podLoading}
                >
                  <Save className="mr-2 h-4 w-4" />
                  저장하고 계속하기
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 환경변수 입력 다이얼로그 */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-gray-900 text-white border-gray-700 w-[580px] max-w-[90vw] mx-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center">
              {selectedService && (
                <>
                  <ServiceIcon name={selectedService.icon} active={true} className="mr-2 h-5 w-5" />
                  {selectedService.name} 환경변수 설정
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="ml-2 h-5 w-5">
                          <Info className="h-4 w-4 text-gray-400" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent className="max-w-[300px] p-4 bg-gray-800 border border-gray-700">
                        <p className="text-sm text-gray-300">
                          환경변수는 서비스가 정상적으로 작동하기 위해 필요한 설정값입니다.
                          {selectedService?.icon === 'notion' ? (
                            <>
                              각 환경변수에 대한 자세한 설명은{" "}
                              <a 
                                href="https://www.notion.so/nimoot/Notion-1ee5a5a7520d802a91e4d790e5af9e49?pvs=4"
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-purple-400 hover:text-purple-300 underline"
                              >
                                Notion 서비스 문서
                              </a>
                              를 참고해주세요.
                            </>
                          ) : selectedService?.icon === 'gitlab' ? (
                            <>
                              각 환경변수에 대한 자세한 설명은{" "}
                              <a 
                                href="https://www.notion.so/nimoot/Gitlab-1f15a5a7520d806fb059e37af9d895ef?pvs=4"
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-purple-400 hover:text-purple-300 underline"
                              >
                                GitLab 서비스 문서
                              </a>
                              를 참고해주세요.
                            </>
                          ) : selectedService?.icon === 'kakao-map' ? (
                            <>
                              각 환경변수에 대한 자세한 설명은{" "}
                              <a 
                                href="https://www.notion.so/Kakao-Map-1f53218fb43580dfa486f6589843fb83"
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-purple-400 hover:text-purple-300 underline"
                              >
                                카카오맵 서비스 문서
                              </a>
                              를 참고해주세요.
                            </>
                          ) : selectedService?.icon === 'figma' ? (
                            <>
                              각 환경변수에 대한 자세한 설명은{" "}
                              <a 
                                href="https://www.notion.so/Figma-1f93218fb43580d89b19e7936920635d"
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-purple-400 hover:text-purple-300 underline"
                              >
                                Figma 서비스 문서
                              </a>
                              를 참고해주세요.
                            </>
                          ) : selectedService?.icon === 'dart-mcp' ? (
                            <>
                              각 환경변수에 대한 자세한 설명은{" "}
                              <a 
                                href="https://www.notion.so/Dart-1f93218fb43580a7a8b5f444ca43a017"
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-purple-400 hover:text-purple-300 underline"
                              >
                                DART 서비스 문서
                              </a>
                              를 참고해주세요.
                            </>
                          ) : (
                            "각 환경변수에 대한 자세한 설명은 서비스 문서를 참고해주세요."
                          )}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </>
              )}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {selectedService?.description && (
              <div className="text-gray-400 text-sm bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                {selectedService.description}
              </div>
            )}
            
            {dialogLoading ? (
              <div className="flex justify-center items-center py-8">
                <Loader2 className="h-6 w-6 text-purple-500 animate-spin" />
                <span className="ml-3 text-white">{selectedService?.name} 서비스의 환경변수를 불러오는 중...</span>
              </div>
            ) : (
              selectedService?.required_env_vars.map((envVar: {key: string, value: string}, index: number) => (
                <div key={envVar.key} className="space-y-2">
                  <label htmlFor={envVar.key} className="text-sm font-medium text-gray-300 block mb-2">
                    {envVar.key}
                  </label>
                  <Input
                    id={envVar.key}
                    value={envVar.value}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleEnvVarChange(index, e.target.value)}
                    placeholder={`${envVar.key} 값을 입력하세요`}
                    className="bg-gray-800 border-gray-700 text-white"
                    required
                  />
                </div>
              ))
            )}
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setIsDialogOpen(false)}>
              <X className="mr-2 h-4 w-4" />
              취소
            </Button>
            {selectedService?.required_env_vars.length > 0 && (
              <Button onClick={handleSaveEnvVars}>
                <Save className="mr-2 h-4 w-4" />
                저장
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}