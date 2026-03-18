import logging
import os
import json
from dataclasses import dataclass
import pandas as pd
from datetime import datetime, date
from typing import List, Optional
import tushare as ts
import requests
from scrapling import Fetcher
from pathlib import Path
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
    inventory: float
    change: float  # 变化
    change_pct: float  # 变化百分比

class PriceMonitor(BaseMonitor):
    """价格行情监控 - 国际黄金(COMEX)/白银 + Tushare国内 + 金银ETF/COMEX库存
    专注监控黄金白银市场
    """
    
    def __init__(self, token: str, 
                 stocks: List[str] = None, 
                 gold_enabled: bool = True, 
                 silver_enabled: bool = True, 
                 etf_monitor: bool = True,
                 data_dir: str = "./data"):
        self.token = token
        self.stocks = stocks or []  # 黄金白银相关股票
        self.gold_enabled = gold_enabled
        self.silver_enabled = silver_enabled
        self.etf_monitor = etf_monitor
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.fetcher = Fetcher()
        if token:
            ts.set_token(token)
            self.pro = ts.pro_api()
        else:
            self.pro = None
        
    def fetch_latest(self) -> List[PriceData]:
        """获取最新价格数据"""
        results = []
        
        # 获取国际黄金价格 (COMEX/伦敦金)
        if self.gold_enabled:
            gold_price = self.fetch_intl_gold_price()
            if gold_price:
                results.append(gold_price)
                # 保存到本地历史数据
                self.save_price_to_local('XAUUSD', gold_price)
                logger.info(f"Fetched international gold price: {gold_price.price:.2f}")
        
        # 获取国际白银价格 (COMEX)
        if self.silver_enabled:
            silver_price = self.fetch_intl_silver_price()
            if silver_price:
                results.append(silver_price)
                self.save_price_to_local('XAGUSD', silver_price)
                logger.info(f"Fetched international silver price: {silver_price.price:.2f}")
        
        # 获取股票实时行情（黄金白银相关个股）
        for symbol in self.stocks:
            try:
                if not self.pro:
                    continue
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
                
        logger.info(f"Fetched {len(results)} price data total")
        
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
    
    def fetch_intl_gold_price(self) -> Optional[PriceData]:
        """获取伦敦金/国际黄金最新价格
        使用金投网免费API
        """
        try:
            # 金投网免费API获取黄金价格
            url = "https://www.cngoldquote.com/api/getQuote?code=XAUUSD"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 100.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 200 and data.get('data'):
                    latest = data['data']
                    price = float(latest.get('lastPrice', 0))
                    prev_close = float(latest.get('closePrice', 0))
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
                    current_time = datetime.now()
                    return PriceData(
                        symbol="XAUUSD",
                        name="COMEX黄金",
                        price=price,
                        change=change,
                        change_pct=change_pct,
                        timestamp=current_time,
                        volume=None
                    )
            return None
        except Exception as e:
            logger.error(f"Failed to fetch international gold price: {e}")
            return None
    
    def fetch_intl_silver_price(self) -> Optional[PriceData]:
        """获取国际白银最新价格
        使用金投网免费API
        """
        try:
            url = "https://www.cngoldquote.com/api/getQuote?code=XAGUSD"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 100.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 200 and data.get('data'):
                    latest = data['data']
                    price = float(latest.get('lastPrice', 0))
                    prev_close = float(latest.get('closePrice', 0))
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
                    current_time = datetime.now()
                    return PriceData(
                        symbol="XAGUSD",
                        name="COMEX白银",
                        price=price,
                        change=change,
                        change_pct=change_pct,
                        timestamp=current_time,
                        volume=None
                    )
            return None
        except Exception as e:
            logger.error(f"Failed to fetch international silver price: {e}")
            return None
    
    def save_price_to_local(self, symbol: str, price: PriceData):
        """保存价格到本地CSV文件，用于历史数据查询"""
        csv_path = self.data_dir / f"{symbol}_prices.csv"
        today_str = date.today().strftime("%Y%m%d")
        
        # 创建新DataFrame
        new_row = pd.DataFrame([{
            'trade_date': today_str,
            'open': price.price,
            'high': price.price,
            'low': price.price,
            'close': price.price,
            'vol': price.volume or 0
        }])
        
        if csv_path.exists():
            # 读取已有数据
            df = pd.read_csv(csv_path)
            # 如果今天已经有数据，更新，否则添加
            if len(df[df['trade_date'] == int(today_str)]) > 0:
                df.loc[df['trade_date'] == int(today_str), 'close'] = price.price
            else:
                df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row
        
        df.to_csv(csv_path, index=False)
        logger.debug(f"Saved {symbol} price to {csv_path}")
        
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
        """获取历史数据用于指标计算
        对于国际黄金(XAUUSD)和白银(XAGUSD)，从本地CSV读取
        对于股票，从tushare读取
        """
        # 如果是国际黄金/白银，从本地读取
        if symbol in ['XAUUSD', 'XAGUSD', 'gold', 'silver']:
            actual_symbol = 'XAUUSD' if symbol in ['gold', 'XAUUSD'] else 'XAGUSD'
            csv_path = self.data_dir / f"{actual_symbol}_prices.csv"
            if not csv_path.exists():
                logger.warning(f"No local history found for {symbol}")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_path)
            df = df.sort_values('trade_date')
            return df
        
        # 如果是其他symbol，用tushare
        try:
            if not self.pro:
                logger.error(f"No tushare token configured for {symbol}")
                return pd.DataFrame()
            df = self.pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            df = df.sort_values('trade_date')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch history for {symbol}: {e}")
            return pd.DataFrame()
