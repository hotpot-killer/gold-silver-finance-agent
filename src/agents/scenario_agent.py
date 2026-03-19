"""
Scenario Agent - 情景概率合成代理
基于Quant Agent的量化预测 + Macro Agent的宏观数据，LLM合成多情景概率

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PriceScenario:
    """单个价格情景"""
    name: str                     # 情景名称
    probability: float             # 概率 0-1
    price_median_range: str       # 价格中位数区间 例如 "4800-5200"
    trigger_conditions: List[str]  # 触发条件

@dataclass
class ForecastResult:
    """预测输出结果"""
    current_date: str
    current_gold_price: float
    gold_silver_ratio: float
    gold_oil_ratio: float
    geo_risk_score: int
    quant_prediction: Optional[float]
    scenarios: List[PriceScenario]
    most_probable_window: str       # 最可能的时间窗口 例如 "2026年5-7月"
    main_risks: List[str]         # 主要风险/反转信号

class ScenarioAgent:
    """情景概率合成 Agent - 使用LLM合成多情景"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        self.api_key = openai_api_key
        self.model = model
        self.base_url = base_url
        
    def synthesize(
        self,
        current_gold_price: float,
        gold_silver_ratio: float,
        gold_oil_ratio: float,
        geo_risk_score: int,
        middle_east_news: List[str],
        quant_prediction: Optional[float] = None,
    ) -> Optional[ForecastResult]:
        """合成多情景预测"""
        from datetime import datetime
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        system_prompt = """你是一位专业的黄金市场分析师，擅长基于宏观因子和量化预测合成多情景概率预测。

请严格按照以下要求输出：
1. 输出三个情景：基准预期 / 上涨 / 暴涨，给出概率百分比
2. 每个情景说明价格中位数区间和主要触发条件
3. 给出最可能出现大行情的时间窗口（例如 "2026年5-7月"）
4. 列出主要风险/反转信号
5. 保持简洁，总共不超过300字
"""
        
        user_prompt = f"""
当前日期: {datetime.now().strftime('%Y-%m-%d')}

最新市场数据:
- 伦敦现货黄金价格: {current_gold_price:.2f} USD/oz
- 金银比: {gold_silver_ratio:.1f}
- 金油比: {gold_oil_ratio:.1f}
- 地缘风险评分(0-10): {geo_risk_score}
- 最新中东/地缘新闻:
{chr(10).join([f'  {i+1}. {t}' for i, t in enumerate(middle_east_news)])}
"""

        if quant_prediction is not None:
            user_prompt += f"""
量化模型预测未来3个月对数收益率: {quant_prediction:.4f}
请参考这个量化预测给出概率判断
"""

        user_prompt += """
请按照要求输出预测：
"""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )
            content = response.choices[0].message.content
            logger.info("Scenario synthesis completed")
            # 这里可以进一步做JSON解析，MVP先保留文本输出
            # 后续改进可以强制JSON输出结构化
            return content
            
        except Exception as e:
            logger.error(f"Failed to synthesize scenarios: {e}")
            return None
