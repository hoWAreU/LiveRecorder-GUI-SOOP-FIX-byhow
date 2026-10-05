# LiveRecorder 桌面介面

這個目錄是 React、TypeScript、Vite 與 shadcn/ui 的桌面前端。建置結果位於 `dist/`，由專案根目錄的 Python 本機服務提供 `/desktop/` 頁面，並透過 WebView2 顯示於桌面視窗。

在專案根目錄執行：

```powershell
npm ci --prefix desktop-ui
npm run build --prefix desktop-ui
.\recorder-core\.venv\Scripts\python launcher.py --desktop
```

開發時可先啟動 `start-webui.bat`，再執行 `npm run dev --prefix desktop-ui`。Vite 將 `/api` 轉送到本機錄製服務。使用 `npx shadcn@latest add <component>` 加入元件，元件原始碼會寫入 `src/components/ui/`。
