import os
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

def load_config():
    """Loads configuration from the .env file."""
    config = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
    except FileNotFoundError:
        print("Warning: .env file not found.")
    return config

def generate_report(flights, config):
    """Generates a report for the top 3 flights using an LLM."""
    if not flights:
        print("No flights to generate a report for.")
        return

    top_3_flights = flights[:3]

    prompt_template = """You are a data formatting machine. You do not have a personality. You do not think. You only convert data from one format to another.
Your task is to convert the given JSON data into the specified format.
You must not output any text other than the formatted data.

DATA:
```json
{json_flights_data}
```

FORMAT:
✈️ **航班 1:** [价格]
- **销售商:** [销售商名称]
- **行程:** [出发机场] [出发时间] → [到达机场] [到达时间]
- **时长:** [总时长]
- **中转:** [中转次数]

✈️ **航班 2:** [价格]
- **销售商:** [销售商名称]
- **行程:** [出发机场] [出发时间] → [到达机场] [到达时间]
- **时长:** [总时长]
- **中转:** [中转次数]

✈️ **航班 3:** [价格]
- **销售商:** [销售商名称]
- **行程:** [出发机场] [出发时间] → [到达机场] [到达时间]
- **时长:** [总时长]
- **中转:** [中转次数]

💡 **备注:** [任何重要的注意事项, e.g. self-transfer]
"""
    prompt = prompt_template.format(json_flights_data=json.dumps(top_3_flights, indent=2, ensure_ascii=False))

    api_host = config.get("GEMINI_API_ENDPOINT")
    api_key = config.get("GEMINI_API_KEY")
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
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n--- LLM Report ---")
        print(result['candidates'][0]['content']['parts'][0]['text'])
        print("--- End of Report ---\n")

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

    all_flights = []
    with webdriver.Chrome(options=chrome_options) as driver:
        for dest in destinations:
            for date in departure_dates:
                print(f"Scraping for {origin} -> {dest} on {date}...")
                slice_info = f"{origin}-{dest}"
                url = f"https://www.tour.ne.jp/w_air/list/?air_type={air_type}&slice_info={slice_info}#dpt_date={date}&page_from=index"

                driver.get(url)

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "flight-area"))
                    )
                    time.sleep(5)

                    html_content = driver.page_source
                    cleaned_html = clean_html(html_content)

                    soup = BeautifulSoup(cleaned_html, 'lxml')
                    flights = parse_flight_data(soup)

                    if not flights:
                        print("No flight data found.")
                        continue
                    
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
        generate_report(flights, config)

if __name__ == "__main__":
    main()
