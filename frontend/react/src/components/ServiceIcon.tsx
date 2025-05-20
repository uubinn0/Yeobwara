// 서비스 아이콘 컴포넌트
import PaperSearchIcon from '@/assets/icons/papersearch.svg?react'
import AirbnbIcon from '@/assets/icons/airbnb.svg?react'
import NotionIcon from '@/assets/icons/notion.svg?react'
import GitlabIcon from '@/assets/icons/gitlab.svg?react'
import DuckDuckGoSearchIcon from '@/assets/icons/duckduckgo-search.svg?react'
// import DartMcpIcon from '@/assets/icons/dart-mcp.svg?react'
import FigmaIcon from '@/assets/icons/figma.svg?react'
import KakaoMapIcon from '@/assets/icons/kakaomap.svg?react'
import SpellCheckIcon from '@/assets/icons/spell-check.svg?react'
export default function ServiceIcon({ name, active, className = "h-8 w-8" }: { name: string; active: boolean; className?: string }) {
  const color = active ? "text-white" : "text-gray-500"
  
  // name 값 로깅
  console.log("ServiceIcon received name:", name)

  switch (name) {
    case "gitlab":
      return <GitlabIcon className={`${className} ${color}`} />
    case "notion":
      return <NotionIcon className={`${className} ${color}`} />
    case "duckduckgo-search":
      return <DuckDuckGoSearchIcon className={`${className} ${color}`} />
    case "korean-spell-checker":
      return <SpellCheckIcon className={`${className} ${color}`} />
    case "airbnb":
      return <AirbnbIcon className={`${className} ${color}`} />
    case "kakao-map":
      return <KakaoMapIcon className={`${className} ${color}`} />  
    case "figma":
      return <FigmaIcon className={`${className} ${color}`} />  
    case "paper-search":
      return <PaperSearchIcon className={`${className} ${color}`} />
    // case "dart-mcp":
    //   return <DartMcpIcon className={`${className} ${color}`} />  
    default:
      return (
        <svg
          className={`${className} ${color}`}
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect width="18" height="18" x="3" y="3" rx="2" />
          <path d="M12 8v8" />
          <path d="M8 12h8" />
        </svg>
      )
  }
}