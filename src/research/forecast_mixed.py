"""
黄金长期概率预测 - 混合模型版本 (中期进阶)
混合架构:
1. Macro Agent: 收集宏观数据 → 计算因子
2. Quant Agent: XGBoost 预测 → 给出量化预期
3. Scenario Agent: LLM 合成多情景概率
4. Risk Agent: 提取风险和反转信号

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import List, Optional
import pandas as pd
from src.agents.macro_agent import MacroAgent
from src.agents.quant_agent import QuantAgent
from src.agents.scenario_agent import ScenarioAgent
from src.agents.risk_agent import RiskAgent

logger = logging.getLogger(__name__)

class MixedGoldForecaster:
    """混合模型黄金预测器 - 中级进阶版本
    Macro Agent + Quant Model + LLM Scenario + Risk Agent
    """
    
    def __init__(
        self,
        openai_api_key: str,
        openai_model: str = "gpt-4o-mini",
        openai_base_url: Optional[str] = None,
        fred_api_key: Optional[str] = None,
        xgb_model_path: Optional[str] = None,
    ):
        self.macro_agent = MacroAgent(fred_api_key=fred_api_key)
        self.quant_agent = QuantAgent(model_path=xgb_model_path) if xgb_model_path else None
        self.scenario_agent = ScenarioAgent(
            openai_api_key=openai_api_key,
            model=openai_model,
            base_url=openai_base_url
        )
        self.risk_agent = RiskAgent()
    
    def forecast(
        self,
        current_gold_price: float,
        gold_silver_ratio: float,
        gold_oil_ratio: float,
        geo_risk_score: int,
        middle_east_news: List[str],
    ) -> Optional[str]:
        """运行完整混合预测流程"""
        # 1. Macro Agent 已经收集好数据，我们这里用传入的
        # 2. Quant Agent 预测
        quant_prediction = None
        if self.quant_agent and self.quant_agent.model:
            # 这里已经有宏观数据了，实际使用的时候从macro agent获取完整特征
            # 为了适配现有流程，这里使用已经计算好的比值
            # quant_prediction 已经提前算好，或者这里留空给LLM
            pass
            
        # 3. Scenario Agent 合成情景概率
        scenario_text = self.scenario_agent.synthesize(
            current_gold_price=current_gold_price,
            gold_silver_ratio=gold_silver_ratio,
            gold_oil_ratio=gold_oil_ratio,
            geo_risk_score=geo_risk_score,
            middle_east_news=middle_east_news,
            quant_prediction=quant_prediction,
        )
        
        # 4. Risk Agent 提取风险
        risks = self.risk_agent.analyze_risks(
            gold_price=current_gold_price,
            gold_oil_ratio=gold_oil_ratio,
            geo_risk_score=geo_risk_score,
            quant_prediction=quant_prediction,
        )
        
        # 组装输出
        output = scenario_text
        output += "\n\n### ⚠️ 主要风险\n\n"
        for i, risk in enumerate(risks, 1):
            output += f"{i}. {risk}\n"
        
        logger.info("✅ Mixed forecasting completed")
        return output
