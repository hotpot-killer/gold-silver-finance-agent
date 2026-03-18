import logging
import pandas as pd
import numpy as np
import ta
from typing import Optional

logger = logging.getLogger(__name__)

class IndicatorCalculator:
    """技术指标计算器"""
    
    @staticmethod
    def ma(df: pd.DataFrame, period: int = 50) -> pd.Series:
        """计算均线"""
        return ta.trend.sma_indicator(df.close, window=period)
    
    @staticmethod
    def ratio(gold_df: pd.DataFrame, silver_df: pd.DataFrame) -> float:
        """计算最新金银比 (黄金价格/白银价格)"""
        if len(gold_df) == 0 or len(silver_df) == 0:
            return 0
        gold_price = gold_df['close'].iloc[-1]
        silver_price = silver_df['close'].iloc[-1]
        if silver_price == 0:
            return 0
        return gold_price / silver_price
    
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算RSI"""
        return ta.momentum.rsi(df.close, window=period)
    
    @staticmethod
    def check_rsi_divergence(df: pd.DataFrame, period: int = 14, lookback: int = 10) -> Optional[str]:
        """检测RSI顶底背离
        返回: 'top' = 顶背离, 'bottom' = 底背离, None = 无背离
        """
        if len(df) < lookback + period:
            return None
        
        rsi = IndicatorCalculator.rsi(df, period)
        
        # 获取最近 lookback 周期内的价格高点/低点
        recent_prices = df.tail(lookback + 1)
        recent_rsi = rsi.tail(lookback + 1)
        
        price_high = recent_prices['close'].max()
        price_high_index = recent_prices['close'].idxmax()
        rsi_at_high = recent_rsi.loc[price_high_index]
        
        price_low = recent_prices['close'].min()
        price_low_index = recent_prices['close'].idxmin()
        rsi_at_low = recent_rsi.loc[price_low_index]
        
        current_price = df['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        # 顶背离：价格新高，但RSI没有新高 → 预示顶部
        if current_price > price_high and current_rsi < rsi_at_high:
            return 'top'
        
        # 底背离：价格新低，但RSI没有新低 → 预示底部
        if current_price < price_low and current_rsi > rsi_at_low:
            return 'bottom'
        
        return None
    
    @staticmethod
    def rsi_slope(df: pd.DataFrame, period: int = 14, slope_period: int = 3) -> float:
        """计算RSI最近斜率 → 判断加速上涨/下跌"""
        rsi = IndicatorCalculator.rsi(df, period)
        if len(rsi) < slope_period:
            return 0
        # 简单斜率计算：(当前 - N天前)/N
        current = rsi.iloc[-1]
        prev = rsi.iloc[-slope_period - 1]
        slope = (current - prev) / slope_period
        return slope
    
    @staticmethod
    def check_ma_cross(df: pd.DataFrame, fast_period: int = 20, slow_period: int = 50) -> Optional[str]:
        """检测均线金叉死叉"""
        if len(df) < slow_period + 1:
            return None
        
        ma_fast = IndicatorCalculator.ma(df, fast_period)
        ma_slow = IndicatorCalculator.ma(df, slow_period)
        
        current_fast = ma_fast.iloc[-1]
        prev_fast = ma_fast.iloc[-2]
        current_slow = ma_slow.iloc[-1]
        prev_slow = ma_slow.iloc[-2]
        
        # 金叉：快线从下方穿慢线 → 上涨趋势启动
        if prev_fast < prev_slow and current_fast > current_slow:
            return 'golden_cross'
        
        # 死叉：快线从上方穿慢线 → 下跌趋势启动
        if prev_fast > prev_slow and current_fast < current_slow:
            return 'dead_cross'
        
        return None
    
    @staticmethod
    def check_price_break_ma(df: pd.DataFrame, ma_period: int = 50) -> Optional[str]:
        """检测价格突破均线"""
        if len(df) < ma_period + 1:
            return None
        
        ma = IndicatorCalculator.ma(df, ma_period)
        current_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        current_ma = ma.iloc[-1]
        prev_ma = ma.iloc[-2]
        
        # 向上突破：从下方到上方
        if prev_close < prev_ma and current_close > current_ma:
            return 'up_break'
        
        # 向下突破：从上方到下方
        if prev_close > prev_ma and current_close < current_ma:
            return 'down_break'
        
        return None
        
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
        
    @staticmethod
    def macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """计算 MACD"""
        macd_indicator = ta.trend.MACD(
            df.close, 
            window_slow=slow_period,
            window_fast=fast_period,
            window_sign=signal_period
        )
        return (
            macd_indicator.macd().iloc[-1],
            macd_indicator.macd_signal().iloc[-1],
            macd_indicator.macd_diff().iloc[-1]
        )
        
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> float:
        """计算 ATR 平均真实波动范围"""
        return ta.volatility.average_true_range(df.high, df.low, df.close, window=period).iloc[-1]
