#!/usr/bin/env python3
import argparse
import logging
import os
import yaml
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from src.monitor import PriceMonitor, NewsMonitor, NewsItem, PriceData
from src.research import ReportSummarizer
from src.research.report_summarizer import MIDDLE_EAST_KEYWORDS
from src.alert import AlertTrigger, Alert
from src.notifier import (
    DingTalkNotifier, 
    WorkWechatNotifier, 
    TelegramNotifier,
    format_alerts
)
from src.scheduler.job import TaskScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 顶级配置类，方便IDE识别
@dataclass
class TushareConfig:
    token: str = ""

@dataclass
class LLMConfig:
    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    base_url: str = ""

@dataclass
class MonitorConfig:
    interval: int = 60
    stocks: List[str] = field(default_factory=list)
    gold: dict = field(default_factory=dict)
    silver: dict = field(default_factory=dict)
    crude_oil: dict = field(default_factory=dict)
    etf_monitor: dict = field(default_factory=dict)
    cot: dict = field(default_factory=dict)
    economic_calendar: dict = field(default_factory=dict)
    news_sources: List[str] = field(default_factory=list)

@dataclass
class ResearchConfig:
    auto_fetch: bool = True
    only_related: bool = True
    summary_points: int = 3

@dataclass
class DataApiConfig:
    fred: str = ""

@dataclass
class ForecastConfig:
    enabled: bool = False
    use_mixed_model: bool = False
    xgb_model_path: str = ""

@dataclass
class ScenarioConfig:
    enabled: bool = False


@dataclass
class AlertConfig:
    alerts: List[dict] = field(default_factory=list)

@dataclass
class DingTalkNotifyConfig:
    enabled: bool = False
    webhook_url: str = ""
    secret: str = ""

@dataclass
class WorkWechatNotifyConfig:
    enabled: bool = False
    webhook_url: str = ""

@dataclass
class FeishuNotifyConfig:
    enabled: bool = False
    webhook_url: str = ""

@dataclass
class TelegramNotifyConfig:
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""

@dataclass
class NotifyConfig:
    dingtalk: DingTalkNotifyConfig = field(default_factory=DingTalkNotifyConfig)
    workwechat: WorkWechatNotifyConfig = field(default_factory=WorkWechatNotifyConfig)
    feishu: FeishuNotifyConfig = field(default_factory=FeishuNotifyConfig)
    telegram: TelegramNotifyConfig = field(default_factory=TelegramNotifyConfig)

@dataclass
class TradingHoursConfig:
    start: str = "06:00"
    end: str = "04:00"

@dataclass
class ScheduleConfig:
    only_trading_hours: bool = True
    trading_hours: TradingHoursConfig = field(default_factory=TradingHoursConfig)

