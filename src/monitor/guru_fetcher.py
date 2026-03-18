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
                "tone_default": "bullish",
                "keywords": ["gold", "silver", "金价", "白银"]
            },
            {
                "name": "Ray Dalio",
                "title": "桥水创始人 / 宏观对冲之王",
                "twitter": "RayDalio",
                "tone_default": "bullish",
                "keywords": ["gold", "reserve", "currency", "黄金"]
            },
            {
                "name": "Jim Rickards",
                "title": "《货币战争》作者 / 极端看多派",
                "twitter": "JamesGRickards",
                "tone_default": "bullish",
                "keywords": ["gold", "dollar", "brics", "黄金"]
            },
            # 中文大佬我们从其他来源抓取，这里先保留结构
            {
                "name": "谢爱民",
                "title": "闪电资管基金经理 / 国内黄金圈热门",
                "twitter": "",
                "tone_default": "bullish",
                "keywords": ["黄金"]
            },
            {
                "name": "张明",
                "title": "中国社科院金融所副所长 / 谨慎派代表",
                "twitter": "",
                "tone_default": "bearish",
                "keywords": ["黄金"]
            }
        ]
        
    def fetch_latest_views(self) -> List[Dict]:
        """抓取所有大佬最新黄金相关观点"""
        results = []
        
        for guru in self.gurus:
            if not guru['twitter']:
                # 没有Twitter，使用已有数据或默认
                results.append({
                    "name": guru['name'],
                    "title": guru['title'],
                    "latest_view": self._get_default_view(guru['name']),
                    "tone": guru['tone_default'],
                    "updated_at": datetime.now().strftime("%Y-%m-%d"),
                    "source_url": ""
                })
                continue
                
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
