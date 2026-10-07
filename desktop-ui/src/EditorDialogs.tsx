import { type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { emptySettings, formats, qualities, type RoomDraft, type Settings, type SettingsDraft } from "@/api"
import { useLanguage } from "@/i18n"

function Choice({ id, value, options, change, labels = {} }: { id: string; value: string; options: string[]; change: (value: string) => void; labels?: Record<string, string> }) {
  return <select id={id} className="native-select" value={value} onChange={(event) => change(event.target.value)}>
    {options.map((option) => <option key={option} value={option}>{labels[option] ?? option}</option>)}
  </select>
}

export function RoomEditor({ open, edit, draft, setDraft, save, close }: {
  open: boolean; edit: boolean; draft: RoomDraft; setDraft: (draft: RoomDraft) => void;
  save: (event: FormEvent<HTMLFormElement>) => void; close: () => void;
}) {
  const { t } = useLanguage()
  return <Dialog open={open} onOpenChange={(next) => { if (!next) close() }}><DialogContent className="editor-dialog">
    <DialogHeader><DialogTitle>{t(edit ? "editRoom" : "addRoom")}</DialogTitle><DialogDescription>{t("roomEditorDescription")}</DialogDescription></DialogHeader>
    <form className="editor-form" onSubmit={save}>
      <div className="form-field"><Label htmlFor="room-url">{t("roomUrl")}</Label><Input id="room-url" type="url" required placeholder="https://play.sooplive.com/..." value={draft.url} onChange={(event) => setDraft({ ...draft, url: event.target.value })} /></div>
      <div className="form-field"><Label htmlFor="room-name">{t("broadcasterName")}</Label><Input id="room-name" placeholder={t("optional")} value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></div>
      <div className="form-field"><Label htmlFor="room-quality">{t("targetResolution")}</Label><Choice id="room-quality" value={draft.quality} options={qualities} change={(quality) => setDraft({ ...draft, quality })} /></div>
      <div className="switch-row"><div><strong>{t("enableMonitoring")}</strong><small>{t("monitoringHint")}</small></div><Switch aria-label={t("enableMonitoring")} checked={draft.enabled} onCheckedChange={(enabled) => setDraft({ ...draft, enabled })} /></div>
      <DialogFooter className="editor-actions"><Button type="button" variant="outline" onClick={close}>{t("cancel")}</Button><Button type="submit">{t("saveRoom")}</Button></DialogFooter>
    </form>
  </DialogContent></Dialog>
}

export function SettingsEditor({ open, draft, setDraft, current, save, close }: {
  open: boolean; draft: SettingsDraft; setDraft: (draft: SettingsDraft) => void; current?: Settings;
  save: (event: FormEvent<HTMLFormElement>) => void; close: () => void;
}) {
  const { t } = useLanguage()
  const value = draft || emptySettings
  return <Dialog open={open} onOpenChange={(next) => { if (!next) close() }}><DialogContent className="settings-dialog">
    <DialogHeader><DialogTitle>{t("recordingSettings")}</DialogTitle><DialogDescription>{t("settingsDescription")}</DialogDescription></DialogHeader>
    <form className="editor-form settings-form" onSubmit={save}>
      <div className="settings-body">
        <section className="settings-section" aria-labelledby="settings-recording-title">
          <h3 id="settings-recording-title">{t("recordingStorage")}</h3>
          <div className="settings-grid">
            <div className="form-field span-two"><Label htmlFor="set-output">{t("outputPath")}</Label><Input id="set-output" placeholder={t("outputPlaceholder")} value={value.output} onChange={(event) => setDraft({ ...value, output: event.target.value })} /></div>
            <div className="form-field"><Label htmlFor="set-format">{t("videoFormat")}</Label><Choice id="set-format" value={value.format} options={formats} labels={{ "mp3音頻": t("mp3Audio"), "m4a音頻": t("m4aAudio") }} change={(format) => setDraft({ ...value, format })} /></div>
            <div className="form-field"><Label htmlFor="set-fps">{t("preferredFps")}</Label><Choice id="set-fps" value={value.fps} options={["自動", "30", "60"]} labels={{ "自動": t("auto") }} change={(fps) => setDraft({ ...value, fps })} /></div>
          </div>
          <p className="settings-hint">{t("nativeStreamHint")}</p>
        </section>
        <section className="settings-section" aria-labelledby="settings-network-title">
          <h3 id="settings-network-title">{t("monitoringNetwork")}</h3>
          <div className="settings-grid">
            <div className="form-field"><Label htmlFor="set-interval">{t("checkInterval")}</Label><Input id="set-interval" type="number" min="10" value={value.interval} onChange={(event) => setDraft({ ...value, interval: event.target.value })} /></div>
            <div className="form-field"><Label htmlFor="set-proxy">{t("proxyAddress")}</Label><Input id="set-proxy" placeholder="127.0.0.1:7890" value={value.proxy} onChange={(event) => setDraft({ ...value, proxy: event.target.value })} /></div>
          </div>
          <div className="switch-row"><div><strong>{t("enableProxy")}</strong><small>{t("proxyHint")}</small></div><Switch aria-label={t("enableProxy")} checked={value.proxyEnabled} onCheckedChange={(proxyEnabled) => setDraft({ ...value, proxyEnabled })} /></div>
        </section>
        <section className="settings-section" aria-labelledby="settings-soop-title">
          <h3 id="settings-soop-title">{t("soopLogin")} <span>{t("soopLoginHint")}</span></h3>
          <div className="form-field"><Label htmlFor="set-user">{t("soopAccount")}</Label><Input id="set-user" value={value.soopUsername} onChange={(event) => setDraft({ ...value, soopUsername: event.target.value })} /></div>
          <div className="settings-grid"><div className="form-field"><Label htmlFor="set-password">{t("soopPassword")}</Label><Input id="set-password" type="password" placeholder={t("keepCurrent")} value={value.soopPassword} onChange={(event) => setDraft({ ...value, soopPassword: event.target.value })} /></div>
            <div className="form-field"><Label htmlFor="set-cookie">Cookie</Label><Textarea id="set-cookie" rows={2} placeholder={t("keepCurrent")} value={value.soopCookie} onChange={(event) => setDraft({ ...value, soopCookie: event.target.value })} /></div></div>
          <p className="credential-hint">{t("credentialStatus", { password: t(current?.hasSoopPassword ? "configured" : "notConfigured"), cookie: t(current?.hasSoopCookie ? "configured" : "notConfigured") })}</p>
        </section>
      </div>
      <DialogFooter className="editor-actions settings-actions"><Button type="button" variant="outline" onClick={close}>{t("cancel")}</Button><Button type="submit">{t("saveSettings")}</Button></DialogFooter>
    </form>
  </DialogContent></Dialog>
}
