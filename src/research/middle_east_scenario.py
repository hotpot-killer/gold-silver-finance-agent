"""
中东局势多情景推演模块 - 参考 MiroFish 思想
模拟中东局势各种演进方向，预测黄金/白银/原油价格走势，给出操作建议

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ScenarioType(Enum):
    """中东局势情景类型"""
    ESCALATION = "escalation"        # 局势升级
    DEESCALATION = "de-escalation"   # 局势缓和
    STATUS_QUO = "status-quo"        # 维持现状
    MAJOR_CRISIS = "major-crisis"     # 重大危机

@dataclass
class MiddleEastScenario:
    """中东局势单个情景"""
    name: str                      # 情景名称
    type: ScenarioType              # 情景类型
    probability: float             # 概率 0-1
    description: str              # 详细描述
    gold_impact: str              # 黄金影响描述
    silver_impact: str            # 白银影响描述
    crude_impact: str             # 原油影响描述
    gold_price_range: str          # 黄金价格区间（例如 "4800-5200"）
    silver_price_range: str        # 白银价格区间（例如 "75-85"）
    crude_price_range: str         # 原油价格区间（例如 "95-110"）
    suggested_action: str         # 建议操作（例如 "做多黄金"）
    trigger_signals: List[str]     # 触发信号

class MiddleEastScenarioSimulator:
    """中东局势多情景模拟器 - 参考 MiroFish 思想"""
    
    def __init__(self, llm_api_key: str, llm_model: str = "gpt-4o-mini", llm_base_url: Optional[str] = None):
        self.api_key = llm_api_key
        self.model = llm_model
        self.base_url = llm_base_url
    
    def simulate(
        self,
        current_gold_price: float,
        current_silver_price: float,
        current_crude_price: float,
        recent_news: List[str],
    ) -> List[MiddleEastScenario]:
        """基于当前市场和新闻，模拟中东局势多种演进方向"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        system_prompt = """你是一位专业的地缘政治与大宗商品分析师，擅长分析中东局势对黄金、白银、原油价格的影响。

请基于以下信息，模拟中东局势的4种主要演进情景，每种情景给出：
1. 情景名称和类型
2. 发生概率（0-1）
3. 详细描述（包括可能的事件链）
4. 对黄金、白银、原油的价格影响和预期区间
5. 操作建议
6. 该情景的触发信号

请严格按照要求输出，保持专业、简洁。
"""
        
        user_prompt = f"""
当前市场数据:
- 伦敦现货黄金: {current_gold_price:.2f} USD/oz
- 伦敦现货白银: {current_silver_price:.2f} USD/oz
- WTI原油期货: {current_crude_price:.2f} USD/barrel

近期相关新闻:
{chr(10).join([f'- {t}' for t in recent_news[:10]])}

请模拟中东局势的4种主要演进情景：
1. 维持现状（Status Quo）- 最可能的情景
2. 局势缓和（De-escalation）- 概率中等
3. 局势升级（Escalation）- 概率中等
4. 重大危机（Major Crisis）- 小概率高影响

每种情景请给出：
- 情景名称
- 类型
- 概率（0-1，总和应为1）
- 详细描述
- 对黄金、白银、原油的影响（包括价格区间）
- 操作建议
- 触发信号
"""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=3000,
            )
            content = response.choices[0].message.content
            
            # MVP版本先返回文本，后续可解析为 MiddleEastScenario 结构化对象
            logger.info("Middle East scenario simulation completed")
            
            # 构造伪数据返回
            return self._parse_text_to_scenarios(content, current_gold_price, current_silver_price, current_crude_price)
            
        except Exception as e:
            logger.error(f"Failed to simulate Middle East scenarios: {e}")
            return []
    
    def _parse_text_to_scenarios(
        self, 
        text: str, 
        gold_price: float, 
        silver_price: float, 
        crude_price: float
    ) -> List[MiddleEastScenario]:
        """简单解析文本为情景列表（MVP版本）"""
        scenarios = []
        
        # 先返回一个包含原始文本的默认情景
        scenarios.append(MiddleEastScenario(
            name="完整推演报告",
            type=ScenarioType.STATUS_QUO,
            probability=1.0,
            description=text,
            gold_impact=f"当前金价 {gold_price:.2f}",
            silver_impact=f"当前银价 {silver_price:.2f}",
            crude_impact=f"当前油价 {crude_price:.2f}",
            gold_price_range=f"{int(gold_price*0.95)}-{int(gold_price*1.05)}",
            silver_price_range=f"{int(silver_price*0.95)}-{int(silver_price*1.05)}",
            crude_price_range=f"{int(crude_price*0.95)}-{int(crude_price*1.05)}",
            suggested_action="请查看详细报告",
            trigger_signals=[]
        ))
        
        return scenarios
    
    def format_for_report(self, scenarios: List[MiddleEastScenario]) -> str:
        """格式化为报告文本"""
        if len(scenarios) == 0:
            return "中东局势情景推演暂不可用"
        
        output = scenarios[0].description
        return output
    
    def get_best_scenario(self, scenarios: List[MiddleEastScenario]) -> Optional[MiddleEastScenario]:
        """获取概率最高的情景"""
        if not scenarios:
            return None
        return max(scenarios, key=lambda s: s.probability)
