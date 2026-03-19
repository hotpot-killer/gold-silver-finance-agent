"""
XGBoost预测模型 - 传统ML做月度回报预测
混合模型：XGBoost给出量化预测区间，LLM做情景合成

Author: wzh
Date: 2026-03-19
"""
import logging
from typing import Dict, Optional, Tuple
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

logger = logging.getLogger(__name__)

try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    logger.warning("xgboost not installed, install with: pip install xgboost")

class GoldXGBoostForecast:
    """XGBoost 黄金月度收益率预测"""
    
    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.1, max_depth: int = 5):
        if not XGB_AVAILABLE:
            raise ImportError("xgboost is required for this model")
            
        self.model = XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            objective='reg:squarederror',
            random_state=42
        )
        self.is_fitted = False
        
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, float]:
        """训练模型，返回验证集metrics"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        
        # 评估
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        logger.info(f"XGBoost trained: test MSE = {mse:.4f}")
        
        return {
            'test_mse': mse,
            'train_size': len(X_train),
            'test_size': len(X_test),
        }
    
    def predict(self, X: pd.DataFrame) -> float:
        """预测未来三个月预期对数收益率"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet")
            
        pred = self.model.predict(X)
        return float(pred[0])
    
    def save(self, path: str):
        """保存模型到文件"""
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> "GoldXGBoostForecast":
        """从文件加载模型"""
        with open(path, 'rb') as f:
            model = pickle.load(f)
        model.is_fitted = True
        return model
    
    def feature_importance(self, feature_names: List[str]) -> List[Tuple[str, float]]:
        """获取特征重要性排序"""
        if not self.is_fitted:
            return []
        importances = self.model.feature_importances_
        ranked = sorted(zip(feature_names, importances), key=lambda x: -x[1])
        return ranked
