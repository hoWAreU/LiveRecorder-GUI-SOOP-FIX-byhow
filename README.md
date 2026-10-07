# LiveRecorder GUI（SOOP Fix byhow）

這是以 [ihmily/DouyinLiveRecorder](https://github.com/ihmily/DouyinLiveRecorder) 為錄製核心製作的 Windows 圖形化介面。桌面版與瀏覽器版現在共用同一套 React + shadcn/ui 控制台；桌面版由 WebView2 顯示，錄製核心仍是 Python。專案保留舊版網頁與 Tkinter 備用介面，並針對 SOOP 韓國站網址、登入、畫質與直播預覽進行相容性調整。

## 主要功能

- 共用 React 介面的桌面 GUI 與瀏覽器 Web UI，以及舊版備用介面
- 深色／淺色主題切換
- 新增、編輯、刪除及停用直播間
- 每個直播間可獨立開始或停止，不影響其他直播
- 啟動 Web UI 時自動恢復已啟用的直播間
- 最後一個直播停止後自動關閉錄製核心
- 關閉提供服務的 CMD 或桌面程式時，自動結束錄製核心與 FFmpeg；只關閉瀏覽器分頁不會停止錄製
- 錄製畫質選項：2K、1080P、720P、540P、360P、240P
- FPS 偏好：自動、30 FPS、60 FPS
- 影片格式與分段錄製設定
- SOOP 帳號、密碼及 Cookie 設定
- Live Preview：錄製時每 15 秒從實際影片擷取畫面，未錄製時使用 SOOP 縮圖或主播圖片
- 即時錄製日誌與自動捲動
- 簡體中文日誌轉換為繁體中文

> 畫質及 FPS 選項只會選擇平台實際提供的原生串流。若平台沒有指定規格，程式會使用最接近或最高可用的來源，不會透過重新編碼虛增解析度或幀率。

## 系統需求

- Windows 10／11
- FFmpeg（必須可透過系統 `PATH` 執行）
- WebView2 Runtime（新版桌面視窗需要；若缺少，啟動器會提示並開啟 Tkinter 備用介面）
- 從原始碼執行或自行打包：Python 3.10 以上、Node.js 與 npm

已打包的 EXE 不需要另外安裝 Python 或執行 `npm install`。部分直播平台的 JavaScript 簽名功能可能仍需 Node.js。

## EXE 版本

取得打包完成的整個 `LiveRecorder` 資料夾後，執行其中的 `LiveRecorder.exe`。首先會顯示與桌面控制台同風格的 React 介面選擇視窗，可選擇：

- **桌面版**：以 WebView2 開啟 React + shadcn/ui 三欄式桌面控制台。
- **網頁版**：啟動本機服務並在預設瀏覽器開啟同一套 React 控制台。

請保留整個 `LiveRecorder` 資料夾，不要只單獨移動 EXE。程式核心、React 建置檔、Web 靜態檔及相依 DLL 集中放在 `_internal/`；使用者會操作的 `config/`、`downloads/`、`logs/` 與 `backup_config/` 則放在 EXE 同一層。首次執行時會由範例建立設定，不會把開發電腦上的帳密或 Cookie 打包進去。

開發者若要自行打包，先依下方步驟安裝相依套件，再安裝 PyInstaller 並執行 `build-exe.bat`；輸出位於 `dist/LiveRecorder/`。

## 安裝

```powershell
git clone https://github.com/hoWAreU/LiveRecorder-GUI-SOOP-FIX-byhow.git
cd LiveRecorder-GUI-SOOP-FIX-byhow\recorder-core
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
cd ..
.\recorder-core\.venv\Scripts\python -m pip install -r desktop-requirements.txt
npm ci --prefix desktop-ui
npm run build --prefix desktop-ui
```

`desktop-ui/` 是 React + TypeScript + Vite 專案；套件版本由 `package-lock.json` 固定。第一次啟動桌面或瀏覽器 GUI 前，都須先完成 React 建置。若只使用瀏覽器版，可以略過桌面專用的 `desktop-requirements.txt`，但不能略過 React 建置。

### 預覽 React 介面

在專案根目錄開兩個 PowerShell 視窗。第一個啟動本機 API；若只檢查介面、不想讓已啟用的直播間自動錄製，可設定預覽模式：

```powershell
$env:LIVE_RECORDER_UI_PREVIEW = "1"
.\recorder-core\.venv\Scripts\python -m webui.server
```

第二個啟動 Vite：

```powershell
npm run dev --prefix desktop-ui
```

開啟 Vite 顯示的本機網址（預設 `http://127.0.0.1:5173`）。開發伺服器會將 `/api` 轉送至 `127.0.0.1:8765`。預覽模式只停用啟動時的自動錄製；若在介面中手動按「開始」，仍會啟動錄製。

## 啟動 Web UI

雙擊 `start-webui.bat`，或在專案根目錄執行：

```powershell
.\recorder-core\.venv\Scripts\python -m webui.server
```

瀏覽器會開啟 [http://127.0.0.1:8765](http://127.0.0.1:8765)。首頁與桌面版的 `/desktop/` 使用同一套 React 控制台、功能與 API；原本的網頁介面保留在 [http://127.0.0.1:8765/legacy/](http://127.0.0.1:8765/legacy/) 作為備用。服務預設只監聽本機位址，不會對區域網路或網際網路公開。

在同一個服務中開啟多個瀏覽器分頁，直播間設定與核心狀態會定期刷新。不要同時執行兩個獨立的 LiveRecorder 服務程序來操作同一份設定；桌面版與網頁版的「選擇模式」是擇一啟動，並非讓兩個錄製核心並行。

如需更換連接埠，可先設定環境變數：

```powershell
$env:LIVE_RECORDER_PORT = "9000"
.\start-webui.bat
```

Web UI 的直播間開關就是錄製控制：

- 開始第一個直播時會自動啟動錄製核心。
- 停止某個直播只會結束該直播的 FFmpeg。
- 停止最後一個直播時會自動關閉錄製核心。
- 關閉 Web UI 的 CMD 視窗時，Windows 會一併回收錄製核心及其 FFmpeg 子程序。
- 只關閉瀏覽器分頁不會關閉本機服務；需關閉啟動服務的 CMD 視窗才會停止由它管理的錄製。

## 啟動桌面 GUI

雙擊 `start-gui.bat`，或在專案根目錄使用虛擬環境執行：

```powershell
.\recorder-core\.venv\Scripts\python launcher.py --desktop
```

`launcher.py --desktop`（以及 `start-gui.bat`）會直接進入新版 React 控制台；不帶參數啟動 `launcher.py` 則會先顯示 React 桌面版／網頁版選擇視窗。選擇之前不會啟動錄製核心。若要直接使用舊版 Tkinter，可執行 `python launcher.py --desktop-classic`。

新版桌面 GUI 使用 React + [shadcn/ui](https://ui.shadcn.com/) 元件，透過 Windows WebView2 顯示。左側是可獨立開始／停止的直播間清單，中間是預覽與畫質資訊，右側是錄製日誌；亮色與暗色主題會保留選擇。介面經由本機 `127.0.0.1` API 操作 Python 錄製核心，關閉桌面視窗時會停止由該視窗啟動的錄製服務。

若未安裝 WebView2 Runtime 或缺少 React 建置檔，啟動器會提示原因並開啟 Tkinter 備用選擇視窗；舊版 Tkinter GUI 也仍可使用。

## 自行打包 EXE

在完成「安裝」步驟後，於專案根目錄執行：

```powershell
.\recorder-core\.venv\Scripts\python -m pip install pyinstaller
.\build-exe.bat
```

`build-exe.bat` 會重新安裝鎖定的前端相依套件、建置 React、確認桌面 Python 相依套件，再產生 `dist/LiveRecorder/LiveRecorder.exe`。請連同 `dist/LiveRecorder/` 內其他檔案一起分發；不要提交 `dist/`、`build/` 或本機執行設定。

## 設定檔

首次啟動時，程式會由以下範例建立本機設定：

- `recorder-core/config/config.example.ini`
- `recorder-core/config/URL_config.example.ini`

實際執行時使用：

- `recorder-core/config/config.ini`
- `recorder-core/config/URL_config.ini`

實際設定檔可能包含 SOOP 帳號、密碼及 Cookie，已由 Git 忽略。請勿強制加入版本控制或上傳至公開儲存庫。

## SOOP 注意事項

- 建議使用 `https://play.sooplive.com/主播ID/直播編號` 格式。
- 19+ 或需登入的直播必須設定有效的 SOOP 帳密或 Cookie。
- 韓國站觀看 API 已改用 `https://api.m.sooplive.com`。若既有 Cookie 過期並導致 SOOP 回傳 HTML，程式會自動改用匿名狀態重新確認、以帳密登入並更新 Cookie。
- 舊直播編號結束後，SOOP 可能對縮圖回傳 404；介面會自動改用最近成功畫面或主播圖片。
- 2K 代表選擇平台提供的最高原生畫質，平台未提供 2K 時不會進行放大重新編碼。

## 錄製檔案

預設儲存位置：

```text
recorder-core/downloads/
```

建議使用 `ts` 格式。若程式、網路或電腦意外中止，TS 通常比 MP4 更容易保留已錄製的內容。

正在錄製的檔案會被 FFmpeg 鎖定。請先在 Web UI 停止該直播，等待錄製結束後再移動、重新命名或刪除檔案。

## 安全性

以下內容不會提交至 Git：

- 執行中的帳號、密碼與 Cookie 設定
- 直播間執行設定
- 錄影片與下載內容
- 執行日誌
- Python 虛擬環境及快取

提交前仍建議使用 `git status` 再次確認，避免意外公開敏感資料。

## 授權與原專案

錄製核心來自 [ihmily/DouyinLiveRecorder](https://github.com/ihmily/DouyinLiveRecorder)，授權內容請參閱 [recorder-core/LICENSE](recorder-core/LICENSE)。GUI 與 Web UI 修改部分沿用本儲存庫授權。
