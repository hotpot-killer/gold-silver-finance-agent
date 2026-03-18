import logging
from datetime import datetime, timedelta
from typing import List
from scrapling import Fetcher
from .base import BaseMonitor, NewsItem

logger = logging.getLogger(__name__)

class NewsMonitor(BaseMonitor):
    """宏观新闻监控 - 华尔街见闻/雪球/新浪财经"""
    
    SOURCES = {
        'wallstreetcn': 'https://wallstreetcn.com/news',
        'xueqiu': 'https://xueqiu.com/news',
        'sina': 'https://finance.sina.com.cn/roll/',
        'caixin': 'https://www.caixin.com',
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
                elif source == 'sina':
                    items = self._parse_sina(cutoff)
                    results.extend(items)
                elif source == 'caixin':
                    items = self._parse_caixin(cutoff)
                    results.extend(items)
            except Exception as e:
                logger.error(f"Failed to fetch from {source}: {e}")
                
        logger.info(f"Fetched {len(results)} news items from {len(self.sources)} sources")
        return results
        
    def _parse_wallstreetcn(self, cutoff: datetime) -> List[NewsItem]:
        """解析华尔街见闻"""
        from parsel import Selector
        url = "https://wallstreetcn.com/news"
        page = self.fetcher.get(url)
        selector = Selector(page.text)
        results = []
        
        for article in selector.css('.article-item'):
            try:
                title = article.css('.title::text').get().strip()
                url = article.css('a::attr(href)').get()
                results.append(NewsItem(
                    title=title,
                    content='',
                    url=url,
                    source='wallstreetcn',
                    publish_time=datetime.now()
                ))
            except Exception as e:
                continue
                
        return results
        
    def _parse_xueqiu(self, cutoff: datetime) -> List[NewsItem]:
        """解析雪球"""
        from parsel import Selector
        url = "https://xueqiu.com/news"
        page = self.fetcher.get(url)
        selector = Selector(page.text)
        results = []
        
        for article in selector.css('.news-item'):
            try:
                title = article.css('.title::text').get().strip()
                url = article.css('a::attr(href)').get()
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
        
    def _parse_sina(self, cutoff: datetime) -> List[NewsItem]:
        """解析新浪财经"""
        url = "https://finance.sina.com.cn/roll/"
        page = self.fetcher.get(url)
        from parsel import Selector
        selector = Selector(page.text)
        results = []
        
        for article in selector.css('.feed-card-item'):
            try:
                title = article.css('a::text').get()
                url = article.css('a::attr(href)').get()
                if title and url:
                    results.append(NewsItem(
                        title=title.strip(),
                        content='',
                        url=url,
                        source='sina',
                        publish_time=datetime.now()
                    ))
            except Exception as e:
                continue
                
        return results
        
    def _parse_caixin(self, cutoff: datetime) -> List[NewsItem]:
        """解析财新"""
        url = "https://www.caixin.com"
        page = self.fetcher.get(url)
        from parsel import Selector
        selector = Selector(page.text)
        results = []
        
        articles = selector.css('.article-list li')
        for article in articles:
            try:
                title = article.css('a::text').get()
                url = article.css('a::attr(href)').get()
                if title and url:
                    results.append(NewsItem(
                        title=title.strip(),
                        content='',
                        url=url,
                        source='caixin',
                        publish_time=datetime.now()
                    ))
            except Exception as e:
                continue
                
        return results
