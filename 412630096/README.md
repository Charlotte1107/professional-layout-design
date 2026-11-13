# LINE Messaging API 註冊申請與 Echo Bot
作者：利蓁琳｜學號：412630096｜日期：2026-11-13
班級：資管系4C｜座號：5

## 編譯
在本目錄執行三次（Windows 需安裝 MiKTeX、XeLaTeX 及標楷體）：
```
xelatex -interaction=nonstopmode -halt-on-error -jobname=412630096 main.tex
```
輸出為 412630096.pdf。中文使用 DFKai-SB，其他系統請替換為已安裝的繁體中文字型。

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

## GitHub 與版本紀錄
已上傳至 https://github.com/Charlotte1107/professional-layout-design 。
此工作區已設定 origin，後續更新請在儲存庫根目錄執行：
```powershell
git add 412630096
git commit -m '更新：說明本次實際變更'
git push origin main
```
首次下載可執行 `git clone https://github.com/Charlotte1107/professional-layout-design.git`，再進入其下的學號資料夾編譯與測試，無須重複新增 origin。

ZIP 包含學號資料夾、PDF、LaTeX、程式與驗證紀錄；version-history.txt 與 repository.bundle 保存本機版本歷史。bundle 可用 `git clone repository.bundle restored-repository` 還原。

## 排版與驗收
中文採標楷體，封面、評分表、單行章標題與頁尾頁碼參照題目 PDF，程式標題置頂並自動產生行號。英數程式碼保留等寬字型。
17 項測試涵蓋核心邏輯、本機 HTTP 接收與錯誤紀錄；測試不會向真實 LINE 發送訊息。真實 Verify、手機回覆與截圖仍待本人完成，PDF 已列出可操作的驗收程序。

視覺優化：五張 TikZ 向量圖涵蓋架構、開通、憑證、訊息時序與分層驗收；程式碼採淡藍灰底、細圓角框、內嵌行號與語法配色。app.py 分為五段，保留實際行號，並預留換頁空間以避免標題落單。所有圖均為自行繪製的示意圖。
