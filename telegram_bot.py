import requests

def send_telegram_message(message, config):
    """Sends a message to a Telegram chat."""
    bot_token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Warning: Telegram bot token or chat ID not found in config. Skipping message.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Successfully sent message to Telegram.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

def send_telegram_photo(photo_path, config, caption="🛫 航班报告已生成 📱"):
    """Sends a photo to a Telegram chat."""
    bot_token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Warning: Telegram bot token or chat ID not found in config. Skipping photo.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                print("Successfully sent photo to Telegram.")
                return True
            else:
                print(f"Telegram API error: {result}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"Error sending photo to Telegram: {e}")
        return False
    except FileNotFoundError:
        print(f"Photo file not found: {photo_path}")
        return False