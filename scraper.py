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
    """Render HTML file to PNG using headless Chrome with mobile optimization."""
    try:
        chrome_options = Options()
        # Essential for Docker and headless environments
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        # Mobile optimization - simulate iPhone 12 Pro portrait mode
        chrome_options.add_argument("--window-size=390,844")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1")
        
        # Additional options for better rendering
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Get absolute path for the HTML file
        abs_html_path = os.path.abspath(html_file_path)
        file_url = f"file://{abs_html_path}"
        
        print(f"Loading HTML file: {file_url}")
        driver.get(file_url)
        
        # Wait for page to load completely
        time.sleep(3)
        
        # Get full page height for screenshot
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(390, total_height + 100)  # Add some padding
        
        # Take screenshot
        driver.save_screenshot(png_file_path)
        
        # Cleanup
        driver.quit()
        
        print(f"PNG screenshot saved to: {png_file_path}")
        return png_file_path
        
    except Exception as e:
        print(f"Error rendering HTML to PNG: {e}")
        return None

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

def generate_report(flights, config, airport_data):
    """Generates a modern HTML webpage report and renders it as PNG using headless Chrome."""
    if not flights:
        print("No flights to generate a report for.")
        return

    top_3_flights = flights[:3]

    origin_airport_code = top_3_flights[0]['departure']['airport']
    destination_airport_code = top_3_flights[0]['arrival']['airport']
    origin_airport_name = airport_data.get(origin_airport_code, origin_airport_code)
    destination_airport_name = airport_data.get(destination_airport_code, destination_airport_code)

    all_airport_codes = {origin_airport_code, destination_airport_code}
    for flight in top_3_flights:
        for airport_code in flight['transfers']['airports']:
            all_airport_codes.add(airport_code)

    airport_names_map = {code: airport_data.get(code, code) for code in all_airport_codes}
    airport_names_str = ", ".join([f"{code} ({name})" for code, name in airport_names_map.items()])
    
    today_date = datetime.now().strftime('%Y年 %m月 %d日')
    
    # Get the source URL from the first flight in top_3_flights
    report_url = top_3_flights[0].get('source_url', '#')

    prompt_template = """You are a data formatter. Your only task is to convert the given JSON data into a modern HTML webpage format optimized for mobile viewing.
Your response must be in Chinese.
You MUST NOT output any text other than the complete HTML code.

The user is searching for flights from {origin_airport_name} ({origin_airport_code}) to {destination_airport_name} ({destination_airport_code}).
Here is a list of airport codes and their names: {airport_names}. Please use these names in your response.
you will translate the airport name into chinese

DATA:
```json
{json_flights_data}
```

FORMAT:
Generate a complete, modern HTML webpage optimized for mobile viewing with the following structure:
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Report - {origin_airport_name} to {destination_airport_name}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            padding: 10px; 
            line-height: 1.6; 
            color: #333;
        }
        .container { 
            max-width: 480px; /* Optimized for mobile vertical resolution */
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
            overflow: hidden; 
            margin-bottom: 20px;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 20px; 
            text-align: center; 
            position: relative; 
        }
        .header::before { 
            content: '✈️'; 
            font-size: 40px; 
            position: absolute; 
            top: 10px; 
            right: 15px; 
            opacity: 0.3; 
        }
        .header h1 { 
            font-size: 1.8em; 
            margin-bottom: 5px; 
            font-weight: 300; 
        }
        .header .subtitle { 
            font-size: 1em; 
            opacity: 0.9; 
        }
        .date { 
            background: #f8f9fa; 
            padding: 12px; 
            text-align: center; 
            font-size: 0.95em; 
            color: #495057; 
            border-bottom: 1px solid #dee2e6; 
        }
        .flights-container { 
            padding: 20px; 
        }
        .flight-card { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
            border-radius: 12px; 
            padding: 20px; 
            margin-bottom: 20px; 
            color: white; 
            box-shadow: 0 8px 20px rgba(0,0,0,0.1); 
            transition: transform 0.3s ease, box-shadow 0.3s ease; 
        }
        .flight-card:hover { 
            transform: translateY(-3px); 
            box-shadow: 0 12px 25px rgba(0,0,0,0.15); 
        }
        .flight-card:nth-child(2) { 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
        }
        .flight-card:nth-child(3) { 
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
        }
        .flight-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 15px; 
            padding-bottom: 10px; 
            border-bottom: 1px solid rgba(255,255,255,0.3); 
            flex-wrap: wrap;
            gap: 10px;
        }
        .flight-number { 
            font-size: 1.3em; 
            font-weight: bold; 
        }
        .flight-price { 
            font-size: 1.6em; 
            font-weight: bold; 
            text-shadow: 1px 1px 3px rgba(0,0,0,0.3); 
        }
        .flight-details { 
            display: grid; 
            grid-template-columns: 1fr; 
            gap: 12px; 
            margin-top: 15px; 
        }
        .detail-item { 
            background: rgba(255,255,255,0.1); 
            padding: 12px; 
            border-radius: 8px; 
            backdrop-filter: blur(10px); 
        }
        .detail-label { 
            font-weight: bold; 
            margin-bottom: 3px; 
            opacity: 0.9; 
            font-size: 0.85em;
        }
        .detail-value { 
            font-size: 0.95em; 
            word-break: break-word;
        }
        .route-info { 
            background: rgba(255,255,255,0.15); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 15px 0; 
            text-align: center; 
            font-size: 1em; 
        }
        .airports { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin: 10px 0; 
            flex-wrap: wrap;
            gap: 10px;
        }
        .airport { 
            text-align: center; 
            flex: 1;
            min-width: 80px;
        }
        .airport-code { 
            font-size: 1.2em; 
            font-weight: bold; 
        }
        .airport-name { 
            font-size: 0.8em; 
            opacity: 0.8; 
        }
        .arrow { 
            font-size: 1.5em; 
            opacity: 0.7; 
            margin: 0 5px;
        }
        .footer { 
            background: #343a40; 
            color: white; 
            padding: 20px; 
            text-align: center; 
            font-size: 0.9em;
        }
        .footer-note { 
            margin-bottom: 15px; 
            font-size: 0.95em; 
            line-height: 1.5;
        }
        .footer-link { 
            display: inline-block; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 10px 20px; 
            border-radius: 20px; 
            text-decoration: none; 
            font-weight: bold; 
            transition: all 0.3s ease; 
            font-size: 0.9em;
        }
        .footer-link:hover { 
            transform: scale(1.05); 
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
        }
        h2 {
            text-align: center; 
            margin-bottom: 20px; 
            color: #495057; 
            font-size: 1.5em;
            font-weight: 400;
        }
        @media (max-width: 480px) { 
            .header h1 { font-size: 1.5em; } 
            .header .subtitle { font-size: 0.9em; }
            .flight-header { flex-direction: column; text-align: center; } 
            .flight-number { font-size: 1.1em; }
            .flight-price { font-size: 1.4em; }
            .flight-details { gap: 10px; }
            .airports { flex-direction: column; } 
            .arrow { transform: rotate(90deg); margin: 10px 0; } 
            .footer { padding: 15px; font-size: 0.85em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ 航班查询报告</h1>
            <div class="subtitle">从 {origin_airport_name} 到 {destination_airport_name}</div>
        </div>
        
        <div class="date">📅 今天是 {today_date}</div>
        
        <div class="flights-container">
            <h2>🎯 最便宜的三个航班</h2>
            
            <!-- Generate flight cards for the top 3 flights -->
            <!-- Flight 1, Flight 2, Flight 3 with all details -->
            <!-- Each flight should include: price, airline, flight number, route, duration, transfers, aircraft, baggage info -->
            
            [Generate the flight cards based on the JSON data provided]
        </div>
        
        <div class="footer">
            <div class="footer-note">
                💡 <strong>备注：</strong> [Important notes about self-transfers or other requirements]
            </div>
            <a href="{report_url}" class="footer-link" target="_blank">🌐 点此链接查看详情</a>
        </div>
    </div>
</body>
</html>

The HTML should be complete, modern, and beautiful with proper styling optimized for mobile viewing. Make it responsive and visually appealing with gradients, cards, and hover effects. The design should work well in vertical orientation on cell phones."""
    prompt = prompt_template.format(
        today_date=today_date,
        json_flights_data=json.dumps(top_3_flights, indent=2, ensure_ascii=False),
        origin_airport_code=origin_airport_code,
        destination_airport_code=destination_airport_code,
        origin_airport_name=origin_airport_name,
        destination_airport_name=destination_airport_name,
        airport_names=airport_names_str,
        report_url=report_url
    )
    
    print(prompt)

    api_host = config.get("GEMINI_API_ENDPOINT")
    api_key = config.get("GEMINI_API_KEY")
    # do not change this line, must use non thinking model
    model = "gemini-flash-latest-non-thinking"
    
    url = f"{api_host}/models/{model}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        # bypass llm, testing telegram bot
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        report_html = result['candidates'][0]['content']['parts'][0]['text']

        print("\n--- Generated HTML Report ---")
        print(f"HTML length: {len(report_html)} characters")
        print("--- End of HTML Report ---\n")

        # Save the HTML report to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"data/flight_report_{origin_airport_code}_{destination_airport_code}_{timestamp}.html"
        png_filename = f"data/flight_report_{origin_airport_code}_{destination_airport_code}_{timestamp}.png"
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        print(f"HTML report saved to: {html_filename}")

        # Render HTML as PNG using headless Chrome
        try:
            png_path = render_html_to_png(html_filename, png_filename, config)
            if png_path:
                print(f"PNG screenshot saved to: {png_path}")
                
                # Send PNG to Telegram instead of text
                from telegram_bot import send_telegram_photo
                send_telegram_photo(png_path, config, caption=f"🛫 航班报告已生成\n📍 从 {origin_airport_name} 到 {destination_airport_name}\n📅 {today_date}")
                
                # Clean up HTML file after successful PNG generation
                try:
                    os.remove(html_filename)
                    print(f"Cleaned up HTML file: {html_filename}")
                except OSError:
                    pass
            else:
                # Fallback to text if PNG generation fails
                text_summary = f"🛫 航班报告已生成\n📍 从 {origin_airport_name} 到 {destination_airport_name}\n📅 {today_date}"
                send_telegram_message(text_summary, config)
                
        except Exception as chrome_error:
            print(f"Chrome screenshot failed: {chrome_error}")
            # Fallback to text if Chrome fails
            text_summary = f"🛫 航班报告已生成\n📍 从 {origin_airport_name} 到 {destination_airport_name}\n📅 {today_date}"
            send_telegram_message(text_summary, config)

    except requests.exceptions.RequestException as e:
        print(f"Error generating report: {e}")
    except (KeyError, IndexError) as e:
        print(f"Error parsing LLM response: {e}")
        print(f"Full response: {response.text}")

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
