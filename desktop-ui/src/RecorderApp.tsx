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
import { LanguageToggle, useLanguage } from "@/i18n"

type LogResponse = { logs: LogLine[]; running: boolean }

export default function RecorderApp() {
  const { theme, setTheme } = useTheme()
  const { language, t } = useLanguage()
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
  const label = (room: Room) => roomLabel(room, t("unnamedRoom"))
  const enabledCount = rooms.filter((room) => room.enabled).length
  const normalizedQuery = roomQuery.trim().toLocaleLowerCase()
  const visibleRooms = rooms.map((room, index) => ({ room, index })).filter(({ room }) =>
    !normalizedQuery || `${label(room)} ${room.url}`.toLocaleLowerCase().includes(normalizedQuery))
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
      announce(language === "en" ? t(enabled ? result.running ? "roomStarted" : "coreStartFailed" : "roomStopped") : result.message)
    } catch (error) { announce((error as Error).message) }
  }

  function openRoom(index: number | null) {
    setEditing(index)
    setRoomDraft(index === null ? { ...emptyRoom } : { ...rooms[index] })
    setRoomOpen(true)
  }

  async function saveRoom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!/^https?:\/\//i.test(roomDraft.url.trim())) { announce(t("invalidUrl")); return }
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
      announce(t("roomSaved"))
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
      announce(t("roomDeleted"))
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
      announce(t("settingsSaved"))
    } catch (error) { announce((error as Error).message) }
  }

  async function openDownloads() {
    try { await api("/api/open-downloads", {}) }
    catch (error) { announce((error as Error).message) }
  }

  return <div className="app-shell">
    <aside className="room-sidebar">
      <div className="brand-block"><Radio className="brand-mark" aria-hidden="true" /><div className="brand-title">LIVE RECORDER</div></div>
      <div className="sidebar-summary"><span className={`status-dot ${state?.running ? "is-active" : ""}`} /><span>{t(state?.running ? "coreRunning" : "coreStopped")}</span><span className="ml-auto tabular-nums">{t("enabledCount", { enabled: enabledCount, total: rooms.length })}</span></div>
      <div className="sidebar-actions"><Button variant="outline" onClick={openSettings}><Settings2 />{t("settings")}</Button><Button onClick={() => openRoom(null)}><Plus />{t("addRoom")}</Button></div>
      <div className="sidebar-section-title"><span>{t("rooms")}</span><span>{visibleRooms.length} / {rooms.length}</span></div>
      <div className="room-search"><Search aria-hidden="true" /><Input type="search" value={roomQuery} onChange={(event) => setRoomQuery(event.target.value)} placeholder={t("searchRooms")} aria-label={t("searchRooms")} /></div>
      <ScrollArea className="room-scroll"><div className="room-items">
        {rooms.length === 0 && <div className="empty-list">{t("noRooms")}<br />{t("addRoomHint")}</div>}
        {rooms.length > 0 && visibleRooms.length === 0 && <div className="empty-list">{t("noSearchResults", { query: roomQuery.trim() })}</div>}
        {visibleRooms.map(({ room, index }) => <div className={`room-item ${selected === index ? "selected" : ""}`} key={`${room.url}-${index}`}>
          <button className="room-select" onClick={() => { setSelected(index); setPreviewFailed(false) }} aria-label={t("selectRoomNamed", { name: label(room) })} aria-current={selected === index ? "true" : undefined}><span className={`status-dot ${room.enabled ? "is-active" : ""}`} /><span className="room-text"><strong>{label(room)}</strong><small>{room.quality} · {t(room.enabled ? "monitoringEnabled" : "paused")}</small></span></button>
          <Button size="xs" variant="outline" className={room.enabled ? "room-stop" : ""} onClick={() => controlRoom(index, !room.enabled)} aria-label={t("roomAction", { action: t(room.enabled ? "stop" : "start"), name: label(room) })}>
            {room.enabled ? <Square className="size-3" /> : <Play className="size-3" />}{t(room.enabled ? "stop" : "start")}
          </Button>
        </div>)}
      </div></ScrollArea>
      <div className="sidebar-footer"><span>LIVE RECORDER · v0.4.2</span><div className="sidebar-preferences"><LanguageToggle /><Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t(theme === "dark" ? "lightTheme" : "darkTheme")} title={t(theme === "dark" ? "lightTheme" : "darkTheme")}>{theme === "dark" ? <Sun /> : <Moon />}</Button></div></div>
    </aside>

    <main className="detail-panel">
      <div className="panel-eyebrow">{t("roomDetails")}</div>
      <div className="preview-frame">{previewSupported && !previewFailed ? <img src={`/api/preview?url=${encodeURIComponent(selectedRoom!.url)}&t=${previewTick}`} alt={t("previewAlt", { name: label(selectedRoom!) })} onError={() => setPreviewFailed(true)} /> : <div className="preview-placeholder"><Radio className="size-7" /><span>{t(!selectedRoom ? "selectForPreview" : previewSupported ? "previewUnavailable" : "previewUnsupported")}</span></div>}</div>
      <div className="detail-heading"><h1>{selectedRoom ? label(selectedRoom) : t("selectRoom")}</h1><span className="detail-state"><span className={`status-dot ${selectedRoom?.enabled ? "is-active" : ""}`} />{t(selectedRoom ? selectedRoom.enabled ? "monitoringEnabled" : "paused" : "notSelected")}</span></div>
      <Separator />
      <dl className="detail-fields"><div className="detail-field"><dt>{t("roomUrl")}</dt><dd>{selectedRoom ? <a href={selectedRoom.url} target="_blank" rel="noreferrer" className="room-url">{selectedRoom.url}<ExternalLink className="size-3.5" /></a> : <span className="field-empty">—</span>}</dd></div>
        <div className="detail-field"><dt>{t("targetQuality")}</dt><dd>{selectedRoom?.quality ?? "—"}</dd></div>
        <div className="detail-field"><dt>{t("storageFormat")}</dt><dd>{state?.settings.format === "mp3音頻" ? t("mp3Audio") : state?.settings.format === "m4a音頻" ? t("m4aAudio") : state?.settings.format ?? "—"}</dd></div></dl>
      <div className="detail-note"><CircleHelp className="size-4" /><span>{t("detailNote")}</span></div>
      <div className="detail-actions"><Button disabled={!selectedRoom} variant={selectedRoom?.enabled ? "outline" : "default"} onClick={() => selectedRoom && controlRoom(selected, !selectedRoom.enabled)}>{selectedRoom?.enabled ? <Square /> : <Play />}{t(selectedRoom?.enabled ? "stopThisRoom" : "startThisRoom")}</Button><Button disabled={!selectedRoom} variant="outline" onClick={() => openRoom(selected)}><Pencil />{t("edit")}</Button><Button disabled={!selectedRoom} variant="outline" className="delete-button" onClick={() => setDeleteOpen(true)}><Trash2 />{t("delete")}</Button></div>
    </main>

    <section className="log-panel"><div className="log-header"><h2>{t("logs")}</h2><Button variant="outline" onClick={openDownloads}><FolderOpen />{t("recordingsFolder")}</Button></div>
      <div className="log-summary"><span className={`status-dot ${state?.running ? "is-active" : ""}`} /><span>{t(state?.running ? "coreRunningShort" : "coreStoppedShort")}</span><label className="log-filter-label">{t("show")}<select className="native-select log-filter" value={logFilter} onChange={(event) => setLogFilter(event.target.value as "all" | "error" | "success")}><option value="all">{t("all")}</option><option value="error">{t("errors")}</option><option value="success">{t("successes")}</option></select></label><span className="log-count">{t("logCount", { visible: visibleLogs.length, total: logs.length })}</span></div>
      <div className="log-window">{logs.length === 0 ? <div className="log-empty">{t("noLogs")}</div> : visibleLogs.length === 0 && <div className="log-empty">{t("noFilteredLogs")}</div>}{visibleLogs.map((line) => <div className={`log-line level-${line.level}`} key={line.id}><time>{line.time}</time><span>{line.text}</span></div>)}<div ref={logEnd} /></div>
      <div className="log-footer"><label className="flex items-center gap-2"><Checkbox checked={autoScroll} onCheckedChange={(value) => setAutoScroll(value === true)} />{t("autoScroll")}</label><Button variant="ghost" size="sm" onClick={() => setLogs([])}>{t("clearDisplay")}</Button></div>
    </section>

    <RoomEditor open={roomOpen} edit={editing !== null} draft={roomDraft} setDraft={setRoomDraft} save={saveRoom} close={() => setRoomOpen(false)} />
    <SettingsEditor open={settingsOpen} draft={settingsDraft} setDraft={setSettingsDraft} current={state?.settings} save={saveSettings} close={() => setSettingsOpen(false)} />
    <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}><DialogContent><DialogHeader><DialogTitle>{t("deleteConfirm")}</DialogTitle><DialogDescription>{t("deleteDescription", { name: selectedRoom ? label(selectedRoom) : t("thisRoom") })}</DialogDescription></DialogHeader><DialogFooter><Button variant="outline" onClick={() => setDeleteOpen(false)}>{t("cancel")}</Button><Button variant="destructive" onClick={deleteRoom}>{t("deleteRoom")}</Button></DialogFooter></DialogContent></Dialog>
    {notice && <div className="notice" role="status">{notice}</div>}
  </div>
}
