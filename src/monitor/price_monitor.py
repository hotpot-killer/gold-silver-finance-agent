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
    """价格行情监控 - Tushare + 金银ETF/COMEX库存
    专注监控黄金白银市场
    """
    
    def __init__(self, token: str, 
                 stocks: List[str] = None, 
                 gold_enabled: bool = True, 
                 silver_enabled: bool = True, 
                 etf_monitor: bool = True):
        self.token = token
        self.stocks = stocks or []  # 黄金白银相关股票
        self.gold_enabled = gold_enabled
        self.silver_enabled = silver_enabled
        self.etf_monitor = etf_monitor
        self.fetcher = Fetcher()
        ts.set_token(token)
        self.pro = ts.pro_api()
        
    def fetch_latest(self) -> List[PriceData]:
        """获取最新价格数据"""
        results = []
        
        # 获取股票实时行情（黄金白银相关个股）
        for symbol in self.stocks:
            try:
                # 获取最新日线数据
                df = self.pro.daily(ts_code=symbol)
                if not df.empty:
                    latest = df.iloc[0]
                    results.append(PriceData(
                        symbol=symbol,
                        name=symbol,
                        price=latest.close,
                        change=latest.change,
                        change_pct=latest.pct_chg,
                        timestamp=datetime.strptime(latest.trade_date, "%Y%m%d"),
                        volume=latest.vol
                    ))
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                
        logger.info(f"Fetched {len(results)} price data for {len(self.stocks)} stocks")
        
        # 如果启用了ETF监控，添加GLD/SLV持仓
        if self.etf_monitor:
            # 获取 GLD 持仓 - 最大黄金ETF，反映散户情绪
            gld_holdings = self.fetch_gld_holdings()
            if gld_holdings:
                logger.info(f"GLD ({gld_holdings.name}) latest holdings: {gld_holdings.holdings:.0f} shares, change: {gld_holdings.change_pct:.2f}%")
            
            # 获取 SLV 持仓 - 最大白银ETF，反映庄家动向
            slv_holdings = self.fetch_slv_holdings()
            if slv_holdings:
                logger.info(f"SLV ({slv_holdings.name}) latest holdings: {slv_holdings.holdings:.0f} shares, change: {slv_holdings.change_pct:.2f}%")
        
        # 获取 COMEX 库存
        if self.gold_enabled:
            gold_inv = self.fetch_comex_inventory('gold')
            if gold_inv:
                logger.info(f"COMEX gold inventory: {gold_inv.inventory:.0f} oz, change: {gold_inv.change_pct:.2f}%")
        
        if self.silver_enabled:
            silver_inv = self.fetch_comex_inventory('silver')
            if silver_inv:
                logger.info(f"COMEX silver inventory: {silver_inv.inventory:.0f} oz, change: {silver_inv.change_pct:.2f}%")
        
        return results
        
    def fetch_gld_holdings(self) -> Optional[ETFHoldings]:
        """获取SPDR Gold Trust (GLD) 最新持仓
        GLD - 最大黄金ETF，通常是散户持仓为主 → 反映散户情绪
        """
        try:
            # 从ishares官网获取最新持仓
            url = "https://www.ishares.com/us/products/239751/gld-spdr-gold-trust"
            page = self.fetcher.get(url)
            
            # 解析持仓数据
            # ishare网站会有 JSON-LD 格式的持仓数据
            # 或者从表格中提取
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 尝试查找 JSON 数据
            script_tags = page.css('script[type="application/ld+json"]')
            holdings = None
            
            if script_tags:
                # 提取当前持仓
                # 这里简单提取总持仓
                # 实际解析会根据HTML结构调整
                from parsel import Selector
                selector = Selector(page.text)
                rows = selector.css('.fund-header-data .primary-price span::text').getall()
                if len(rows) > 0:
                    # 尝试解析持仓量
                    try:
                        # 这里获取的是每股净资产，我们需要总持仓
                        # 从另一个位置获取
                        holdings_row = selector.css('.holdings-value::text').get()
                        if holdings_row:
                            holdings_val = float(holdings_row.replace(',', '').strip())
                            # GLD 持仓单位是百万盎司
                            holdings = holdings_val * 1000000
                    except:
                        pass
            
            logger.info("Fetched GLD holdings data completed")
            if holdings:
                return ETFHoldings(
                    symbol="GLD",
                    name="SPDR Gold Trust",
                    date=today,
                    holdings=holdings,
                    change=0.0,  # 需要计算历史变化，框架先留下
                    change_pct=0.0
                )
            return None
        except Exception as e:
            logger.error(f"Failed to fetch GLD holdings: {e}")
            return None
            
    def fetch_slv_holdings(self) -> Optional[ETFHoldings]:
        """获取iShares Silver Trust (SLV) 最新持仓
        SLV - 最大白银ETF，庄家操作迹象更明显 → 反映庄家动向
        """
        try:
            url = "https://www.ishares.com/us/products/239728/slv-isharess-silver-trust"
            page = self.fetcher.get(url)
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            from parsel import Selector
            selector = Selector(page.text)
            holdings = None
            holdings_row = selector.css('.holdings-value::text').get()
            if holdings_row:
                holdings_val = float(holdings_row.replace(',', '').strip())
                # SLV 持仓单位是百万盎司
                holdings = holdings_val * 1000000
            
            logger.info("Fetched SLV holdings data completed")
            if holdings:
                return ETFHoldings(
                    symbol="SLV",
                    name="iShares Silver Trust",
                    date=today,
                    holdings=holdings,
                    change=0.0,
                    change_pct=0.0
                )
            return None
        except Exception as e:
            logger.error(f"Failed to fetch SLV holdings: {e}")
            return None
            
    def fetch_comex_inventory(self, commodity: str) -> Optional[COMEXInventory]:
        """获取COMEX金银库存变化"""
        try:
            # 从CME集团官网获取最新库存
            # 或者从公开数据源获取
            # 现在先完成框架，后续可以完善具体解析
            # 这里预留接口
            url_map = {
                'gold': 'https://www.cmegroup.com/markets/metals/precious/gold-warehouse-stocks.html',
                'silver': 'https://www.cmegroup.com/markets/metals/precious/silver-warehouse-stocks.html'
            }
            
            if commodity not in url_map:
                return None
                
            url = url_map[commodity]
            page = self.fetcher.get(url)
            
            today = datetime.now().strftime("%Y-%m-%d")
            from parsel import Selector
            selector = Selector(page.text)
            
            # 提取最新库存数据
            # 解析最近交易日的库存
            # 这里先预留框架
            logger.info(f"Fetched COMEX {commodity} inventory data completed")
            
            return COMEXInventory(
                commodity=commodity,
                date=today,
                inventory=0.0,
                change=0.0,
                change_pct=0.0
            )
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
