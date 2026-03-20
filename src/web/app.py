import logging
import json
import requests
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tushare as ts
import uvicorn
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

app = FastAPI(title="gold-silver-finance-agent Web API")

# 添加CORS跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 预警日志文件路径
ALERT_LOG_PATH = Path('./data/alerts.log')

# 获取当前文件所在目录
CURRENT_DIR = Path(__file__).parent
TEMPLATE_DIR = CURRENT_DIR / 'templates'
STATIC_DIR = CURRENT_DIR / 'static'

# 读取配置获取tushare token
def get_tushare_token():
    """从配置文件读取tushare token"""
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        config_path = Path('config/config.example.yaml')
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('tushare', {}).get('token', '')
    except:
        return ''

def load_alerts():
    """加载历史预警"""
    alerts = []
    if not ALERT_LOG_PATH.exists():
        return alerts
    
    with open(ALERT_LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                alert = json.loads(line)
                alerts.append(alert)
            except:
                continue
    
    # 按时间倒序排列
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return alerts

@app.get("/", response_class=HTMLResponse)
async def index():
    """首页 - 显示历史预警 (Vue 前端)"""
    with open(TEMPLATE_DIR / 'index.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

# 挂载静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/api/alerts")
async def api_alerts():
    """API - 获取预警列表"""
    alerts = load_alerts()
    return {
        'count': len(alerts),
        'alerts': alerts
    }

@app.get("/api/stats")
async def api_stats():
    """API - 获取统计信息"""
    alerts = load_alerts()
    stats = {
        'total': len(alerts),
        'by_asset': {},
        'by_signal_type': {}
    }
    
    for alert in alerts:
        asset = alert.get('asset', 'unknown')
        signal_type = alert.get('type', 'unknown')
        
        if asset not in stats['by_asset']:
            stats['by_asset'][asset] = 0
        stats['by_asset'][asset] += 1
        
        if signal_type not in stats['by_signal_type']:
            stats['by_signal_type'][signal_type] = 0
        stats['by_signal_type'][signal_type] += 1
    
    return stats

@app.get("/api/price/{symbol}")
async def api_price(symbol: str):
    """API - 获取价格历史数据用于K线图
    - 对于 XAUUSD/XAGUSD/CL 从本地CSV读取（国际黄金/白银/原油），如果没有则实时获取
    - 对于其他symbol从tushare读取
    """
    from pathlib import Path
    import pandas as pd
    from datetime import datetime
    
    # 国际黄金/白银/原油
    if symbol in ['XAUUSD', 'XAGUSD', 'CL']:
        data_dir = Path('./data')
        csv_path = data_dir / f"{symbol}_prices.csv"
        candles = []
        
        # 如果本地有历史数据，读取
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                df = df.sort_values('trade_date')
                
                # 获取最近一年的数据
                if len(df) > 365:
                    df = df.tail(365)
                
                # 转换格式
                for _, row in df.iterrows():
                    date_str = str(int(row.trade_date))
                    dt = datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
                    timestamp = int(dt.timestamp())
                    candles.append({
                        'time': timestamp,
                        'open': float(row.open),
                        'high': float(row.high),
                        'low': float(row.low),
                        'close': float(row.close),
                        'volume': float(row.vol) if row.vol else 0
                    })
            except Exception as e:
                logger.error(f"Failed to read local price for {symbol}: {e}")
        
        # 每次请求都实时获取最新价格，更新本地数据
        try:
            from datetime import date
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://stockapp.finance.qq.com/",
                "Origin": "https://stockapp.finance.qq.com"
            }
            url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/rank/worldCommodities?"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                price = None
                change_pct = 0
                target_code_map = {
                    'XAUUSD': 'XAU',       # 伦敦现货黄金
                    'XAGUSD': 'XAG',       # 伦敦现货白银
                    'CL': 'CL',            # WTI原油
                }
                target_code = target_code_map.get(symbol)
                
                if data.get("code") == 0 and "data" in data and target_code:
                    # Select correct list based on asset type
                    items = None
                    if symbol in ['XAUUSD', 'XAGUSD'] and "preciousMetal" in data["data"]:
                        items = data["data"]["preciousMetal"]
                    elif symbol == 'CL' and "energy" in data["data"]:
                        items = data["data"]["energy"]
                    
                    if items:
                        for item in items:
                            if item["code"] == target_code:
                                price = float(item["zxj"])
                                if "zde" in item:
                                    change = float(item["zde"])  # zde already is percentage change
                                break
                
                # 如果成功获取到价格，更新到本地CSV
                if price is not None:
                    today = datetime.now()
                    today_date = date.today()
                    today_str = int(today_date.strftime('%Y%m%d'))
                    
                    # 更新DataFrame
                    if 'df' in locals() and len(df) > 0:
                        if len(df[df['trade_date'] == today_str]) > 0:
                            # 更新今天的价格
                            df.loc[df['trade_date'] == today_str, 'close'] = price
                            df.loc[df['trade_date'] == today_str, 'open'] = price
                            df.loc[df['trade_date'] == today_str, 'high'] = price
                            df.loc[df['trade_date'] == today_str, 'low'] = price
                        else:
                            # 添加今天的新行
                            new_row = pd.DataFrame([{
                                'trade_date': today_str,
                                'open': price,
                                'high': price,
                                'low': price,
                                'close': price,
                                'vol': 0
                            }])
                            df = pd.concat([df, new_row], ignore_index=True)
                        
                        # 保存更新后的CSV
                        df = df.sort_values('trade_date')
                        df.to_csv(csv_path, index=False)
                        
                        # 更新candles最后一个价格
                        for candle in candles:
                            if candle['time'] == int(today.timestamp()):
                                candle['close'] = price
                                candle['open'] = price
                                candle['high'] = price
                                candle['low'] = price
                                break
                        else:
                            candles.append({
                                'time': int(today.timestamp()),
                                'open': price,
                                'high': price,
                                'low': price,
                                'close': price,
                                'volume': 0
                            })
        except Exception as e:
            logger.error(f"Failed to fetch/update realtime price for {symbol}: {e}")
            # 失败了也不影响，继续返回已有数据
        
        latest = candles[-1] if len(candles) > 0 else None
        
        return {
            'symbol': symbol,
            'latest': latest,
            'count': len(candles),
            'data': candles
        }
    
    # 其他symbol从tushare读取
    token = get_tushare_token()
    if not token:
        return {'error': 'Tushare token not configured', 'data': []}
    
    try:
        ts.set_token(token)
        pro = ts.pro_api()
        # 获取最近一年的数据
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        df = pro.daily(ts_code=symbol, start_date=start_date)
        df = df.sort_values('trade_date')
        
        # 转换为K线图需要的格式
        candles = []
        for _, row in df.iterrows():
            # 转换时间格式 trade_date YYYYMMDD -> timestamp
            date_str = str(row.trade_date)
            dt = datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
            timestamp = int(dt.timestamp())
            candles.append({
                'time': timestamp,
                'open': float(row.open),
                'high': float(row.high),
                'low': float(row.low),
                'close': float(row.close),
                'volume': float(row.vol) if row.vol else 0
            })
        
        latest = candles[-1] if candles else None
        
        return {
            'symbol': symbol,
            'latest': latest,
            'count': len(candles),
            'data': candles
        }
    except Exception as e:
        logger.error(f"Failed to fetch price for {symbol}: {e}")
        return {'error': str(e), 'data': []}

@app.get("/api/guru-views")
async def api_guru_views():
    """获取大佬最新观点"""
    try:
        from src.monitor.guru_fetcher import GuruViewsFetcher
        
        # 数据目录
        data_dir = "./data"
        fetcher = GuruViewsFetcher(data_dir=data_dir)
        views = fetcher.get_cached_views()
        return {
            'success': True,
            'data': views
        }
    except Exception as e:
        logger.error(f"Failed to fetch guru views: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': []
        }

@app.post("/api/chat")
async def api_chat(request: Request):
    """聊天 API - 基于当前信息进行 AI 对话"""
    try:
        from typing import Optional, Dict, Any
        
        # 解析请求
        json_body = await request.json()
        user_message = json_body.get('message', '')
        context = json_body.get('context', {})
        
        # 读取配置，获取 LLM API key
        config_path = Path('config/config.yaml')
        llm_api_key = ''
        llm_base_url = ''
        llm_model = 'gpt-4o-mini'
        
        try:
            if config_path.exists():
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                if 'llm' in config:
                    llm_api_key = config['llm'].get('api_key', '')
                    llm_base_url = config['llm'].get('base_url', '')
                    llm_model = config['llm'].get('model', 'gpt-4o-mini')
        except Exception as e:
            logger.warning(f"Failed to load LLM config: {e}")
        
        # 如果没有配置 LLM，返回友好的默认响应
        if not llm_api_key or llm_api_key in ['your-openai-api-key', '']:
            return {
                'success': True,
                'message': '你好！我是黄金白银 AI 助手。\n\n目前我处于离线模式，但我可以帮你：\n\n1. 📊 查看实时价格走势\n2. 🌍 了解地缘政治风险地图\n3. ⚠️ 查看市场预警信号\n4. 🧠 阅读宏观大佬观点\n\n如需完整的 AI 分析功能，请在 `config/config.yaml` 中配置你的 LLM API Key。'
            }
        
        # 构建系统提示
        system_prompt = """你是一位资深的黄金白银市场分析师，拥有15年以上的贵金属市场研究经验。

你的专业领域：
1. 地缘政治风险（特别是中东局势）对贵金属价格的影响机制
2. 全球宏观经济指标与金银价格的相关性分析
3. 大宗商品市场（黄金、白银、原油）的联动效应
4. 市场情绪分析与资金流向追踪
5. 多情景推演与风险收益评估

你的回答原则：
1. 专业严谨：基于数据和事实，避免主观臆断
2. 量化优先：优先使用百分比、价格区间、时间周期等量化指标
3. 逻辑清晰：分点说明，层次分明
4. 风险提示：所有建议必须包含风险提示
5. 行动导向：给出明确的观察指标和操作建议

回答结构（适用于复杂问题）：
【核心观点】一句话总结
【关键逻辑】分点说明推理过程
【价格影响】给出具体的价格区间预估
【操作建议】明确的行动建议
【风险提示】必须包含的风险因素

请基于当前提供的上下文信息，给出专业、严谨、有深度的分析。
"""
        
        # 构建上下文信息
        context_text = "当前市场信息：\n"
        
        # 中东局势情景
        if 'middleEastScenarios' in context:
            scenarios = context['middleEastScenarios']
            context_text += "\n中东局势情景：\n"
            for s in scenarios:
                context_text += f"- {s['name']} (概率 {s['probability']*100:.0f}%): 黄金 {s['gold_price_range']}, 白银 {s['silver_price_range']}, 原油 {s['crude_price_range']}\n"
        
        # 大佬观点
        if 'guruViews' in context:
            gurus = context['guruViews']
            context_text += "\n大佬观点：\n"
            for g in gurus[:3]:
                context_text += f"- {g.get('name', 'Unknown')}: {g.get('view', g.get('latest_view', ''))}\n"
        
        # 最近预警
        if 'recentAlerts' in context:
            alerts = context['recentAlerts']
            context_text += "\n最近预警：\n"
            for a in alerts:
                asset = a.get('asset', 'Unknown')
                message = a.get('message', '')
                context_text += f"- {asset}: {message}\n"
        
        # 当前价格
        if 'currentPrice' in context:
            context_text += f"\n当前价格: {context['currentPrice']}\n"
        
        from openai import OpenAI
        client = OpenAI(
            api_key=llm_api_key,
            base_url=llm_base_url if llm_base_url else None
        )
        
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context_text}\n\n用户问题: {user_message}"}
            ],
            temperature=0.7,
            max_tokens=32768
        )
        
        assistant_message = response.choices[0].message.content
        
        return {
            'success': True,
            'message': assistant_message
        }
        
    except Exception as e:
        logger.error(f"Chat API failed: {e}")
        return {
            'success': False,
            'message': f'发生错误：{str(e)}'
        }

