import { useState } from "react"
import { LoaderCircle, Moon, Radio, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/components/theme-provider"
import { LanguageToggle, useLanguage } from "@/i18n"

type Mode = "desktop" | "web"
type PickerWindow = Window & {
  pywebview?: { api?: { choose_mode: (mode: Mode) => Promise<{ mode: Mode }> } }
}

export default function ModePicker() {
  const { theme, setTheme } = useTheme()
  const { t } = useLanguage()
  const [busy, setBusy] = useState<Mode | null>(null)
  const [error, setError] = useState("")

  async function choose(mode: Mode) {
    if (busy) return
    const bridge = (window as PickerWindow).pywebview?.api
    if (!bridge) {
      setError(t("launcherNotReady"))
      return
    }
    setBusy(mode)
    setError("")
    try {
      const result = await bridge.choose_mode(mode)
      if (result.mode === "desktop") window.location.replace("/desktop/")
      // Selecting web closes this native window; Python opens the browser next.
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : t("launchFailed"))
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
            <span>{t("launcher")}</span>
          </div>
          <div className="picker-preferences"><LanguageToggle /><Button type="button" variant="ghost" size="icon" className="picker-theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={t(theme === "dark" ? "lightTheme" : "darkTheme")} title={t(theme === "dark" ? "lightTheme" : "darkTheme")}>
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </Button></div>
        </header>

        <div className="picker-content">
          <section className="picker-intro">
            <h1>{t("chooseInterface")}</h1>
            <p>{t("pickerIntro")}</p>
          </section>

          <section className="picker-options" aria-label={t("chooseInterface")} aria-busy={!!busy}>
            <div className="picker-option">
              <span className="picker-option-number" aria-hidden="true">01</span>
              <div className="picker-option-copy">
                <h2>{t("desktop")}</h2>
                <p>{t("desktopDescription")}</p>
              </div>
              <Button type="button" className="picker-select" disabled={!!busy} onClick={() => choose("desktop")}>
                {busy === "desktop" && <LoaderCircle className="picker-spinner" aria-hidden="true" />}
                {t(busy === "desktop" ? "opening" : "openDesktop")}
              </Button>
            </div>

            <div className="picker-option">
              <span className="picker-option-number" aria-hidden="true">02</span>
              <div className="picker-option-copy">
                <h2>{t("web")}</h2>
                <p>{t("webDescription")}</p>
              </div>
              <Button type="button" variant="outline" className="picker-select" disabled={!!busy} onClick={() => choose("web")}>
                {busy === "web" && <LoaderCircle className="picker-spinner" aria-hidden="true" />}
                {t(busy === "web" ? "opening" : "openWeb")}
              </Button>
            </div>
          </section>
        </div>

        <footer className="picker-footer">
          <span>{t("localOnly")}</span>
          {error ? <span className="picker-error" role="alert">{error}</span> : <span className="picker-feedback" role="status">{t(busy ? "starting" : "chooseAgain")}</span>}
        </footer>
      </div>
    </main>
  )
}
