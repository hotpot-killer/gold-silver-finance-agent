import logging
import json
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import uvicorn

logger = logging.getLogger(__name__)

app = FastAPI(title="gold-silver-finance-agent Web API")

# 预警日志文件路径
ALERT_LOG_PATH = Path('./data/alerts.log')

# 获取当前文件所在目录
CURRENT_DIR = Path(__file__).parent
TEMPLATE_DIR = CURRENT_DIR / 'templates'
STATIC_DIR = CURRENT_DIR / 'static'

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

def run_web_server(host='0.0.0.0', port=5000):
    """启动Web服务器"""
    # 确保data目录存在
    ALERT_LOG_PATH.parent.mkdir(exist_ok=True)
    uvicorn.run(app, host=host, port=port)

if __name__ == '__main__':
    run_web_server()
