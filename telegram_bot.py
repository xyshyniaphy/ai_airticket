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

            # Debug: log the request
            print(f"Sending photo to Telegram chat_id={chat_id}")

            response = requests.post(url, files=files, data=data, timeout=30)

            # Debug: log response for troubleshooting
            print(f"Telegram response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Telegram response body: {response.text}")

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


def send_telegram_document(file_path, config, caption="🛫 航班报告已生成 📱", filename="flight_report.jpg"):
    """Sends a document to a Telegram chat (no compression, preserves quality)."""
    bot_token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Warning: Telegram bot token or chat ID not found in config. Skipping document.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    try:
        with open(file_path, 'rb') as file:
            files = {'document': (filename, file, 'image/jpeg')}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }

            # Debug: log the request
            print(f"Sending document to Telegram chat_id={chat_id}")

            response = requests.post(url, files=files, data=data, timeout=60)

            # Debug: log response for troubleshooting
            print(f"Telegram response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Telegram response body: {response.text}")

            response.raise_for_status()

            result = response.json()
            if result.get('ok'):
                print("Successfully sent document to Telegram.")
                return True
            else:
                print(f"Telegram API error: {result}")
                return False

    except requests.exceptions.RequestException as e:
        print(f"Error sending document to Telegram: {e}")
        return False
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False