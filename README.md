# Live Recorder GUI

這是 [ihmily/DouyinLiveRecorder](https://github.com/ihmily/DouyinLiveRecorder) 的 Windows 桌面控制介面，錄製核心保留在 `recorder-core/`，GUI 直接管理上游的設定檔並啟停核心程序。

## 功能

- 新增、編輯、暫停與刪除直播間
- 為每個直播間設定畫質與主播名稱
- 設定輸出路徑、錄影格式、檢查間隔與代理
- 啟動/停止錄製，並在 GUI 查看即時日誌
- 自動將錄製核心的簡體中文日誌轉換為臺灣繁體中文

## 執行

需要 Python 3.10 以上與上游依賴：

```powershell
cd recorder-core
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
cd ..
.\recorder-core\.venv\Scripts\python gui.py
```

也可以在已安裝依賴的 Python 環境中雙擊 `start-gui.bat`。

首次啟動時，程式會從 `config.example.ini` 與 `URL_config.example.ini` 建立本機設定。實際設定檔可能包含帳密與 Cookie，已由 Git 忽略，不會上傳。

建議錄製格式使用 `ts`，避免非預期中止時整個檔案損壞。抖音等平台可能需要在 `recorder-core/config/config.ini` 填入有效 Cookie；請勿把 Cookie 提交到公開儲存庫。

## 授權

錄製核心由原作者以 MIT License 發布，詳見 `recorder-core/LICENSE`。本 GUI 同樣以 MIT License 發布。
