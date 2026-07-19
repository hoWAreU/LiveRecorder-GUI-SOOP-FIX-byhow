# LiveRecorder GUI（SOOP Fix byhow）

這是以 [ihmily/DouyinLiveRecorder](https://github.com/ihmily/DouyinLiveRecorder) 為錄製核心製作的 Windows 圖形化介面。專案提供桌面 GUI 與本機 Web UI，並針對 SOOP 韓國站網址、登入、畫質與直播預覽進行相容性調整。

## 主要功能

- 桌面 GUI 與瀏覽器 Web UI
- 深色／淺色主題切換
- 新增、編輯、刪除及停用直播間
- 每個直播間可獨立開始或停止，不影響其他直播
- 啟動 Web UI 時自動恢復已啟用的直播間
- 最後一個直播停止後自動關閉錄製核心
- 關閉 CMD 或 Web UI 時，自動結束錄製核心與 FFmpeg
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
- Python 3.10 以上
- FFmpeg（必須可透過系統 `PATH` 執行）

## 安裝

```powershell
git clone https://github.com/hoWAreU/LiveRecorder-GUI-SOOP-FIX-byhow.git
cd LiveRecorder-GUI-SOOP-FIX-byhow\recorder-core
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
cd ..
```

## 啟動 Web UI

雙擊：

```text
start-webui.bat
```

瀏覽器會開啟 [http://127.0.0.1:8765](http://127.0.0.1:8765)。服務預設只監聽本機位址，不會對區域網路或網際網路公開。

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

## 啟動桌面 GUI

雙擊：

```text
start-gui.bat
```

或使用虛擬環境直接執行：

```powershell
.\recorder-core\.venv\Scripts\python gui.py
```

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
