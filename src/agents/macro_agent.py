"""
Macro Agent - 宏观数据收集代理
负责收集最新宏观数据、地缘新闻，交给后续Agent处理

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import Dict, Optional, List
import pandas as pd
from src.data.macro_fetcher import MacroDataFetcher
from src.features.factor_engine import GoldFactorEngine

logger = logging.getLogger(__name__)

class MacroAgent:
    """宏观数据收集 Agent"""
    
    def __init__(self, fred_api_key: Optional[str] = None):
        self.fetcher = MacroDataFetcher(fred_api_key)
        self.factor_engine = GoldFactorEngine()
        
    def run(self, current_gold_price: Optional[float] = None) -> pd.DataFrame:
        """运行Macro Agent：收集所有宏观数据，计算因子，返回特征DataFrame"""
        # 从yfinance获取价格
        daily_data = self.fetcher.fetch_daily_prices(period="5y")
        
        # 从FRED获取宏观数据
        macro_data = self.fetcher.fetch_fred_data()
        
        # 计算因子
        features_df = self.factor_engine.prepare_features(daily_data, macro_data)
        
        logger.info(f"Macro Agent completed: generated {features_df.shape[1]} features")
        return features_df
    
    def get_geo_risk_score(self, middle_east_news: List[str]) -> int:
        """计算地缘风险评分 0-10，基于中东新闻条数"""
        return min(len(middle_east_news) * 2, 10)
