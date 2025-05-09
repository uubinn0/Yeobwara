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
import { useNavigate } from "react-router-dom"
import { Save, X, ArrowLeft, Loader2 } from "lucide-react"
import "@/styles/globals.css"
import ServiceIcon from "@/components/ServiceIcon"
import { fetchMcpServices, saveMcpServiceSettings } from "@/api/mcpService"
import { McpService, McpServiceResponse } from "@/types/mcp"

export default function McpSetupPage() {
  const navigate = useNavigate()
  const [selectedService, setSelectedService] = useState<McpService | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
        
        // 로컬스토리지에서 저장된 사용자 설정 불러오기
        const savedUserSettings = localStorage.getItem("mcpServices")
        const userSettings = savedUserSettings ? JSON.parse(savedUserSettings) : []
        
        // API 응답을 McpService 형태로 변환
        const formattedServices: McpService[] = servicesData.map((service: McpServiceResponse) => {
          const savedService = Array.isArray(userSettings) ? 
            userSettings.find((s: McpService) => s.id === service.public_id) : 
            undefined
          
          return {
            id: service.public_id,
            name: service.name,
            icon: service.mcp_type, // mcp_type을 icon으로 사용
            active: savedService ? savedService.active : false,
            required_env_vars: service.required_env_vars.map((key: string) => {
              const savedValue = savedService ? 
                savedService.required_env_vars?.find((sev: {key: string, value: string}) => sev.key === key)?.value : 
                ""
              return { key, value: savedValue || "" }
            })
          }
        })
        // console.log("MCP 서비스 목록 가져오기 성공:", formattedServices)
        setServices(formattedServices)
      } catch (err) {
        console.error("MCP 서비스 목록 가져오기 실패:", err)
        setError("서비스 목록을 불러오는 중 오류가 발생했습니다.")
        setServices([]) // 에러 시 빈 배열로 설정
      } finally {
        setLoading(false)
      }
    }

    getMcpServices()
  }, [])

  const openServiceDialog = (service: McpService) => {
    setSelectedService(service)
    setIsDialogOpen(true)
  }

  const handleSaveEnvVars = () => {
    if (!selectedService) return

    // 모든 환경변수가 입력되었는지 확인
    const allEnvVarsComplete = selectedService.required_env_vars
      .every((ev: { key: string; value: string }) => ev.value.trim() !== "");

    if (!allEnvVarsComplete) {
      // 환경변수가 입력되지 않은 경우 알림
      alert("모든 환경변수를 입력해주세요.");
      return;
    }

    setServices(
      services.map((service) => (service.id === selectedService.id ? { ...selectedService, active: true } : service)),
    )

    setIsDialogOpen(false)
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

  const handleSaveAll = async () => {
    // 모든 환경변수가 입력된 서비스만 활성화 가능
    const incompleteServices = services
      .filter(service => service.active)
      .filter(service => 
        service.required_env_vars.some((ev: { key: string; value: string }) => ev.value.trim() === "")
      );

    if (incompleteServices.length > 0) {
      const serviceNames = incompleteServices.map(s => s.name).join(", ");
      alert(`다음 서비스의 모든 환경변수를 입력해주세요: ${serviceNames}`);
      return;
    }

    try {
      // API를 통해 서비스 설정 저장
      await saveMcpServiceSettings(services)
      
      // 로컬 스토리지에도 저장
      localStorage.setItem("mcpServices", JSON.stringify(services))
      navigate("/chat")
    } catch (err) {
      console.error("MCP 서비스 설정 저장 실패:", err)
      // 실패해도 로컬에는 저장
      localStorage.setItem("mcpServices", JSON.stringify(services))
      navigate("/chat")
    }
  }

  return (
    <div className="min-h-screen bg-black flex flex-col items-center p-4 sm:p-6">
      {/* 별 배경 */}
      <div className="absolute inset-0 z-0">
        <div className="stars"></div>
        <div className="twinkling"></div>
      </div>

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
                <span className="ml-3 text-white">서비스 목록을 불러오는 중...</span>
              </div>
            ) : error ? (
              <div className="text-center p-6 text-red-400">{error}</div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
                {services.map((service) => (
                  <div
                    key={service.id}
                    onClick={() => openServiceDialog(service)}
                    className={`
                      flex flex-col items-center justify-center p-4 rounded-lg border border-gray-700 
                      cursor-pointer transition-all duration-200 hover:border-gray-500
                      ${service.active ? "bg-gray-800/50" : "bg-gray-900/30"}
                    `}
                  >
                    <div
                      className={`w-16 h-16 flex items-center justify-center rounded-full mb-3 ${service.active ? "bg-gradient-to-r from-indigo-500 to-purple-600" : "bg-gray-800"}`}
                    >
                      <ServiceIcon name={service.icon} active={service.active} />
                    </div>
                    <span className={`text-sm font-medium ${service.active ? "text-white" : "text-gray-400"}`}>
                      {service.name}
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end">
              <Button
                onClick={handleSaveAll}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
                disabled={loading}
              >
                <Save className="mr-2 h-4 w-4" />
                저장하고 계속하기
              </Button>
            </div>
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
                </>
              )}
            </DialogTitle>
            <DialogDescription className="text-gray-400">
              이 서비스를 사용하기 위해 필요한 환경변수를 입력하세요
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {selectedService?.required_env_vars.map((envVar: {key: string, value: string}, index: number) => (
              <div key={envVar.key} className="space-y-2">
                <label htmlFor={envVar.key} className="text-sm font-medium text-gray-300">
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
            ))}
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setIsDialogOpen(false)}>
              <X className="mr-2 h-4 w-4" />
              취소
            </Button>
            <Button onClick={handleSaveEnvVars}>
              <Save className="mr-2 h-4 w-4" />
              저장
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}