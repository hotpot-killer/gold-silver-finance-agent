"""
基础功能测试用例
"""
import os
import sys
# 添加项目根目录到Python路径
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """测试所有模块是否能正常导入"""
    logger.info("Testing module imports...")
    
    from src.monitor.base import BaseMonitor, NewsItem, PriceData
    logger.info("✓ monitor.base imported")
    
    from src.monitor.price_monitor import PriceMonitor
    logger.info("✓ monitor.price_monitor imported")
    
    from src.monitor.news_monitor import NewsMonitor
    logger.info("✓ monitor.news_monitor imported")
    
    from src.research.report_summarizer import ReportSummarizer
    logger.info("✓ research.report_summarizer imported")
    
    from src.alert.indicator import IndicatorCalculator
    logger.info("✓ alert.indicator imported")
    
    from src.alert.trigger import AlertTrigger, Alert
    logger.info("✓ alert.trigger imported")
    
    from src.notifier.sender import (
        DingTalkNotifier, WorkWechatNotifier, TelegramNotifier, format_alerts
    )
    logger.info("✓ notifier.sender imported")
    
    from src.scheduler.job import TaskScheduler
    logger.info("✓ scheduler.job imported")
    
    import main
    logger.info("✓ main imported")
    
    logger.info("\n✅ All modules imported successfully!")
    return True

def test_config_loading():
    """测试配置加载"""
    from main import load_config, Config
    
    config_path = "config/config.example.yaml"
    assert os.path.exists(config_path), f"Config example not found at {config_path}"
    
    config = load_config(config_path)
    
    assert config is not None
    assert hasattr(config, 'tushare')
    assert hasattr(config, 'llm')
    assert hasattr(config, 'monitor')
    assert hasattr(config, 'alerts')
    assert hasattr(config, 'notify')
    
    logger.info(f"✅ Config loaded successfully")
    logger.info(f"  - Watching {len(config.monitor.stocks)} stocks")
    logger.info(f"  - {len(config.alerts.alerts)} alert rules")
    
    return True

def test_indicator_calculator():
    """测试技术指标计算"""
    import pandas as pd
    import numpy as np
    from src.alert.indicator import IndicatorCalculator
    
    # 创建模拟数据
    data = pd.DataFrame({
        'close': np.random.normal(100, 5, 100)
    })
    
    ma = IndicatorCalculator.ma(data, 20)
    assert len(ma) == 100
    logger.info("✅ MA calculation passed")
    
    rsi = IndicatorCalculator.rsi(data, 14)
    assert len(rsi) == 100
    logger.info("✅ RSI calculation passed")
    
    upper, middle, lower = IndicatorCalculator.bollinger_bands(data, 20)
    assert len(upper) == 100
    logger.info("✅ Bollinger Bands calculation passed")
    
    vol = IndicatorCalculator.volatility(data, 20)
    assert isinstance(vol, float)
    logger.info("✅ Volatility calculation passed")
    
    return True

def main():
    """运行所有测试"""
    tests = [
        test_imports,
        test_config_loading,
        test_indicator_calculator,
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*60)
    print("Running Active Finance Agent - Basic Tests")
    print("="*60 + "\n")
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Project is ready to go!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
