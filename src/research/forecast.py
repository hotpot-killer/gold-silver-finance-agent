"""
黄金长期概率预测模块 - 完成版
基于LLM Agent + 宏观因子结构化推理，输出多情景概率预测，支持JSON结构化输出

Author: wzh
Date: 2026-03-19
"""
import logging
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ForecastInput:
    """预测输入数据结构"""
    current_gold_price: float         # 当前金价 (XAUUSD)
    current_silver_price: float       # 当前银价 (XAGUSD)
    current_crude_price: float       # 当前油价 (WTI)
    gold_silver_ratio: float         # 金银比
    gold_oil_ratio: float           # 金油比
    geo_risk_score: int            # 地缘风险评分 0-10
    middle_east_news: List[str]    # 最新中东/地缘新闻标题
    
@dataclass
class PriceScenario:
    """单个价格情景"""
    name: str                     # 情景名称
    probability: float             # 概率 0-1
    price_median_range: str       # 价格中位数区间 例如 "4800-5200"
    trigger_conditions: List[str] # 触发条件

@dataclass
class ForecastResult:
    """预测输出结果"""
    current_date: str
    current_gold_price: float
    gold_silver_ratio: float
    gold_oil_ratio: float
    geo_risk_score: int
    scenarios: List[PriceScenario]
    most_probable_window: str       # 最可能的时间窗口 例如 "2026年5-7月"
    main_risks: List[str]         # 主要风险/反转信号
    raw_text: Optional[str] = None  # 原始文本（保留兼容性）

class GoldPriceForecaster:
    """黄金长期价格预测器 - 完成版
    使用LLM + 宏观因子做结构化概率预测，支持JSON结构化输出
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        self.api_key = openai_api_key
        self.model = model
        self.base_url = base_url
        
    def fetch_current_macro_data(self) -> Dict:
        """从yfinance拉取最新宏观数据"""
        try:
            # GC=F = COMEX黄金期货
            gold = yf.Ticker("GC=F")
            gold_hist = gold.history(period="5d")
            current_gold = gold_hist['Close'].iloc[-1]
            
            # SI=F = COMEX白银期货
            silver = yf.Ticker("SI=F")
            silver_hist = silver.history(period="5d")
            current_silver = silver_hist['Close'].iloc[-1]
            
            # CL=F = WTI原油期货
            crude = yf.Ticker("CL=F")
            crude_hist = crude.history(period="5d")
            current_crude = crude_hist['Close'].iloc[-1]
            
            logger.info(f"Fetched from yfinance: gold={current_gold:.2f}, silver={current_silver:.2f}, crude={current_crude:.2f}")
            
            return {
                "current_gold_price": float(current_gold),
                "current_silver_price": float(current_silver),
                "current_crude_price": float(current_crude),
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch macro data from yfinance: {e}")
            return {}
    
    def generate_forecast(
        self, 
        current_data: ForecastInput,
        system_prompt: Optional[str] = None
    ) -> Optional[ForecastResult]:
        """生成预测，调用LLM做结构化推理，返回结构化对象"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        if system_prompt is None:
            system_prompt = """你是一位专业的黄金市场分析师，擅长基于宏观因子做长期概率预测。

请根据当前提供的数据，输出严格的JSON格式预测，遵循以下格式：

{
  "current_date": "2026-03-19",
  "scenarios": [
    {
      "name": "基准预期",
      "probability": 0.6,
      "price_median_range": "4800-5100",
      "trigger_conditions": ["地缘局势维持现状", "美联储政策按预期执行"]
    },
    {
      "name": "上涨",
      "probability": 0.25,
      "price_median_range": "5100-5400",
      "trigger_conditions": ["中东局势升级", "美联储降息提前"]
    },
    {
      "name": "暴涨",
      "probability": 0.15,
      "price_median_range": "5400-5800",
      "trigger_conditions": ["重大地缘危机", "金融市场动荡"]
    }
  ],
  "most_probable_window": "2026年5-7月",
  "main_risks": [
    "美联储货币政策突变",
    "地缘局势超预期缓和"
  ]
}

注意：
- 概率总和应为 1.0
- 只返回JSON，不要有其他文本
"""
        
        # 构建prompt
        user_prompt = f"""
当前日期: {datetime.now().strftime('%Y-%m-%d')}

最新市场数据:
- 伦敦现货黄金: {current_data.current_gold_price:.2f} USD/oz
- 伦敦现货白银: {current_data.current_silver_price:.2f} USD/oz
- WTI原油: {current_data.current_crude_price:.2f} USD/barrel
- 金银比: {current_data.gold_silver_ratio:.1f}
- 金油比: {current_data.gold_oil_ratio:.1f}
- 地缘风险评分(0-10): {current_data.geo_risk_score}
- 最新中东/地缘新闻:
{chr(10).join([f'  {i+1}. {t}' for i, t in enumerate(current_data.middle_east_news)])}

请按照要求输出严格的JSON格式预测：
"""
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            logger.info("Generated forecast successfully")
            
            # 解析JSON为结构化对象
            parsed = json.loads(content)
            
            # 构建 PriceScenario 列表
            scenarios = []
            for s in parsed.get("scenarios", []):
                scenarios.append(PriceScenario(
                    name=s.get("name", "未知"),
                    probability=float(s.get("probability", 0)),
                    price_median_range=s.get("price_median_range", ""),
                    trigger_conditions=s.get("trigger_conditions", [])
                ))
            
            # 构建 ForecastResult
            result = ForecastResult(
                current_date=parsed.get("current_date", datetime.now().strftime('%Y-%m-%d')),
                current_gold_price=current_data.current_gold_price,
                gold_silver_ratio=current_data.gold_silver_ratio,
                gold_oil_ratio=current_data.gold_oil_ratio,
                geo_risk_score=current_data.geo_risk_score,
                scenarios=scenarios,
                most_probable_window=parsed.get("most_probable_window", ""),
                main_risks=parsed.get("main_risks", []),
                raw_text=content
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate forecast: {e}")
            return None
    
    def format_result_to_text(self, result: ForecastResult) -> str:
        """将结构化 ForecastResult 格式化为报告文本"""
        output = []
        output.append(f"**当前日期**: {result.current_date}\n")
        output.append(f"**伦敦现货黄金**: {result.current_gold_price:.2f} USD/oz\n")
        output.append(f"**金银比**: {result.gold_silver_ratio:.1f}\n")
        output.append(f"**金油比**: {result.gold_oil_ratio:.1f}\n")
        output.append(f"**地缘风险评分**: {result.geo_risk_score}/10\n")
        output.append("\n")
        
        output.append("### 多情景预测\n")
        for s in result.scenarios:
            output.append(f"- **{s.name}** (概率: {s.probability*100:.0f}%)\n")
            output.append(f"  价格区间: {s.price_median_range}\n")
            output.append(f"  触发条件: {', '.join(s.trigger_conditions)}\n")
        
        output.append("\n")
        output.append(f"**最可能时间窗口**: {result.most_probable_window}\n")
        output.append("\n")
        
        output.append("### 主要风险/反转信号\n")
        for r in result.main_risks:
            output.append(f"- {r}\n")
        
        return "\n".join(output)

