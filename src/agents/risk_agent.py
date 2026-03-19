"""
Risk Agent - 风险反转信号提取代理
识别主要风险因素和反转信号，输出给用户

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class RiskAgent:
    """风险/反转信号 Agent"""
    
    def __init__(self):
        pass
    
    def analyze_risks(
        self,
        gold_price: float,
        gold_oil_ratio: float,
        geo_risk_score: int,
        quant_prediction: Optional[float] = None,
    ) -> List[str]:
        """分析主要风险和反转信号"""
        risks = []
        
        # 地缘风险
        if geo_risk_score >= 7:
            risks.append(f"当前地缘风险评分 {geo_risk_score}/10 较高，突发地缘事件可能引发油价和金价剧烈波动")
        
        # 金油比风险
        if gold_oil_ratio > 50:
            risks.append("金油比显著高于历史常态，若地缘局势缓解油价上涨，黄金可能相对跑输原油")
        
        if gold_oil_ratio < 15:
            risks.append("金油比显著低于历史常态，若原油继续强势可能进一步挤压黄金上涨空间")
        
        # 量化预测提醒
        if quant_prediction is not None:
            if quant_prediction < -0.02:
                risks.append("量化模型预测未来三个月黄金负回报，建议谨慎追高")
            elif quant_prediction > 0.05:
                risks.append("量化模型预测未来三个月黄金正回报较高，可以关注机会")
        
        # 默认总有风险
        if len(risks) == 0:
            risks = [
                "大宗商品价格受宏观因素影响大，波动率高，任何预测都有不确定性",
                "美联储货币政策突变可能引发趋势反转",
            ]
        
        logger.info(f"Risk analysis completed: found {len(risks)} risk factors")
        return risks
