import logging
import json
import requests
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tushare as ts
import uvicorn

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
                change = 0
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

def run_web_server(host='0.0.0.0', port=5000):
    """启动Web服务器"""
    # 确保data目录存在
    ALERT_LOG_PATH.parent.mkdir(exist_ok=True)
    uvicorn.run(app, host=host, port=port)

if __name__ == '__main__':
    run_web_server()
