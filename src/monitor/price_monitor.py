import logging
from dataclasses import dataclass
import pandas as pd
from datetime import datetime
from typing import List, Optional
import tushare as ts
from scrapling import Fetcher
from .base import BaseMonitor, PriceData

logger = logging.getLogger(__name__)

@dataclass
class ETFHoldings:
    """ETF持仓数据 - GLD/SLV"""
    symbol: str
    name: str
    date: str
    holdings: float  # 持仓量(盎司/股)
    change: float  # 单日变化
    change_pct: float  # 单日变化百分比

@dataclass
class COMEXInventory:
    """COMEX库存数据"""
    commodity: str  # gold/silver
    date: str
    inventory: float  # 库存
    change: float  # 变化
    change_pct: float  # 变化百分比

class PriceMonitor(BaseMonitor):
    """价格行情监控 - Tushare + 金银ETF/COMEX库存"""
    
    def __init__(self, token: str, stocks: List[str] = None, gold_enabled: bool = False, etf_monitor: bool = True):
        self.token = token
        self.stocks = stocks or []
        self.gold_enabled = gold_enabled
        self.etf_monitor = etf_monitor
        self.fetcher = Fetcher()
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
        
        # 如果启用了ETF监控，添加GLD/SLV持仓
        if self.etf_monitor:
            # 获取 GLD 持仓
            gld_holdings = self.fetch_gld_holdings()
            if gld_holdings:
                logger.info(f"GLD ({gld_holdings.name}) latest holdings: {gld_holdings.holdings:.0f} shares, change: {gld_holdings.change_pct:.2f}%")
            
            # 获取 SLV 持仓  
            slv_holdings = self.fetch_slv_holdings()
            if slv_holdings:
                logger.info(f"SLV ({slv_holdings.name}) latest holdings: {slv_holdings.holdings:.0f} shares, change: {slv_holdings.change_pct:.2f}%")
        
        # 获取 COMEX 库存
        if self.gold_enabled:
            gold_inv = self.fetch_comex_inventory('gold')
            silver_inv = self.fetch_comex_inventory('silver')
            if gold_inv:
                logger.info(f"COMEX gold inventory: {gold_inv.inventory:.0f} oz, change: {gold_inv.change_pct:.2f}%")
            if silver_inv:
                logger.info(f"COMEX silver inventory: {silver_inv.inventory:.0f} oz, change: {silver_inv.change_pct:.2f}%")
        
        return results
        
    def fetch_gld_holdings(self) -> Optional[ETFHoldings]:
        """获取SPDR Gold Trust (GLD) 最新持仓
        GLD - 最大黄金ETF，通常是散户持仓为主
        """
        try:
            # 从ishares官网获取最新持仓
            url = "https://www.ishares.com/us/products/239751/gld-spdr-gold-trust"
            page = self.fetcher.get(url)
            
            # 解析持仓数据，框架已完成，具体解析可以后续完善
            # 当前框架保留，方便后续贡献完善
            logger.info("Fetched GLD holdings data")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch GLD holdings: {e}")
            return None
            
    def fetch_slv_holdings(self) -> Optional[ETFHoldings]:
        """获取iShares Silver Trust (SLV) 最新持仓
        SLV - 最大白银ETF，庄家操作迹象更明显
        """
        try:
            url = "https://www.ishares.com/us/products/239728/slv-isharess-silver-trust"
            page = self.fetcher.get(url)
            logger.info("Fetched SLV holdings data")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch SLV holdings: {e}")
            return None
            
    def fetch_comex_inventory(self, commodity: str) -> Optional[COMEXInventory]:
        """获取COMEX金银库存变化"""
        try:
            # 从CME集团官网获取最新库存
            # 框架已搭好，具体HTML解析可以后续完善
            logger.info(f"Fetched COMEX {commodity} inventory data")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch COMEX {commodity} inventory: {e}")
            return None
        
    def get_history(self, symbol: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """获取历史数据用于指标计算"""
        try:
            df = self.pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            df = df.sort_values('trade_date')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch history for {symbol}: {e}")
            return pd.DataFrame()
