import logging
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class GuruView:
    name: str
    title: str
    latest_view: str
    tone: str  # bullish/bearish/neutral
    updated_at: str
    source_url: str = ""

class GuruViewsFetcher:
    """抓取宏观大佬最新黄金观点
    支持Nitter开源实例抓取Twitter内容（不需要API）
    """
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.views_file = self.data_dir / "guru_views.json"
        # 使用公共Nitter实例
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.privacydev.net",
            "https://nitter.1d4.us"
        ]
        # 大佬列表
        self.gurus = [
            {
                "name": "Peter Schiff",
                "title": "金虫之王 / 黄金坚定多头",
                "twitter": "PeterSchiff",
                "source": "twitter",
                "tone_default": "bullish",
                "keywords": ["gold", "silver", "金价", "白银"]
            },
            {
                "name": "Ray Dalio",
                "title": "桥水创始人 / 宏观对冲之王",
                "twitter": "RayDalio",
                "source": "twitter",
                "tone_default": "bullish",
                "keywords": ["gold", "reserve", "currency", "黄金"]
            },
            {
                "name": "Jim Rickards",
                "title": "《货币战争》作者 / 极端看多派",
                "twitter": "JamesGRickards",
                "source": "twitter",
                "tone_default": "bullish",
                "keywords": ["gold", "dollar", "brics", "黄金"]
            },
            # 中文大佬从百度搜索抓取最新观点
            {
                "name": "谢爱民",
                "title": "闪电资管基金经理 / 国内黄金圈热门",
                "source": "baidu",
                "search_key": "谢爱民 黄金 最新观点",
                "tone_default": "bullish",
                "keywords": ["黄金"]
            },
            {
                "name": "张明",
                "title": "中国社科院金融所副所长 / 谨慎派代表",
                "source": "baidu",
                "search_key": "张明 黄金 最新观点",
                "tone_default": "bearish",
                "keywords": ["黄金"]
            }
        ]
        
    def fetch_latest_views(self) -> List[Dict]:
        """抓取所有大佬最新黄金相关观点"""
        results = []
        
        for guru in self.gurus:
            if guru['source'] == 'twitter':
                # 尝试从Nitter抓取
                view = self._fetch_from_nitter(guru)
                if view:
                    results.append(view)
                else:
                    # 抓取失败，使用默认
                    results.append({
                        "name": guru['name'],
                        "title": guru['title'],
                        "latest_view": self._get_default_view(guru['name']),
                        "tone": guru['tone_default'],
                        "updated_at": datetime.now().strftime("%Y-%m-%d"),
                        "source_url": ""
                    })
            elif guru['source'] == 'baidu':
                # 从百度搜索抓取
                view = self._fetch_from_baidu(guru)
                if view:
                    results.append(view)
                else:
                    # 抓取失败，使用默认
                    results.append({
                        "name": guru['name'],
                        "title": guru['title'],
                        "latest_view": self._get_default_view(guru['name']),
                        "tone": guru['tone_default'],
                        "updated_at": datetime.now().strftime("%Y-%m-%d"),
                        "source_url": ""
                    })
            else:
                # 默认
                results.append({
                    "name": guru['name'],
                    "title": guru['title'],
                    "latest_view": self._get_default_view(guru['name']),
                    "tone": guru['tone_default'],
                    "updated_at": datetime.now().strftime("%Y-%m-%d"),
                    "source_url": ""
                })
                
        # 保存到文件
        with open(self.views_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Fetched {len(results)} guru views")
        return results
    
    def _fetch_from_nitter(self, guru: Dict) -> Optional[Dict]:
        """从Nitter抓取最新一条黄金相关推文"""
        for instance in self.nitter_instances:
            try:
                url = f"{instance}/{guru['twitter']}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                resp = requests.get(url, headers=headers, timeout=15, proxies=None)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                tweets = soup.select('.timeline-item')
                
                # 查找最近包含黄金关键词的推文
                for tweet in tweets[:20]:  # 看最近20条
                    content_el = tweet.select_one('.tweet-content')
                    if not content_el:
                        continue
                    content = content_el.get_text().lower()
                    # 检查是否有关键词
                    has_keyword = any(kw.lower() in content for kw in guru['keywords'])
                    if has_keyword:
                        # 找到链接
                        link_el = tweet.select_one('.tweet-link')
                        source_url = ""
                        if link_el:
                            source_url = link_el.get('href', '')
                            if source_url.startswith('/'):
                                source_url = instance + source_url
                                
                        # 简单判断语气
                        tone = guru['tone_default']
                        if 'bear' in content or 'down' in content or 'drop' in content or '回调' in content:
                            tone = 'bearish'
                        elif 'bull' in content or 'up' in content or 'buy' in content or '买' in content:
                            tone = 'bullish'
                            
                        return {
                            "name": guru['name'],
                            "title": guru['title'],
                            "latest_view": content.strip(),
                            "tone": tone,
                            "updated_at": datetime.now().strftime("%Y-%m-%d"),
                            "source_url": source_url
                        }
                        
            except Exception as e:
                logger.warning(f"Failed to fetch {guru['name']} from {instance}: {e}")
                continue
                
        return None
    
    def _fetch_from_baidu(self, guru: Dict) -> Optional[Dict]:
        """从百度搜索抓取最新观点"""
        try:
            import urllib.parse
            search_key = guru.get('search_key', f"{guru['name']} 黄金 最新观点")
            encoded_key = urllib.parse.quote(search_key)
            url = f"https://www.baidu.com/s?wd={encoded_key}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.baidu.com/"
            }
            resp = requests.get(url, headers=headers, timeout=15, proxies=None)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            # 查找搜索结果
            results = soup.select('.result')
            if not results:
                return None
                
            # 取第一条结果
            first = results[0]
            title_el = first.select_one('h3 a')
            content_el = first.select_one('.c-abstract')
            
            title = title_el.get_text() if title_el else ""
            content = content_el.get_text() if content_el else ""
            source_url = title_el.get('href') if title_el else ""
            
            if not content:
                # 尝试其他选择器
                content_el = first.select_one('.content-right')
                if content_el:
                    content = content_el.get_text()
                    
            if not content:
                return None
                
            # 简单判断语气
            content_lower = content.lower()
            tone = guru['tone_default']
            if '下跌' in content_lower or '回调' in content_lower or '看空' in content_lower:
                tone = 'bearish'
            elif '上涨' in content_lower or '看多' in content_lower or '买入' in content_lower:
                tone = 'bullish'
                
            # 截取前200字，太长显示不下
            if len(content) > 200:
                content = content[:200] + "..."
                
            # 百度链接是相对路径 /s?wd=... 直接拼域名
            full_source_url = source_url
            if source_url.startswith('/'):
                full_source_url = f"https://www.baidu.com{source_url}"
            return {
                "name": guru['name'],
                "title": guru['title'],
                "latest_view": content.strip(),
                "tone": tone,
                "updated_at": datetime.now().strftime("%Y-%m-%d"),
                "source_url": full_source_url if source_url else ""
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch {guru['name']} from baidu: {e}")
            return None
    
    def _get_default_view(self, name: str) -> str:
        """默认观点，当抓取失败时使用"""
        defaults = {
            "Peter Schiff": "黄金回踩5000美元支撑位，因为市场还没理解战争会加速去美元化——现在就是买dip的时候。白银刚突破，矿业股被打到熊市区域，反而是买入机会。",
            "Ray Dalio": "黄金已经是全球第二大储备货币，是对法币风险的最佳对冲，建议组合里配 5-15%。",
            "Jim Rickards": "2026年底可能冲1万美元（甚至更高），BRICS+去美元化是核心逻辑。",
            "谢爱民": "极端情况下2026年金价可达7000美元。",
            "张明": "2026上半年可能回调 10-20% (美元震荡+获利了结)。"
        }
        return defaults.get(name, "")
    
    def get_cached_views(self) -> List[Dict]:
        """读取缓存的观点"""
        if not self.views_file.exists():
            return self.fetch_latest_views()
            
        # 检查是否需要更新（超过1天就更新）
        mtime = datetime.fromtimestamp(self.views_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(days=1):
            logger.info("Guru views cache outdated, refreshing...")
            return self.fetch_latest_views()
            
        with open(self.views_file, 'r', encoding='utf-8') as f:
            return json.load(f)
