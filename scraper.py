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
    """Generates a report for the top 3 flights using an LLM."""
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
    # Assuming all flights in top_3_flights came from the same URL for the report
    report_url = top_3_flights[0].get('source_url', '#')

    prompt_template = """You are a data formatter. Your only task is to convert the given JSON data into a specific format.
Your response must be in Chinese.
You MUST NOT output any text other than the formatted data.

The user is searching for flights from {origin_airport_name} ({origin_airport_code}) to {destination_airport_name} ({destination_airport_code}).
Here is a list of airport codes and their names: {airport_names}. Please use these names in your response.
you will translate the airport name into chinese

DATA:
```json
{json_flights_data}
```

FORMAT:
今天是 {today_date}
从 [ {origin_airport_name} ] 到 [ {destination_airport_name} ]  的最便宜的机票如下
✈️ **航班 1:** [价格]
- **销售商:** [销售商名称]
- **航司:** [航空公司]
- **航班号:** [航班号]
- **行程:** [出发日期] [出发时间] →  [到达日期] [到达时间]
- **时长:** [总时长]
- **中转:** [中转信息]
- **机型:** [飞机型号]
- **行李:** [行李信息]

✈️ **航班 2:** [价格]
- **销售商:** [销售商名称]
- **航司:** [航空公司]
- **航班号:** [航班号]
- **行程:** [出发日期] [出发时间] →  [到达日期] [到达时间]
- **时长:** [总时长]
- **中转:** [中转信息]
- **机型:** [飞机型号]
- **行李:** [行李信息]

✈️ **航班 3:** [价格]
- **销售商:** [销售商名称]
- **航司:** [航空公司]
- **航班号:** [航班号]
- **行程:** [出发日期] [出发时间] → [到达日期] [到达时间]
- **时长:** [总时长]
- **中转:** [中转信息]
- **机型:** [飞机型号]
- **行李:** [行李信息]

💡 **备注:** [任何重要的注意事项, e.g. self-transfer]
- [点此链接查看详情]({report_url})
"""
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
        
        report_text = result['candidates'][0]['content']['parts'][0]['text']


        #report_text= 'test message'

        print("\n--- LLM Report ---")
        print(report_text)
        print("--- End of Report ---\n")

        send_telegram_message(report_text, config)

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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
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
                    WebDriverWait(driver, 240).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "flight-area"))
                    )
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
