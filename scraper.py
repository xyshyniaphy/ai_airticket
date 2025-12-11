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

def generate_report(flights, config, airport_data):
    """Generates a modern HTML webpage report for the top 3 flights using an LLM."""
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

    prompt_template = """You are a data formatter. Your only task is to convert the given JSON data into a modern HTML webpage format.
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
Generate a complete, modern HTML webpage with the following structure:
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
            padding: 20px; 
            line-height: 1.6; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            overflow: hidden; 
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 40px; 
            text-align: center; 
            position: relative; 
        }
        .header::before { 
            content: '✈️'; 
            font-size: 80px; 
            position: absolute; 
            top: 20px; 
            right: 40px; 
            opacity: 0.3; 
        }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px; 
            font-weight: 300; 
        }
        .header .subtitle { 
            font-size: 1.2em; 
            opacity: 0.9; 
        }
        .date { 
            background: #f8f9fa; 
            padding: 20px; 
            text-align: center; 
            font-size: 1.1em; 
            color: #495057; 
            border-bottom: 1px solid #dee2e6; 
        }
        .flights-container { 
            padding: 40px; 
        }
        .flight-card { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
            border-radius: 15px; 
            padding: 30px; 
            margin-bottom: 30px; 
            color: white; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.1); 
            transition: transform 0.3s ease, box-shadow 0.3s ease; 
        }
        .flight-card:hover { 
            transform: translateY(-5px); 
            box-shadow: 0 15px 40px rgba(0,0,0,0.15); 
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
            margin-bottom: 20px; 
            padding-bottom: 15px; 
            border-bottom: 2px solid rgba(255,255,255,0.3); 
        }
        .flight-number { 
            font-size: 1.8em; 
            font-weight: bold; 
        }
        .flight-price { 
            font-size: 2.2em; 
            font-weight: bold; 
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3); 
        }
        .flight-details { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-top: 20px; 
        }
        .detail-item { 
            background: rgba(255,255,255,0.1); 
            padding: 15px; 
            border-radius: 10px; 
            backdrop-filter: blur(10px); 
        }
        .detail-label { 
            font-weight: bold; 
            margin-bottom: 5px; 
            opacity: 0.9; 
        }
        .detail-value { 
            font-size: 1.1em; 
        }
        .route-info { 
            background: rgba(255,255,255,0.15); 
            padding: 20px; 
            border-radius: 10px; 
            margin: 20px 0; 
            text-align: center; 
            font-size: 1.2em; 
        }
        .airports { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin: 15px 0; 
        }
        .airport { 
            text-align: center; 
        }
        .airport-code { 
            font-size: 1.5em; 
            font-weight: bold; 
        }
        .airport-name { 
            font-size: 0.9em; 
            opacity: 0.8; 
        }
        .arrow { 
            font-size: 2em; 
            opacity: 0.7; 
        }
        .footer { 
            background: #343a40; 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .footer-note { 
            margin-bottom: 20px; 
            font-size: 1.1em; 
        }
        .footer-link { 
            display: inline-block; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 12px 30px; 
            border-radius: 25px; 
            text-decoration: none; 
            font-weight: bold; 
            transition: all 0.3s ease; 
        }
        .footer-link:hover { 
            transform: scale(1.05); 
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); 
        }
        @media (max-width: 768px) { 
            .header h1 { font-size: 2em; } 
            .flight-header { flex-direction: column; text-align: center; } 
            .flight-details { grid-template-columns: 1fr; } 
            .airports { flex-direction: column; } 
            .arrow { transform: rotate(90deg); margin: 20px 0; } 
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
            <h2 style="text-align: center; margin-bottom: 30px; color: #495057; font-size: 1.8em;">🎯 最便宜的三个航班</h2>
            
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

The HTML should be complete, modern, and beautiful with proper styling. Make it responsive and visually appealing with gradients, cards, and hover effects."""
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
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        print(f"HTML report saved to: {html_filename}")

        # Also send a text summary to Telegram
        text_summary = f"🛫 航班报告已生成\n📍 从 {origin_airport_name} 到 {destination_airport_name}\n📅 {today_date}\n🔗 查看详细HTML报告: {html_filename}"
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
