import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_chat_id():
    bot_token = "7500100407:AAEZ8gm19g7YIw8BY8DakxTuCWPMIiEzZT4"
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    print(f"\nChecking bot status...")
    
    try:
        # First, check if the bot is valid
        me_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        me_response = requests.get(me_url)
        me_data = me_response.json()
        
        if me_data["ok"]:
            bot_info = me_data["result"]
            print(f"\nBot information:")
            print(f"Name: {bot_info['first_name']}")
            print(f"Username: @{bot_info['username']}")
            print(f"Bot ID: {bot_info['id']}")
        else:
            print("\nError: Could not get bot information. Please verify your bot token.")
            return

        # Now check for messages
        print("\nChecking for messages...")
        response = requests.get(url)
        data = response.json()
        
        print(f"\nAPI Response:")
        print(data)
        
        if data["ok"] and data["result"]:
            # Get the most recent message
            latest = data["result"][-1]
            chat_id = latest["message"]["chat"]["id"]
            chat_title = latest["message"]["chat"].get("title", "Private Chat")
            
            print(f"\nFound chat:")
            print(f"Chat ID: {chat_id}")
            print(f"Chat Title: {chat_title}")
            print("\nAdd this to your .env file:")
            print(f"TELEGRAM_CHAT_ID={chat_id}")
        else:
            print("\nNo messages found. Please:")
            print("1. Verify the bot is in your group")
            print("2. Make the bot an admin in the group")
            print("3. Send a new message in the group")
            print("4. Run this script again")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_chat_id() 