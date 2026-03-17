import logging
import schedule
import time
from typing import Callable

logger = logging.getLogger(__name__)

class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.job = None
        
    def add_interval_job(self, interval_minutes: int, task: Callable):
        """添加间隔任务"""
        schedule.every(interval_minutes).minutes.do(task)
        logger.info(f"Scheduled job every {interval_minutes} minutes")
        
    def start(self):
        """启动调度器"""
        logger.info("Scheduler started, waiting for next job...")
        while True:
            schedule.run_pending()
            time.sleep(60)
