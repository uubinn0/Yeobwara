import { useState } from "react"
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
import { Save, X } from "lucide-react"
import "@/styles/globals.css"
import ServiceIcon from "@/components/ServiceIcon"

// MCP 서비스 타입 정의
interface McpService {
  id: string
  name: string
  icon: string
  active: boolean
  envVars: { key: string; value: string }[]
}

export default function McpSetupPage() {
  const navigate = useNavigate()
  const [selectedService, setSelectedService] = useState<McpService | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  // MCP 서비스 목록
  const [services, setServices] = useState<McpService[]>([
    {
      id: "github",
      name: "GitHub",
      icon: "github",
      active: false,
      envVars: [
        { key: "GITHUB_TOKEN", value: "" },
        { key: "GITHUB_USERNAME", value: "" },
      ],
    },
    {
      id: "jira",
      name: "Jira",
      icon: "jira",
      active: false,
      envVars: [
        { key: "JIRA_API_TOKEN", value: "" },
        { key: "JIRA_DOMAIN", value: "" },
      ],
    },
    {
      id: "notion",
      name: "Notion",
      icon: "notion",
      active: false,
      envVars: [
        { key: "NOTION_API_KEY", value: "" },
        { key: "NOTION_WORKSPACE_ID", value: "" },
      ],
    },
    {
      id: "naver",
      name: "Naver",
      icon: "naver",
      active: false,
      envVars: [
        { key: "NAVER_CLIENT_ID", value: "" },
        { key: "NAVER_CLIENT_SECRET", value: "" },
      ],
    },
    {
      id: "google",
      name: "Google",
      icon: "google",
      active: false,
      envVars: [
        { key: "GOOGLE_API_KEY", value: "" },
        { key: "GOOGLE_CLIENT_ID", value: "" },
      ],
    },
    {
      id: "googlemaps",
      name: "Google Maps",
      icon: "map",
      active: false,
      envVars: [{ key: "GOOGLE_MAPS_API_KEY", value: "" }],
    },
  ])

  const openServiceDialog = (service: McpService) => {
    setSelectedService(service)
    setIsDialogOpen(true)
  }

  const handleSaveEnvVars = () => {
    if (!selectedService) return

    setServices(
      services.map((service) => (service.id === selectedService.id ? { ...selectedService, active: true } : service)),
    )

    setIsDialogOpen(false)
  }

  const handleEnvVarChange = (index: number, value: string) => {
    if (!selectedService) return

    const updatedEnvVars = [...selectedService.envVars]
    updatedEnvVars[index] = { ...updatedEnvVars[index], value }

    setSelectedService({
      ...selectedService,
      envVars: updatedEnvVars,
    })
  }

  const handleSaveAll = () => {
    // 실제 구현에서는 서비스 설정 저장 로직 추가
    localStorage.setItem("mcpServices", JSON.stringify(services))
    navigate("/chat")
  }

  return (
    <div className="min-h-screen bg-black flex flex-col items-center p-4 sm:p-6">
      {/* 별 배경 */}
      <div className="absolute inset-0 z-0">
        <div className="stars"></div>
        <div className="twinkling"></div>
      </div>

      <div className="w-full max-w-4xl z-10">
        <Card className="bg-black/60 border border-gray-800 backdrop-blur-lg">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-white">MCP 서비스 설정</CardTitle>
            <CardDescription className="text-gray-400">
              사용할 서비스를 선택하고 필요한 환경변수를 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
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

            <div className="flex justify-end">
              <Button
                onClick={handleSaveAll}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
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
        <DialogContent className="bg-gray-900 text-white border-gray-700">
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
            {selectedService?.envVars.map((envVar, index) => (
              <div key={envVar.key} className="space-y-2">
                <label htmlFor={envVar.key} className="text-sm font-medium text-gray-300">
                  {envVar.key}
                </label>
                <Input
                  id={envVar.key}
                  value={envVar.value}
                  onChange={(e) => handleEnvVarChange(index, e.target.value)}
                  placeholder={`${envVar.key} 값을 입력하세요`}
                  className="bg-gray-800 border-gray-700 text-white"
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