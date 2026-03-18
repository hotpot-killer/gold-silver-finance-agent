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
        """检查RSI动量穿越 + 背离预警
        升级逻辑：
        1. 动量穿越：RSI从超买回落穿越65 / 从超卖回升穿越35 → 更早提示
        2. 顶底背离提前预警：价格新高RSI不新高 = 顶背离提前预警
        3. RSI斜率加速预警：连续上涨斜率过大提示加速
        """
        period = config.get('params', {}).get('period', 14)
        overbought_cross = config.get('params', {}).get('overbought_cross', 65)
        oversold_cross = config.get('params', {}).get('oversold_cross', 35)
        lookback = config.get('params', {}).get('lookback', 10)
        slope_threshold = config.get('params', {}).get('slope_threshold', 3)
        
        rsi = IndicatorCalculator.rsi(df, period)
        
        if len(rsi) < 2:
            return None
        
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        
        # 先检测背离 - 提前预警
        divergence = IndicatorCalculator.check_rsi_divergence(df, period, lookback)
        if divergence == 'top':
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi_divergence_top',
                message=f"⚠️ RSI{period} 顶背离：价格创新高但RSI未创新高",
                current_value=current_rsi,
                threshold=0,
                suggestion="价格新高但动能不足，潜在顶部反转信号，注意止盈"
            )
        if divergence == 'bottom':
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi_divergence_bottom',
                message=f"⚠️ RSI{period} 底背离：价格创新低但RSI未创新低",
                current_value=current_rsi,
                threshold=0,
                suggestion="价格新低但动能衰竭，潜在底部反转信号，关注布局机会"
            )
        
        # 检测RSI斜率加速
        slope = IndicatorCalculator.rsi_slope(df, period, 3)
        if slope >= slope_threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi_accelerate_up',
                message=f"🚀 RSI{period} 加速上涨：连续{3}天RSI斜率={slope:.1f} > 阈值{slope_threshold}",
                current_value=slope,
                threshold=slope_threshold,
                suggestion="上涨动能加速，趋势可能延续，顺势而为"
            )
        if slope <= -slope_threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi_accelerate_down',
                message=f"📉 RSI{period} 加速下跌：连续{3}天RSI斜率={slope:.1f} < 阈值-{slope_threshold}",
                current_value=slope,
                threshold=-slope_threshold,
                suggestion="下跌动能加速，趋势可能延续，注意规避风险"
            )
        
        # 超卖后向上穿越35 → 触发多头信号（比穿越50更早）
        if prev_rsi <= oversold_cross and current_rsi > oversold_cross:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi_cross_up',
                message=f"RSI{period} 从超卖区({oversold_cross}↓)向上突破，当前={current_rsi:.1f}",
                current_value=current_rsi,
                threshold=oversold_cross,
                suggestion="RSI从超卖区回升，空头力量耗尽，可能开启反弹，关注做多机会"
            )
        
        # 超买后向下穿越65 → 触发空头信号（比穿越50更早）
        if prev_rsi >= overbought_cross and current_rsi < overbought_cross:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='rsi_cross_down',
                message=f"RSI{period} 从超买区({overbought_cross}↑)向下突破，当前={current_rsi:.1f}",
                current_value=current_rsi,
                threshold=overbought_cross,
                suggestion="RSI从超买区回落，多头力量开始衰减，注意回调风险"
            )
            
        return None
        
    def check_ma_break(self, df: pd.DataFrame, config: dict) -> Optional[Alert]:
        """检查价格突破均线 → 趋势启动信号
        金叉死叉（快慢均线交叉）也在这里处理
        """
        ma_period = config.get('params', {}).get('ma_period', 50)
        fast_ma = config.get('params', {}).get('fast_ma', 20)
        slow_ma = config.get('params', {}).get('slow_ma', 50)
        
        # 先检查价格突破
        break_type = IndicatorCalculator.check_price_break_ma(df, ma_period)
        
        if break_type == 'up_break':
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='ma_break_up',
                message=f"📈 价格从下方突破MA{ma_period}，形成上涨突破",
                current_value=df.close.iloc[-1],
                threshold=IndicatorCalculator.ma(df, ma_period).iloc[-1],
                suggestion=f"价格突破{ma_period}日均线，上涨趋势可能启动，关注做多机会"
            )
        
        if break_type == 'down_break':
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='ma_break_down',
                message=f"📉 价格从上方跌破MA{ma_period}，形成下跌突破",
                current_value=df.close.iloc[-1],
                threshold=IndicatorCalculator.ma(df, ma_period).iloc[-1],
                suggestion=f"价格跌破{ma_period}日均线，下跌趋势可能启动，注意规避风险"
            )
        
        # 检查快慢均线金叉死叉
        cross_type = IndicatorCalculator.check_ma_cross(df, fast_ma, slow_ma)
        if cross_type == 'golden_cross':
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='golden_cross',
                message=f"🥳 MA{fast_ma} 金叉 MA{slow_ma}",
                current_value=0,
                threshold=0,
                suggestion=f"短期均线上穿长期均线，上涨趋势确立，趋势跟踪策略可入场"
            )
        
        if cross_type == 'dead_cross':
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='dead_cross',
                message=f"💀 MA{fast_ma} 死叉 MA{slow_ma}",
                current_value=0,
                threshold=0,
                suggestion=f"短期均线下穿长期均线，下跌趋势确立，建议减仓规避风险"
            )
            
        return None
    
    def check_volatility(self, df: pd.DataFrame, config: dict) -> Optional[Alert]:
        """检查波动率异常 - 分级预警：
        1.5倍 → 温和预警（开始放大）
        2.0倍 → 强预警（高波动确认）
        """
        window = config.get('params', {}).get('window', 20)
        mild_threshold = config.get('params', {}).get('mild_threshold', 1.5)
        strong_threshold = config.get('params', {}).get('strong_threshold', 2.0)
        
        vol = IndicatorCalculator.volatility(df, window)
        historical_vol = IndicatorCalculator.volatility(df.iloc[:-1], window)
        if historical_vol == 0:
            return None
        
        if vol > historical_vol * strong_threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='volatility_strong',
                message=f"⚡️ 波动率强力放大：当前 {vol:.2f} > {strong_threshold}x 历史均值 {historical_vol:.2f}",
                current_value=vol,
                threshold=historical_vol * strong_threshold,
                suggestion="波动率已经强力放大，大行情大概率已经启动，密切关注方向信号"
            )
        elif vol > historical_vol * mild_threshold:
            return Alert(
                asset=config.get('asset', 'unknown'),
                alert_type='volatility_mild',
                message=f"⚠️ 波动率开始放大：当前 {vol:.2f} > {mild_threshold}x 历史均值 {historical_vol:.2f}",
                current_value=vol,
                threshold=historical_vol * mild_threshold,
                suggestion="波动率开始扩张，可能酝酿大行情，提前做好准备"
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
            elif alert_type == 'ma_break':
                # 均线突破/金叉死叉（趋势启动信号）
                if len(df) >= 200:
                    ma_200 = IndicatorCalculator.ma(df, 200)
                    current_price = df.close.iloc[-1]
                    current_ma200 = ma_200.iloc[-1]
                    deviation = abs(current_price - current_ma200) / current_ma200
                    max_deviation = config.get('params', {}).get('max_deviation_from_ma200', 0.2)
                    if deviation > max_deviation:
                        # 趋势行情，突破才更有效，所以不过滤
                        pass
                alert = self.check_ma_break(df, config)
            elif alert_type == 'volatility':
                # MA200过滤同理
                if len(df) >= 200:
                    ma_200 = IndicatorCalculator.ma(df, 200)
                    current_price = df.close.iloc[-1]
                    current_ma200 = ma_200.iloc[-1]
                    deviation = abs(current_price - current_ma200) / current_ma200
                    max_deviation = config.get('params', {}).get('max_deviation_from_ma200', 0.2)
                    if deviation > max_deviation:
                        if deviation > max_deviation:
                            pass
                alert = self.check_volatility(df, config)
            elif alert_type == 'ratio':
                # 金银比需要黄金和白银数据
                if gold_df is not None and silver_df is not None and len(gold_df) > 0 and len(silver_df) > 0:
                    alert = self.check_gold_silver_ratio(gold_df, silver_df, config)
                
            if alert:
                alerts.append(alert)
                
        return alerts
