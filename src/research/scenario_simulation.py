"""
多情景逻辑推演模块 - 基于消息面和技术面进行推演
参考 MiroFish 的思想，针对金融黄金白银场景做轻量化实现

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ScenarioBranch:
    """单个情景分支"""
    name: str                      # 情景名称
    description: str               # 描述
    probability: float             # 概率（0-1）
    short_term_pred: str           # 短期（1-4周）
    medium_term_pred: str          # 中期（1-3个月）
    long_term_pred: str            # 长期（6-12个月）
    monthly_forecast: Dict[str, str]  # 每月预测 例如: {"2026-04": "价格预期 4900-5050"}

class ScenarioSimulator:
    """多情景推演模拟器"""
    
    def __init__(self, llm_api_key: str, llm_model: str = "gpt-4o-mini", llm_base_url: Optional[str] = None):
        self.api_key = llm_api_key
        self.model = llm_model
        self.base_url = llm_base_url
    
    def simulate(
        self,
        current_gold_price: float,
        current_silver_price: float,
        crude_oil_price: float,
        gold_silver_ratio: float,
        gold_oil_ratio: float,
        recent_news: List[str],
        technical_indicators: Dict[str, float]
    ) -> List[ScenarioBranch]:
        """运行多情景推演"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        system_prompt = """你是一位专业的黄金白银市场分析师，擅长基于消息面和技术面进行多情景推演预测。

请严格按照以下要求输出预测结果：
1. 输出3个主要情景分支（基准、乐观、悲观），每个分支给出概率
2. 每个分支分别给出：短期（1-4周）、中期（1-3个月）、长期（6-12个月）的价格预期和逻辑
3. 给出接下来6个月的每月预测（从当前月份开始）
4. 保持专业、简洁，每个分支不超过300字
"""
        
        user_prompt = f"""
当前市场数据:
- 日期: {datetime.now().strftime('%Y-%m-%d')}
- 伦敦现货黄金价格: {current_gold_price:.2f} USD/oz
- 伦敦现货白银价格: {current_silver_price:.2f} USD/oz
- WTI原油价格: {crude_oil_price:.2f} USD/barrel
- 金银比: {gold_silver_ratio:.1f}
- 金油比: {gold_oil_ratio:.1f}

近期新闻（消息面）:
{chr(10).join([f'- {t}' for t in recent_news])}

技术指标（技术面）:
{chr(10).join([f'- {k}: {v:.2f}' for k, v in technical_indicators.items()])}

请基于以上数据进行多情景推演预测。
"""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2500,
            )
            content = response.choices[0].message.content
            
            # MVP版本先返回原始文本，后续可解析为ScenarioBranch结构化对象
            logger.info("Scenario simulation completed")
            
            # 为了快速集成，这里先构造伪数据格式，后面解析为结构化
            branches = self._parse_text_to_branches(content)
            
            return branches
            
        except Exception as e:
            logger.error(f"Failed to simulate scenarios: {e}")
            return []
    
    def _parse_text_to_branches(self, text: str) -> List[ScenarioBranch]:
        """简单解析文本为情景分支（MVP版本，后续用更精确的JSON解析）"""
        branches = []
        
        # 先返回原始文本作为第一个情景，后面改进为完整结构化
        branches.append(ScenarioBranch(
            name="完整推演报告",
            description=text,
            probability=1.0,
            short_term_pred="",
            medium_term_pred="",
            long_term_pred="",
            monthly_forecast={}
        ))
        
        return branches
    
    def format_for_report(self, branches: List[ScenarioBranch]) -> str:
        """格式化为报告文本"""
        if len(branches) == 0:
            return "情景推演暂不可用"
        
        output = branches[0].description
        return output
