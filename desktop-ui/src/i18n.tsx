import * as React from "react"

export type Language = "zh-TW" | "en"

const zh = {
  switchToEnglish: "切換至英文",
  switchToChinese: "Switch to Traditional Chinese",
  lightTheme: "切換亮色主題",
  darkTheme: "切換暗色主題",
  launcher: "啟動器",
  chooseInterface: "選擇介面",
  pickerIntro: "選擇在桌面視窗或瀏覽器操作；錄製設定與直播間清單共用。",
  desktop: "桌面版",
  desktopDescription: "獨立視窗，集中查看直播間、預覽與日誌。",
  openDesktop: "開啟桌面版",
  web: "網頁版",
  webDescription: "使用預設瀏覽器，保留分頁操作方式。",
  openWeb: "開啟網頁版",
  opening: "正在開啟…",
  localOnly: "控制介面僅於本機開放",
  starting: "正在啟動，請稍候…",
  chooseAgain: "下次啟動時仍可重新選擇",
  launcherNotReady: "啟動器尚未就緒，請稍後重試；或從 LiveRecorder.exe 開啟。",
  launchFailed: "無法啟動所選介面",
  coreRunning: "錄製核心執行中",
  coreStopped: "錄製核心未啟動",
  enabledCount: "已啟用 {enabled}/{total}",
  settings: "設定",
  addRoom: "新增直播間",
  rooms: "直播間",
  searchRooms: "搜尋名稱或網址",
  noRooms: "尚未新增直播間",
  addRoomHint: "按「新增直播間」開始設定。",
  noSearchResults: "沒有符合「{query}」的直播間。",
  selectRoomNamed: "選取 {name}",
  unnamedRoom: "未命名直播間",
  monitoringEnabled: "監看已啟用",
  paused: "已暫停",
  start: "開始",
  stop: "停止",
  roomAction: "{action} {name}",
  roomDetails: "直播間詳情",
  previewAlt: "{name} 的直播預覽",
  selectForPreview: "選擇直播間以載入預覽",
  previewUnavailable: "目前沒有可用預覽",
  previewUnsupported: "此平台暫不支援縮圖預覽",
  selectRoom: "請選擇直播間",
  notSelected: "未選取",
  roomUrl: "直播間網址",
  targetQuality: "目標畫質",
  storageFormat: "儲存格式",
  detailNote: "啟用監看不代表正在直播或錄製。預覽可能是縮圖或錄影截圖；畫質與 FPS 依來源串流而定。",
  stopThisRoom: "停止此直播",
  startThisRoom: "開始此直播",
  edit: "編輯",
  delete: "刪除",
  logs: "執行日誌",
  recordingsFolder: "錄影資料夾",
  coreRunningShort: "核心執行中",
  coreStoppedShort: "核心未啟動",
  show: "顯示",
  all: "全部",
  errors: "錯誤",
  successes: "成功",
  logCount: "{visible}/{total} 筆",
  noLogs: "尚無執行日誌。啟動直播間後，輸出會顯示在這裡。",
  noFilteredLogs: "此篩選目前沒有日誌。",
  autoScroll: "自動捲動日誌",
  clearDisplay: "清除畫面",
  deleteConfirm: "刪除直播間？",
  deleteDescription: "將從監看清單移除「{name}」。",
  thisRoom: "此直播間",
  cancel: "取消",
  deleteRoom: "刪除直播間",
  invalidUrl: "請輸入完整的直播間網址",
  roomSaved: "直播間已儲存",
  roomDeleted: "直播間已刪除",
  settingsSaved: "錄製設定已儲存",
  roomStarted: "此直播間已開始監看與錄製",
  roomStopped: "此直播間已停止錄製",
  coreStartFailed: "已啟用監看，但錄製核心未能啟動；請查看執行日誌。",
  operationFailed: "操作失敗",
  editRoom: "編輯直播間",
  roomEditorDescription: "設定直播網址、名稱與錄製畫質。",
  broadcasterName: "主播名稱",
  optional: "選填",
  targetResolution: "目標解析度",
  enableMonitoring: "啟用監看與錄製",
  monitoringHint: "錄製核心會監看此直播間",
  saveRoom: "儲存直播間",
  recordingSettings: "錄製設定",
  settingsDescription: "變更檔案格式、檢查頻率與 SOOP 登入資訊。",
  recordingStorage: "錄製與儲存",
  outputPath: "儲存路徑",
  outputPlaceholder: "留空使用預設下載資料夾",
  videoFormat: "影片格式",
  preferredFps: "偏好 FPS",
  nativeStreamHint: "畫質與 FPS 僅選擇平台提供的來源串流，不會強制轉碼。",
  monitoringNetwork: "監看與網路",
  checkInterval: "檢查間隔（秒）",
  proxyAddress: "代理地址",
  enableProxy: "啟用代理",
  proxyHint: "錄製核心將使用上方代理地址",
  soopLogin: "SOOP 登入",
  soopLoginHint: "19+ 直播可能需要",
  soopAccount: "SOOP 帳號",
  soopPassword: "SOOP 密碼",
  keepCurrent: "留空保持原值",
  credentialStatus: "目前狀態：密碼{password}，Cookie {cookie}。留空不會清除現有值。",
  configured: "已設定",
  notConfigured: "未設定",
  saveSettings: "儲存設定",
  auto: "自動",
  mp3Audio: "mp3音頻",
  m4aAudio: "m4a音頻",
} as const

