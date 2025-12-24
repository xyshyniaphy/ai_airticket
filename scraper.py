import os
import os
from dotenv import load_dotenv
import json
import time
import glob
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from parser import parse_flight_data, clean_html
from telegram_bot import send_telegram_message
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import base64
import io
import markdown
from PIL import Image

def load_config():
    """
    Loads configuration from a .env file (for local development)
    and then from environment variables.
    """
    # Load .env file if it exists
    load_dotenv()

    config = {}
    config['GEMINI_API_ENDPOINT'] = os.environ.get('GEMINI_API_ENDPOINT')
    config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY')
    config['ORIGIN'] = os.environ.get('ORIGIN')
    config['DESTINATIONS'] = os.environ.get('DESTINATIONS')
    config['DEPARTURE_DATES'] = os.environ.get('DEPARTURE_DATES')
    config['AIR_TYPE'] = os.environ.get('AIR_TYPE')
    config['USE_CACHE'] = os.environ.get('USE_CACHE')
    config['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN')
    config['TELEGRAM_CHAT_ID'] = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not all([config['ORIGIN'], config['DESTINATIONS'], config['DEPARTURE_DATES']]):
        print("Error: Essential environment variables (ORIGIN, DESTINATIONS, DEPARTURE_DATES) are not set.")
        
    return config

def render_html_to_png(html_file_path, png_file_path, config):
    """Render HTML file to JPG using headless Chrome with mobile optimization.

    Args:
        html_file_path: Path to the HTML file to render
        png_file_path: Path where the JPG will be saved (note: param name kept for compatibility)
        config: Configuration dict (not currently used, but kept for compatibility)

    Returns:
        Path to the JPG file if successful, None otherwise
    """
    driver = None
    # Temporary PNG path for Selenium screenshot
    temp_png_path = png_file_path.replace('.jpg', '.png').replace('.jpeg', '.png')
    if temp_png_path == png_file_path:
        temp_png_path = png_file_path + '_temp.png'

    try:
        # Setup Chrome options for headless rendering
        chrome_options = Options()

        # Essential options for Docker and headless environments
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")

        # Mobile viewport - 2x resolution for high quality
        chrome_options.add_argument("--window-size=780,1688")
        chrome_options.add_argument("--force-device-scale-factor=2")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1")

        # Additional rendering options
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-dev-tools")

        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_script_timeout(30)
        driver.set_page_load_timeout(30)

        # Get absolute path for the HTML file and convert to file:// URL
        abs_html_path = os.path.abspath(html_file_path)
        file_url = f"file://{abs_html_path}"

        print(f"Loading HTML file: {file_url}")
        driver.get(file_url)

        # Wait for page load and fonts to render
        time.sleep(2)

        # Wait for all images and fonts to be loaded
        driver.execute_script("""
            // Wait for all images to load
            const images = document.querySelectorAll('img');
            images.forEach(img => {
                if (!img.complete) {
                    img.onload = () => console.log('Image loaded');
                }
            });
        """)

        # Additional wait for dynamic content
        time.sleep(1)

        # Get actual page dimensions
        body_width = driver.execute_script("return document.body.scrollWidth")
        body_height = driver.execute_script("return document.body.scrollHeight")

        print(f"Page dimensions: {body_width}x{body_height}")

        # Set window size to match content (with some padding)
        driver.set_window_size(body_width, body_height + 20)

        # Final wait after resize
        time.sleep(0.5)

        # Take full page screenshot as PNG (Selenium only supports PNG)
        driver.save_screenshot(temp_png_path)

        # Convert PNG to JPG with moderate quality
        if os.path.exists(temp_png_path):
            img = Image.open(temp_png_path)
            # Convert to RGB (JPG doesn't support transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save as JPG with moderate quality (75)
            img.save(png_file_path, 'JPEG', quality=75, optimize=True)

            # Delete temporary PNG file
            os.remove(temp_png_path)

        # Verify file was created
        if os.path.exists(png_file_path) and os.path.getsize(png_file_path) > 0:
            file_size_kb = os.path.getsize(png_file_path) / 1024
            print(f"JPG screenshot saved: {png_file_path} ({file_size_kb:.1f} KB)")
            return png_file_path
        else:
            print(f"Error: JPG file was not created or is empty")
            return None

    except Exception as e:
        print(f"Error rendering HTML to JPG: {type(e).__name__}: {e}")
        # Clean up temp file if it exists
        if os.path.exists(temp_png_path):
            try:
                os.remove(temp_png_path)
            except:
                pass
        return None

    finally:
        # Always cleanup driver, even if an error occurred
        if driver is not None:
            try:
                driver.quit()
                print("Chrome driver closed")
            except Exception as e:
                print(f"Warning: Error closing driver: {e}")

