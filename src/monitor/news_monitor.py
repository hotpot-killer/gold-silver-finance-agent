"""
多地区新闻监控 - 支持中东、美国、中国等地区新闻
参考 MiroFish 思想：从现实世界提取种子信息
使用 requests + parsel（避免 scrapling 的异步/同步问题）

Author: wzh
Date: 2026-03-19
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from parsel import Selector
from .base import BaseMonitor, NewsItem

logger = logging.getLogger(__name__)

class NewsMonitor(BaseMonitor):
    """多地区新闻监控 - 使用 requests + parsel（稳定）"""
    
    # 地区新闻源配置 - 搜狐新闻
    NEWS_SOURCES = {
        'global': {
            'name': '全球',
            'urls': [
                'https://news.sohu.com/',
            ],
            'keywords': ['黄金', '白银', '原油', '金价', '银价', '油价', '贵金属', '大宗商品']
        },
        'middle_east': {
            'name': '中东',
            'urls': [
                'https://news.sohu.com/',
            ],
            'keywords': ['中东', '以色列', '哈马斯', '伊朗', '也门', '胡塞', '海湾', '原油', '油价', '石油', '中东局势', '巴以', '伊核', '霍尔木兹']
        },
        'us': {
            'name': '美国',
            'urls': [
                'https://news.sohu.com/',
            ],
            'keywords': ['美联储', '降息', '加息', '通胀', '非农', 'CPI', 'PPI', '美国经济', '美元']
        },
        'cn': {
            'name': '中国',
            'urls': [
                'https://news.sohu.com/',
            ],
            'keywords': ['中国央行', '人民币', '汇率', '中国经济', '进出口', '黄金储备']
        }
    }
    
    def __init__(self, sources: List[str] = None, regions: List[str] = None):
        """
        初始化新闻监控
        :param sources: 旧参数（保留兼容）
        :param regions: 地区列表，可选 'global', 'middle_east', 'us', 'cn'
        """
        self.sources = sources or []
        self.regions = regions or ['global', 'middle_east', 'us', 'cn']
    
    def fetch_latest(self, hours: int = 24) -> List[NewsItem]:
        """
        获取最近N小时新闻，支持多地区
        :param hours: 最近多少小时
        :return: 新闻列表
        """
        all_news = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # 从每个地区的新闻源抓取
        for region in self.regions:
            if region not in self.NEWS_SOURCES:
                continue
                
            region_config = self.NEWS_SOURCES[region]
            
            for url in region_config['urls']:
                try:
                    news = self._fetch_from_sohu(url, region_config.get('keywords', []), region, cutoff)
                    all_news.extend(news)
                except Exception as e:
                    logger.error(f"Failed to fetch from {url} for {region}: {e}")
        
        # 去重（按标题）
        seen_titles = set()
        unique_news = []
        for item in all_news:
            if item.title not in seen_titles:
                seen_titles.add(item.title)
                unique_news.append(item)
        
        # 兜底：如果没有新闻，返回默认新闻
        if len(unique_news) == 0:
            unique_news.append(NewsItem(
                title="市场简讯：关注黄金白银原油市场动态",
                content="",
                url="",
                source="system",
                region="global",
                publish_time=datetime.now()
            ))
        
        logger.info(f"Fetched {len(unique_news)} unique news items from regions: {', '.join(self.regions)}")
        return unique_news
    
    def _fetch_from_sohu(self, url: str, keywords: List[str], region: str, cutoff: datetime) -> List[NewsItem]:
        """使用 requests + parsel 从搜狐新闻抓取（稳定）"""
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://news.sohu.com/"
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return results
                
            # 使用 parsel 解析 HTML
            sel = Selector(text=resp.text)
            
            # 尝试多个选择器获取链接
            href_selectors = [
                'a[href*="/a/"]::attr(href)',
                'a[href*="news.sohu.com"]::attr(href)',
                'h4 a::attr(href)',
                '.news-item a::attr(href)',
            ]
            
            hrefs = set()
            for sel_str in href_selectors:
                hrefs.update(sel.css(sel_str).getall())
            
            # 同时获取标题
            title_selectors = [
                'a[href*="/a/"]::text',
                'a[href*="news.sohu.com"]::text',
                'h4 a::text',
                '.news-item a::text',
                '.title::text',
            ]
            
            titles = []
            for sel_str in title_selectors:
                titles.extend([t.strip() for t in sel.css(sel_str).getall() if t.strip()])
            
            # 组合标题和链接
            for i, href in enumerate(list(hrefs)[:20]):
                try:
                    if i >= len(titles):
                        continue
                        
                    title = titles[i].strip()
                    if not title:
                        continue
                        
                    # 如果有关键词，只保留包含关键词的新闻
                    if keywords:
                        title_lower = title.lower()
                        has_keyword = any(kw.lower() in title_lower for kw in keywords)
                        if not has_keyword and region != 'global':
                            continue  # 非全球区域只保留相关新闻
                    
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = 'https://news.sohu.com' + href
                        else:
                            href = 'https://news.sohu.com/' + href
                    
                    # 给 NewsItem 添加 region 字段（通过动态属性）
                    news_item = NewsItem(
                        title=title,
                        content='',
                        url=href,
                        source='sohu_news',
                        publish_time=datetime.now()
                    )
                    # 动态添加 region 属性
                    news_item.region = region
                    results.append(news_item)
                    
                except Exception as e:
                    continue
                        
        except Exception as e:
            logger.error(f"Failed to fetch from {url} with requests: {e}")
        
        return results
    
    def get_news_by_region(self, news: List[NewsItem], region: str) -> List[NewsItem]:
        """按地区筛选新闻"""
        return [n for n in news if hasattr(n, 'region') and n.region == region]
