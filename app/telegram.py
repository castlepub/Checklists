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
        self.webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")  # Should be your Railway app URL + /telegram/webhook
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not configured")
        if not self.chat_id:
            logger.warning("TELEGRAM_CHAT_ID not configured")
        if not self.webhook_url:
            logger.warning("TELEGRAM_WEBHOOK_URL not configured")
            
        if self.bot_token:
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
            self.send_message_url = f"{self.api_url}/sendMessage"
            self.set_commands_url = f"{self.api_url}/setMyCommands"
            self.set_webhook_url = f"{self.api_url}/setWebhook"
            self.get_webhook_info_url = f"{self.api_url}/getWebhookInfo"
            logger.info("Telegram bot initialized successfully")
        else:
            self.api_url = None
            logger.warning("Telegram bot not initialized due to missing credentials")

    async def _setup_bot(self):
        """Set up the bot commands and webhook."""
        await self._setup_commands()
        await self._setup_webhook()

    async def get_webhook_info(self):
        """Get current webhook information."""
        if not self.bot_token:
            return {"error": "Bot token not configured"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.get_webhook_info_url) as response:
                    return await response.json()
            except Exception as e:
                logger.error(f"Error getting webhook info: {str(e)}")
                return {"error": str(e)}

    async def _setup_webhook(self):
        """Set up the webhook for receiving updates."""
        if not self.webhook_url:
            logger.error("Cannot set up webhook - TELEGRAM_WEBHOOK_URL not configured")
            return

        # First, delete any existing webhook
        async with aiohttp.ClientSession() as session:
            try:
                logger.info("Removing existing webhook")
                await session.post(f"{self.api_url}/deleteWebhook")
            except Exception as e:
                logger.error(f"Error deleting existing webhook: {str(e)}")

        # Set up new webhook
        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"Setting up webhook to {self.webhook_url}")
                async with session.post(
                    self.set_webhook_url,
                    json={
                        "url": self.webhook_url,
                        "allowed_updates": ["message"],
                        "drop_pending_updates": True
                    }
                ) as response:
                    result = await response.json()
                    if response.status == 200 and result.get('ok'):
                        logger.info("Webhook set up successfully")
                    else:
                        logger.error(f"Failed to set up webhook: {result}")
            except Exception as e:
                logger.error(f"Error setting up webhook: {str(e)}")

    async def _setup_commands(self):
        """Set up the bot commands in Telegram."""
        commands = [
            {"command": "clear_all", "description": "Clear all checklist items"}
        ]
        
        async with aiohttp.ClientSession() as session:
            try:
                logger.info("Setting up bot commands")
                async with session.post(
                    self.set_commands_url,
                    json={"commands": commands}
                ) as response:
                    result = await response.json()
                    if response.status == 200 and result.get('ok'):
                        logger.info("Bot commands set up successfully")
                    else:
                        logger.error(f"Failed to set up bot commands: {result}")
            except Exception as e:
                logger.error(f"Error setting up bot commands: {str(e)}")

    async def send_message(self, text: str):
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram message not sent - missing credentials")
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

    async def handle_update(self, update: dict):
        """Handle incoming updates from Telegram."""
        try:
            message = update.get('message', {})
            if not message:
                logger.warning("Received update with no message")
                return
            
            chat_id = str(message.get('chat', {}).get('id'))
            if chat_id != self.chat_id:
                logger.warning(f"Received message from unauthorized chat: {chat_id}")
                return
            
            text = message.get('text', '')
            if not text:
                logger.warning("Received message with no text")
                return
                
            logger.info(f"Processing command: {text}")
            if text.startswith('/clear_all'):
                await self._handle_clear_all_command(message)
            else:
                logger.info(f"Ignoring unknown command: {text}")
        except Exception as e:
            logger.error(f"Error handling Telegram update: {str(e)}")

    async def _handle_clear_all_command(self, message: dict):
        """Handle the /clear_all command."""
        try:
            # Get the username or first name of who sent the command
            user = message.get('from', {})
            username = user.get('username') or user.get('first_name', 'Unknown user')
            
            logger.info(f"Clearing all checklists as requested by {username}")
            
            # Clear all checklist items
            db = SessionLocal()
            try:
                # Clear all chore completions
                result_completions = db.execute(text("DELETE FROM chore_completions"))
                # Clear all signatures
                result_signatures = db.execute(text("DELETE FROM signatures"))
                db.commit()
                
                completions_count = result_completions.rowcount
                signatures_count = result_signatures.rowcount
                
                response = (
                    f"✅ All checklist items cleared by @{username}\n"
                    f"Cleared {completions_count} completions and {signatures_count} signatures"
                )
                logger.info(f"Checklists cleared by {username}: {completions_count} completions, {signatures_count} signatures")
            except Exception as e:
                response = f"❌ Error clearing checklists: {str(e)}"
                logger.error(f"Error clearing checklists: {str(e)}")
                db.rollback()
            finally:
                db.close()
            
            await self.send_message(response)
        except Exception as e:
            logger.error(f"Error handling clear_all command: {str(e)}")
            await self.send_message(f"❌ Error processing command: {str(e)}")

    async def notify_chore_completion(self, staff_name: str, chore_description: str):
        time = datetime.now().strftime("%H:%M")
        message = f"{staff_name} marked '{chore_description}' as done at {time}"
        await self.send_message(message)

    async def notify_checklist_completion(self, staff_name: str, checklist_name: str):
        time = datetime.now().strftime("%H:%M")
        message = f"{staff_name} COMPLETED FULL {checklist_name} at {time} ✅"
        await self.send_message(message)

telegram = TelegramNotifier() 