def send_telegram_photo(photo_path, config):
    """Send photo to Telegram channel."""
    try:
        bot_token = config.get('TELEGRAM_BOT_TOKEN')
        chat_id = config.get('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("Telegram bot token or chat ID not configured")
            return False
            
        import requests
        
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {
                'chat_id': chat_id,
                'caption': '🛫 航班报告已生成 📱',
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                print(f"Photo sent to Telegram successfully")
                return True
            else:
                print(f"Telegram API error: {result}")
                return False
                
    except Exception as e:
        print(f"Error sending photo to Telegram: {e}")
        return False

def generate_flight_card_html(flight, index, comment_html=""):
    """Generate HTML for a single flight card."""
    header = f'''        <div class="flight-card">
            <div class="flight-header">
                <div class="flight-number">#{index + 1} {flight['airline']}</div>
                <div class="flight-price">{flight['price']}</div>
            </div>'''

    route_info = f'''        <div class="route-info">
                <div class="airports">
                    <div class="airport">
                        <div class="airport-code">{flight['departure']['airport']}</div>
                        <div class="airport-name">{flight['departure']['date']} {flight['departure']['time']}</div>
                    </div>
                    <div class="arrow">✈️</div>
                    <div class="airport">
                        <div class="airport-code">{flight['arrival']['airport']}</div>
                        <div class="airport-name">{flight['arrival']['date']} {flight['arrival']['time']}</div>
                    </div>
                </div>
            </div>'''

    details = f'''        <div class="flight-details">
                <div class="detail-item">
                    <div class="detail-label">⏱️ 飞行时长</div>
                    <div class="detail-value">{flight['duration']}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">🔄 中转</div>
                    <div class="detail-value">{flight['transfers']['count_str']}</div>
                </div>'''

    if flight.get('plane_model'):
        details += f'''
                <div class="detail-item">
                    <div class="detail-label">✈️ 机型</div>
                    <div class="detail-value">{flight['plane_model']}</div>
                </div>'''

    if flight.get('baggage'):
        baggage_str = ', '.join(flight['baggage'])
        details += f'''
                <div class="detail-item">
                    <div class="detail-label">🎒 行李</div>
                    <div class="detail-value">{baggage_str}</div>
                </div>'''

    if flight.get('provider_name'):
        details += f'''
                <div class="detail-item">
                    <div class="detail-label">🏢 销售商</div>
                    <div class="detail-value">{flight['provider_name']}</div>
                </div>'''

    closing = '''        </div>'''

    comment_section = ""
    if comment_html:
        comment_section = f'''
        <div class="flight-comment">
            <div class="comment-title">💡 航班点评</div>
            <div class="comment-content">{comment_html}</div>
        </div>'''

    return f'''{header}
{route_info}
{details}
{comment_section}
{closing}
    </div>'''


def normalize_flight_data(flights):
    """Normalize flight data from different formats to the standard format.

    Handles old format (with 'schedule' key) and new format (with 'departure'/'arrival' keys).
    """
    normalized = []
    for flight in flights:
        # Check if this is the old format with 'schedule' key
        if 'schedule' in flight:
            schedule = flight['schedule']
            normalized_flight = {
                'provider_name': flight.get('provider_name', 'N/A'),
                'price': flight.get('price', 'N/A'),
                'trip_type': schedule.get('trip_type', 'N/A'),
                'airline': flight.get('airline', 'N/A'),
                'departure': {
                    'date': '',  # Old format doesn't have date
                    'time': schedule.get('departure_time', 'N/A'),
                    'airport': schedule.get('departure_airport', 'N/A')
                },
                'arrival': {
                    'date': '',  # Old format doesn't have date
                    'time': schedule.get('arrival_time', 'N/A'),
                    'airport': schedule.get('arrival_airport', 'N/A')
                },
                'duration': schedule.get('duration', 'N/A'),
                'transfers': {
                    'count_str': schedule.get('transfers', 'N/A'),
                    'airports': []  # Old format doesn't have airport list
                },
                'plane_model': flight.get('plane_model', 'N/A'),
                'baggage': flight.get('baggage', []),
                'source_url': flight.get('source_url', '#')
            }
            normalized.append(normalized_flight)
        else:
            # Already in new format, just ensure all required fields exist
            normalized_flight = {
                'provider_name': flight.get('provider_name', 'N/A'),
                'price': flight.get('price', 'N/A'),
                'trip_type': flight.get('trip_type', 'N/A'),
                'airline': flight.get('airline', 'N/A'),
                'departure': flight.get('departure', {'date': '', 'time': 'N/A', 'airport': 'N/A'}),
                'arrival': flight.get('arrival', {'date': '', 'time': 'N/A', 'airport': 'N/A'}),
                'duration': flight.get('duration', 'N/A'),
                'transfers': flight.get('transfers', {'count_str': 'N/A', 'airports': []}),
                'plane_model': flight.get('plane_model', 'N/A'),
                'baggage': flight.get('baggage', []),
                'source_url': flight.get('source_url', '#')
            }
            normalized.append(normalized_flight)
    return normalized


def generate_report(flights, config, airport_data):
    """Generates a modern HTML webpage report and renders it as PNG using headless Chrome."""
    if not flights:
        print("No flights to generate a report for.")
        return

    # Normalize flight data to handle both old and new formats
    flights = normalize_flight_data(flights)
    top_3_flights = flights[:3]

    origin_airport_code = top_3_flights[0]['departure']['airport']
    destination_airport_code = top_3_flights[0]['arrival']['airport']
    origin_airport_name = airport_data.get(origin_airport_code, origin_airport_code)
    destination_airport_name = airport_data.get(destination_airport_code, destination_airport_code)

    today_date = datetime.now().strftime('%Y年 %m月 %d日')

    # Get the source URL from the first flight in top_3_flights
    report_url = top_3_flights[0].get('source_url', '#')

    # Generate summary and flight comments via LLM
    prompt_template = """You are a flight analysis assistant. Analyze the flight data and provide a detailed summary and individual flight comments in Chinese.

DATA:
```json
{json_flights_data}
```

OUTPUT FORMAT (valid JSON only, no markdown):
```json
{{
    "summary_note": "Brief note about the flights (e.g., self-transfer requirements, best value recommendations, price differences)",
    "flight_comments": [
        "Comment for flight 1 in markdown format - discuss transfer info, what to watch out for, pros/cons",
        "Comment for flight 2 in markdown format - discuss transfer info, what to watch out for, pros/cons",
        "Comment for flight 3 in markdown format - discuss transfer info, what to watch out for, pros/cons"
    ]
}}
```

IMPORTANT: Each flight comment should include:
- Transfer information (if any): self-transfer or protected transfer
- What travelers should watch out for: layover time, visa requirements, terminal changes
- Pros: price, timing, airline quality
- Cons: long layover, early departure, etc.

Use markdown formatting: **bold**, *italic*, - bullets, numbered lists.

Keep the summary_note concise (under 100 Chinese characters). Keep each flight comment under 150 Chinese characters."""
    prompt = prompt_template.format(
        json_flights_data=json.dumps(top_3_flights, indent=2, ensure_ascii=False)
    )

    api_host = config.get("GEMINI_API_ENDPOINT")
    api_key = config.get("GEMINI_API_KEY")
    model = "gemini-flash-latest-non-thinking"

    url = f"{api_host}/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    # Default summary and comments
    summary_note = "以上为最便宜的三个航班选项，请根据个人需求选择。"
    flight_comments = ["暂无详细信息", "暂无详细信息", "暂无详细信息"]

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        llm_response = result['candidates'][0]['content']['parts'][0]['text']

        # Extract JSON from response
        if '```json' in llm_response:
            json_str = llm_response.split('```json')[1].split('```')[0].strip()
        else:
            json_str = llm_response.strip()

        summary_data = json.loads(json_str)
        summary_note = summary_data.get('summary_note', summary_note)
        flight_comments = summary_data.get('flight_comments', flight_comments)
        print(f"LLM Summary: {summary_note}")

    except Exception as e:
        print(f"LLM analysis failed: {e}, using default summary")

    # Generate flight cards HTML with comments
    flight_cards_html = ""
    for i, flight in enumerate(top_3_flights):
        comment_md = flight_comments[i] if i < len(flight_comments) else ""
        comment_html = markdown.markdown(comment_md) if comment_md else ""
        flight_cards_html += generate_flight_card_html(flight, i, comment_html)

    # Load HTML template and fill with data
    template_path = os.path.join(os.path.dirname(__file__), 'template.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
    except FileNotFoundError:
        print(f"Error: template.html not found at {template_path}")
        return

    # Replace placeholders
    report_html = html_template.format(
        origin_airport_name=origin_airport_name,
        destination_airport_name=destination_airport_name,
        today_date=today_date,
        flight_cards=flight_cards_html,
        summary_note=summary_note,
        report_url=report_url
    )

    # Save and render
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_filename = f"data/flight_report_{origin_airport_code}_{destination_airport_code}_{timestamp}.html"
    jpg_filename = f"data/flight_report_{origin_airport_code}_{destination_airport_code}_{timestamp}.jpg"

    os.makedirs("data", exist_ok=True)

    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(report_html)

    print(f"HTML report saved to: {html_filename}")

    # Check if Telegram is configured
    telegram_token = config.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = config.get('TELEGRAM_CHAT_ID')
    telegram_enabled = telegram_token and telegram_chat_id and telegram_token.strip() and telegram_chat_id.strip()

    # Render HTML as JPG using headless Chrome
    try:
        jpg_path = render_html_to_png(html_filename, jpg_filename, config)
        if jpg_path:
            print(f"JPG screenshot saved to: {jpg_path}")

            if telegram_enabled:
                # Send JPG to Telegram
                from telegram_bot import send_telegram_photo
                send_telegram_photo(jpg_path, config, caption=f"🛫 航班报告已生成\n📍 从 {origin_airport_name} 到 {destination_airport_name}\n📅 {today_date}")

                # Clean up HTML file after successful JPG generation
                try:
                    os.remove(html_filename)
                    print(f"Cleaned up HTML file: {html_filename}")
                except OSError:
                    pass
            else:
                print("Telegram not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)")
                print(f"Report files saved to data folder:")
                print(f"  - HTML: {html_filename}")
                print(f"  - JPG:  {jpg_filename}")
        else:
            print("JPG generation failed, HTML file preserved for debugging")

    except Exception as chrome_error:
        print(f"Chrome screenshot failed: {chrome_error}")
        print(f"HTML file saved to: {html_filename}")
        if telegram_enabled:
            text_summary = f"🛫 航班报告已生成\n📍 从 {origin_airport_name} 到 {destination_airport_name}\n📅 {today_date}"
            send_telegram_message(text_summary, config)

def get_flights_from_cache():
    """Reads flight data from the latest cache file."""
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print("Cache directory 'data' not found.")
        return None

    list_of_files = glob.glob(os.path.join(data_dir, '*.md'))
    if not list_of_files:
        print("No cache files found in 'data' directory.")
        return None

    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Using cache file: {latest_file}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        json_str = content.split('```json')[1].split('```')[0]
        return json.loads(json_str)
    except (IndexError, json.JSONDecodeError) as e:
        print(f"Could not parse json from file: {e}")
        return None

def scrape_flights(config):
    """Scrapes flight data from the website."""
    origin = config.get("ORIGIN")
    destinations = config.get("DESTINATIONS", "").split(',')
    departure_dates = config.get("DEPARTURE_DATES", "").split(',')
    air_type = config.get("AIR_TYPE", "0")

    chrome_options = Options()
    # 1. Essential for Docker and Headless environments
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") # A must-have for running as a non-root user
    chrome_options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems
    
    # 2. Performance and Stability Boosters
    chrome_options.add_argument("--disable-gpu") # Not needed for headless, saves resources
    chrome_options.add_argument("--window-size=1920,1080") # Set a standard resolution
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")

    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--v=1")

    all_flights = []
    with webdriver.Chrome(options=chrome_options) as driver:
        for dest in destinations:
            for date in departure_dates:
                print(f"Scraping for {origin} -> {dest} on {date}...")
                slice_info = f"{origin}-{dest}"
                url = f"https://www.tour.ne.jp/w_air/list/?air_type={air_type}&slice_info={slice_info}#dpt_date={date}&page_from=index"

                driver.get(url)

                try:
                    # WebDriverWait is disabled , it will crash in docker
                    # WebDriverWait(driver, 240).until(
                    #     EC.presence_of_element_located((By.CLASS_NAME, "flight-area"))
                    # )
                    time.sleep(55)

                    html_content = driver.page_source
                    cleaned_html = clean_html(html_content)

                    soup = BeautifulSoup(cleaned_html, 'lxml')
                    flights = parse_flight_data(soup)

                    if not flights:
                        print("No flight data found.")
                        continue
                    for flight in flights:
                        flight['source_url'] = url
                    all_flights.extend(flights)

                    # Save results
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"data/{origin}-{dest}-{date}-{timestamp}.md"
                    os.makedirs("data", exist_ok=True)

                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"# Flight Search Results for {origin} to {dest} on {date}\n\n")
                        f.write("```json\n")
                        f.write(json.dumps(flights, indent=2, ensure_ascii=False))
                        f.write("\n```\n")

                    print(f"Saved {len(flights)} flight results to {filename}")

                except Exception as e:
                    print(f"An error occurred while scraping {url}: {e}")
    return all_flights

def load_airport_data(file_path='iata-icao.csv'):
    """Loads airport data from the CSV file."""
    airport_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip header
            next(f)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    iata = parts[2].strip().strip('\"')
                    airport_name = parts[4].strip().strip('\"')
                    if iata:
                        airport_data[iata] = airport_name
    except FileNotFoundError:
        print("Warning: iata-icao.csv file not found.")
    return airport_data

def main():
    """Main function to process flight data."""
    config = load_config()
    use_cache = config.get("USE_CACHE", "false").lower() == "true"

    flights = None
    if use_cache:
        flights = get_flights_from_cache()
    else:
        flights = scrape_flights(config)

    if flights:
        airport_data = load_airport_data()
        generate_report(flights, config, airport_data)

if __name__ == "__main__":
    main()
