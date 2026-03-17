from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

logger = __import__('logging').getLogger(__name__)

@dataclass
class NewsItem:
    """新闻数据结构"""
    title: str
    content: str
    url: str
    source: str
    publish_time: datetime
    related_assets: List[str] = None

@dataclass
class PriceData:
    """价格数据结构"""
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    timestamp: datetime
    volume: Optional[float] = None

class BaseMonitor(ABC):
    """监控器基类"""
    
    @abstractmethod
    def fetch_latest(self) -> List:
        """获取最新数据"""
        pass
