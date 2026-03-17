import logging
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from .indicator import IndicatorCalculator

logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """预警数据结构"""
    asset: str
    alert_type: str
    message: str
    current_value: float
    threshold: float
    suggestion: str

class AlertTrigger:
    """预警触发器 - 判断是否满足预警条件"""
    
    def __init__(self, config_list: List[dict]):
        self.configs = config_list
        
    def check_ma_deviation(self, df: pd.DataFrame, config: dict) -> Optional[Alert]:
        """检查均线偏离"""
        ma_period = config.get('params', {}).get('ma_period', 50)
        threshold = config.get('params', {}).get('threshold', 0.05)
        direction = config.get('params', {}).get('direction', 'both')
        
        deviation = IndicatorCalculator.current_deviation_from_ma(df, ma_period)
        
        if direction == 'up' and deviation > threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='ma_deviation',
                message=f"价格偏离MA{ma_period} {deviation*100:.1f}% > 阈值 {threshold*100:.1f}%",
                current_value=deviation,
                threshold=threshold,
                suggestion=f"当前价格向上偏离{ma_period}日均线较多，注意回调风险"
            )
        elif direction == 'down' and deviation < -threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='ma_deviation',
                message=f"价格偏离MA{ma_period} {deviation*100:.1f}% < -阈值 {threshold*100:.1f}%",
                current_value=deviation,
                threshold=-threshold,
                suggestion=f"当前价格向下偏离{ma_period}日均线较多，可能存在抄底机会"
            )
        elif direction == 'both' and abs(deviation) > threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='ma_deviation',
                message=f"价格偏离MA{ma_period} {abs(deviation*100):.1f}% > 阈值 {threshold*100:.1f}%",
                current_value=deviation,
                threshold=threshold,
                suggestion=f"价格大幅偏离均线，关注后续走势变化"
            )
        
        return None
        
    def check_rsi(self, df: pd.DataFrame, config: dict) -> Optional[Alert]:
        """检查RSI超买超卖"""
        period = config.get('params', {}).get('period', 14)
        overbought = config.get('params', {}).get('overbought', 70)
        oversold = config.get('params', {}).get('oversold', 30)
        
        rsi = IndicatorCalculator.rsi(df, period)
        current_rsi = rsi[-1]
        
        if current_rsi >= overbought:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi',
                message=f"RSI{period} = {current_rsi:.1f} >= 超买阈值 {overbought}",
                current_value=current_rsi,
                threshold=overbought,
                suggestion="当前RSI超买，多头力量消耗过大，注意回调风险"
            )
        elif current_rsi <= oversold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi',
                message=f"RSI{period} = {current_rsi:.1f} <= 超卖阈值 {oversold}",
                current_value=current_rsi,
                threshold=oversold,
                suggestion="当前RSI超卖，空头力量消耗过大，可能有反弹机会"
            )
            
        return None
        
    def check_volatility(self, df: pd.DataFrame, config: dict) -> Optional[Alert]:
        """检查波动率异常"""
        window = config.get('params', {}).get('window', 20)
        threshold = config.get('params', {}).get('threshold', 2.0)
        
        vol = IndicatorCalculator.volatility(df, window)
        historical_vol = IndicatorCalculator.volatility(df.iloc[:-1], window)
        
        if vol > historical_vol * threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='volatility',
                message=f"当前波动率 {vol:.2f} 是历史均值 {historical_vol:.2f} 的 {threshold} 倍以上",
                current_value=vol,
                threshold=historical_vol * threshold,
                suggestion="波动率异常放大，市场分歧加剧，注意控制仓位"
            )
            
        return None
        
    def check_all(self, symbol: str, df: pd.DataFrame) -> List[Alert]:
        """检查所有预警规则"""
        alerts = []
        for config in self.configs:
            if not config.get('enabled', True):
                continue
            if config.get('asset') != symbol and config.get('asset') != 'all':
                continue
                
            alert_type = config.get('type')
            alert = None
            
            if alert_type == 'ma_deviation':
                alert = self.check_ma_deviation(df, config)
            elif alert_type == 'rsi':
                alert = self.check_rsi(df, config)
            elif alert_type == 'volatility':
                alert = self.check_volatility(df, config)
                
            if alert:
                alerts.append(alert)
                
        return alerts
