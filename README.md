# Active Finance Agent
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/active-finance-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/active-finance-agent/actions/workflows/tests.yml)

🤖 **主动式个人财务/资产监控 Multi-Agent** - 24小时帮你盯着钱，睡觉时也能帮你监控行情、分析研报、推送预警

## 🎯 项目理念

> 2026 年的 AI 不再只是画 K 线图，而是帮你**主动干活**！

- ✨ **监控 Agent**: 24小时监控全球宏观新闻 + 你的自选股行情 + 黄金市场波动
- 📑 **研报 Agent**: 自动把长篇大论的财报/研报浓缩成 **3条「对我资产的具体影响」**
- ⚠️ **预警 Agent**: 当金价/股价触发你设定的逻辑（技术指标背离/波动率超阈值），直接**微信/钉钉推送执行建议**

## 🌟 特色

- 👀 **睡觉也帮你盯着** - 定时自动运行，不用你天天盯盘
- 🧠 **Multi-Agent 协作** - 分工明确，每个Agent专注做一件事
- 📊 **技术指标分析** - 内置 TA-Lib 技术指标计算，支持自定义预警规则
- 📰 **多数据源** - Tushare 行情 + 新闻抓取
- 🔔 **多渠道通知** - 钉钉/企业微信/Telegram 推送
- 🛠️ **高度可配置** - 自选股、预警规则、通知渠道全部可配置
- 🐳 **Docker 一键部署**

## 项目结构

```
active-finance-agent/
├── src/
│   ├── monitor/          # 监控 Agent
│   │   ├── __init__.py
│   │   ├── news_monitor.py      # 宏观新闻监控
│   │   └── price_monitor.py    # 行情价格监控 (Tushare)
│   ├── research/         # 研报 Agent
│   │   ├── __init__.py
│   │   └── report_summarizer.py  # 研报浓缩总结
│   ├── alert/           # 预警 Agent
│   │   ├── __init__.py
│   │   ├── indicator.py       # 技术指标计算
│   │   └── trigger.py        # 预警触发判断
│   └── notifier/        # 通知模块
│       ├── __init__.py
│       └── sender.py    # 钉钉/企业微信/Telegram 推送
├── config/
│   └── config.example.yaml
├── tests/               # 测试用例
├── main.py              # 主入口
├── pyproject.toml       # uv 项目配置
├── Dockerfile           # Docker 镜像
├── docker-compose.yml   # Docker Compose
├── Makefile             # 简化命令
└── README.md
```

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/active-finance-agent.git
cd active-finance-agent
```

### 2. 安装依赖

使用 uv 推荐：
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync

# 安装 playwright
uv run playwright install chromium
```

### 3. 配置
```bash
cp config/config.example.yaml config/config.yaml
# 编辑填入你的:
#  - Tushare token
#  - OpenAI API key
#  - 自选股/关注金价
#  - 预警规则
#  - 通知渠道配置
```

### 4. 运行一次
```bash
uv run python main.py --run-once
```

### 5. 启动定时监控
```bash
uv run python main.py --schedule
```

### Docker 部署
```bash
make docker-build
make docker-up
```

## 配置说明

### Tushare
需要注册 [Tushare](https://tushare.pro/) 获取 token，免费额度足够个人使用。

### 预警规则示例

```yaml
alerts:
  - asset: gold
    type: price_deviation
    ma_period: 50
    deviation_threshold: 0.05  # 偏离5%触发
    direction: both  # up/down/both
```

### 技术指标支持

- MA 均线偏离
- RSI 超买超卖
- Bollinger Bands 布林带突破
- 波动率阈值
- 自定义规则

## 工作流程

```
┌─────────────┐
│  定时触发   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 监控 Agent  │  →  抓取新闻 + 拉取最新行情
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 研报 Agent  │  →  如果有新财报/研报，AI浓缩成3条对你资产的影响
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 预警 Agent  │  →  计算技术指标，判断是否触发预警规则
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   通知推送  │  →  钉钉/企业微信/Telegram 推送分析结果和操作建议
└─────────────┘
```

## 趣味点

> 看着自己写的代码在睡觉时帮你盯着钱，这种「掌控感」比看视频生成爽得多！😎

## 路线图

- [ ] 添加更多技术指标
- [ ] 支持更多数据源 (东方财富/雪球)
- [ ] Web 界面查看历史预警
- [ ] LLM 自动生成操作建议
- [ ] 支持交易接口自动下单

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
