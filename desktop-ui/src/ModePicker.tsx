import { useState } from "react"
import { LoaderCircle, Moon, Radio, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/components/theme-provider"

type Mode = "desktop" | "web"
type PickerWindow = Window & {
  pywebview?: { api?: { choose_mode: (mode: Mode) => Promise<{ mode: Mode }> } }
}

export default function ModePicker() {
  const { theme, setTheme } = useTheme()
  const [busy, setBusy] = useState<Mode | null>(null)
  const [error, setError] = useState("")

  async function choose(mode: Mode) {
    if (busy) return
    const bridge = (window as PickerWindow).pywebview?.api
    if (!bridge) {
      setError("啟動器尚未就緒，請稍後重試；或從 LiveRecorder.exe 開啟。")
      return
    }
    setBusy(mode)
    setError("")
    try {
      const result = await bridge.choose_mode(mode)
      if (result.mode === "desktop") window.location.replace("/desktop/")
      // Selecting web closes this native window; Python opens the browser next.
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "無法啟動所選介面")
      setBusy(null)
    }
  }

  return (
    <main className="picker-page">
      <div className="picker-shell">
        <header className="picker-topbar">
          <div className="picker-brand">
            <Radio size={18} strokeWidth={2} aria-hidden="true" />
            <strong>LIVE RECORDER</strong>
            <span>啟動器</span>
          </div>
          <Button type="button" variant="ghost" size="icon" className="picker-theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={theme === "dark" ? "切換亮色主題" : "切換暗色主題"} title={theme === "dark" ? "切換亮色主題" : "切換暗色主題"}>
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </Button>
        </header>

        <div className="picker-content">
          <section className="picker-intro">
            <h1>選擇介面</h1>
            <p>選擇在桌面視窗或瀏覽器操作；錄製設定與直播間清單共用。</p>
          </section>

          <section className="picker-options" aria-label="介面選擇" aria-busy={!!busy}>
            <div className="picker-option">
              <span className="picker-option-number" aria-hidden="true">01</span>
              <div className="picker-option-copy">
                <h2>桌面版</h2>
                <p>獨立視窗，集中查看直播間、預覽與日誌。</p>
              </div>
              <Button type="button" className="picker-select" disabled={!!busy} onClick={() => choose("desktop")}>
                {busy === "desktop" && <LoaderCircle className="picker-spinner" aria-hidden="true" />}
                {busy === "desktop" ? "正在開啟…" : "開啟桌面版"}
              </Button>
            </div>

            <div className="picker-option">
              <span className="picker-option-number" aria-hidden="true">02</span>
              <div className="picker-option-copy">
                <h2>網頁版</h2>
                <p>使用預設瀏覽器，保留分頁操作方式。</p>
              </div>
              <Button type="button" variant="outline" className="picker-select" disabled={!!busy} onClick={() => choose("web")}>
                {busy === "web" && <LoaderCircle className="picker-spinner" aria-hidden="true" />}
                {busy === "web" ? "正在開啟…" : "開啟網頁版"}
              </Button>
            </div>
          </section>
        </div>

        <footer className="picker-footer">
          <span>控制介面僅於本機開放</span>
          {error ? <span className="picker-error" role="alert">{error}</span> : <span className="picker-feedback" role="status">{busy ? "正在啟動，請稍候…" : "下次啟動時仍可重新選擇"}</span>}
        </footer>
      </div>
    </main>
  )
}
