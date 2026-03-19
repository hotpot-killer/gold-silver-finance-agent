import logging
from typing import List, Optional
from openai import OpenAI
from ..monitor import NewsItem

logger = logging.getLogger(__name__)

# 中东局势相关关键词 - 影响原油进而影响金银
MIDDLE_EAST_KEYWORDS = [
    '中东', '以色列', '哈马斯', '伊朗', '也门', '胡塞', '海湾',
    '原油', '油价', '石油', '中东局势', '巴以', '伊核', '霍尔木兹'
]

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
        """过滤出和我资产相关的新闻，包括中东局势（影响原油和金银）"""
        related = []
        for news in news_list:
            title_lower = news.title.lower()
            content_lower = (news.content or '').lower()
            # 检查是否是资产相关或者中东局势相关
            is_asset_related = False
            for asset in my_assets:
                asset_lower = asset.lower()
                if asset_lower in title_lower or asset_lower in content_lower:
                    is_asset_related = True
                    break
            # 检查中东局势相关
            is_mideast_related = any(
                kw in title_lower or kw in content_lower 
                for kw in (kw.lower() for kw in MIDDLE_EAST_KEYWORDS)
            )
            if is_asset_related or is_mideast_related:
                # 标记相关资产
                if not news.related_assets:
                    news.related_assets = my_assets.copy()
                related.append(news)
        return related
        
    def generate_trading_advice(self, market_data: dict, signals: list, strategy_cycle: str = "medium", middle_east_news: list = None) -> Optional[str]:
        """
        LLM 根据当前市场数据和所有信号生成操作建议，加入中东局势分析
        
        Args:
            market_data: 当前市场数据（金价/银价/GLD/SLV/COMEX）
            signals: 所有触发的信号列表
            strategy_cycle: 投资周期 short/medium/long
            middle_east_news: 中东局势相关新闻列表
        """
        try:
            system_prompt = """你是一位专业的黄金白银市场分析师，根据当前提供的市场数据、触发的信号和中东局势新闻，给用户清晰的操作建议。

核心分析逻辑需要遵循：
- 中东局势紧张会推高原油价格，油价暴涨通常会导致美元走强，最终引起黄金和白银价格跳水
- 中东局势缓解会降低原油价格，美元走弱，通常会推动黄金白银价格上涨
- 结合当前实际原油价格变动，分析对黄金白银的影响
- 参考前瞻预测市场（Polymarket/Kalshi等平台）反映的市场一致预期，如果市场多数看涨/看跌，可以结合你的分析给出综合判断
- **根据金银比（金价 ÷ 银价），参考市场主流的 80/50 法则判断**：
  - **金银比 > 80-85** → 白银相对低估，历史上常是**买入白银/换仓白银**的好时机
  - **70-80** → 正常偏高，黄金相对占优
  - **55-70** → 大多数人认可的"正常区间中枢"，目前大概率落在此区间
  - **< 50-55** → 白银相对强势/可能高估，历史上常对应白银大级别上涨后期
  - **< 40** → 极端低位（2011年最低≈32-35，之后白银见顶）
- **根据金油比（盎司金价 ÷ 桶油价，1盎司黄金能买多少桶原油），宏观/地缘晴雨表**：
  当代市场主流判断框架：
  - **金油比 > 50** → 仍显著高于历史常态 → 黄金相对原油偏贵，**原油更有相对机会**
  - **40 < 金油比 ≤ 50** → 高于历史常态 → 黄金相对原油仍偏贵
  - **20 ≤ 金油比 ≤ 40** → 正常区间
  - **15 ≤ 金油比 < 20** → 低于历史常态 → **原油相对黄金偏贵，黄金更有相对机会**
  - **< 15** → 极端低位 → 原油极端强势/黄金极端便宜
  - 长期历史中枢 ≈ 16–20，当前50+仍明显偏高，说明市场仍在为避险/通胀支付溢价

请遵循：
1. 先总结当前市场状态，**说明当前金银比+金油比具体数值，分别参考对应法则给出判断**
2. 如果有中东局势新闻，重点分析中东局势对原油和金银的影响
3. 结合技术信号、原油走势、市场一致预期给出综合判断
4. 根据投资周期给出具体操作建议（加仓/减仓/持有/观望）
5. 说明风险提示
保持简洁，不超过 300 字。"""

            user_prompt = f"""当前市场数据:
{market_data}

当前触发的信号:
{signals}

"""
            if middle_east_news and len(middle_east_news) > 0:
                user_prompt += f"""最新中东局势相关新闻:
{[news.title for news in middle_east_news]}

"""

            user_prompt += f"""投资周期: {strategy_cycle} (短线/中线/长线)

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
