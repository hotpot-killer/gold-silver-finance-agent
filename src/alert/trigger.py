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
        """检查RSI超买超卖
        改进逻辑：只有进入超买/超卖区后，反向穿越中轴才触发，降低假信号
        默认：超买阈值65，超卖阈值35，穿越50中轴触发
        """
        period = config.get('params', {}).get('period', 14)
        overbought = config.get('params', {}).get('overbought', 65)
        oversold = config.get('params', {}).get('oversold', 35)
        mid = config.get('params', {}).get('mid', 50)
        
        rsi = IndicatorCalculator.rsi(df, period)
        
        if len(rsi) < 2:
            return None
        
        current_rsi = rsi[-1]
        prev_rsi = rsi[-2]
        
        # 超卖后向上穿越50中线 → 触发多头信号
        if prev_rsi <= oversold and current_rsi > mid:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi',
                message=f"RSI{period} 从超卖区({oversold}↓)向上穿越中线{mid}，当前={current_rsi:.1f}",
                current_value=current_rsi,
                threshold=mid,
                suggestion="RSI从超卖区回升，空头力量耗尽，可能开启反弹"
            )
        
        # 超买后向下穿越50中线 → 触发空头信号
        if prev_rsi >= overbought and current_rsi < mid:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi',
                message=f"RSI{period} 从超买区({overbought}↑)向下穿越中线{mid}，当前={current_rsi:.1f}",
                current_value=current_rsi,
                threshold=mid,
                suggestion="RSI从超买区回落，多头力量耗尽，注意回调风险"
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
    
    def check_gold_silver_ratio(self, gold_df: pd.DataFrame, silver_df: pd.DataFrame, config: dict) -> Optional[Alert]:
        """检查金银比极端值
        正常区间 60-80，超过80或低于60都是极端
        """
        high_threshold = config.get('params', {}).get('high', 80)
        low_threshold = config.get('params', {}).get('low', 60)
        
        ratio = IndicatorCalculator.ratio(gold_df, silver_df)
        if ratio <= 0:
            return None
        
        if ratio >= high_threshold:
            return Alert(
                asset='gold-silver',
                alert_type='ratio',
                message=f"金银比 = {ratio:.1f} >= 极端上限 {high_threshold}",
                current_value=ratio,
                threshold=high_threshold,
                suggestion="金银比极端高估，黄金相对于白银太贵，关注做空黄金/做多白银机会"
            )
        
        if ratio <= low_threshold:
            return Alert(
                asset='gold-silver',
                alert_type='ratio',
                message=f"金银比 = {ratio:.1f} <= 极端下限 {low_threshold}",
                current_value=ratio,
                threshold=low_threshold,
                suggestion="金银比极端低估，黄金相对于白银太便宜，关注做多黄金/做空白银机会"
            )
            
        return None
        
    def check_all(self, symbol: str, df: pd.DataFrame, gold_df: pd.DataFrame = None, silver_df: pd.DataFrame = None) -> List[Alert]:
        """检查所有预警规则
        对于金银比，需要同时传入gold_df和silver_df
        """
        alerts = []
        for config in self.configs:
            if not config.get('enabled', True):
                continue
            if config.get('asset') != symbol and config.get('asset') != 'all' and config.get('type') != 'ratio':
                continue
                
            alert_type = config.get('type')
            alert = None
            
            if alert_type == 'ma_deviation':
                # MA200过滤：只在价格偏离MA200不太大的时候触发（非趋势行情）
                ma_200 = IndicatorCalculator.ma(df, 200)
                current_price = df.close.iloc[-1]
                current_ma200 = ma_200.iloc[-1]
                deviation = abs(current_price - current_ma200) / current_ma200
                # 偏离超过20%认为是趋势行情，不触发预警
                max_deviation = config.get('params', {}).get('max_deviation_from_ma200', 0.2)
                if deviation > max_deviation:
                    # 趋势行情，过滤掉，不触发
                    continue
                alert = self.check_ma_deviation(df, config)
            elif alert_type == 'rsi':
                # MA200过滤同理
                if len(df) >= 200:  # 有足够数据才过滤
                    ma_200 = IndicatorCalculator.ma(df, 200)
                    current_price = df.close.iloc[-1]
                    current_ma200 = ma_200.iloc[-1]
                    deviation = abs(current_price - current_ma200) / current_ma200
                    max_deviation = config.get('params', {}).get('max_deviation_from_ma200', 0.2)
                    if deviation > max_deviation:
                        continue
                alert = self.check_rsi(df, config)
            elif alert_type == 'volatility':
                # MA200过滤同理
                if len(df) >= 200:
                    ma_200 = IndicatorCalculator.ma(df, 200)
                    current_price = df.close.iloc[-1]
                    current_ma200 = ma_200.iloc[-1]
                    deviation = abs(current_price - current_ma200) / current_ma200
                    max_deviation = config.get('params', {}).get('max_deviation_from_ma200', 0.2)
                    if deviation > max_deviation:
                        continue
                alert = self.check_volatility(df, config)
            elif alert_type == 'ratio':
                # 金银比需要黄金和白银数据
                if gold_df is not None and silver_df is not None and len(gold_df) > 0 and len(silver_df) > 0:
                    alert = self.check_gold_silver_ratio(gold_df, silver_df, config)
                
            if alert:
                alerts.append(alert)
                
        return alerts
