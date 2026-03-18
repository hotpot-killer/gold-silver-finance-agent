import logging
import pandas as pd
import requests
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class COTFetcher:
    """COT持仓报告抓取 - CFTC公开数据
    获取黄金白银非商业净持仓数据，判断机构情绪
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        # 使用免费公开COT数据API
        self.api_url = "https://api.fx611.com/api/cot/latest"
        
    def fetch_cot_data(self) -> Optional[pd.DataFrame]:
        """抓取最新COT数据"""
        try:
            # 使用公开免费API获取
            resp = requests.get(self.api_url, timeout=15, proxies=None)
            resp.raise_for_status()
            data = resp.json()
            
            if 'data' not in data:
                logger.error("No data in COT API response")
                return None
            
            df = pd.DataFrame(data['data'])
            # 保存到本地
            today = datetime.now().strftime("%Y%m%d")
            df.to_csv(self.data_dir / f"cot_data_{today}.csv", index=False)
            logger.info(f"Fetched latest COT data, {len(df)} records")
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch COT data: {e}")
            return None
    
    def get_gold_silver_cot(self, df: pd.DataFrame = None) -> Optional[Dict]:
        """获取黄金和白银COT数据
        返回非商业净持仓数据和百分比
        """
        if df is None:
            df = self.fetch_cot_data()
        if df is None or df.empty:
            return None
        
        result = {}
        # 查找黄金和白银
        gold_symbols = ['GC', 'GOLD', 'COMEX Gold']
        silver_symbols = ['SI', 'SILVER', 'COMEX Silver']
        
        for _, row in df.iterrows():
            symbol = str(row.get('symbol', '')).upper()
            name = str(row.get('name', '')).upper()
            
            # 匹配黄金
            for gs in gold_symbols:
                if gs in symbol or gs in name:
                    result['gold'] = {
                        'date': row.get('date', ''),
                        'net_noncommercial': float(row.get('net_noncommercial', 0)),
                        'pct_of_open_interest': float(row.get('pct_noncommercial', 0)),
                        'change': float(row.get('change', 0))
                    }
                    break
            
            # 匹配白银
            for ss in silver_symbols:
                if ss in symbol or ss in name:
                    result['silver'] = {
                        'date': row.get('date', ''),
                        'net_noncommercial': float(row.get('net_noncommercial', 0)),
                        'pct_of_open_interest': float(row.get('pct_noncommercial', 0)),
                        'change': float(row.get('change', 0))
                    }
                    break
        
        return result if result else None
    
    def check_extreme_positioning(self, cot_data: Dict) -> Optional[Dict]:
        """检查是否处于极端持仓
        黄金/白银非商业净持仓达到历史极值，说明拥挤，可能反转
        """
        alerts = {}
        
        if 'gold' in cot_data:
            pct = cot_data['gold']['pct_of_open_interest']
            # 阈值：> 30% = 极端多头拥挤 / < -20% = 极端空头拥挤
            if pct >= 30:
                alerts['gold'] = {
                    'extreme': 'bullish_extreme',
                    'message': f"黄金非商业净多头持仓占比 {pct:.1f}%，达到极端多头水平",
                    'suggestion': "机构多头过于拥挤，警惕多头平仓反转风险"
                }
            elif pct <= -20:
                alerts['gold'] = {
                    'extreme': 'bearish_extreme',
                    'message': f"黄金非商业净空头持仓占比 {abs(pct):.1f}%，达到极端空头水平",
                    'suggestion': "机构空头过于拥挤，警惕空头平仓反弹机会"
                }
        
        if 'silver' in cot_data:
            pct = cot_data['silver']['pct_of_open_interest']
            if pct >= 35:
                alerts['silver'] = {
                    'extreme': 'bullish_extreme',
                    'message': f"白银非商业净多头持仓占比 {pct:.1f}%，达到极端多头水平",
                    'suggestion': "机构多头过于拥挤，警惕多头平仓反转风险"
                }
            elif pct <= -25:
                alerts['silver'] = {
                    'extreme': 'bearish_extreme',
                    'message': f"白银非商业净空头持仓占比 {abs(pct):.1f}%，达到极端空头水平",
                    'suggestion': "机构空头过于拥挤，警惕空头平仓反弹机会"
                }
        
        return alerts if alerts else None
