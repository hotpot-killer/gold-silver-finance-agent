"""
黄金长期概率预测模块 - MVP版本
基于LLM Agent + 宏观因子结构化推理，输出多情景概率预测

Author: wzh
Date: 2026-03-19
"""
import logging
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

class GoldPriceForecaster:
    """黄金长期价格预测器 - MVP Version
    使用LLM + 宏观因子做结构化概率预测
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
        """生成预测，调用LLM做结构化推理"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        if system_prompt is None:
            system_prompt = """你是一位专业的黄金市场分析师，擅长基于宏观因子做长期概率预测。

请根据当前提供的数据，输出结构化的长期预测，遵循以下规则：
1. 输出分三个情景：基准预期 / 上涨 / 暴涨，给出概率百分比
2. 每个情景给出价格中位数区间，说明触发条件
3. 给出最可能出现大行情的时间窗口（比如"2026年5-7月"）
4. 列出主要风险/反转信号
5. 控制在300字以内，结构清晰，用中文输出
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
            logger.info("Generated forecast successfully")
            
            # TODO: 解析为结构化 ForecastResult
            # MVP先返回文本，后续可以改进为JSON结构化
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate forecast: {e}")
            return None
