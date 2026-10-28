[简体中文](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md)

# ⏱️ SpanCalc

> 别再为「90 分钟后是几点」「周五加 1 个工作日是哪天」翻日历、敲计算器。SpanCalc 一行命令就算清楚，而且算错了会直接报错，绝不悄悄给你一个错答案。

## 🎉 项目介绍

写脚本、排 CI、做数据处理时，时间算术到处都是：「这批任务要跑 2 天 3 小时，什么时候结束？」「两个时间戳之间差多久？」「今天是周五，承诺 1 个工作日后交付，那是周几？」「这个时间戳对应北京时间几点？」

通常的解法是拼一段 `date` 命令、打开在线换算器，或者引入一个日期库——小题大做，还不一定算得对。SpanCalc 就是为这类小事准备的：一个**零依赖、纯计算、完全离线**的 Python 工具，既能当命令行用，也能当库 import。它不计时、不追踪、不联网、不存任何状态，只负责把时间算对。

## ✨ 核心特性

- 🗣️ **人类可读的时长** — `1w 2d 3h 30m`、`1h30m`、`1.5h`、`2天3小时`、`PT90M`（ISO 8601）、`1:30:00`，怎么写都行
- 📅 **日期加减** — 给任意日期加一段时长，支持 IANA 时区（如 `Asia/Shanghai`）
- ↔️ **时间差** — 两个时间点之间差多少，自动拆成周 / 天 / 小时 / 分钟，并给出工作日天数
- 💼 **工作日计算** — 跳过周六日，节假日用你自己提供的文件传入，不内置会过期的假日表
- 🕰️ **时间戳互转** — 日期时间与 Unix 时间戳双向换算，默认 UTC，可指定时区
- 🧩 **可作库用** — `parse_duration`、`add_duration`、`diff_datetimes` 等函数全部可直接 import
- 🛡️ **算错就报错** — 未知单位、写错的日期、不存在的时区一律报错并以退出码 2 结束，脚本和 CI 可以放心依赖它
- 🪶 **零依赖** — 只用 Python 3.9+ 标准库，不装任何第三方包

## 🚀 快速开始

环境要求：Python 3.9 或更高版本，不需要安装任何依赖。

```bash
git clone https://github.com/gitstq/spancalc.git
cd spancalc
python -m spancalc parse "1w 2d 3h 30m"
```

```bash
# 输出：1周2天3小时30分钟
python -m spancalc parse "1h30m"
python -m spancalc add --from "2026-10-28 10:00" --duration "2d 3h" --tz Asia/Shanghai
python -m spancalc diff --from "2026-10-28" --to "2026-10-30"
python -m spancalc business --from "2026-10-30" --days 1
python -m spancalc epoch --to-datetime 0
```

以库的方式使用：

```python
from spancalc import parse_duration, add_duration, diff_datetimes

parse_duration("1h30m")          # 5400.0（秒）
add_duration("2026-10-28 10:00", "2d 3h", tz="Asia/Shanghai")
diff_datetimes("2026-10-28", "2026-10-30")["human_zh"]  # '2天'
```

## 📖 详细使用指南

### ⏳ 解析时长：`parse`

```bash
python -m spancalc parse "1w 2d 3h 30m"
python -m spancalc parse "2天3小时"
python -m spancalc parse "PT90M"
python -m spancalc parse "1:30:00"
python -m spancalc --json parse "90m"
```

支持的写法：混合单位（`1w 2d 3h 30m`）、连写（`1h30m`）、小数（`1.5h`）、中文单位（`天 / 小时 / 分钟 / 秒 / 周 / 年 / 月`）、ISO 8601（`P2DT3H`、`PT90M`）、冒号写法（`1:30:00` 表示 1 小时 30 分，`90:00` 表示 90 分钟）、纯数字（按秒算）、前置负号（`-2h`）。单位说明：`w = 7 天，d = 24 小时`；`年`和`月`是固定换算（1 年 = 365 天，1 月 = 30 天），文档里写明了这一点，不假装它们是精确的日历月。

### 🔄 单位换算：`convert`

```bash
python -m spancalc convert "90m" --to hours
python -m spancalc convert "2d" --to seconds
```

`--to` 可选 `weeks / days / hours / minutes / seconds / milliseconds`。

### ➕➖ 日期加减：`add` / `sub`

```bash
python -m spancalc add --from "2026-10-28 10:00" --duration "2d 3h" --tz Asia/Shanghai
python -m spancalc sub --from "2026-10-28 10:00" --duration "1d"
```