type Key = keyof typeof zh

const en: Record<Key, string> = {
  switchToEnglish: "Switch to English",
  switchToChinese: "Switch to Traditional Chinese",
  lightTheme: "Switch to light theme",
  darkTheme: "Switch to dark theme",
  launcher: "Launcher",
  chooseInterface: "Choose interface",
  pickerIntro: "Use a desktop window or your browser. Recording settings and room list are shared.",
  desktop: "Desktop",
  desktopDescription: "A dedicated window for rooms, previews, and logs.",
  openDesktop: "Open desktop",
  web: "Web",
  webDescription: "Use your default browser and keep normal tab controls.",
  openWeb: "Open web UI",
  opening: "Opening…",
  localOnly: "Controls are available only on this computer",
  starting: "Starting, please wait…",
  chooseAgain: "You can choose again next time",
  launcherNotReady: "The launcher is not ready. Try again, or open LiveRecorder.exe.",
  launchFailed: "Could not open the selected interface",
  coreRunning: "Recorder core running",
  coreStopped: "Recorder core stopped",
  enabledCount: "Enabled {enabled}/{total}",
  settings: "Settings",
  addRoom: "Add room",
  rooms: "Rooms",
  searchRooms: "Search name or URL",
  noRooms: "No rooms added yet",
  addRoomHint: "Select Add room to get started.",
  noSearchResults: "No rooms match “{query}”.",
  selectRoomNamed: "Select {name}",
  unnamedRoom: "Unnamed room",
  monitoringEnabled: "Monitoring enabled",
  paused: "Paused",
  start: "Start",
  stop: "Stop",
  roomAction: "{action} {name}",
  roomDetails: "Room details",
  previewAlt: "Live preview for {name}",
  selectForPreview: "Select a room to load its preview",
  previewUnavailable: "No preview available",
  previewUnsupported: "Thumbnail preview is unavailable for this platform",
  selectRoom: "Select a room",
  notSelected: "Not selected",
  roomUrl: "Room URL",
  targetQuality: "Target quality",
  storageFormat: "File format",
  detailNote: "Monitoring enabled does not mean the stream is live or being recorded. The preview may be a thumbnail or recording frame; quality and FPS depend on the source stream.",
  stopThisRoom: "Stop this room",
  startThisRoom: "Start this room",
  edit: "Edit",
  delete: "Delete",
  logs: "Activity log",
  recordingsFolder: "Recordings folder",
  coreRunningShort: "Core running",
  coreStoppedShort: "Core stopped",
  show: "Show",
  all: "All",
  errors: "Errors",
  successes: "Success",
  logCount: "{visible}/{total} entries",
  noLogs: "No activity yet. Output appears here after a room starts.",
  noFilteredLogs: "No log entries match this filter.",
  autoScroll: "Auto-scroll logs",
  clearDisplay: "Clear display",
  deleteConfirm: "Delete room?",
  deleteDescription: "Remove “{name}” from the monitoring list.",
  thisRoom: "this room",
  cancel: "Cancel",
  deleteRoom: "Delete room",
  invalidUrl: "Enter a complete room URL",
  roomSaved: "Room saved",
  roomDeleted: "Room deleted",
  settingsSaved: "Recording settings saved",
  roomStarted: "Monitoring and recording enabled for this room",
  roomStopped: "Recording stopped for this room",
  coreStartFailed: "Monitoring was enabled, but the recorder core could not start. Check the activity log.",
  operationFailed: "Operation failed",
  editRoom: "Edit room",
  roomEditorDescription: "Set the stream URL, name, and target quality.",
  broadcasterName: "Broadcaster name",
  optional: "Optional",
  targetResolution: "Target resolution",
  enableMonitoring: "Enable monitoring and recording",
  monitoringHint: "The recorder core will monitor this room",
  saveRoom: "Save room",
  recordingSettings: "Recording settings",
  settingsDescription: "Configure file format, check interval, and SOOP sign-in.",
  recordingStorage: "Recording and storage",
  outputPath: "Save location",
  outputPlaceholder: "Leave empty for the default downloads folder",
  videoFormat: "Video format",
  preferredFps: "Preferred FPS",
  nativeStreamHint: "Quality and FPS select available source streams; the app does not force transcoding.",
  monitoringNetwork: "Monitoring and network",
  checkInterval: "Check interval (seconds)",
  proxyAddress: "Proxy address",
  enableProxy: "Enable proxy",
  proxyHint: "The recorder core will use the address above",
  soopLogin: "SOOP sign-in",
  soopLoginHint: "May be needed for 19+ streams",
  soopAccount: "SOOP username",
  soopPassword: "SOOP password",
  keepCurrent: "Leave empty to keep the current value",
  credentialStatus: "Current status: password {password}, Cookie {cookie}. Empty fields will not erase existing values.",
  configured: "set",
  notConfigured: "not set",
  saveSettings: "Save settings",
  auto: "Auto",
  mp3Audio: "MP3 audio",
  m4aAudio: "M4A audio",
}

