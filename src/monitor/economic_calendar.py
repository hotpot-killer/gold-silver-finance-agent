import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EconomicEvent:
    """经济事件"""
    name: str
    country: str
    date: str
    time: str
    impact: str  # low/medium/high
    actual: str = None
    forecast: str = None
    previous: str = None

class EconomicCalendar:
    """经济日历抓取 - 提前提醒高影响事件"""
    
    def __init__(self):
        # 使用免费API
        self.api_url = "https://api.ninjaapi.co/economic-calendar"
        
    def get_high_impact_events_next_day(self) -> List[EconomicEvent]:
        """获取明天高影响事件（对贵金属影响大的：非农/CPI/Fed利率）"""
        try:
            # 获取明天日期
            tomorrow = datetime.now() + timedelta(days=1)
            date_str = tomorrow.strftime("%Y-%m-%d")
            
            params = {
                'date': date_str
            }
            
            resp = requests.get(self.api_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            events = []
            for item in data.get('data', []):
                impact = item.get('impact', '').lower()
                if impact != 'high':
                    continue  # 只保留高影响事件
                
                # 过滤出对黄金影响较大的事件
                name = item.get('name', '').lower()
                important_keywords = [
                    'nonfarm', 'payroll', 'nfp',  # 非农
                    'cpi', 'inflation',  # CPI通胀
                    'fed', 'rate', 'interest',  # 利率决议
                    'ppi', 
                    'gdp',
                    'unemployment'
                ]
                
                is_important = False
                for kw in important_keywords:
                    if kw in name:
                        is_important = True
                        break
                        
                if is_important:
                    events.append(EconomicEvent(
                        name=item.get('name'),
                        country=item.get('country'),
                        date=item.get('date'),
                        time=item.get('time', ''),
                        impact=impact,
                        forecast=str(item.get('forecast', '')),
                        previous=str(item.get('previous', ''))
                    ))
            
            logger.info(f"Found {len(events)} high impact economic events for tomorrow")
            return events
        except Exception as e:
            logger.error(f"Failed to fetch economic calendar: {e}")
            return []
    
    def format_events_for_notification(self, events: List[EconomicEvent]) -> str:
        """格式化为通知文本"""
        if not events:
            return ""
            
        content = "### 📅 明日高影响经济事件提醒\n\n"
        content += "> 明天有重要宏观数据公布，波动率大概率放大，请提前做好准备：\n\n"
        
        for ev in events:
            content += f"**{ev.name}** ({ev.country})\n"
            if ev.forecast:
                content += f"- 预期: {ev.forecast}\n"
            if ev.previous:
                content += f"- 前值: {ev.previous}\n"
            content += "\n"
        
        content += "---\n\n"
        return content