日期接受 `YYYY-MM-DD`、`YYYY-MM-DD HH:MM[:SS]` 和 ISO 8601 写法。没有时区信息的输入默认按 UTC 理解；传了 `--tz` 就按该时区理解；输入本身带时区偏移时不要再传 `--tz`。

### ↔️ 求时间差：`diff`

```bash
python -m spancalc diff --from "2026-10-28 10:00" --to "2026-10-30 13:00" --tz Asia/Shanghai
python -m spancalc --json diff --from "2026-10-28" --to "2026-10-30"
```

输出包含总秒数、周 / 天 / 小时 / 分钟拆分、中文与英文可读写法，以及这两个日期之间的工作日天数（`business_days`）。

### 💼 工作日：`business`

```bash
python -m spancalc business --from "2026-10-30" --days 1
python -m spancalc business --from "2026-10-30" --days 1 --holidays examples/holidays.example.txt
```

默认跳过周六、周日；`--days` 为负数时往回推。节假日文件每行一个 `YYYY-MM-DD` 日期，`#` 开头的行是注释。工作日的定义是明确的：起始日期本身不算在内，数满 N 个工作日的那天就是结果。

### 🕰️ 时间戳：`epoch`

```bash
python -m spancalc epoch --from-datetime "2026-10-28 10:00" --tz Asia/Shanghai
python -m spancalc epoch --to-datetime 1761612000
python -m spancalc epoch --to-datetime 0 --tz Asia/Shanghai
```

`--from-datetime` 和 `--to-datetime` 二选一，同时传或都不传都会报错。

### 🧩 输出格式与退出码

所有子命令都支持全局 `--json`，输出机器可读的 JSON，方便脚本和 CI 解析：

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
  "human": "1小时30分钟"
}
```

退出码：`0` 表示成功，`2` 表示输入有问题（未知单位、解析失败、时区不存在等）。

## 🧠 设计思路与迭代规划

SpanCalc 的定位是「算时间的瑞士军刀里最小的那一把」：只做确定性计算，不做计时、追踪、排程。核心层（`spancalc/core.py`）完全不碰 I/O 和全局状态，所以既能跑测试，也能被别的程序 import；命令行层（`spancalc/cli.py`）只负责参数解析、打印和退出码。

和同类工具的区别：很多日期库什么都想做，结果为了一个小算术要装一堆依赖；很多在线换算器要联网、不能进脚本。SpanCalc 反过来：**零依赖、离线、报错明确、结果可进管道**。它也不做计时追踪——那是另一类工具的活，SpanCalc 只算，不记。

后续规划：

- v1.1：相对表达解析（如「下周一」「月底」），前提是语义必须无歧义，否则宁可不做
- v1.2：批量模式，从标准输入一次处理多条时长或日期
- v1.3：按地区划分的节假日数据文件（仍由用户显式传入，保持离线）

## 📦 打包与部署指南

本项目是**工具库 / 命令行工具类**，按规则不发 Release，安装方式就是克隆后直接运行，不需要打包发布。

```bash
git clone https://github.com/gitstq/spancalc.git
cd spancalc
python -m unittest discover -s tests -v
python -m spancalc --help
```

如需装成系统命令（可选）：

```bash
pip install .
spancalc parse "1h30m"
```

兼容环境：Python 3.9+，Windows / macOS / Linux 均可；时区功能依赖系统自带的 IANA 时区数据库（Python `zoneinfo`），极少数精简系统上可能需要另行安装 `tzdata`。

常见问题：

- **Q: `Unknown timezone` 怎么办？** A: 检查时区名拼写（如 `Asia/Shanghai`），并确认系统有时区数据库。
- **Q: 为什么 `1月` 不是日历上的 1 个月？** A: 时长字符串里的「月」没有固定天数，本工具按 30 天固定换算，并在文档和代码注释里写明；需要精确日历月运算时请用日期库。
- **Q: 工作日为什么不内置节假日？** A: 节假日年年变、各地不同，内置表迟早过时；用 `--holidays` 传你自己的文件，永远准确。

## 🤝 贡献指南

欢迎提 Issue 和 Pull Request，详见 [CONTRIBUTING.md](CONTRIBUTING.md)。基本要求：改动要小、要有测试、三个语言版本的 README 要同步更新、新增行为必须有测试用例。

## 📄 开源协议

MIT 协议，详见 [LICENSE](LICENSE)。
