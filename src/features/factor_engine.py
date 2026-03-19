"""
因子工程模块 - 计算宏观因子用于预测
计算并整理所有预测需要的特征，LLM不擅长数值计算，这里预计算

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import Dict, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class GoldFactorEngine:
    """黄金预测因子工程 - 计算所有宏观因子"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def calculate_ratios(gold_price: float, silver_price: float, crude_price: float) -> Dict[str, float]:
        """计算关键比率：金银比、金油比"""
        ratios = {}
        if silver_price > 0:
            ratios['gold_silver_ratio'] = gold_price / silver_price
        else:
            ratios['gold_silver_ratio'] = np.nan
            
        if crude_price > 0:
            ratios['gold_oil_ratio'] = gold_price / crude_price
        else:
            ratios['gold_oil_ratio'] = np.nan
            
        return ratios
    
    @staticmethod
    def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
        """计算技术特征：均线、RSI、波动率，使用pandas-ta"""
        try:
            import pandas_ta as ta
            # 均线
            df['sma_20'] = ta.sma(df['close'], length=20)
            df['sma_50'] = ta.sma(df['close'], length=50)
            df['sma_200'] = ta.sma(df['close'], length=200)
            
            # RSI
            df['rsi_14'] = ta.rsi(df['close'], length=14)
            
            # 波动率
            df['volatility_20'] = df['close'].rolling(20).std()
            
            return df
        except ImportError:
            logger.warning("pandas_ta not installed, skip technical features")
            return df
    
    def prepare_features(
        self,
        daily_data: Dict[str, float],
        macro_data: Dict[str, float],
        history: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """准备完整特征向量"""
        features = {}
        
        # 价格
        features['gold_price'] = daily_data.get('gold', np.nan)
        features['silver_price'] = daily_data.get('silver', np.nan)
        features['crude_price'] = daily_data.get('crude', np.nan)
        features['dxy'] = daily_data.get('dxy', np.nan)
        features['vix'] = daily_data.get('vix', np.nan)
        
        # 关键比率
        if not pd.isna(features['gold_price']) and not pd.isna(features['silver_price']):
            features['gold_silver_ratio'] = features['gold_price'] / features['silver_price']
        if not pd.isna(features['gold_price']) and not pd.isna(features['crude_price']):
            features['gold_oil_ratio'] = features['gold_price'] / features['crude_price']
        
        # 宏观因子来自FRED
        features['real_rate_10y'] = macro_data.get('real_rate_10y', np.nan)
        features['breakeven_inflation_10y'] = macro_data.get('breakeven_inflation_10y', np.nan)
        
        # 地缘风险评分：由上层根据新闻条数计算 0-10
        # 这里只是占位
        
        return pd.DataFrame([features])
