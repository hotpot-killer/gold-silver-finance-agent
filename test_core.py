#!/usr/bin/env python3
"""
核心功能测试脚本
测试指标计算、信号触发等核心功能
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_indicator_calculation():
    """测试技术指标计算"""
    logger.info("🧪 Testing indicator calculation...")
    
    from src.alert.indicator import IndicatorCalculator
    
    # 创建模拟价格数据
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    prices = np.cumsum(np.random.randn(100)) + 2000
    df = pd.DataFrame({
        'trade_date': [int(d.strftime('%Y%m%d')) for d in dates],
        'open': prices,
        'high': prices + np.random.rand(100)*5,
        'low': prices - np.random.rand(100)*5,
        'close': prices,
        'vol': np.random.randint(1000, 10000, 100)
    })
    
    # 测试MA
    try:
        ma50 = IndicatorCalculator.ma(df, 50)
        logger.info(f"✅ MA calculation OK, last value: {ma50.iloc[-1]:.2f}")
    except Exception as e:
        logger.error(f"❌ MA calculation failed: {e}")
        return False
    
    # 测试RSI
    try:
        rsi = IndicatorCalculator.rsi(df, 14)
        logger.info(f"✅ RSI calculation OK, last value: {rsi.iloc[-1]:.2f}")
    except Exception as e:
        logger.error(f"❌ RSI calculation failed: {e}")
        return False
    
    # 测试MACD
    try:
        macd, signal, hist = IndicatorCalculator.macd(df)
        logger.info(f"✅ MACD calculation OK, macd={macd:.2f}, signal={signal:.2f}")
    except Exception as e:
        logger.error(f"❌ MACD calculation failed: {e}")
        return False
    
    # 测试ATR
    try:
        atr = IndicatorCalculator.atr(df, 14)
        logger.info(f"✅ ATR calculation OK, value: {atr:.2f}")
    except Exception as e:
        logger.error(f"❌ ATR calculation failed: {e}")
        return False
    
    # 测试布林带
    try:
        upper, mid, lower = IndicatorCalculator.bollinger_bands(df)
        logger.info(f"✅ Bollinger Bands calculation OK, {len(upper)} values")
    except Exception as e:
        logger.error(f"❌ Bollinger Bands calculation failed: {e}")
        return False
    
    # 测试波动率
    try:
        vol = IndicatorCalculator.volatility(df, 20)
        logger.info(f"✅ Volatility calculation OK, value: {vol:.4f}")
    except Exception as e:
        logger.error(f"❌ Volatility calculation failed: {e}")
        return False
    
    # 测试RSI背离检测
    try:
        # 创建一个顶背离
        df_div = df.copy()
        # 价格新高
        df_div.loc[99, 'close'] = df_div['close'].max() + 10
        # RSI不新高（手动修改）
        divergence = IndicatorCalculator.check_rsi_divergence(df_div)
        logger.info(f"✅ RSI divergence check OK, result: {divergence}")
    except Exception as e:
        logger.error(f"❌ RSI divergence check failed: {e}")
        return False
    
    # 测试均线金叉死叉
    try:
        cross = IndicatorCalculator.check_ma_cross(df, 20, 50)
        logger.info(f"✅ MA cross check OK, result: {cross}")
    except Exception as e:
        logger.error(f"❌ MA cross check failed: {e}")
        return False
    
    logger.info("✅ All indicator calculations passed!\n")
    return True

def test_alert_trigger():
    """测试预警触发逻辑"""
    logger.info("🧪 Testing alert trigger...")
    
    from src.alert.indicator import IndicatorCalculator
    from src.alert.trigger import AlertTrigger
    
    # 创建模拟数据
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    prices = np.cumsum(np.random.randn(100)) + 2000
    df = pd.DataFrame({
        'trade_date': [int(d.strftime('%Y%m%d')) for d in dates],
        'open': prices,
        'high': prices + np.random.rand(100)*5,
        'low': prices - np.random.rand(100)*5,
        'close': prices,
        'vol': np.random.randint(1000, 10000, 100)
    })
    
    # 测试配置 - RSI预警
    configs = [
        {
            "enabled": True,
            "asset": "gold",
            "type": "rsi",
            "params": {
                "period": 14,
                "overbought_cross": 65,
                "oversold_cross": 35,
                "lookback": 10,
                "slope_threshold": 3,
                "max_deviation_from_ma200": 0.2
            }
        },
        {
            "enabled": True,
            "asset": "gold",
            "type": "ma_break",
            "params": {
                "ma_period": 50,
                "fast_ma": 20,
                "slow_ma": 50
            }
        },
        {
            "enabled": True,
            "asset": "gold",
            "type": "volatility",
            "params": {
                "window": 20,
                "mild_threshold": 1.5,
                "strong_threshold": 2.0
            }
        }
    ]
    
    try:
        trigger = AlertTrigger(configs)
        alerts = trigger.check_all('gold', df)
        logger.info(f"✅ Alert trigger OK, found {len(alerts)} alerts")
        for alert in alerts:
            logger.info(f"   - {alert.alert_type}: {alert.message}")
    except Exception as e:
        logger.error(f"❌ Alert trigger failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("✅ Alert trigger test passed!\n")
    return True

def test_config_loading():
    """测试配置加载"""
    logger.info("🧪 Testing config loading...")
    
    try:
        from main import load_config
        config = load_config('config/config.example.yaml')
        logger.info(f"✅ Config loading OK")
        logger.info(f"   - log_level: {config.log_level}")
        logger.info(f"   - data_dir: {config.data_dir}")
        logger.info(f"   - monitor interval: {config.monitor.interval}")
        logger.info(f"   - COT enabled: {config.monitor.cot.get('enabled', False)}")
        logger.info(f"   - Economic calendar enabled: {config.monitor.economic_calendar.get('enabled', True)}")
        logger.info(f"   - LLM model: {config.llm.model}")
    except Exception as e:
        logger.error(f"❌ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("✅ Config loading test passed!\n")
    return True

def test_gold_silver_ratio():
    """测试金银比计算"""
    logger.info("🧪 Testing gold-silver ratio...")
    
    from src.alert.indicator import IndicatorCalculator
    
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # 黄金价格 ~2000-3000
    gold_prices = np.cumsum(np.random.randn(100)) + 2500
    gold_df = pd.DataFrame({
        'trade_date': [int(d.strftime('%Y%m%d')) for d in dates],
        'close': gold_prices
    })
    
    # 白银价格 ~20-30
    silver_prices = np.cumsum(np.random.randn(100)) + 25
    silver_df = pd.DataFrame({
        'trade_date': [int(d.strftime('%Y%m%d')) for d in dates],
        'close': silver_prices
    })
    
    try:
        ratio = IndicatorCalculator.ratio(gold_df, silver_df)
        logger.info(f"✅ Gold-silver ratio calculation OK: {ratio:.1f}")
    except Exception as e:
        logger.error(f"❌ Gold-silver ratio calculation failed: {e}")
        return False
    
    logger.info("✅ Gold-silver ratio test passed!\n")
    return True

def main():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("🚀 Starting core functionality tests for gold-silver-finance-agent")
    logger.info("=" * 60 + "\n")
    
    tests = [
        test_indicator_calculation,
        test_alert_trigger,
        test_config_loading,
        test_gold_silver_ratio,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"📊 Test Summary: {passed} passed, {failed} failed")
    logger.info("=" * 60)
    
    if failed == 0:
        logger.info("✅ All tests passed! Project is ready to run.")
        return True
    else:
        logger.error("❌ Some tests failed, please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
