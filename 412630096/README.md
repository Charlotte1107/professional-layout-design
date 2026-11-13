# LINE Messaging API 註冊申請與 Echo Bot
作者：利蓁琳｜學號：412630096｜日期：2026-11-13
班級：資管系4C｜座號：5

## 編譯
在本目錄執行三次（Windows 需安裝 MiKTeX、XeLaTeX 及新細明體）：
```
xelatex -interaction=nonstopmode -halt-on-error -jobname=412630096 main.tex
```
輸出為 412630096.pdf。中文使用 PMingLiU，其他系統請替換為已安裝的繁體中文字型。

## 執行
Python 3.10+，僅使用標準函式庫，不需 pip 套件。
在 PowerShell 設定真正的環境變數（.env.example 僅為欄位說明，不會自動載入）：
```powershell
$env:LINE_CHANNEL_SECRET = '貼入自己的 secret'
$env:LINE_CHANNEL_ACCESS_TOKEN = '貼入自己的 token'
python app.py
```
另一個終端機執行 `ngrok http 8000`，將公開 HTTPS 網址加上 `/callback` 設為 Webhook URL。
ngrok 請依官方指引安裝並設定自己的 authtoken。

## 測試
```
python -m unittest -v test_app.py
```
測試使用假憑證及 mock，不會發送 LINE 訊息。真實 LINE 帳號、token、外部 HTTPS 通道及手機端回覆需由本人完成實測。

## GitHub
專案在上層工作區 Git 中版本控管。確認個人 GitHub 儲存庫後，在上層目錄執行：
```
git remote add origin https://github.com/Charlotte1107/professional-layout-design.git
git push -u origin HEAD
```
上述是操作說明，不代表已上傳成功。不可提交真正的 secret、token 或 .env。
ZIP 包含學號資料夾與交付檔案；Git 版本歷史另以學號資料夾中的 version-history.txt 保存可讀紀錄，repository.bundle 保存可還原的 Git 歷史。

指定作業儲存庫：https://github.com/Charlotte1107/professional-layout-design
