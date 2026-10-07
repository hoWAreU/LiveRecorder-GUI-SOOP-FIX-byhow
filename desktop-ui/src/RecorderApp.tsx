import { useEffect, useRef, useState, type FormEvent } from "react"
import { CircleHelp, ExternalLink, FolderOpen, Moon, Pencil, Play, Plus, Radio, Search, Settings2, Square, Sun, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useTheme } from "@/components/theme-provider"
import { api, emptyRoom, emptySettings, roomLabel, type LogLine, type Room, type RoomDraft, type SettingsDraft, type Snapshot } from "@/api"
import { RoomEditor, SettingsEditor } from "@/EditorDialogs"

type LogResponse = { logs: LogLine[]; running: boolean }

export default function RecorderApp() {
  const { theme, setTheme } = useTheme()
  const [state, setState] = useState<Snapshot | null>(null)
  const [selected, setSelected] = useState(0)
  const [roomQuery, setRoomQuery] = useState("")
  const [logs, setLogs] = useState<LogLine[]>([])
  const [logFilter, setLogFilter] = useState<"all" | "error" | "success">("all")
  const [autoScroll, setAutoScroll] = useState(true)
  const [notice, setNotice] = useState("")
  const [roomOpen, setRoomOpen] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [roomDraft, setRoomDraft] = useState<RoomDraft>(emptyRoom)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [settingsDraft, setSettingsDraft] = useState<SettingsDraft>(emptySettings)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [previewTick, setPreviewTick] = useState(0)
  const [previewFailed, setPreviewFailed] = useState(false)
  const logSince = useRef(0)
  const logEnd = useRef<HTMLDivElement>(null)

  const rooms = state?.rooms ?? []
  const selectedRoom = rooms[selected] ?? null
  const enabledCount = rooms.filter((room) => room.enabled).length
  const normalizedQuery = roomQuery.trim().toLocaleLowerCase()
  const visibleRooms = rooms.map((room, index) => ({ room, index })).filter(({ room }) =>
    !normalizedQuery || `${roomLabel(room)} ${room.url}`.toLocaleLowerCase().includes(normalizedQuery))
  const visibleLogs = logFilter === "all" ? logs : logs.filter((line) => line.level === logFilter)
  const previewSupported = !!selectedRoom && /play\.sooplive\.(com|co\.kr)\/.+\/\d+/.test(selectedRoom.url)

  function announce(message: string) {
    setNotice(message)
    window.setTimeout(() => setNotice((current) => current === message ? "" : current), 4200)
  }

  async function loadState() {
    const data = await api<Snapshot>("/api/state")
    setState(data)
    setSelected((current) => Math.max(0, Math.min(current, data.rooms.length - 1)))
  }

  useEffect(() => {
    api<Snapshot>("/api/state").then((data) => setState(data))
      .catch((error: Error) => announce(error.message))
    const previewTimer = window.setInterval(() => { setPreviewFailed(false); setPreviewTick(Date.now()) }, 15000)
    return () => window.clearInterval(previewTimer)
  }, [])

  useEffect(() => {
    let active = true
    let timer = 0
    async function refreshState() {
      try {
        const data = await api<Snapshot>("/api/state")
        if (active) {
          setState(data)
          setSelected((current) => Math.max(0, Math.min(current, data.rooms.length - 1)))
        }
      } catch { /* Retry on the next poll. */ }
      if (active) timer = window.setTimeout(refreshState, 2500)
    }
    timer = window.setTimeout(refreshState, 2500)
    return () => { active = false; window.clearTimeout(timer) }
  }, [])

  useEffect(() => {
    let active = true
    let timer = 0
    async function poll() {
      try {
        const data = await api<LogResponse>(`/api/logs?since=${logSince.current}`)
        if (!active) return
        if (data.logs.length) {
          logSince.current = Math.max(logSince.current, ...data.logs.map((line) => line.id))
          setLogs((current) => [...current, ...data.logs].slice(-700))
        }
        setState((current) => current ? { ...current, running: data.running } : current)
      } catch { /* Retry on the next poll. */ }
      if (active) timer = window.setTimeout(poll, 1200)
    }
    poll()
    return () => { active = false; window.clearTimeout(timer) }
  }, [])

  useEffect(() => {
    if (autoScroll) logEnd.current?.scrollIntoView({ block: "end" })
  }, [logs, autoScroll])

  async function controlRoom(index: number, enabled: boolean) {
    try {
      const result = await api<{ rooms: Room[]; running: boolean; message: string }>("/api/room/control", { index, enabled })
      setState((current) => current ? { ...current, rooms: result.rooms, running: result.running } : current)
      announce(result.message)
    } catch (error) { announce((error as Error).message) }
  }

  function openRoom(index: number | null) {
    setEditing(index)
    setRoomDraft(index === null ? { ...emptyRoom } : { ...rooms[index] })
    setRoomOpen(true)
  }

  async function saveRoom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!/^https?:\/\//i.test(roomDraft.url.trim())) { announce("請輸入完整的直播間網址"); return }
    const updated = rooms.map((room) => ({ ...room }))
    const item = { ...roomDraft, url: roomDraft.url.trim(), name: roomDraft.name.trim() }
    const target = editing === null ? updated.length : editing
    if (editing === null) updated.push({ ...item, id: String(target) })
    else updated[editing] = { ...updated[editing], ...item }
    try {
      const result = await api<{ rooms: Room[] }>("/api/rooms/save", { rooms: updated })
      setState((current) => current ? { ...current, rooms: result.rooms } : current)
      setSelected(target)
      setRoomQuery("")
      setPreviewFailed(false)
      setRoomOpen(false)
      if (item.enabled && !state?.running) await api("/api/recorder/start", {})
      if (!result.rooms.some((room) => room.enabled) && state?.running) await api("/api/recorder/stop", {})
      await loadState()
      announce("直播間已儲存")
    } catch (error) { announce((error as Error).message) }
  }

  async function deleteRoom() {
    if (!selectedRoom) return
    try {
      const result = await api<{ rooms: Room[] }>("/api/rooms/save", { rooms: rooms.filter((_, index) => index !== selected) })
      setState((current) => current ? { ...current, rooms: result.rooms } : current)
      setSelected(Math.max(0, selected - 1))
      setPreviewFailed(false)
      setDeleteOpen(false)
      if (!result.rooms.some((room) => room.enabled) && state?.running) await api("/api/recorder/stop", {})
      await loadState()
      announce("直播間已刪除")
    } catch (error) { announce((error as Error).message) }
  }

  function openSettings() {
    if (!state) return
    setSettingsDraft({ ...state.settings, soopPassword: "", soopCookie: "" })
    setSettingsOpen(true)
  }

  async function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      await api("/api/settings", settingsDraft)
      setSettingsOpen(false)
      await loadState()
      announce("錄製設定已儲存")
    } catch (error) { announce((error as Error).message) }
  }

  async function openDownloads() {
    try { await api("/api/open-downloads", {}) }
    catch (error) { announce((error as Error).message) }
  }

  return <div className="app-shell">
    <aside className="room-sidebar">
      <div className="brand-block"><Radio className="brand-mark" aria-hidden="true" /><div className="brand-title">LIVE RECORDER</div></div>
      <div className="sidebar-summary"><span className={`status-dot ${state?.running ? "is-active" : ""}`} /><span>{state?.running ? "錄製核心執行中" : "錄製核心未啟動"}</span><span className="ml-auto tabular-nums">已啟用 {enabledCount}/{rooms.length}</span></div>
      <div className="sidebar-actions"><Button variant="outline" onClick={openSettings}><Settings2 />設定</Button><Button onClick={() => openRoom(null)}><Plus />新增直播間</Button></div>
      <div className="sidebar-section-title"><span>直播間</span><span>{visibleRooms.length} / {rooms.length}</span></div>
      <div className="room-search"><Search aria-hidden="true" /><Input type="search" value={roomQuery} onChange={(event) => setRoomQuery(event.target.value)} placeholder="搜尋名稱或網址" aria-label="搜尋直播間" /></div>
      <ScrollArea className="room-scroll"><div className="room-items">
        {rooms.length === 0 && <div className="empty-list">尚未新增直播間<br />按「新增直播間」開始設定。</div>}
        {rooms.length > 0 && visibleRooms.length === 0 && <div className="empty-list">沒有符合「{roomQuery.trim()}」的直播間。</div>}
        {visibleRooms.map(({ room, index }) => <div className={`room-item ${selected === index ? "selected" : ""}`} key={`${room.url}-${index}`}>
          <button className="room-select" onClick={() => { setSelected(index); setPreviewFailed(false) }} aria-label={`選取 ${roomLabel(room)}`} aria-current={selected === index ? "true" : undefined}><span className={`status-dot ${room.enabled ? "is-active" : ""}`} /><span className="room-text"><strong>{roomLabel(room)}</strong><small>{room.quality} · {room.enabled ? "監看已啟用" : "已暫停"}</small></span></button>
          <Button size="xs" variant="outline" className={room.enabled ? "room-stop" : ""} onClick={() => controlRoom(index, !room.enabled)} aria-label={`${room.enabled ? "停止" : "開始"} ${roomLabel(room)}`}>
            {room.enabled ? <Square className="size-3" /> : <Play className="size-3" />}{room.enabled ? "停止" : "開始"}
          </Button>
        </div>)}
      </div></ScrollArea>
      <div className="sidebar-footer"><span>LIVE RECORDER · v0.4.1</span><Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="切換亮色或暗色主題" title="切換主題">{theme === "dark" ? <Sun /> : <Moon />}</Button></div>
    </aside>

    <main className="detail-panel">
      <div className="panel-eyebrow">直播間詳情</div>
      <div className="preview-frame">{previewSupported && !previewFailed ? <img src={`/api/preview?url=${encodeURIComponent(selectedRoom!.url)}&t=${previewTick}`} alt={`${roomLabel(selectedRoom!)} 的直播預覽`} onError={() => setPreviewFailed(true)} /> : <div className="preview-placeholder"><Radio className="size-7" /><span>{!selectedRoom ? "選擇直播間以載入預覽" : previewSupported ? "目前沒有可用預覽" : "此平台暫不支援縮圖預覽"}</span></div>}</div>
      <div className="detail-heading"><h1>{selectedRoom ? roomLabel(selectedRoom) : "請選擇直播間"}</h1><span className="detail-state"><span className={`status-dot ${selectedRoom?.enabled ? "is-active" : ""}`} />{selectedRoom ? selectedRoom.enabled ? "監看已啟用" : "已暫停" : "未選取"}</span></div>
      <Separator />
      <dl className="detail-fields"><div className="detail-field"><dt>直播間網址</dt><dd>{selectedRoom ? <a href={selectedRoom.url} target="_blank" rel="noreferrer" className="room-url">{selectedRoom.url}<ExternalLink className="size-3.5" /></a> : <span className="field-empty">—</span>}</dd></div>
        <div className="detail-field"><dt>目標畫質</dt><dd>{selectedRoom?.quality ?? "—"}</dd></div>
        <div className="detail-field"><dt>儲存格式</dt><dd>{state?.settings.format ?? "—"}</dd></div></dl>
      <div className="detail-note"><CircleHelp className="size-4" /><span>啟用監看不代表正在直播或錄製。預覽可能是縮圖或錄影截圖；畫質與 FPS 依來源串流而定。</span></div>
      <div className="detail-actions"><Button disabled={!selectedRoom} variant={selectedRoom?.enabled ? "outline" : "default"} onClick={() => selectedRoom && controlRoom(selected, !selectedRoom.enabled)}>{selectedRoom?.enabled ? <Square /> : <Play />}{selectedRoom?.enabled ? "停止此直播" : "開始此直播"}</Button><Button disabled={!selectedRoom} variant="outline" onClick={() => openRoom(selected)}><Pencil />編輯</Button><Button disabled={!selectedRoom} variant="outline" className="delete-button" onClick={() => setDeleteOpen(true)}><Trash2 />刪除</Button></div>
    </main>

    <section className="log-panel"><div className="log-header"><h2>執行日誌</h2><Button variant="outline" onClick={openDownloads}><FolderOpen />錄影資料夾</Button></div>
      <div className="log-summary"><span className={`status-dot ${state?.running ? "is-active" : ""}`} /><span>{state?.running ? "核心執行中" : "核心未啟動"}</span><label className="log-filter-label">顯示<select className="native-select log-filter" value={logFilter} onChange={(event) => setLogFilter(event.target.value as "all" | "error" | "success")}><option value="all">全部</option><option value="error">錯誤</option><option value="success">成功</option></select></label><span className="log-count">{visibleLogs.length}/{logs.length} 筆</span></div>
      <div className="log-window">{logs.length === 0 ? <div className="log-empty">尚無執行日誌。啟動直播間後，輸出會顯示在這裡。</div> : visibleLogs.length === 0 && <div className="log-empty">此篩選目前沒有日誌。</div>}{visibleLogs.map((line) => <div className={`log-line level-${line.level}`} key={line.id}><time>{line.time}</time><span>{line.text}</span></div>)}<div ref={logEnd} /></div>
      <div className="log-footer"><label className="flex items-center gap-2"><Checkbox checked={autoScroll} onCheckedChange={(value) => setAutoScroll(value === true)} />自動捲動日誌</label><Button variant="ghost" size="sm" onClick={() => setLogs([])}>清除畫面</Button></div>
    </section>

    <RoomEditor open={roomOpen} edit={editing !== null} draft={roomDraft} setDraft={setRoomDraft} save={saveRoom} close={() => setRoomOpen(false)} />
    <SettingsEditor open={settingsOpen} draft={settingsDraft} setDraft={setSettingsDraft} current={state?.settings} save={saveSettings} close={() => setSettingsOpen(false)} />
    <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}><DialogContent><DialogHeader><DialogTitle>刪除直播間？</DialogTitle><DialogDescription>將從監看清單移除「{selectedRoom ? roomLabel(selectedRoom) : "此直播間"}」。</DialogDescription></DialogHeader><DialogFooter><Button variant="outline" onClick={() => setDeleteOpen(false)}>取消</Button><Button variant="destructive" onClick={deleteRoom}>刪除直播間</Button></DialogFooter></DialogContent></Dialog>
    {notice && <div className="notice" role="status">{notice}</div>}
  </div>
}
