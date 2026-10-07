import RecorderApp from "@/RecorderApp"
import ModePicker from "@/ModePicker"

export function App() {
  return new URLSearchParams(window.location.search).has("launcher") ? <ModePicker /> : <RecorderApp />
}

export default App
