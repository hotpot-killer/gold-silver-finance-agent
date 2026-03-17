import logging
import json
from datetime import datetime
from flask import Flask, render_template, jsonify
from pathlib import Path

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gold-silver-finance-agent-secret-key'

# 预警日志文件路径
ALERT_LOG_PATH = Path('./data/alerts.log')

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

@app.route('/')
def index():
    """首页 - 显示历史预警"""
    alerts = load_alerts()
    return render_template('index.html', alerts=alerts)

@app.route('/api/alerts')
def api_alerts():
    """API - 获取预警列表"""
    alerts = load_alerts()
    return jsonify({
        'count': len(alerts),
        'alerts': alerts
    })

@app.route('/api/stats')
def api_stats():
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
    
    return jsonify(stats)

def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """启动Web服务器"""
    # 确保data目录存在
    ALERT_LOG_PATH.parent.mkdir(exist_ok=True)
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_web_server(debug=True)
