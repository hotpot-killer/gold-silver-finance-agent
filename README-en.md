# gold-silver-finance-agent

🤖 **AI-Powered Gold & Silver Active Monitoring Agent**  
Upgrade from *passive alerting* to **proactive signal generation**, combining technical indicators + market expectations + crowd wisdom + LLM comprehensive analysis.

## ✨ Core Features

### 🎯 From "post-alerting" → "proactive signal generation"

| Feature | Description |
|------|------|
| **Forward-looking Technical Signals** | RSI divergence early warning, momentum crossover earlier trigger, RSI slope acceleration alert |
| **Trend Following Signals** | Price break MA50 + MA20/MA50 golden/dead cross → actively signal trend start |
| **Volatility Graded Alerts** | 1.5x → mild warning "market brewing", 2.0x → strong alert "big trend confirmed" |
| **MA200 Filtering** | Only trigger mean-reversion signals in range-bound markets, filter out false signals in strong trends |
| **Gold/Silver Ratio Extreme Alert** | Ratio > 85 / < 65 → alert rotation opportunities |
| **COT Positioning Alert** | Weekly update CFTC data, alert extreme positioning before reversal |
| **Macro Event Reminder**提前提醒 tomorrow high-impact events (nonfarm/CPI/rate) today |

### 🔮 Market Expectations

- Dashboard directly links **Polymarket** (long-term) + **Kalshi** (short-term weekly/monthly)
- Click to check market pricing probabilities anytime

### 🧠 Crowd Wisdom Composite

- Auto daily update 5 top macro gurus' latest views:
  - Peter Schiff → auto fetch from Twitter/Nitter
  - Ray Dalio → auto fetch from Twitter/Nitter
  - Jim Rickards → auto fetch from Twitter/Nitter
  - Aimin Xie (Chinese fund manager) → auto fetch from Baidu search
  - Ming Zhang (Chinese Academy of Social Sciences) → auto fetch from Baidu search
- No API key required, 100% free
- Both bullish and bearish views for cross-validation with technical signals

### 📊 Complete Web Dashboard

- Statistics cards overview
- Guru views section
- Recent alerts list
- Interactive candlestick chart (gold/silver switchable)
- Asset/alert type filtering + pagination
- Elegant modern UI design

### 🤖 Full LLM Empowerment

1. **News auto summary** → auto fetch gold-related news, LLM summarizes key points
2. **Composite Signal Analysis** → integrate technical signals + guru views + current price, LLM gives final comprehensive judgment and trading advice

### 📡 Multi-channel Notification

- Feishu/Dingtalk/WeChat Work/Telegram supported
- Default Feishu webhook adaptation for domestic users

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configuration

Copy `config/config.example.yaml` to `config/config.yaml`, modify:
- `tushare.token` → your tushare token (optional, for domestic stocks)
- `llm.api_key` → your OpenAI API key (for news summary and composite analysis, optional, basic features work without it)
- `notify.feishu.webhook_url` → your Feishu webhook URL
- keep other defaults

### 3. Run

```bash
# Run once to fetch all data
python main.py --run-once

# Start scheduled monitoring (every 60 minutes)
python main.py --schedule

# Start web dashboard
python main.py --web --port 5000
```

## 📋 Default Alert Configuration

| Alert Type | Threshold | Description |
|---------|------|------|
| RSI Momentum | overbought 65 / oversold 35 | Divergence early warning, trigger on crossover |
| MA Deviation | gold 5% / silver 7% | Alert for mean reversion when too far from MA50 |
| MA Breakout | break MA50 + golden/dead cross | active trend start signal |
| Volatility Grading | 1.5x mild / 2.0x strong | early sense trend starting |
| Gold/Silver Ratio | >85 / <65 | extreme level alert rotation opportunity |
| COT Positioning | gold >30% / <-20% | alert reversal at institutional extreme positioning |

All parameters can be adjusted in config file.

## 🎨 UI Preview

- Gradient header with prediction market links
- Statistics cards grid
- Responsive guru cards grid
- Recent alerts list
- Interactive candlestick chart
- Elegant rounded corners + layered shadows + smooth interactions

## 🔧 Project Structure

```
├── config/             # Configuration files
├── data/               # Data cache (price history / alert log / guru views)
├── src/
│   ├── alert/          # Indicator calculation / alert trigger
│   ├── monitor/        # Price / news / COT / guru fetching
│   ├── notifier/       # Notification sending
│   ├── research/       # News summary (LLM)
│   └── web/            # Web dashboard
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

## 📝 Changelog

### 2026-03-18 Major Upgrade: From Passive Monitoring → Proactive Signal Generation

1. **Forward-looking Technical Indicators**
   - RSI upgrade: top/bottom divergence early warning + momentum crossover earlier trigger + RSI acceleration alert
   - MA upgrade: price break MA50 + golden/dead cross active trend signal
   - Volatility grading: 1.5x mild warning + 2.0x strong alert
   - MA200 filtering: only trigger range-bound signals in non-trending markets

2. **Intermediate Forward-looking Signals**
   - Gold/silver ratio threshold optimized to 85/65
   - COT extreme positioning alert
   - Macro event pre-reminder (tomorrow nonfarm alert today)

3. **Market Expectation Links**
   - Add Polymarket (long-term) + Kalshi (short-term) to dashboard

4. **Crowd Wisdom**
   - Auto daily update 5 top macro gurus' latest views
   - Twitter for foreigners, Baidu search for Chinese, completely free

5. **LLM Comprehensive Analysis**
   - News research auto summary
   - Integrate all information gives final comprehensive judgment and trading advice

6. **UI Elegance Upgrade**
   - Rounded corners, layered shadows, smooth animation, responsive layout

## 📄 License

MIT
