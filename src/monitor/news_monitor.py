"""
多地区新闻监控 - 支持中东、美国、中国等地区新闻
参考 MiroFish 思想：从现实世界提取种子信息

Author: wzh
Date: 2026-03-19
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from .base import BaseMonitor, NewsItem

logger = logging.getLogger(__name__)

class NewsMonitor(BaseMonitor):
    """多地区新闻监控 - 支持中东、美国、中国等地区新闻"""
    
    # 地区新闻源配置
    NEWS_SOURCES = {
        'global': {
            'name': '全球',
            'sources': [
                'https://pacaio.match.qq.com/irs/rcd?cid=146&token=49c1b3d9a1f429c2&ext=top',  # 腾讯财经
            ]
        },
        'middle_east': {
            'name': '中东',
            'sources': [
                'https://pacaio.match.qq.com/irs/rcd?cid=146&token=49c1b3d9a1f429c2&ext=top',  # 腾讯财经全球
            ],
            'keywords': ['中东', '以色列', '哈马斯', '伊朗', '也门', '胡塞', '海湾', '原油', '油价', '石油', '中东局势', '巴以', '伊核', '霍尔木兹']
        },
        'us': {
            'name': '美国',
            'sources': [
                'https://pacaio.match.qq.com/irs/rcd?cid=146&token=49c1b3d9a1f429c2&ext=top',  # 腾讯财经全球
            ],
            'keywords': ['美联储', '降息', '加息', '通胀', '非农', 'CPI', 'PPI', '美国经济', '美元']
        },
        'cn': {
            'name': '中国',
            'sources': [
                'https://pacaio.match.qq.com/irs/rcd?cid=146&token=49c1b3d9a1f429c2&ext=top',  # 腾讯财经全球
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
            
            for source_url in region_config['sources']:
                try:
                    news = self._fetch_from_source(source_url, region_config.get('keywords', []), region, cutoff)
                    all_news.extend(news)
                except Exception as e:
                    logger.error(f"Failed to fetch from {source_url} for {region}: {e}")
        
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
    
    def _fetch_from_source(self, url: str, keywords: List[str], region: str, cutoff: datetime) -> List[NewsItem]:
        """从单个新闻源抓取"""
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://finance.qq.com/"
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return results
                
            data = resp.json()
            if data.get('code') == '0' and 'list' in data:
                for item in data['list']:
                    try:
                        title = item.get('title', '').strip()
                        if not title:
                            continue
                        
                        # 如果有关键词，只保留包含关键词的新闻
                        if keywords:
                            title_lower = title.lower()
                            has_keyword = any(kw.lower() in title_lower for kw in keywords)
                            if not has_keyword and region != 'global':
                                continue  # 非全球区域只保留相关新闻
                        
                        url = item.get('vurl', '')
                        
                        # 给 NewsItem 添加 region 字段（通过动态属性）
                        news_item = NewsItem(
                            title=title,
                            content='',
                            url=url,
                            source='qq_finance',
                            publish_time=datetime.now()
                        )
                        # 动态添加 region 属性
                        news_item.region = region
                        results.append(news_item)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to fetch from {url}: {e}")
        
        return results
    
    def get_news_by_region(self, news: List[NewsItem], region: str) -> List[NewsItem]:
        """按地区筛选新闻"""
        return [n for n in news if hasattr(n, 'region') and n.region == region]
