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

@dataclass
class Config:
    """配置类"""
    log_level: str = "INFO"
    data_dir: str = "./data"
    cache_dir: str = "./cache"
    
    @dataclass
    class TushareConfig:
        token: str = ""
    tushare: TushareConfig = field(default_factory=TushareConfig)
    
    @dataclass
    class LLMConfig:
        provider: str = "openai"
        api_key: str = ""
        model: str = "gpt-4o-mini"
        base_url: str = ""
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    @dataclass
    class MonitorConfig:
        interval: int = 60
        stocks: List[str] = field(default_factory=list)
        gold: dict = field(default_factory=dict)
        silver: dict = field(default_factory=dict)
        etf_monitor: dict = field(default_factory=dict)
        news_sources: List[str] = field(default_factory=list)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    
    @dataclass
    class ResearchConfig:
        auto_fetch: bool = True
        only_related: bool = True
        summary_points: int = 3
    research: ResearchConfig = field(default_factory=ResearchConfig)
    
    @dataclass
    class AlertConfig:
        alerts: List[dict] = field(default_factory=list)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    
    @dataclass
    class NotifyConfig:
        @dataclass
        class DingTalkConfig:
            enabled: bool = False
            webhook_url: str = ""
            secret: str = ""
        dingtalk: DingTalkConfig = field(default_factory=DingTalkConfig)
        
        @dataclass
        class WorkWechatConfig:
            enabled: bool = False
            webhook_url: str = ""
        workwechat: WorkWechatConfig = field(default_factory=WorkWechatConfig)
        
        @dataclass
        class FeishuConfig:
            enabled: bool = False
            webhook_url: str = ""
        feishu: FeishuConfig = field(default_factory=FeishuConfig)
        
        @dataclass
        class TelegramConfig:
            enabled: bool = False
            bot_token: str = ""
            chat_id: str = ""
        telegram: TelegramConfig = field(default_factory=TelegramConfig)
    notify: NotifyConfig = field(default_factory=NotifyConfig)
    
    @dataclass
    class ScheduleConfig:
        only_trading_hours: bool = True
        @dataclass
        class TradingHours:
            start: str = "09:30"
            end: str = "15:00"
        trading_hours: TradingHours = field(default_factory=TradingHours)
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
        config.monitor.etf_monitor = data['monitor'].get('etf_monitor', {})
        config.monitor.news_sources = data['monitor'].get('news_sources', [])
    
    if 'research' in data:
        config.research.auto_fetch = data['research'].get('auto_fetch', True)
        config.research.only_related = data['research'].get('only_related', True)
        config.research.summary_points = data['research'].get('summary_points', 3)
    
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
            config.schedule.trading_hours.start = data['schedule']['trading_hours'].get('start', '09:30')
            config.schedule.trading_hours.end = data['schedule']['trading_hours'].get('end', '15:00')
    
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
    """运行一次完整监控流程"""
    logger.info("Starting finance agent monitoring round...")
    
    # 1. 监控 - 获取新闻和价格
    logger.info("Step 1: Fetching latest data...")
    
    # 价格监控 - 专注黄金白银
    price_monitor = PriceMonitor(
        config.tushare.token,
        config.monitor.stocks,
        config.monitor.gold.get('enabled', True),
        config.monitor.silver.get('enabled', True),
        config.monitor.etf_monitor.get('enabled', True)
    )
    prices = price_monitor.fetch_latest()
    
    # 新闻监控
    news_monitor = NewsMonitor(config.monitor.news_sources)
    news = news_monitor.fetch_latest(hours=config.monitor.interval)
    
    logger.info(f"Fetched {len(prices)} prices, {len(news)} news")
    
    # 2. 研报总结 - 如果有相关新闻
    summaries = []
    if config.research.auto_fetch and len(news) > 0:
        logger.info("Step 2: Summarizing related news/reports...")
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
        
        for news_item in news[:5]:  # 最多处理5条
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
    
    logger.info(f"Summarized {len(summaries)} news items")
    
    # 3. 预警检查
    logger.info("Step 3: Checking alert rules...")
    trigger = AlertTrigger(config.alerts.alerts)
    all_alerts = []
    
    for symbol in config.monitor.stocks:
        df = price_monitor.get_history(symbol, start_date='20240101')
        if not df.empty:
            alerts = trigger.check_all(symbol, df)
            all_alerts.extend(alerts)
    
    # TODO: gold 单独处理
    logger.info(f"Found {len(all_alerts)} triggered alerts")
    
    # 4. 发送通知
    logger.info("Step 4: Sending notification...")
    
    content_parts = []
    
    if len(summaries) > 0:
        content_parts.append("### 📑 最新研报/新闻总结\n\n")
        for s in summaries:
            content_parts.append(f"**[{s['title']}]({s['url']})**\n\n")
            for i, point in enumerate(s['summary'], 1):
                content_parts.append(f"{i}. {point}\n")
            content_parts.append("\n---\n\n")
    
    if len(all_alerts) > 0:
        content_parts.append("### ⚠️ 触发预警\n\n")
        content_parts.append(format_alerts(all_alerts))
        content_parts.append("\n")
    else:
        content_parts.append("✅ 没有触发预警规则，市场平稳。\n\n")
    
    content_parts.append(f"📊 本次监控完成: {len(prices)} 价格, {len(news)} 新闻, {len(summaries)} 总结, {len(all_alerts)} 预警")
    
    full_content = ''.join(content_parts)
    title = f"🤖 Active Finance Agent 监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    notified = send_notification(config, title, full_content)
    
    if notified:
        logger.info("Notification sent successfully")
    else:
        logger.info("No notification channels enabled or send failed")
    
    logger.info("Monitoring round completed")
    return True

def main():
    parser = argparse.ArgumentParser(description='Active Finance Agent - 主动式个人财务资产监控')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    parser.add_argument('--run-once', action='store_true', help='Run once and exit')
    parser.add_argument('--schedule', action='store_true', help='Start scheduled monitoring')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    # 创建数据目录
    os.makedirs(config.data_dir, exist_ok=True)
    os.makedirs(config.cache_dir, exist_ok=True)
    
    if args.run_once or not config.schedule.only_trading_hours:
        # 单次运行
        run_once(config)
    elif args.schedule:
        # 定时运行
        scheduler = TaskScheduler()
        
        def job():
            # 判断是否在交易时段
            now = datetime.now()
            start_h, start_m = map(int, config.schedule.trading_hours.start.split(':'))
            end_h, end_m = map(int, config.schedule.trading_hours.end.split(':'))
            
            start_dt = now.replace(hour=start_h, minute=start_m, second=0)
            end_dt = now.replace(hour=end_h, minute=end_m, second=0)
            
            if start_dt <= now <= end_dt and now.weekday() < 5:  # 工作日
                run_once(config)
            else:
                logger.info("Not in trading hours, skipping")
        
        # 按间隔运行
        interval_minutes = config.monitor.interval
        logger.info(f"Starting scheduler, interval {interval_minutes} minutes")
        
        # 立即运行一次
        job()
        
        # 开始调度 - 使用schedule每interval_minutes分钟运行
        import schedule
        schedule.every(interval_minutes).minutes.do(job)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_once(config)

if __name__ == '__main__':
    main()