def run_web_server(host='0.0.0.0', port=5000):
    """启动Web服务器"""
    # 确保data目录存在
    ALERT_LOG_PATH.parent.mkdir(exist_ok=True)
    uvicorn.run(app, host=host, port=port)


# 中东局势沙盘缓存（每10分钟更新一次）
_middle_east_cache = {
    'data': None,
    'last_updated': 0
}

def get_default_middle_east_scenarios():
    """获取默认的伊朗局势焦点情景"""
    return [
        {
            'name': '维持现状 (Status Quo)',
            'type': 'status-quo',
            'probability': 0.55,
            'gold_price_range': '4800-5100',
            'silver_price_range': '74-78',
            'crude_price_range': '95-105',
            'suggested_action': 'wait',
            'action_text': '观望持有',
            'trigger_signals': [
                '伊朗局势保持稳定，无新的军事行动',
                '霍尔木兹海峡航运正常',
                '以色列与伊朗未发生直接冲突'
            ]
        },
        {
            'name': '局势缓和 (De-escalation)',
            'type': 'de-escalation',
            'probability': 0.2,
            'gold_price_range': '4600-4900',
            'silver_price_range': '71-75',
            'crude_price_range': '88-98',
            'suggested_action': 'sell',
            'action_text': '减持黄金',
            'trigger_signals': [
                '美国与伊朗达成新的协议',
                '伊朗石油出口恢复正常',
                '地缘紧张局势缓解'
            ]
        },
        {
            'name': '局势升级 (Escalation)',
            'type': 'escalation',
            'probability': 0.2,
            'gold_price_range': '5100-5400',
            'silver_price_range': '78-83',
            'crude_price_range': '105-115',
            'suggested_action': 'buy',
            'action_text': '增持黄金',
            'trigger_signals': [
                '伊朗革命卫队发动军事行动',
                '霍尔木兹海峡航运受阻',
                '伊朗核设施受到打击'
            ]
        },
        {
            'name': '重大危机 (Major Crisis)',
            'type': 'major-crisis',
            'probability': 0.05,
            'gold_price_range': '5400-5900',
            'silver_price_range': '83-92',
            'crude_price_range': '115-130',
            'suggested_action': 'buy',
            'action_text': '重仓做多',
            'trigger_signals': [
                '伊朗与美国/以色列爆发全面冲突',
                '霍尔木兹海峡完全封锁',
                '中东地区爆发大规模战争'
            ]
        }
    ]