const STORAGE_KEY = "live-recorder-language"
const LanguageContext = React.createContext<{
  language: Language
  setLanguage: (language: Language) => void
  t: (key: Key, values?: Record<string, string | number>) => string
} | null>(null)

function validLanguage(value: unknown): value is Language {
  return value === "zh-TW" || value === "en"
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = React.useState<Language>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return validLanguage(saved) ? saved : "zh-TW"
  })
  const changedLocally = React.useRef(false)

  React.useEffect(() => {
    let active = true
    fetch("/api/ui-language")
      .then((response) => response.ok ? response.json() : null)
      .then((data: { language?: unknown } | null) => {
        if (active && !changedLocally.current && validLanguage(data?.language)) {
          setLanguageState(data.language)
          localStorage.setItem(STORAGE_KEY, data.language)
        }
      })
      .catch(() => { /* The local preference remains available without the API. */ })
    return () => { active = false }
  }, [])

  React.useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  React.useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY && validLanguage(event.newValue)) setLanguageState(event.newValue)
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  const setLanguage = React.useCallback((next: Language) => {
    changedLocally.current = true
    setLanguageState(next)
    localStorage.setItem(STORAGE_KEY, next)
    void fetch("/api/ui-language", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language: next }),
    }).catch(() => { /* Keep the local setting if the server is temporarily unavailable. */ })
  }, [])

  const t = React.useCallback((key: Key, values?: Record<string, string | number>) => {
    const template = (language === "en" ? en : zh)[key]
    return values ? template.replace(/\{(\w+)\}/g, (match, name: string) =>
      Object.prototype.hasOwnProperty.call(values, name) ? String(values[name]) : match) : template
  }, [language])

  return <LanguageContext.Provider value={{ language, setLanguage, t }}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const context = React.useContext(LanguageContext)
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider")
  return context
}

export function LanguageToggle() {
  const { language, setLanguage, t } = useLanguage()
  const label = t(language === "en" ? "switchToChinese" : "switchToEnglish")
  return <button type="button" className="language-toggle" onClick={() => setLanguage(language === "en" ? "zh-TW" : "en")}
    aria-label={label} title={label}>{language === "en" ? "繁中" : "EN"}</button>
}
