import logging
from datetime import datetime, timedelta
from typing import List
from scrapling import Fetcher
from .base import BaseMonitor, NewsItem

logger = logging.getLogger(__name__)

class NewsMonitor(BaseMonitor):
    """宏观新闻监控 - 华尔街见闻/雪球"""
    
    SOURCES = {
        'wallstreetcn': 'https://wallstreetcn.com/news',
        'wallstreetcn': 'https://wallstreetcn.com/news',
        'xueqiu': 'https://xueqiu.com/news',
    }
    
    def __init__(self, sources: List[str], related_assets: List[str] = None):
        self.fetcher = Fetcher()
        self.sources = sources
        self.related_assets = related_assets or []
        
    def fetch_latest(self, hours: int = 24) -> List[NewsItem]:
        """获取最近N小时新闻"""
        results = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for source in self.sources:
            try:
                if source == 'wallstreetcn':
                    items = self._parse_wallstreetcn(cutoff)
                    results.extend(items)
                elif source == 'xueqiu':
                    items = self._parse_xueqiu(cutoff)
                    results.extend(items)
            except Exception as e:
                logger.error(f"Failed to fetch from {source}: {e}")
                
        logger.info(f"Fetched {len(results)} news items from {len(self.sources)} sources")
        return results
        
    def _parse_wallstreetcn(self, cutoff: datetime) -> List[NewsItem]:
        """解析华尔街见闻"""
        url = "https://wallstreetcn.com/news"
        page = self.fetcher.get(url)
        results = []
        
        for article in page.select('.article-item'):
            try:
                title = article.select_one('.title').get_text().strip()
                url = article.select_one('a').get('href')
                time_text = article.select_one('.time').get_text().strip()
                # 解析时间，判断是否在cutoff后
                
                results.append(NewsItem(
                    title=title,
                    content='',
                    url=url,
                    source='wallstreetcn',
                    publish_time=datetime.now()  # 简化，实际需要解析
                ))
            except Exception as e:
                continue
                
        return results
        
    def _parse_xueqiu(self, cutoff: datetime) -> List[NewsItem]:
        """解析雪球"""
        url = "https://xueqiu.com/news"
        page = self.fetcher.get(url)
        results = []
        
        for article in page.select('.news-item'):
            try:
                title = article.select_one('.title').get_text().strip()
                url = article.select_one('a').get('href')
                results.append(NewsItem(
                    title=title,
                    content='',
                    url=url,
                    source='xueqiu',
                    publish_time=datetime.now()
                ))
            except Exception as e:
                continue
                
        return results
