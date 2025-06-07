import os
import aiohttp
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import SessionLocal

# Configure logging
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not configured")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        if not self.chat_id:
            logger.error("TELEGRAM_CHAT_ID not configured")
            raise ValueError("TELEGRAM_CHAT_ID environment variable is not set")
            
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.send_message_url = f"{self.api_url}/sendMessage"
        logger.info("Telegram bot initialized successfully")
        logger.info(f"Using chat ID: {self.chat_id}")

    async def send_message(self, text: str):
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram message not sent - missing credentials")
            return

        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"Sending Telegram message: {text}")
                async with session.post(
                    self.send_message_url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML"
                    }
                ) as response:
                    result = await response.json()
                    if response.status == 200 and result.get('ok'):
                        logger.info("Telegram message sent successfully")
                    else:
                        logger.error(f"Telegram API error: {result}")
                    return result
            except aiohttp.ClientError as e:
                logger.error(f"Telegram HTTP error: {str(e)}")
            except Exception as e:
                logger.error(f"Error sending Telegram message: {str(e)}")

    async def notify_chore_completion(self, staff_name: str, chore_description: str):
        time = datetime.now().strftime("%H:%M")
        message = f"{staff_name} marked '{chore_description}' as done at {time}"
        await self.send_message(message)

    async def notify_checklist_completion(self, staff_name: str, checklist_name: str):
        time = datetime.now().strftime("%H:%M")
        message = f"{staff_name} COMPLETED FULL {checklist_name} at {time} ✅"
        await self.send_message(message)

# Create the Telegram notifier instance
try:
    telegram = TelegramNotifier()
except Exception as e:
    logger.error(f"Failed to initialize Telegram notifier: {str(e)}")
    # Create a dummy notifier that logs but doesn't send messages
    class DummyNotifier:
        async def send_message(self, text: str):
            logger.warning(f"Would have sent Telegram message (but bot not configured): {text}")
        async def notify_chore_completion(self, staff_name: str, chore_description: str):
            logger.warning(f"Would have notified completion: {staff_name} - {chore_description}")
        async def notify_checklist_completion(self, staff_name: str, checklist_name: str):
            logger.warning(f"Would have notified checklist completion: {staff_name} - {checklist_name}")
    telegram = DummyNotifier() 