"""
Quant Agent - 量化预测代理
运行XGBoost模型给出量化预测区间

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
from src.models.xgboost_forecast import GoldXGBoostForecast
from src.features.factor_engine import GoldFactorEngine

logger = logging.getLogger(__name__)

class QuantAgent:
    """量化预测 Agent"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model: Optional[GoldXGBoostForecast] = None
        if model_path and model_path.endswith('.joblib'):
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """加载预训练模型"""
        try:
            self.model = GoldXGBoostForecast.load(model_path)
            logger.info(f"Loaded XGBoost model from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def predict(self, features: pd.DataFrame) -> Optional[float]:
        """运行预测，返回预期对数收益率"""
        if self.model is None:
            logger.warning("No model loaded, skip quant prediction")
            return None
        
        try:
            pred = self.model.predict(features)
            logger.info(f"Quant Agent completed: predicted log return = {pred:.4f}")
            return pred
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None
    
    def get_feature_importance(self, feature_names: List[str]) -> None:
        """打印特征重要性"""
        if self.model:
            importance = self.model.model.feature_importance(feature_names)
            logger.info("Feature importance:")
            for name, imp in importance:
                logger.info(f"  {name}: {imp:.4f}")
