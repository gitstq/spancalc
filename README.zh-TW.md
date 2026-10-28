[简体中文](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md)

# ⏱️ SpanCalc

> 別再為了「90 分鐘後是幾點」「週五加 1 個工作天是哪天」翻日曆、按計算機。SpanCalc 一行指令就算清楚，而且算錯了會直接報錯，絕不會悄悄給你一個錯答案。

## 🎉 專案介紹

寫腳本、排 CI、做資料處理時，時間算術無處不在：「這批任務要跑 2 天 3 小時，什麼時候結束？」「兩個時間戳之間差多久？」「今天是週五，承諾 1 個工作天後交付，那是週幾？」「這個時間戳對應台北時間幾點？」

常見的解法是拼一段 `date` 指令、打開線上換算器，或者引入一個日期函式庫——小題大作，還不一定算得對。SpanCalc 就是為這類小事準備的：一個**零依賴、純計算、完全離線**的 Python 工具，既能當命令列用，也能當函式庫 import。它不計時、不追蹤、不連網、不存任何狀態，只負責把時間算對。

## ✨ 核心特性

- 🗣️ **人類可讀的時長** — `1w 2d 3h 30m`、`1h30m`、`1.5h`、`2天3小時`、`PT90M`（ISO 8601）、`1:30:00`，怎麼寫都行
- 📅 **日期加減** — 給任意日期加一段時長，支援 IANA 時區（如 `Asia/Taipei`）
- ↔️ **時間差** — 兩個時間點之間差多少，自動拆成週 / 天 / 小時 / 分鐘，並給出工作天天數
- 💼 **工作天計算** — 跳過週六日，假日用你自己提供的檔案傳入，不內建會過期的假日表
- 🕰️ **時間戳互轉** — 日期時間與 Unix 時間戳雙向換算，預設 UTC，可指定時區
- 🧩 **可作函式庫用** — `parse_duration`、`add_duration`、`diff_datetimes` 等函式全部可直接 import
- 🛡️ **算錯就報錯** — 未知單位、寫錯的日期、不存在的時區一律報錯並以結束碼 2 結束，腳本和 CI 可以放心依賴它
- 🪶 **零依賴** — 只用 Python 3.9+ 標準函式庫，不裝任何第三方套件

## 🚀 快速開始

環境需求：Python 3.9 或更新版本，不需要安裝任何依賴。

```bash
git clone https://github.com/gitstq/spancalc.git
cd spancalc
python -m spancalc parse "1w 2d 3h 30m"
```

```bash
# 輸出：1週2天3小時30分鐘
python -m spancalc parse "1h30m"
python -m spancalc add --from "2026-10-28 10:00" --duration "2d 3h" --tz Asia/Taipei
python -m spancalc diff --from "2026-10-28" --to "2026-10-30"
python -m spancalc business --from "2026-10-30" --days 1
python -m spancalc epoch --to-datetime 0
```

以函式庫的方式使用：

```python
from spancalc import parse_duration, add_duration, diff_datetimes

parse_duration("1h30m")          # 5400.0（秒）
add_duration("2026-10-28 10:00", "2d 3h", tz="Asia/Taipei")
diff_datetimes("2026-10-28", "2026-10-30")["human_zh"]  # '2天'
```

## 📖 詳細使用指南

### ⏳ 解析時長：`parse`

```bash
python -m spancalc parse "1w 2d 3h 30m"
python -m spancalc parse "2天3小時"
python -m spancalc parse "PT90M"
python -m spancalc parse "1:30:00"
python -m spancalc --json parse "90m"
```

支援的寫法：混合單位（`1w 2d 3h 30m`）、連寫（`1h30m`）、小數（`1.5h`）、中文單位（`天 / 小時 / 分鐘 / 秒 / 週 / 年 / 月`）、ISO 8601（`P2DT3H`、`PT90M`）、冒號寫法（`1:30:00` 表示 1 小時 30 分，`90:00` 表示 90 分鐘）、純數字（按秒算）、前置負號（`-2h`）。單位說明：`w = 7 天，d = 24 小時`；`年`和`月`是固定換算（1 年 = 365 天，1 月 = 30 天），文件裡寫明了這一點，不假裝它們是精確的日曆月。

### 🔄 單位換算：`convert`

```bash
python -m spancalc convert "90m" --to hours
python -m spancalc convert "2d" --to seconds
```

`--to` 可選 `weeks / days / hours / minutes / seconds / milliseconds`。

### ➕➖ 日期加減：`add` / `sub`

```bash
python -m spancalc add --from "2026-10-28 10:00" --duration "2d 3h" --tz Asia/Taipei
python -m spancalc sub --from "2026-10-28 10:00" --duration "1d"
```

