import { type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { emptySettings, formats, qualities, type RoomDraft, type Settings, type SettingsDraft } from "@/api"

function Choice({ id, value, options, change }: { id: string; value: string; options: string[]; change: (value: string) => void }) {
  return <select id={id} className="native-select" value={value} onChange={(event) => change(event.target.value)}>
    {options.map((option) => <option key={option} value={option}>{option}</option>)}
  </select>
}

export function RoomEditor({ open, edit, draft, setDraft, save, close }: {
  open: boolean; edit: boolean; draft: RoomDraft; setDraft: (draft: RoomDraft) => void;
  save: (event: FormEvent<HTMLFormElement>) => void; close: () => void;
}) {
  return <Dialog open={open} onOpenChange={(next) => { if (!next) close() }}><DialogContent className="editor-dialog">
    <DialogHeader><DialogTitle>{edit ? "編輯直播間" : "新增直播間"}</DialogTitle><DialogDescription>設定直播網址、名稱與錄製畫質。</DialogDescription></DialogHeader>
    <form className="editor-form" onSubmit={save}>
      <div className="form-field"><Label htmlFor="room-url">直播間網址</Label><Input id="room-url" type="url" required placeholder="https://play.sooplive.com/..." value={draft.url} onChange={(event) => setDraft({ ...draft, url: event.target.value })} /></div>
      <div className="form-field"><Label htmlFor="room-name">主播名稱</Label><Input id="room-name" placeholder="選填" value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></div>
      <div className="form-field"><Label htmlFor="room-quality">目標解析度</Label><Choice id="room-quality" value={draft.quality} options={qualities} change={(quality) => setDraft({ ...draft, quality })} /></div>
      <div className="switch-row"><div><strong>啟用監看與錄製</strong><small>錄製核心會監看此直播間</small></div><Switch checked={draft.enabled} onCheckedChange={(enabled) => setDraft({ ...draft, enabled })} /></div>
      <DialogFooter><Button type="button" variant="outline" onClick={close}>取消</Button><Button type="submit">儲存直播間</Button></DialogFooter>
    </form>
  </DialogContent></Dialog>
}

export function SettingsEditor({ open, draft, setDraft, current, save, close }: {
  open: boolean; draft: SettingsDraft; setDraft: (draft: SettingsDraft) => void; current?: Settings;
  save: (event: FormEvent<HTMLFormElement>) => void; close: () => void;
}) {
  const value = draft || emptySettings
  return <Dialog open={open} onOpenChange={(next) => { if (!next) close() }}><DialogContent className="settings-dialog">
    <DialogHeader><DialogTitle>錄製設定</DialogTitle><DialogDescription>變更檔案格式、檢查頻率與 SOOP 登入資訊。</DialogDescription></DialogHeader>
    <form className="editor-form settings-form" onSubmit={save}>
      <div className="settings-grid">
        <div className="form-field span-two"><Label htmlFor="set-output">儲存路徑</Label><Input id="set-output" placeholder="留空使用預設下載資料夾" value={value.output} onChange={(event) => setDraft({ ...value, output: event.target.value })} /></div>
        <div className="form-field"><Label htmlFor="set-format">影片格式</Label><Choice id="set-format" value={value.format} options={formats} change={(format) => setDraft({ ...value, format })} /></div>
        <div className="form-field"><Label htmlFor="set-fps">偏好 FPS</Label><Choice id="set-fps" value={value.fps} options={["自動", "30", "60"]} change={(fps) => setDraft({ ...value, fps })} /></div>
        <div className="form-field"><Label htmlFor="set-interval">檢查間隔（秒）</Label><Input id="set-interval" type="number" min="10" value={value.interval} onChange={(event) => setDraft({ ...value, interval: event.target.value })} /></div>
        <div className="form-field"><Label htmlFor="set-proxy">代理地址</Label><Input id="set-proxy" placeholder="127.0.0.1:7890" value={value.proxy} onChange={(event) => setDraft({ ...value, proxy: event.target.value })} /></div>
      </div>
      <div className="switch-row"><div><strong>啟用代理</strong><small>錄製核心將使用上方代理地址</small></div><Switch checked={value.proxyEnabled} onCheckedChange={(proxyEnabled) => setDraft({ ...value, proxyEnabled })} /></div>
      <Separator />
      <div className="form-section-title">SOOP 登入 <span>19+ 直播可能需要</span></div>
      <div className="form-field"><Label htmlFor="set-user">SOOP 帳號</Label><Input id="set-user" value={value.soopUsername} onChange={(event) => setDraft({ ...value, soopUsername: event.target.value })} /></div>
      <div className="settings-grid"><div className="form-field"><Label htmlFor="set-password">SOOP 密碼</Label><Input id="set-password" type="password" placeholder="留空保持原值" value={value.soopPassword} onChange={(event) => setDraft({ ...value, soopPassword: event.target.value })} /></div>
        <div className="form-field"><Label htmlFor="set-cookie">Cookie</Label><Textarea id="set-cookie" rows={2} placeholder="留空保持原值" value={value.soopCookie} onChange={(event) => setDraft({ ...value, soopCookie: event.target.value })} /></div></div>
      <p className="credential-hint">目前狀態：密碼{current?.hasSoopPassword ? "已設定" : "未設定"}，Cookie {current?.hasSoopCookie ? "已設定" : "未設定"}。留空不會清除現有值。</p>
      <DialogFooter><Button type="button" variant="outline" onClick={close}>取消</Button><Button type="submit">儲存設定</Button></DialogFooter>
    </form>
  </DialogContent></Dialog>
}
