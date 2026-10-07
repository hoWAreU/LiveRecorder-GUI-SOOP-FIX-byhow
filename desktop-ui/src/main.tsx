import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import "./index.css"
import App from "./App.tsx"
import { ThemeProvider } from "@/components/theme-provider.tsx"
import { LanguageProvider } from "@/i18n.tsx"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="live-recorder-desktop-theme">
      <LanguageProvider><App /></LanguageProvider>
    </ThemeProvider>
  </StrictMode>
)
