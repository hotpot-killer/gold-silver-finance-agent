import logging
import json
import requests
from typing import List
from ..alert import Alert

logger = logging.getLogger(__name__)

class BaseNotifier:
    """通知器基类"""
    def send(self, title: str, content: str) -> bool:
        raise NotImplementedError

class DingTalkNotifier(BaseNotifier):
    """钉钉群机器人通知"""
    def __init__(self, webhook_url: str, secret: str = None):
        self.webhook_url = webhook_url
        self.secret = secret
        
    def send(self, title: str, content: str) -> bool:
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"## {title}\n\n{content}"
            }
        }
        try:
            resp = requests.post(self.webhook_url, json=data, timeout=10)
            result = resp.json()
            if result.get('errcode', 0) == 0:
                logger.info("DingTalk notification sent")
                return True
            else:
                logger.error(f"DingTalk send failed: {result.get('errmsg')}")
                return False
        except Exception as e:
            logger.error(f"DingTalk exception: {e}")
            return False

class WorkWechatNotifier(BaseNotifier):
    """企业微信机器人通知"""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    def send(self, title: str, content: str) -> bool:
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"## {title}\n\n{content}"
            }
        }
        try:
            resp = requests.post(self.webhook_url, json=data, timeout=10)
            result = resp.json()
            if result.get('errcode', 0) == 0:
                logger.info("WorkWechat notification sent")
                return True
            else:
                logger.error(f"WorkWechat send failed: {result.get('errmsg')}")
                return False
        except Exception as e:
            logger.error(f"WorkWechat exception: {e}")
            return False

class TelegramNotifier(BaseNotifier):
    """Telegram 机器人通知"""
    def __init__(self, bot_token: str, chat_id: str):
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.chat_id = chat_id
        
    def send(self, title: str, content: str) -> bool:
        text = f"*{title}*\n\n{content}"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            resp = requests.post(self.api_url, data=data, timeout=10)
            result = resp.json()
            if result.get('ok', False):
                logger.info("Telegram notification sent")
                return True
            else:
                logger.error(f"Telegram send failed: {result.get('description')}")
                return False
        except Exception as e:
            logger.error(f"Telegram exception: {e}")
            return False

class FeishuNotifier(BaseNotifier):
    """飞书机器人通知 - 适配飞书webhook触发器"""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    def send(self, title: str, content: str) -> bool:
        """发送飞书消息
        根据飞书webhook触发器文档要求：
        - msg_type 必须为文本类型
        - 文本消息内容必须放在 content.text
        """
        full_text = f"{title}\n\n{content}"
        data = {
            "msg_type": "text",
            "content": {
                "text": full_text
            }
        }
        try:
            resp = requests.post(self.webhook_url, json=data, timeout=10)
            result = resp.json()
            if result.get('code', 0) == 0:
                logger.info("Feishu notification sent")
                return True
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"Feishu send failed: {error_msg}")
                return False
        except Exception as e:
            logger.error(f"Feishu exception: {e}")
            return False

def format_alerts(alerts: List[Alert]) -> str:
    """格式化预警消息"""
    if not alerts:
        return "没有触发预警规则。"
    
    content = ""
    for i, alert in enumerate(alerts, 1):
        content += f"### {i}. {alert.alert_type} - {alert.asset}\n\n"
        content += f"**📊 信息**: {alert.message}\n\n"
        content += f"**💡 建议**: {alert.suggestion}\n\n"
        content += "---\n\n"
        
    content += f"共触发 {len(alerts)} 条预警，请关注市场变化。"
    return content
