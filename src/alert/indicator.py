import logging
import pandas as pd
import numpy as np
import ta

logger = logging.getLogger(__name__)

class IndicatorCalculator:
    """技术指标计算器"""
    
    @staticmethod
    def ma(df: pd.DataFrame, period: int = 50) -> pd.Series:
        """计算均线"""
        return ta.trend.sma_indicator(df.close, window=period)
        
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI"""
        return ta.momentum.rsi(df.close, window=period)
        
    @staticmethod
    def bollinger_bands(df: pd.DataFrame, period: int = 20, nbdevup: float = 2, nbdevdn: float = 2):
        """计算布林带"""
        indicator = ta.volatility.BollingerBands(df.close, window=period, window_dev=nbdevup)
        return (
            indicator.bollinger_hband().values,
            indicator.bollinger_mavg().values, 
            indicator.bollinger_lband().values
        )
        
    @staticmethod
    def volatility(df: pd.DataFrame, window: int = 20) -> float:
        """计算最近N天波动率"""
        returns = df.close.pct_change().dropna()
        return returns.rolling(window=window).std().iloc[-1]
        
    @staticmethod
    def current_deviation_from_ma(df: pd.DataFrame, ma_period: int = 50) -> float:
        """当前价格偏离MA的百分比"""
        if len(df) < ma_period:
            return 0
        ma = IndicatorCalculator.ma(df, ma_period)
        current_price = df.close.iloc[-1]
        current_ma = ma.iloc[-1]
        return (current_price - current_ma) / current_ma