@app.get("/api/middle-east-scenarios")
async def api_middle_east_scenarios():
    """API - 获取中东局势推演沙盘（每10分钟更新，基于实时新闻）"""
    import time
    from datetime import datetime
    
    current_time = time.time()
    cache_ttl = 600  # 10分钟缓存
    
    # 如果缓存存在且未过期，直接返回
    if _middle_east_cache['data'] and (current_time - _middle_east_cache['last_updated'] < cache_ttl):
        return {
            'success': True,
            'data': _middle_east_cache['data'],
            'cached': True,
            'last_updated': _middle_east_cache['last_updated']
        }
    
    # 读取配置，尝试使用 LLM 生成真实数据
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        config_path = Path('config/config.example.yaml')
    
    llm_api_key = ''
    llm_base_url = ''
    llm_model = 'gpt-4o-mini'
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        if 'llm' in config:
            llm_api_key = config['llm'].get('api_key', '')
            llm_base_url = config['llm'].get('base_url', '')
            llm_model = config['llm'].get('model', 'gpt-4o-mini')
    except:
        pass
    
    scenarios = get_default_middle_east_scenarios()
    
    # 抓取中东实时新闻
    latest_news = []
    try:
        from monitor.news_monitor import NewsMonitor
        news_monitor = NewsMonitor(regions=['middle_east'])
        latest_news = news_monitor.fetch_latest(hours=6)
        logger.info(f"Fetched {len(latest_news)} Middle East news items")
    except Exception as e:
        logger.warning(f"Failed to fetch Middle East news: {e}")
    
    # 如果配置了 LLM，尝试基于实时新闻生成真实数据
    if llm_api_key:
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=llm_api_key,
                base_url=llm_base_url if llm_base_url else None
            )
            
            # 构建新闻上下文
            news_context = ""
            if latest_news:
                news_context = "以下是最近6小时的中东相关新闻：\n"
                for i, news in enumerate(latest_news[:5]):
                    news_context += f"{i+1}. {news.title}\n"
            
            system_prompt = """你是一位专业的地缘政治与大宗商品分析师。

请基于当前中东局势（重点关注伊朗），返回4种情景的JSON数据，格式如下：
[
  {
    "name": "情景名称",
    "type": "status-quo|de-escalation|escalation|major-crisis",
    "probability": 0.0-1.0,
    "gold_price_range": "4800-5100",
    "silver_price_range": "74-78",
    "crude_price_range": "95-105",
    "suggested_action": "buy|sell|wait",
    "action_text": "操作建议文本",
    "trigger_signals": ["信号1", "信号2", "信号3"]
  }
]

注意：
- 4种情景概率总和应为 1
- type 必须是这4个值之一
- 重点关注伊朗局势
- 如果提供了实时新闻，请基于新闻内容来调整情景
"""
            
            user_prompt = "请生成当前中东局势（重点伊朗）的4种推演情景"
            if news_context:
                user_prompt = f"{news_context}\n\n请基于以上最新新闻，生成当前中东局势（重点伊朗）的4种推演情景"
            
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            if isinstance(result, list) and len(result) == 4:
                scenarios = result
            elif 'scenarios' in result and isinstance(result['scenarios'], list):
                scenarios = result['scenarios']
            
        except Exception as e:
            logger.error(f"Failed to generate Middle East scenarios with LLM: {e}")
            # LLM 失败时使用默认数据
    
    # 更新缓存
    _middle_east_cache['data'] = scenarios
    _middle_east_cache['last_updated'] = current_time
    
    return {
        'success': True,
        'data': scenarios,
        'cached': False,
        'last_updated': current_time,
        'llm_used': bool(llm_api_key)
    }

if __name__ == '__main__':
    run_web_server()