日期接受 `YYYY-MM-DD`、`YYYY-MM-DD HH:MM[:SS]` 和 ISO 8601 寫法。沒有時區資訊的輸入預設按 UTC 理解；傳了 `--tz` 就按該時區理解；輸入本身帶時區偏移時不要再傳 `--tz`。

### ↔️ 求時間差：`diff`

```bash
python -m spancalc diff --from "2026-10-28 10:00" --to "2026-10-30 13:00" --tz Asia/Taipei
python -m spancalc --json diff --from "2026-10-28" --to "2026-10-30"
```

輸出包含總秒數、週 / 天 / 小時 / 分鐘拆分、中文與英文可讀寫法，以及這兩個日期之間的工作天天數（`business_days`）。

### 💼 工作天：`business`

```bash
python -m spancalc business --from "2026-10-30" --days 1
python -m spancalc business --from "2026-10-30" --days 1 --holidays examples/holidays.example.txt
```

預設跳過週六、週日；`--days` 為負數時往回推。假日檔案每行一個 `YYYY-MM-DD` 日期，`#` 開頭的行是註解。工作天的定義是明確的：起始日期本身不算在內，數滿 N 個工作天的那天就是結果。

### 🕰️ 時間戳：`epoch`

```bash
python -m spancalc epoch --from-datetime "2026-10-28 10:00" --tz Asia/Taipei
python -m spancalc epoch --to-datetime 1761612000
python -m spancalc epoch --to-datetime 0 --tz Asia/Taipei
```

`--from-datetime` 和 `--to-datetime` 二選一，同時傳或都不傳都會報錯。

### 🧩 輸出格式與結束碼

所有子命令都支援全域 `--json`，輸出機器可讀的 JSON，方便腳本和 CI 解析：

```bash
python -m spancalc --json parse "90m"
```

```json
{
  "duration": "90m",
  "total_seconds": 5400.0,
  "breakdown": {
    "weeks": 0,
    "days": 0,
    "hours": 1,
    "minutes": 30,
    "seconds": 0,
    "sign": 1,
    "total_seconds": 5400.0
  },
  "human": "1小時30分鐘"
}
```

結束碼：`0` 表示成功，`2` 表示輸入有問題（未知單位、解析失敗、時區不存在等）。

## 🧠 設計思路與迭代規劃

SpanCalc 的定位是「算時間的瑞士刀裡最小的那一把」：只做確定性計算，不做計時、追蹤、排程。核心層（`spancalc/core.py`）完全不碰 I/O 和全域狀態，所以既能跑測試，也能被別的程式 import；命令列層（`spancalc/cli.py`）只負責參數解析、列印和結束碼。

和同類工具的區別：很多日期函式庫什麼都想做，結果為了一個小算術要裝一堆依賴；很多線上換算器要連網、不能進腳本。SpanCalc 反過來：**零依賴、離線、報錯明確、結果可進管道**。它也不做計時追蹤——那是另一類工具的活，SpanCalc 只算，不記。

後續規劃：

- v1.1：相對表達解析（如「下週一」「月底」），前提是語義必須無歧義，否則寧可不做
- v1.2：批次模式，從標準輸入一次處理多條時長或日期
- v1.3：按地區劃分的假日資料檔案（仍由使用者明確傳入，保持離線）

## 📦 打包與部署指南

本專案是**工具庫 / 命令列工具類**，按規則不發 Release，安裝方式就是複製後直接執行，不需要打包發布。

```bash
git clone https://github.com/gitstq/spancalc.git
cd spancalc
python -m unittest discover -s tests -v
python -m spancalc --help
```

如需裝成系統指令（可選）：

```bash
pip install .
spancalc parse "1h30m"
```

相容環境：Python 3.9+，Windows / macOS / Linux 均可；時區功能依賴系統自帶的 IANA 時區資料庫（Python `zoneinfo`），極少數精簡系統上可能需要另外安裝 `tzdata`。

常見問題：

- **Q: `Unknown timezone` 怎麼辦？** A: 檢查時區名稱拼寫（如 `Asia/Taipei`），並確認系統有時區資料庫。
- **Q: 為什麼 `1月` 不是日曆上的 1 個月？** A: 時長字串裡的「月」沒有固定天數，本工具按 30 天固定換算，並在文件和程式碼註解裡寫明；需要精確日曆月運算時請用日期函式庫。
- **Q: 工作天為什麼不內建假日？** A: 假日年年變、各地不同，內建表遲早過時；用 `--holidays` 傳你自己的檔案，永遠準確。

## 🤝 貢獻指南

歡迎提 Issue 和 Pull Request，詳見 [CONTRIBUTING.md](CONTRIBUTING.md)。基本要求：改動要小、要有測試、三個語言版本的 README 要同步更新、新增行為必須有測試案例。

## 📄 開源協議

MIT 協議，詳見 [LICENSE](LICENSE)。
