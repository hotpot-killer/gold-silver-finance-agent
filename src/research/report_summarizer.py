import logging
from typing import List, Optional
from openai import OpenAI
from ..monitor import NewsItem

logger = logging.getLogger(__name__)

class ReportSummarizer:
    """研报/新闻总结 Agent - 使用 LLM 浓缩成"对你资产的影响"""
    
    SYSTEM_PROMPT = """
你是一位专业的金融分析师，现在需要把一篇长篇研报/新闻浓缩成 {num_points} 条清晰结论，重点是 **这些新闻对用户持有的相关资产具体有什么影响**。

请用简洁清晰的语言，每条不超过100字。
格式要求：
1. 第一条：核心结论
2. 第二条：对相关资产的影响
3. 第三条：操作建议（如果有）
"""
    
    USER_PROMPT = """
新闻标题: {title}
新闻内容:
{content}

用户关注的资产: {assets}

请按照要求总结：
"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        
    def summarize(self, content: str, title: str, assets: List[str], num_points: int = 3) -> Optional[List[str]]:
        """总结研报/新闻"""
        try:
            system_prompt = self.SYSTEM_PROMPT.format(num_points=num_points)
            user_prompt = self.USER_PROMPT.format(
                title=title,
                content=content[:8000],  # 截断太长的内容
                assets=', '.join(assets)
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            text = response.choices[0].message.content.strip()
            # 分割成点
            points = []
            for line in text.split('\n'):
                line = line.strip()
                if line and (line[0] in '123456789*-•' or len(points) == 0):
                    # 去掉编号
                    cleaned = line.lstrip('123456789.*-• ')
                    if cleaned:
                        points.append(cleaned)
            
            logger.info(f"Summarized into {len(points)} points")
            return points[:num_points]
            
        except Exception as e:
            logger.error(f"Failed to summarize: {e}")
            return None
            
    def filter_related(self, news_list: List[NewsItem], my_assets: List[str]) -> List[NewsItem]:
        """过滤出和我资产相关的新闻"""
        related = []
        for news in news_list:
            title = news.title.lower()
            content_lower = (news.content or '').lower()
            for asset in my_assets:
                asset_lower = asset.lower()
                if asset_lower in title or asset_lower in content_lower:
                    related.append(news)
                    break
        return related
        
    def generate_trading_advice(self, market_data: dict, signals: list, strategy_cycle: str = "medium") -> Optional[str]:
        """
        LLM 根据当前市场数据和所有信号生成操作建议
        
        Args:
            market_data: 当前市场数据（金价/银价/GLD/SLV/COMEX）
            signals: 所有触发的信号列表
            strategy_cycle: 投资周期 short/medium/long
        """
        try:
            system_prompt = """你是一位专业的黄金白银市场分析师，根据当前提供的市场数据和触发的信号，给用户清晰的操作建议。

请遵循：
1. 先总结当前市场状态
2. 根据投资周期给出具体操作建议（加仓/减仓/持有/观望）
3. 说明风险提示
保持简洁，不超过 300 字。"""

            user_prompt = f"""当前市场数据:
{market_data}

当前触发的信号:
{signals}

投资周期: {strategy_cycle} (短线/中线/长线)

请给出操作建议："""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            advice = response.choices[0].message.content.strip()
            logger.info("Generated trading advice from LLM")
            return advice
            
        except Exception as e:
            logger.error(f"Failed to generate trading advice: {e}")
            return None
