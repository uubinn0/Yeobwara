import React, { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { LogOut, Settings, Send, User, Cog } from "lucide-react"
import type { McpService } from "@/types/mcp"
import api from "../../api/api"
import {
  Popover,
  PopoverContent,
  PopoverTrigger
} from "@/components/ui/popover"

// 메시지 타입 정의
interface Message {
  id: string
  content: string
  sender: "user" | "bot"
  timestamp: Date
}

export default function ChatPage() {
  const navigate = useNavigate()
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      content: "안녕하세요! 무엇을 도와드릴까요?",
      sender: "bot",
      timestamp: new Date(),
    },
  ])
  const [services, setServices] = useState<McpService[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)

  // 로컬 스토리지에서 MCP 서비스 설정 불러오기
  useEffect(() => {
    const savedServices = localStorage.getItem("mcpServices")
    if (savedServices) {
      setServices(JSON.parse(savedServices))
    }
  }, [])

  // 메시지가 추가될 때마다 스크롤 맨 아래로 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    // 사용자 메시지 추가
    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")

    // 봇 응답 시뮬레이션 (실제 구현에서는 AI 응답 로직 추가)
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: getBotResponse(input),
        sender: "bot",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, botMessage])
    }, 1000)
  }

  // 간단한 봇 응답 생성 함수 (실제 구현에서는 AI 모델 사용)
  const getBotResponse = (userInput: string): string => {
    const input = userInput.toLowerCase()

    if (input.includes("안녕") || input.includes("hello")) {
      return "안녕하세요! 오늘 기분이 어떠신가요?"
    } else if (input.includes("도움") || input.includes("help")) {
      return "저는 당신의 질문에 답변하고 도움을 드릴 수 있어요. 무엇이든 물어보세요!"
    } else if (input.includes("mcp") || input.includes("서비스")) {
      const activeServices = services
        .filter((s) => s.active)
        .map((s) => s.name)
        .join(", ")
      return activeServices
        ? `현재 활성화된 MCP 서비스: ${activeServices}`
        : "활성화된 MCP 서비스가 없습니다. MCP 설정 페이지에서 서비스를 설정해보세요."
    } else {
      return "흥미로운 질문이네요. 더 자세히 알려주실 수 있을까요?"
    }
  }

  const handleLogout = () => {
    // 실제 구현에서는 로그아웃 로직 추가
    navigate("/login")
  }

  const handleNavigateToMyPage = () => {
    navigate("/mypage")
    setSettingsOpen(false)
  }

  const handleNavigateToMcpSetup = () => {
    navigate("/mcp-setup")
    setSettingsOpen(false)
  }

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* 별 배경 */}
      <div className="absolute inset-0 z-0">
        <div className="stars"></div>
        <div className="twinkling"></div>
      </div>

      {/* 헤더 */}
      <header className="z-10 p-4 border-b border-gray-800 bg-black/60 backdrop-blur-lg">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold text-white">우주 채팅</h1>
          <div className="flex space-x-2">
            <Popover open={settingsOpen} onOpenChange={setSettingsOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white"
                >
                  <Settings className="h-5 w-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-56 bg-gray-900 border-gray-700 text-white p-0" align="end">
                <div className="flex flex-col">
                  <Button 
                    onClick={handleNavigateToMyPage}
                    variant="ghost"
                    className="flex items-center justify-start gap-2 py-2 px-3 hover:bg-gray-800 rounded-none"
                  >
                    <User className="h-5 w-5 text-purple-400" />
                    <span>마이페이지</span>
                  </Button>
                  <Button 
                    onClick={handleNavigateToMcpSetup}
                    variant="ghost"
                    className="flex items-center justify-start gap-2 py-2 px-3 hover:bg-gray-800 rounded-none"
                  >
                    <Cog className="h-5 w-5 text-purple-400" />
                    <span>MCP 설정</span>
                  </Button>
                </div>
              </PopoverContent>
            </Popover>
            <Button
              variant="outline"
              size="icon"
              onClick={handleLogout}
              className="border-gray-700 text-gray-300 hover:bg-gray-800 hover:text-white"
            >
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* 채팅 영역 */}
      <div className="flex-1 overflow-y-auto p-4 z-10">
        <div className="container mx-auto max-w-4xl">
          <div className="space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
                <Card
                  className={`max-w-[80%] p-3 ${
                    message.sender === "user"
                      ? "bg-purple-600 text-white border-purple-700"
                      : "bg-gray-800/80 text-white border-gray-700"
                  }`}
                >
                  <p>{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </Card>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* 입력 영역 */}
      <div className="p-4 border-t border-gray-800 bg-black/60 backdrop-blur-lg z-10">
        <div className="container mx-auto max-w-4xl">
          <form onSubmit={handleSendMessage} className="flex space-x-2">
            <Input
              value={input}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
              placeholder="메시지를 입력하세요..."
              className="flex-1 bg-gray-900/60 border-gray-700 text-white"
            />
            <Button
              type="submit"
              className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
            >
              <Send className="h-5 w-5" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
