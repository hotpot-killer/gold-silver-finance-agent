import logging
import pandas as pd
from datetime import datetime
from typing import List
import tushare as ts
from .base import BaseMonitor, PriceData

logger = logging.getLogger(__name__)

class PriceMonitor(BaseMonitor):
    """价格行情监控 - Tushare"""
    
    def __init__(self, token: str, stocks: List[str] = None, gold_enabled: bool = False):
        self.token = token
        self.stocks = stocks or []
        self.gold_enabled = gold_enabled
        ts.set_token(token)
        self.pro = ts.pro_api()
        
    def fetch_latest(self) -> List[PriceData]:
        """获取最新价格数据"""
        results = []
        
        # 获取股票实时行情
        for symbol in self.stocks:
            try:
                # 获取最新日线数据
                df = self.pro.daily(ts_code=symbol)
                if not df.empty:
                    latest = df.iloc[0]
                    results.append(PriceData(
                        symbol=symbol,
                        name=symbol,  # 可以进一步获取名称
                        price=latest.close,
                        change=latest.change,
                        change_pct=latest.pct_chg,
                        timestamp=datetime.strptime(latest.trade_date, "%Y%m%d"),
                        volume=latest.vol
                    ))
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                
        logger.info(f"Fetched {len(results)} price data")
        return results
        
    def get_history(self, symbol: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """获取历史数据用于指标计算"""
        try:
            df = self.pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            df = df.sort_values('trade_date')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch history for {symbol}: {e}")
            return pd.DataFrame()
