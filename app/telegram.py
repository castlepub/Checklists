import os
import aiohttp
from datetime import datetime
import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import SessionLocal
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set UK timezone
uk_tz = pytz.timezone('Europe/London')

class TelegramNotifier:
    def __init__(self):
        # Log all environment variables (except sensitive ones)
        env_vars = {k: '***' if 'TOKEN' in k else v for k, v in os.environ.items()}
        logger.info(f"Environment variables: {env_vars}")
        
        # Get credentials
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        
        logger.info("Initializing Telegram notifier...")
        logger.info(f"Bot token present: {bool(self.bot_token)}")
        logger.info(f"Chat ID present: {bool(self.chat_id)}")
        
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
        
        # Test the bot token by getting bot info
        asyncio.create_task(self._test_bot_connection())

    async def _test_bot_connection(self):
        """Test the bot connection by getting bot info."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/getMe") as response:
                    if response.status == 200:
                        bot_info = await response.json()
                        logger.info(f"Connected to Telegram bot: {bot_info}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to connect to Telegram bot. Status: {response.status}, Response: {error_text}")
        except Exception as e:
            logger.error(f"Error testing bot connection: {str(e)}")

    async def send_message(self, text: str):
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram message not sent - missing credentials")
            return

        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"Sending Telegram message to chat {self.chat_id}: {text}")
                
                # Ensure chat_id is a string and properly formatted
                chat_id = str(self.chat_id).strip()
                if not chat_id.startswith('-'):
                    chat_id = f"-{chat_id}"
                
                async with session.post(
                    self.send_message_url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML"
                    }
                ) as response:
                    response_text = await response.text()
                    logger.info(f"Telegram API response: {response_text}")
                    
                    try:
                        result = await response.json()
                    except Exception as e:
                        logger.error(f"Error parsing response JSON: {str(e)}")
                        result = {}
                    
                    if response.status == 200 and result.get('ok'):
                        logger.info("Telegram message sent successfully")
                    else:
                        logger.error(f"Telegram API error: {result}")
                        if 'description' in result:
                            logger.error(f"Error description: {result['description']}")
                    return result
            except aiohttp.ClientError as e:
                logger.error(f"Telegram HTTP error: {str(e)}")
            except Exception as e:
                logger.error(f"Error sending Telegram message: {str(e)}")

    async def notify_chore_completion(self, staff_name: str, chore_description: str):
        time = datetime.now(uk_tz).strftime("%H:%M")
        message = f"✅ {staff_name} marked '{chore_description}' as done at {time}"
        logger.info(f"Notifying chore completion: {message}")
        await self.send_message(message)

    async def notify_chore_uncomplete(self, staff_name: str, chore_description: str):
        time = datetime.now(uk_tz).strftime("%H:%M")
        message = f"❌ {staff_name} marked '{chore_description}' as NOT done at {time}"
        logger.info(f"Notifying chore uncomplete: {message}")
        await self.send_message(message)

    async def notify_checklist_completion(self, staff_name: str, checklist_name: str):
        time = datetime.now(uk_tz).strftime("%H:%M")
        message = f"{staff_name} COMPLETED FULL {checklist_name} at {time} ✅"
        logger.info(f"Notifying checklist completion: {message}")
        await self.send_message(message)

# Create the Telegram notifier instance
try:
    telegram = TelegramNotifier()
    logger.info("Successfully created Telegram notifier instance")
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
    logger.info("Using dummy notifier due to initialization failure") 