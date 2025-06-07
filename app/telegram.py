import os
import aiohttp
from datetime import datetime

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_message(self, text: str):
        if not self.bot_token or not self.chat_id:
            print("Telegram credentials not configured")
            return

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.api_url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML"
                    }
                ) as response:
                    return await response.json()
            except Exception as e:
                print(f"Error sending Telegram message: {e}")

    async def notify_chore_completion(self, staff_name: str, chore_description: str):
        time = datetime.now().strftime("%H:%M")
        message = f"{staff_name} marked '{chore_description}' as done at {time}"
        await self.send_message(message)

    async def notify_checklist_completion(self, staff_name: str, checklist_name: str):
        time = datetime.now().strftime("%H:%M")
        message = f"{staff_name} COMPLETED FULL {checklist_name} at {time} ✅"
        await self.send_message(message)

telegram = TelegramNotifier() 