@dataclass
class Config:
    """配置类"""
    log_level: str = "INFO"
    data_dir: str = "./data"
    cache_dir: str = "./cache"
    tushare: TushareConfig = field(default_factory=TushareConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    forecast: ForecastConfig = field(default_factory=ForecastConfig)
    scenario: ScenarioConfig = field(default_factory=ScenarioConfig)
    data_api: DataApiConfig = field(default_factory=DataApiConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    notify: NotifyConfig = field(default_factory=NotifyConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)

def load_config(config_path: str = "config/config.yaml") -> Config:
    """加载配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    config = Config()
    config.log_level = data.get('log_level', 'INFO')
    config.data_dir = data.get('data_dir', './data')
    config.cache_dir = data.get('cache_dir', './cache')
    
    if 'tushare' in data:
        config.tushare.token = data['tushare'].get('token', '')
    
    if 'llm' in data:
        config.llm.provider = data['llm'].get('provider', 'openai')
        config.llm.api_key = data['llm'].get('api_key', '')
        config.llm.model = data['llm'].get('model', 'gpt-4o-mini')
        config.llm.base_url = data['llm'].get('base_url', '')
    
    if 'monitor' in data:
        config.monitor.interval = data['monitor'].get('interval', 60)
        config.monitor.stocks = data['monitor'].get('stocks', [])
        config.monitor.gold = data['monitor'].get('gold', {})
        config.monitor.silver = data['monitor'].get('silver', {})
        config.monitor.crude_oil = data['monitor'].get('crude_oil', {})
        config.monitor.etf_monitor = data['monitor'].get('etf_monitor', {})
        config.monitor.cot = data['monitor'].get('cot', {})
        config.monitor.economic_calendar = data['monitor'].get('economic_calendar', {})
        config.monitor.news_sources = data['monitor'].get('news_sources', [])
    
    if 'research' in data:
        config.research.auto_fetch = data['research'].get('auto_fetch', True)
        config.research.only_related = data['research'].get('only_related', True)
        config.research.summary_points = data['research'].get('summary_points', 3)
    
    if 'forecast' in data:
        config.forecast.enabled = data['forecast'].get('enabled', False)
        config.forecast.use_mixed_model = data['forecast'].get('use_mixed_model', False)
        config.forecast.xgb_model_path = data['forecast'].get('xgb_model_path', '')
    
    if 'scenario' in data:
        config.scenario.enabled = data['scenario'].get('enabled', False)
    
    if 'data_api' in data:
        config.data_api.fred = data['data_api'].get('fred', '')
    
    if 'alerts' in data:
        config.alerts.alerts = data['alerts']
    
    if 'notify' in data:
        if 'dingtalk' in data['notify']:
            config.notify.dingtalk.enabled = data['notify']['dingtalk'].get('enabled', False)
            config.notify.dingtalk.webhook_url = data['notify']['dingtalk'].get('webhook_url', '')
            config.notify.dingtalk.secret = data['notify']['dingtalk'].get('secret', '')
        if 'workwechat' in data['notify']:
            config.notify.workwechat.enabled = data['notify']['workwechat'].get('enabled', False)
            config.notify.workwechat.webhook_url = data['notify']['workwechat'].get('webhook_url', '')
        if 'feishu' in data['notify']:
            config.notify.feishu.enabled = data['notify']['feishu'].get('enabled', False)
            config.notify.feishu.webhook_url = data['notify']['feishu'].get('webhook_url', '')
        if 'telegram' in data['notify']:
            config.notify.telegram.enabled = data['notify']['telegram'].get('enabled', False)
            config.notify.telegram.bot_token = data['notify']['telegram'].get('bot_token', '')
            config.notify.telegram.chat_id = data['notify']['telegram'].get('chat_id', '')
    
    if 'schedule' in data:
        config.schedule.only_trading_hours = data['schedule'].get('only_trading_hours', True)
        if 'trading_hours' in data['schedule']:
            config.schedule.trading_hours.start = data['schedule']['trading_hours'].get('start', '06:00')
            config.schedule.trading_hours.end = data['schedule']['trading_hours'].get('end', '04:00')
    
    logging.getLogger().setLevel(config.log_level)
    return config

def send_notification(config: Config, title: str, content: str) -> bool:
    """发送通知"""
    from src.notifier import (
        DingTalkNotifier, 
        WorkWechatNotifier, 
        FeishuNotifier,
        TelegramNotifier,
    )
    notified = False
    
    if config.notify.dingtalk.enabled:
        notifier = DingTalkNotifier(
            config.notify.dingtalk.webhook_url,
            config.notify.dingtalk.secret
        )
        if notifier.send(title, content):
            notified = True
    
    if config.notify.workwechat.enabled:
        notifier = WorkWechatNotifier(
            config.notify.workwechat.webhook_url
        )
        if notifier.send(title, content):
            notified = True
    
    if config.notify.feishu.enabled:
        notifier = FeishuNotifier(
            config.notify.feishu.webhook_url
        )
        if notifier.send(title, content):
            notified = True
    
    if config.notify.telegram.enabled:
        notifier = TelegramNotifier(
            config.notify.telegram.bot_token,
            config.notify.telegram.chat_id
        )
        if notifier.send(title, content):
            notified = True
    
    return notified

def run_once(config: Config) -> bool:
    """
    运行一次完整监控流程
    ===========================================
    Step 1: 获取最新数据（价格 + 新闻）
    Step 2: 新闻研报总结（LLM过滤总结）
    Step 3: 检查所有预警规则（技术指标 + COT + ETF）
    Step 4: 更新宏观大佬观点（每日自动更新缓存）
    Step 5: 组装通知 + LLM综合分析（技术+观点→最终结论）
    Step 6: 发送通知
    ===========================================
    """
    logger.info("Starting finance agent monitoring round...")
    
    # ===========================================
    # Step 1: 获取最新数据
    # ===========================================
    logger.info("▶️ Step 1: Fetching latest data...")
    
    # 价格监控 - 专注黄金白银，附带原油价格监控
    price_monitor = PriceMonitor(
        config.tushare.token,
        config.monitor.stocks,
        config.monitor.gold.get('enabled', True),
        config.monitor.silver.get('enabled', True),
        config.monitor.crude_oil.get('enabled', True),
        config.monitor.etf_monitor.get('enabled', True),
        data_dir=config.data_dir
    )
    prices = price_monitor.fetch_latest()
    
    # 新闻监控
    news_monitor = NewsMonitor(config.monitor.news_sources)
    news = news_monitor.fetch_latest(hours=config.monitor.interval)
    
    logger.info(f"✅ Completed: Fetched {len(prices)} prices, {len(news)} news")
    
    # ===========================================
    # Step 2: 新闻研报总结 - LLM过滤总结相关新闻
    # ===========================================
    summaries = []
    if config.research.auto_fetch and len(news) > 0:
        logger.info("▶️ Step 2: Summarizing related news/reports...")
        summarizer = ReportSummarizer(
            config.llm.api_key,
            config.llm.model,
            config.llm.base_url
        )
        
        # 过滤出相关新闻
        my_assets = config.monitor.stocks.copy()
        if config.monitor.gold.get('enabled', False):
            my_assets.append('gold')
        
        if config.research.only_related:
            news = summarizer.filter_related(news, my_assets)
        
        for news_item in news[:5]:  # 最多处理5条，避免通知太长
            try:
                summary = summarizer.summarize(
                    news_item.content or news_item.title,
                    news_item.title,
                    my_assets,
                    config.research.summary_points
                )
                if summary:
                    summaries.append({
                        'title': news_item.title,
                        'summary': summary,
                        'url': news_item.url
                    })
            except Exception as e:
                logger.error(f"Failed to summarize {news_item.title}: {e}")
    
    logger.info(f"✅ Completed: Summarized {len(summaries)} news items")
    
    # ===========================================
    # Step 3: 检查所有预警规则
    # ===========================================
    logger.info("▶️ Step 3: Checking all alert rules...")
    
    trigger = AlertTrigger(config.alerts.alerts)
    all_alerts = []
    
    # 自选股检查
    for symbol in config.monitor.stocks:
        df = price_monitor.get_history(symbol, start_date='20240101')
        if not df.empty:
            alerts = trigger.check_all(symbol, df)
            all_alerts.extend(alerts)
    
    # 黄金单独处理
    gold_df = None
    if config.monitor.gold.get('enabled', False):
        gold_symbol = config.monitor.gold.get('symbol', 'XAUUSD')
        gold_df = price_monitor.get_history(gold_symbol, start_date='20240101')
        if not gold_df.empty:
            alerts = trigger.check_all('gold', gold_df)
            all_alerts.extend(alerts)
            logger.info(f"  Checked gold ({gold_symbol}), found {len(alerts)} alerts")
    
    # 白银单独处理
    silver_df = None
    if config.monitor.silver.get('enabled', False):
        silver_symbol = config.monitor.silver.get('symbol', 'XAGUSD')
        silver_df = price_monitor.get_history(silver_symbol, start_date='20240101')
        if not silver_df.empty:
            alerts = trigger.check_all('silver', silver_df)
            all_alerts.extend(alerts)
            logger.info(f"  Checked silver ({silver_symbol}), found {len(alerts)} alerts")
    
    # 金银比极端预警
    if gold_df is not None and silver_df is not None and not gold_df.empty and not silver_df.empty:
        alerts = trigger.check_all('gold-silver', None, gold_df=gold_df, silver_df=silver_df)
        all_alerts.extend(alerts)
        logger.info(f"  Checked gold-silver ratio, found {len(alerts)} alerts")
    
    # COT持仓报告检查 - 每周更新，领先指标
    if config.monitor.cot.get('enabled', False):
        logger.info("  Fetching COT (Commitment of Traders) data...")
        from src.monitor.cot import COTFetcher
        cot_fetcher = COTFetcher(data_dir=config.data_dir)
        cot_data = cot_fetcher.get_gold_silver_cot()
        if cot_data:
            cot_extreme_alerts = cot_fetcher.check_extreme_positioning(cot_data)
            if cot_extreme_alerts:
                alerts = trigger.check_all('cot', None, None, None, cot_extreme_alerts)
                all_alerts.extend(alerts)
                logger.info(f"  Checked COT positioning, found {len(alerts)} extreme alerts")
    
    # GLD/SLV 持仓异动检查
    if config.monitor.etf_monitor.get('enabled', False):
        if config.monitor.etf_monitor.get('gld', True):
            df = price_monitor.get_history('GLD', start_date='20240101')
            if not df.empty:
                alerts = trigger.check_all('gld', df)
                all_alerts.extend(alerts)
        if config.monitor.etf_monitor.get('slv', True):
            df = price_monitor.get_history('SLV', start_date='20240101')
            if not df.empty:
                alerts = trigger.check_all('slv', df)
                all_alerts.extend(alerts)
    
    logger.info(f"✅ Completed: Found {len(all_alerts)} triggered alerts")
    
    # 记录预警到日志文件供Web界面查看
    import json
    from pathlib import Path
    from datetime import datetime
    alert_log_path = Path(config.data_dir) / 'alerts.log'
    alert_log_path.parent.mkdir(exist_ok=True)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(alert_log_path, 'a', encoding='utf-8') as f:
        for alert in all_alerts:
            alert_log = {
                'asset': alert.asset,
                'type': alert.alert_type,
                'message': alert.message,
                'current_value': alert.current_value,
                'threshold': alert.threshold,
                'suggestion': alert.suggestion,
                'timestamp': current_time
            }
            f.write(json.dumps(alert_log, ensure_ascii=False) + '\n')
    
    logger.info(f"  Logged {len(all_alerts)} alerts to {alert_log_path}")
    
    # ===========================================
    # Step 4: 更新宏观大佬观点（每天更新一次缓存）
    # ===========================================
    logger.info("▶️ Step 4: Fetching latest macro guru views...")
    from src.monitor.guru_fetcher import GuruViewsFetcher
    guru_fetcher = GuruViewsFetcher(data_dir=config.data_dir)
    guru_views = guru_fetcher.get_cached_views()  # 自动缓存，一天更新一次
    logger.info(f"✅ Completed: Loaded {len(guru_views)} guru views")
    
    # ===========================================
    # Step 5: 组装通知内容 + LLM综合分析
    # ===========================================
    logger.info("▶️ Step 5: Building notification content...")
    
    content_parts = []
    gold_price = None
    silver_price = None
    
    # 经济日历 - 提前提醒明天高影响事件
    if config.monitor.economic_calendar.get('enabled', True):
        from src.monitor.economic_calendar import EconomicCalendar
        calendar = EconomicCalendar()
        events = calendar.get_high_impact_events_next_day()
        if events:
            content_parts.append(calendar.format_events_for_notification(events))
    
    # 添加今日行情概览 - 主动提供市场概况，即使没有预警
    crude_oil_price = None
    if len(prices) > 0:
        content_parts.append("---\n\n");
        content_parts.append("# 📈 今日行情概览\n\n");
        # 找到黄金、白银和原油最新价格
        from datetime import datetime
        current_dt = datetime.now().strftime("%Y-%m-%d %H:%M GMT+8")
        content_parts.append(f"**🕒 更新时间**: {current_dt}\n\n");
        
        # 找到黄金、白银和原油最新价格
        for p in prices:
            if p.symbol in ['XAUUSD', 'gold']:
                gold_price = p
            if p.symbol in ['XAGUSD', 'silver']:
                silver_price = p
            if p.symbol in ['CL', 'CO', 'crude_oil']:
                crude_oil_price = p
        
        # 绿表示上涨，红表示下跌（国内习惯：绿涨红跌）
        def get_change_emoji(change):
            return '🟢↑' if change >= 0 else '🔴↓'
        
        # 价格表格形式展示
        content_parts.append("## 核心价格\n\n");
        content_parts.append("| 品种 | 价格 | 涨跌 | 日涨幅 | 数据来源 |\n");
        content_parts.append("|------|------|------|--------|----------|\n");
        
        if gold_price:
            change_emoji = get_change_emoji(gold_price.change)
            change_str = f"{abs(gold_price.change):.2f}" if abs(gold_price.change) >= 0.01 else ""
            content_parts.append(f"| **伦敦现货黄金 (LBMA)** | **{gold_price.price:.2f}** | {change_emoji} {change_str} | {gold_price.change_pct:.2f}% | LBMA |\n");
        
        if silver_price:
            change_emoji = get_change_emoji(silver_price.change)
            change_str = f"{abs(silver_price.change):.2f}" if abs(silver_price.change) >= 0.01 else ""
            content_parts.append(f"| **伦敦现货白银 (LBMA)** | **{silver_price.price:.2f}** | {change_emoji} {change_str} | {silver_price.change_pct:.2f}% | LBMA |\n");
        
        if crude_oil_price:
            change_emoji = get_change_emoji(crude_oil_price.change)
            change_str = f"{abs(crude_oil_price.change):.2f}" if abs(crude_oil_price.change) >= 0.01 else ""
            content_parts.append(f"| **WTI原油期货 (NYMEX)** | **{crude_oil_price.price:.2f}** | {change_emoji} {change_str} | {crude_oil_price.change_pct:.2f}% | NYMEX |\n");
        
        content_parts.append("\n");
        
        # 关键数据速览表格
        content_parts.append("## 📊 关键宏观比率\n\n");
        content_parts.append("| 指标     | 当前值 | 位置解读          | 主流正常区间 |\n");
        content_parts.append("|----------|--------|-------------------|--------------|\n");
        
        # 金银比
        gold_silver_ratio = None
        if gold_price is not None and silver_price is not None and silver_price.price > 0:
            gold_silver_ratio = gold_price.price / silver_price.price
            gs_ratio = gold_silver_ratio
            if gs_ratio > 85:
                interpretation = "🔺 白银极端低估区间"
            elif gs_ratio < 55:
                interpretation = "🔻 黄金极端低估区间"
            else:
                interpretation = "✅ 正常区间"
            content_parts.append(f"| **金银比** | {gs_ratio:.1f} | {interpretation} | 55–85       |\n");
        else:
            content_parts.append("| **金银比** | -      | 数据缺失         | 55–85       |\n");
        
        # 金油比
        gold_oil_ratio = None
        if gold_price is not None and crude_oil_price is not None and crude_oil_price.price > 0:
            gold_oil_ratio = gold_price.price / crude_oil_price.price
            go_ratio = gold_oil_ratio
            if go_ratio > 50:
                interpretation = "🟡 黄金仍偏贵，原油更有机会"
            elif go_ratio > 40:
                interpretation = "🟡 高于历史常态"
            elif go_ratio >= 20:
                interpretation = "⚪ 正常区间"
            elif go_ratio >= 15:
                interpretation = "🟢 黄金更有相对机会"
            else:
                interpretation = "🔵 极端低位"
            content_parts.append(f"| **金油比** | {go_ratio:.1f} | {interpretation} | 15–40       |\n");
        else:
            content_parts.append("| **金油比** | -      | 数据缺失         | 15–40       |\n");
        
        content_parts.append("\n");
        content_parts.append("---\n\n");
    
    # 触发预警列表 - 放前面，用户先看警报
    if len(all_alerts) > 0:
        content_parts.append("## ⚠️ 触发预警\n\n");
        content_parts.append(format_alerts(all_alerts));
        content_parts.append("\n---\n\n");
    else:
        content_parts.append("## ✅ 当前无预警\n\n");
        content_parts.append("当前没有触发预警规则，市场平稳运行。\n\n---\n\n");
    
    # 最新研报/新闻总结
    if len(summaries) > 0:
        content_parts.append("## 📑 最新研报/新闻总结\n\n");
        for s in summaries:
            content_parts.append(f"**[{s['title']}]({s['url']})**\n\n");
            for i, point in enumerate(s['summary'], 1):
                content_parts.append(f"{i}. {point}\n");
            content_parts.append("\n---\n\n");
    
    # 4. ETF-COMEX 关联分析（预留框架）
    etf_comex_analysis = None
    if config.monitor.etf_monitor.get('enabled', False):
        logger.info("Step 4: ETF-COMEX correlation analysis...")
        from src.alert import ETFCOMEXAnalyzer
        # 这里获取最新变化，框架已经打好，具体数据获取在price_monitor
        # 这里整合分析结果
        # 预留整合位置，具体数据解析后续完善
        # etf_comex_analysis = ETFCOMEXAnalyzer.analize(...)
        if etf_comex_analysis is not None:
            content_parts.append(ETFCOMEXAnalyzer.format_for_notification(etf_comex_analysis))
            content_parts.append("\n---\n\n")
    
    # ===========================================
    # Step 6: LLM综合分析 - 结合所有信号给出最终判断，包括中东局势分析
    # ===========================================
    if config.llm.api_key and gold_price and silver_price:
        logger.info("▶️ Step 6: Generating LLM comprehensive analysis...")
        summarizer = ReportSummarizer(
            config.llm.api_key,
            config.llm.model,
            config.llm.base_url
        )
        
        # 准备市场数据
        market_data = {
            "gold_price": gold_price.price if gold_price else None,
            "silver_price": silver_price.price if silver_price else None,
            "crude_oil_price": crude_oil_price.price if crude_oil_price else None,
            "gold_change_pct": gold_price.change_pct if gold_price else None,
            "silver_change_pct": silver_price.change_pct if silver_price else None,
            "crude_oil_change_pct": crude_oil_price.change_pct if crude_oil_price else None,
            "gold_silver_ratio": (gold_price.price / silver_price.price) if gold_price and silver_price else None,
            "gold_oil_ratio": (gold_price.price / crude_oil_price.price) if gold_price and crude_oil_price else None
        }
        
        # 整理信号列表
        signal_list = [f"{a.message} → {a.suggestion}" for a in all_alerts]
        
        # 分离中东局势相关新闻
        middle_east_news = []
        for news_item in news:
            title_lower = news_item.title.lower()
            if any(kw.lower() in title_lower for kw in MIDDLE_EAST_KEYWORDS):
                middle_east_news.append(news_item)
        
        # 使用优化后的generate_trading_advice生成分析，包含中东局势逻辑
        try:
            analysis = summarizer.generate_trading_advice(
                market_data, 
                signal_list, 
                strategy_cycle="medium",
                middle_east_news=middle_east_news
            )
            if analysis:
                content_parts.append("\n---\n\n")
                content_parts.append("## 🧠 AI 综合分析\n\n")
                content_parts.append(analysis + "\n\n")
                logger.info("✅ Completed: LLM comprehensive analysis with Middle East局势 integration")
        except Exception as e:
            logger.error(f"Failed to generate LLM analysis: {e}");
    
    # ===========================================
    # Step 7: 长期概率预测（新增 - 混合模型）
    # ===========================================
    if config.forecast.enabled and config.llm.api_key and gold_price and crude_oil_price:
        logger.info("▶️ Step 7: Generating long-term probability forecast (mixed model)...");
        
        if config.forecast.use_mixed_model:
            # 使用混合模型: Macro Agent + Quant Agent + LLM Scenario + Risk Agent
            from src.research.forecast_mixed import MixedGoldForecaster
            
            forecaster = MixedGoldForecaster(
                openai_api_key=config.llm.api_key,
                openai_model=config.llm.model,
                openai_base_url=config.llm.base_url,
                fred_api_key=config.data_api.get('fred', None) if 'data_api' in config else None,
                xgb_model_path=config.forecast.xgb_model_path,
            );
            
            try:
                forecast_text = forecaster.forecast(
                    current_gold_price=gold_price.price,
                    gold_silver_ratio=gold_silver_ratio if gold_silver_ratio else 0,
                    gold_oil_ratio=gold_oil_ratio if gold_oil_ratio else 0,
                    geo_risk_score=geo_risk_score if 'geo_risk_score' in locals() else len([n for n in news if any(kw.lower() in n.title.lower() for kw in ['中东','以色列','哈马斯','伊朗','也门','胡塞','海湾','原油','油价','石油','中东局势','巴以','伊核','霍尔木兹'])]) * 2,
                    middle_east_news=[n for n in news if any(kw.lower() in n.title.lower() for kw in ['中东','以色列','哈马斯','伊朗','也门','胡塞','海湾','原油','油价','石油','中东局势','巴以','伊核','霍尔木兹'])],
                );
                if forecast_text:
                    content_parts.append("\n---\n\n");
                    content_parts.append("## 🔮 长期概率预测 (混合模型)\n\n");
                    content_parts.append(forecast_text + "\n\n");
                    logger.info("✅ Completed: Long-term probability forecast (mixed model) generated");
            except Exception as e:
                logger.error(f"Failed to generate mixed forecast: {e}");
        else:
            # 使用MVP LLM-only版本
            from src.research.forecast import GoldPriceForecaster
            
            forecaster = GoldPriceForecaster(
                config.llm.api_key,
                config.llm.model,
                config.llm.base_url
            );
            
            # 构建预测输入
            from src.research.forecast import ForecastInput
            forecast_input = ForecastInput(
                current_gold_price=gold_price.price,
                current_silver_price=silver_price.price if silver_price else 0,
                current_crude_price=crude_oil_price.price,
                gold_silver_ratio=gold_silver_ratio if gold_silver_ratio else 0,
                gold_oil_ratio=gold_oil_ratio if gold_oil_ratio else 0,
                geo_risk_score=geo_risk_score if 'geo_risk_score' in locals() else len([n for n in news if any(kw.lower() in n.title.lower() for kw in ['中东','以色列','哈马斯','伊朗','也门','胡塞','海湾','原油','油价','石油','中东局势','巴以','伊核','霍尔木兹'])]) * 2,
                middle_east_news=[n for n in news if any(kw.lower() in n.title.lower() for kw in ['中东','以色列','哈马斯','伊朗','也门','胡塞','海湾','原油','油价','石油','中东局势','巴以','伊核','霍尔木兹'])],
            );
            
            try:
                forecast_text = forecaster.generate_forecast(forecast_input);
                if forecast_text:
                    content_parts.append("\n---\n\n");
                    content_parts.append("## 🔮 长期概率预测 (MVP)\n\n");
                    content_parts.append(forecast_text + "\n\n");
                    logger.info("✅ Completed: Long-term probability forecast (MVP) generated");
            except Exception as e:
                logger.error(f"Failed to generate forecast: {e}");
    
    # ===========================================
    # Step 8: 多情景逻辑推演（参考MiroFish思想）
    # 基于新闻（消息面）和K线（技术面）进行多情景模拟
    # ===========================================
    if config.scenario.enabled and config.llm.api_key and gold_price and silver_price:
        logger.info("▶️ Step 8: Running multi-scenario simulation...");
        from src.research.scenario_simulation import ScenarioSimulator
        
        simulator = ScenarioSimulator(
            config.llm.api_key,
            config.llm.model,
            config.llm.base_url
        );
        
        # 准备技术指标
        technical_indicators = {}
        if gold_df is not None and len(gold_df) > 0:
            # 从gold_df中提取简单技术指标
            last_row = gold_df.iloc[-1]
            technical_indicators['close'] = last_row['close']
            if 'sma_20' in last_row:
                technical_indicators['sma_20'] = last_row['sma_20']
            if 'sma_50' in last_row:
                technical_indicators['sma_50'] = last_row['sma_50']
        
        # 准备新闻列表（仅标题）
        news_titles = [n.title for n in news[:10]]
        
        try:
            branches = simulator.simulate(
                current_gold_price=gold_price.price if gold_price else 0,
                current_silver_price=silver_price.price if silver_price else 0,
                crude_oil_price=crude_oil_price.price if crude_oil_price else 0,
                gold_silver_ratio=gold_silver_ratio if gold_silver_ratio else 0,
                gold_oil_ratio=gold_oil_ratio if gold_oil_ratio else 0,
                recent_news=news_titles,
                technical_indicators=technical_indicators,
            );
            if len(branches) > 0:
                content_parts.append("\n---\n\n");
                content_parts.append("## 🎯 多情景逻辑推演（参考MiroFish思想）\n\n");
                content_parts.append(simulator.format_for_report(branches) + "\n\n");
                logger.info("✅ Completed: Multi-scenario simulation");
        except Exception as e:
            logger.error(f"Failed to run scenario simulation: {e}");
    
    # 免责声明 + 版本更新提示
    content_parts.append("\n---\n\n");
    content_parts.append("## ⚠️ 免责声明\n\n");
    content_parts.append("本报告仅供研究参考，不构成任何投资建议。投资有风险，入市需谨慎，交易请严格设置止损。\n\n");
    
    content_parts.append("## 📊 本次监控概览\n\n");
    content_parts.append("| 项目 | 数量 |\n");
    content_parts.append("|------|------|\n");
    content_parts.append(f"| 价格数据 | {len(prices)} |\n");
    content_parts.append(f"| 新闻资讯 | {len(news)} |\n");
    content_parts.append(f"| 总结内容 | {len(summaries)} |\n");
    content_parts.append(f"| 触发预警 | {len(all_alerts)} |\n");
    content_parts.append("\n");
    content_parts.append("---\n\n");
    content_parts.append("**gold-silver-finance-agent** | AI 赋能黄金白银智能监控\n");
    content_parts.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n");
    
    # ===========================================
    # 发送通知
    # ===========================================
    full_content = ''.join(content_parts)
    title = f"🤖 黄金白银监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    logger.info("📤 Sending notification...")
    notified = send_notification(config, title, full_content)
    
    if notified:
        logger.info("✅ Notification sent successfully")
    else:
        logger.info("ℹ️ No notification channels enabled or send failed")
    
    logger.info("✅ Monitoring round completed!\n")
    return True

def main():
    parser = argparse.ArgumentParser(description='gold-silver-finance-agent - AI 赋能黄金白银主动监控 Agent')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--run-once', action='store_true', help='Run once and exit')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled monitoring')
    parser.add_argument('--web', action='store_true', help='Start web server for historical alerts')
    parser.add_argument('--port', default=5000, type=int, help='Web server port')
    parser.add_argument('--host', default='0.0.0.0', help='Web server host')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    # 创建数据目录
    os.makedirs(config.data_dir, exist_ok=True)
    os.makedirs(config.cache_dir, exist_ok=True)
    
    if args.web:
        # 启动Web服务器查看历史预警
        from src.web.app import run_web_server
        logger.info(f"Starting web server on {args.host}:{args.port}")
        run_web_server(host=args.host, port=args.port)
    elif args.run_once or not config.schedule.only_trading_hours:
        # 单次运行
        run_once(config)
    elif args.schedule:
        # 定时运行
        # 判断是否在交易时段
        def job():
            # 伦敦金交易时间处理：如果结束时间早于开始时间，说明跨天
            now = datetime.now()
            start_h, start_m = map(int, config.schedule.trading_hours.start.split(':'))
            end_h, end_m = map(int, config.schedule.trading_hours.end.split(':'))
            
            # 跨天（例如 06:00 ~ 次日 04:00）
            if end_h > start_h or (end_h == start_h and end_m > start_m):
                # 同一天内
                start_dt = now.replace(hour=start_h, minute=start_m, second=0)
                end_dt = now.replace(hour=end_h, minute=end_m, second=0)
                in_hours = start_dt <= now <= end_dt
            else:
                # 跨天
                if now.hour >= start_h or now.hour < end_h or (now.hour == end_h and now.minute < end_m):
                    in_hours = True
                else:
                    in_hours = False
            
            # 伦敦金：周一 (0) 到 周六 (5) 交易，周日 (6) 休市
            if in_hours and now.weekday() <= 5:  # 周一到周六
                run_once(config)
            else:
                logger.info("Not in trading hours, skipping")
        
        # 按间隔运行
        interval_minutes = config.monitor.interval
        logger.info(f"Starting scheduler, interval {interval_minutes} minutes")
        
        # 立即运行一次
        job()
        
        # 开始调度
        import schedule
        schedule.every(interval_minutes).minutes.do(job)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_once(config)

if __name__ == '__main__':
    main()
