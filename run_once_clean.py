def run_once(config: Config) -> bool:
    """
    运行一次完整监控流程
    ===========================================
    Step 1: 获取最新数据（价格 + 新闻）
    Step 2: 新闻研报总结（LLM过滤总结）
    Step 3: 检查所有预警规则（技术指标 + COT + ETF）
    Step 4: 更新宏观大佬观点（每日自动更新缓存）
    Step 5: 组装通知 + LLM综合分析
    Step 6: 发送通知
    ===========================================
    """
    logger.info("Starting finance agent monitoring round...")
    
    # ===========================================
    # Step 1: 获取最新数据
    # ===========================================
    logger.info("▶️ Step 1: Fetching latest data...")
    
    # 价格监控 - 专注黄金白银
    price_monitor = PriceMonitor(
        config.tushare.token,
        config.monitor.stocks,
        config.monitor.gold.get('enabled', True),
        config.monitor.silver.get('enabled', True),
        config.monitor.etf_monitor.get('enabled', True),
        data_dir=config.data_dir
    )
    prices = price_monitor.fetch_latest()
    
    # 新闻监控
    news_monitor = NewsMonitor(config.monitor.news_sources)
    news = news_monitor.fetch_latest(hours=config.monitor.interval)
    
    logger.info(f"✅ Completed: Fetched {len(prices)} prices, {len(news)} news")
    
    # ===========================================
    # Step 2: 研报总结 - LLM过滤总结相关新闻
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
    if config.monitor.get('cot', {}).get('enabled', False):
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
    
    # ===========================================
    # 记录预警到日志文件供Web界面查看
    # ===========================================
    import json
    from pathlib import Path
    alert_log_path = Path(config.data_dir) / 'alerts.log'
    alert_log_path.parent.mkdir(exist_ok=True)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(alert_log_path, 'a', encoding='utf-8') as f:
        for alert in all_alerts:
            alert_log = {
                'name': alert.name,
                'asset': alert.asset,
                'type': alert.type,
                'message': alert.message,
                'suggestion': alert.suggestion,
                'timestamp': current_time
            }
            f.write(json.dumps(alert_log, ensure_ascii=False) + '\n')
    
    logger.info(f"  Logged {len(all_alerts)} alerts to {alert_log_path}")
    
    # ===========================================
    # Step 4: 更新宏观大佬观点（每日自动更新缓存）
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
    if config.monitor.get('economic_calendar', {}).get('enabled', True):
        from src.monitor.economic_calendar import EconomicCalendar
        calendar = EconomicCalendar()
        events = calendar.get_high_impact_events_next_day()
        if events:
            content_parts.append(calendar.format_events_for_notification(events))
    
    # 添加今日行情概览 - 主动提供市场概况，即使没有预警
    if len(prices) > 0:
        content_parts.append("### 📈 今日行情概览\n\n")
        # 找到黄金和白银最新价格
        for p in prices:
            if p.symbol in ['XAUUSD', 'gold']:
                gold_price = p
            if p.symbol in ['XAGUSD', 'silver']:
                silver_price = p
        
        if gold_price:
            change_emoji = '↑' if gold_price.change >= 0 else '↓'
            content_parts.append(f"**COMEX黄金**: {gold_price.price:.2f}  {change_emoji} {abs(gold_price.change):.2f} ({gold_price.change_pct:.2f}%)\n\n")
        
        if silver_price:
            change_emoji = '↑' if silver_price.change >= 0 else '↓'
            content_parts.append(f"**COMEX白银**: {silver_price.price:.2f}  {change_emoji} {abs(silver_price.change):.2f} ({silver_price.change_pct:.2f}%)\n\n")
        
        # 如果黄金白银都有数据，显示金银比
        if gold_price is not None and silver_price is not None and silver_price.price > 0:
            ratio = gold_price.price / silver_price.price
            if ratio > 80:
                content_parts.append(f"**金银比**: {ratio:.1f} 🔺 接近极端高估区间\n\n")
            elif ratio < 60:
                content_parts.append(f"**金银比**: {ratio:.1f} 🔻 接近极端低估区间\n\n")
            else:
                content_parts.append(f"**金银比**: {ratio:.1f} ✅ 在正常区间(60-80)内\n\n")
        
        # 添加技术指标概览
        if gold_df is not None and len(gold_df) >= 14:
            from src.alert.indicator import IndicatorCalculator
            rsi = IndicatorCalculator.rsi(gold_df, 14)
            current_rsi = rsi.iloc[-1]
            content_parts.append(f"黄金 RSI(14): {current_rsi:.1f}\n")
        
        if silver_df is not None and len(silver_df) >= 14:
            from src.alert.indicator import IndicatorCalculator
            rsi = IndicatorCalculator.rsi(silver_df, 14)
            current_rsi = rsi.iloc[-1]
            content_parts.append(f"白银 RSI(14): {current_rsi:.1f}\n")
        
        content_parts.append("---\n\n")
    
    # 最新研报/新闻总结
    if len(summaries) > 0:
        content_parts.append("### 📑 最新研报/新闻总结\n\n")
        for s in summaries:
            content_parts.append(f"**[{s['title']}]({s['url']})**\n\n")
            for i, point in enumerate(s['summary'], 1):
                content_parts.append(f"{i}. {point}\n")
            content_parts.append("\n---\n\n")
    
    # 触发预警列表
    if len(all_alerts) > 0:
        content_parts.append("### ⚠️ 触发预警\n\n")
        content_parts.append(format_alerts(all_alerts))
        content_parts.append("\n")
    else:
        content_parts.append("✅ 当前没有触发预警规则，市场平稳运行。\n\n")
    
    # ===========================================
    # Step 6: LLM综合分析 - 结合所有信号给出最终判断
    # ===========================================
    if config.llm.api_key and gold_price and silver_price:
        logger.info("▶️ Step 6: Generating LLM comprehensive analysis...")
        
        # 准备prompt
        analysis_prompt = f"""你是黄金白银市场专业分析师，请结合以下所有信息，给出今日综合分析和操作建议：

# 当前行情
- 黄金最新价格: {gold_price.price if gold_price else 'N/A'}
- 白银最新价格: {silver_price.price if silver_price else 'N/A'}
- 金银比: {f"{(gold_price.price / silver_price.price):.1f}" if gold_price and silver_price else 'N/A'}

# 触发的预警信号
{chr(10).join([f"- {a.message} → {a.suggestion}" for a in all_alerts]) if all_alerts else "无"}

# 最新宏观大佬观点
我们跟踪了5位顶级宏观大佬最新观点，请参考他们立场：
"""
        # 加入大佬观点
        for guru in guru_views:
            analysis_prompt += f"- **{guru['name']}** ({guru['title']}): {guru['latest_view']} → 基调: {guru['tone']}\n"
        
        analysis_prompt += """
# 要求
1. 综合以上所有信息，给出今日黄金/白银市场的多空判断
2. 结合技术信号、宏观观点、市场情绪，给出明确操作建议（多头/空头/观望）
3. 说明主要逻辑和风险点
4. 控制在300字以内，简洁明了

请开始分析：
"""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url or None
            )
            response = client.chat.completions.create(
                model=config.llm.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.7,
                max_tokens=600
            )
            analysis = response.choices[0].message.content.strip()
            content_parts.append("\n---\n\n")
            content_parts.append("### 🧠 AI 综合分析\n\n")
            content_parts.append(analysis + "\n\n")
            logger.info("✅ Completed: LLM comprehensive analysis")
        except Exception as e:
            logger.error(f"Failed to generate LLM analysis: {e}")
    
    # 页脚统计信息
    content_parts.append(f"📊 本次监控完成: {len(prices)} 价格, {len(news)} 新闻, {len(summaries)} 总结, {len(all_alerts)} 预警")
    
    # ===========================================
    # 发送通知
    # ===========================================
    full_content = ''.join(content_parts)
    title = f"🤖 Active Finance Agent 监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    logger.info("📤 Sending notification...")
    notified = send_notification(config, title, full_content)
    
    if notified:
        logger.info("✅ Notification sent successfully")
    else:
        logger.info("ℹ️ No notification channels enabled or send failed")
    
    logger.info("✅ Monitoring round completed!\n")
    return True
