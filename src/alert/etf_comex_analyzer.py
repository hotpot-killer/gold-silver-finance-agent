import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

@dataclass
class ETFCOMEXAnalysis:
    """ETF持仓和COMEX库存关联分析结果"""
    gld_holdings_change: float
    slv_holdings_change: float
    comex_gold_change: float
    comex_silver_change: float
    
    # 市场结论
    conclusion: str
    suggestion: str

class ETFCOMEXAnalyzer:
    """
    ETF持仓变化 + COMEX库存变化 关联分析
    
    市场经验:
    - 白银ETF持仓大幅减少  → 庄家在提取实物 → 后市看涨
    - COMEX库存增加  → 实物从交易所提出去了，存量减少供应，对应涨价
    - 如果两者一致 → 信号很强
    """
    
    @staticmethod
    def analyze(
        slv_holdings_change: float,
        comex_silver_change: float,
        gld_holdings_change: float = None,
        comex_gold_change: float = None,
        threshold_pct: float = 1.0  # 超过1%算大幅变动
    ) -> ETFCOMEXAnalysis:
        """
        分析白银ETF持仓和COMEX库存的关联
        返回分析结论和操作建议
        """
        conclusion_parts = []
        suggestion_parts = []
        
        # 白银分析 - 这是重点（你的洞察：庄家提取实物）
        silver_signal = None
        if abs(slv_holdings_change) >= threshold_pct:
            if slv_holdings_change < 0 and comex_silver_change > 0:
                # ETF持仓减少 + COMEX库存增加 = ETF持仓流出，实物提取
                conclusion_parts.append(
                    "🔍 **白银分析**: SLVETF持仓减少 {slv_holdings_change:.1f}%，同时COMEX白银库存增加 {comex_silver_change:.1f}%\n"
                    "→ 说明大量白银从ETF流出被提取实物，庄家看涨后市，信号强烈！"
                )
                suggestion_parts.append("👉 白银大概率向上，可以逢低布局多单")
                silver_signal = "bullish_strong"
            elif slv_holdings_change > 0 and comex_silver_change < 0:
                # ETF持仓增加 + COMEX库存减少 = 实物存入交易所，庄家看跌
                conclusion_parts.append(
                    "🔍 **白银分析**: SLVETF持仓增加 {slv_holdings_change:.1f}%，同时COMEX白银库存减少 {comex_silver_change:.1f}%\n"
                    "→ 说明大量白银存入ETF，庄家抛出兑现，信号强烈看跌！"
                )
                suggestion_parts.append("👉 白银大概率向下，注意规避风险")
                silver_signal = "bearish_strong"
            elif slv_holdings_change < 0:
                conclusion_parts.append(
                    f"🔍 **白银分析**: SLVETF持仓减少 {slv_holdings_change:.1f}%\n"
                    "→ 持仓减少偏多，关注COMEX库存确认"
                )
                silver_signal = "bullish_weak"
            else:
                conclusion_parts.append(
                    f"🔍 **白银分析**: SLVETF持仓增加 {slv_holdings_change:.1f}%\n"
                    "→ 持仓增加偏空，关注COMEX库存确认"
                )
                silver_signal = "bearish_weak"
        else:
            conclusion_parts.append("🔍 **白银分析**: SLV持仓变动小于阈值，无显著信号\n")
            silver_signal = "neutral"
        
        # 黄金分析
        gold_signal = None
        if gld_holdings_change is not None and comex_gold_change is not None and abs(gld_holdings_change) >= threshold_pct:
            if gld_holdings_change < 0 and comex_gold_change > 0:
                conclusion_parts.append(
                    "🔍 **黄金分析**: GLDETF持仓减少 {gld_holdings_change:.1f}%，同时COMEX黄金库存增加 {comex_gold_change:.1f}%\n"
                    "→ 散户抛出，实物提取，看涨后市"
                )
                suggestion_parts.append("👉 黄金大概率向上")
                gold_signal = "bullish_strong"
            elif gld_holdings_change > 0 and comex_gold_change < 0:
                conclusion_parts.append(
                    "🔍 **黄金分析**: GLDETF持仓增加 {gld_holdings_change:.1f}%，同时COMEX黄金库存减少 {comex_gold_change:.1f}%\n"
                    "→ 散户吸入，实物存入交易所，看跌后市"
                )
                suggestion_parts.append("👉 黄金大概率向下")
                gold_signal = "bearish_strong"
        
        conclusion = '\n'.join(conclusion_parts)
        suggestion = '\n'.join(suggestion_parts)
        
        return ETFCOMEXAnalysis(
            gld_holdings_change=gld_holdings_change,
            slv_holdings_change=slv_holdings_change,
            comex_gold_change=comex_gold_change,
            comex_silver_change=comex_silver_change,
            conclusion=conclusion,
            suggestion=suggestion
        )
        
    @staticmethod
    def format_for_notification(analysis: ETFCOMEXAnalysis) -> str:
        """格式化分析结果用于通知推送"""
        text = "### 🧐 ETF-COMEX 关联分析\n\n"
        text += analysis.conclusion
        if analysis.suggestion:
            text += f"\n**💡 操作建议:**\n\n{analysis.suggestion}"
        return text
