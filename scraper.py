import os
import json
import time
import glob
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from parser import parse_flight_data, clean_html

def generate_report(flights):
    """Generates a report for the top 3 flights using an LLM."""
    if not flights:
        print("No flights to generate a report for.")
        return

    top_3_flights = flights[:3]

    prompt_template = """
You are a professional travel assistant analyzing flight search results provided in JSON format.
Your task is to summarize the TOP 3 CHEAPEST flights in a clear, concise format in Chinese.

INPUT DATA:
```json
{json_flights_data}
```

REQUIREMENTS:
1. List exactly 3 flights (cheapest first).
2. For each flight include:
   - Total price (highlight the cheapest).
   - Airline(s).
   - Departure & arrival times (with dates).
   - Total duration.
   - Number of transfers.
   - Baggage allowance.
   - The primary vendor/provider.
3. Add a brief note if there are significant differences in layover times or transfer types (e.g., self-transfer).
4. Use emojis for visual clarity (✈️ 💰 ⏱️ 🎒).
5. Keep total response under 500 words.
6. Write in a friendly but professional tone.
7. **Output must be in Chinese.**

EXAMPLE FORMAT:
[表情] 航班 1: [航空公司] - ¥[价格]
📅 [日期] [时间] → [日期] [时间]
⏱️ [总时长] | 🔄 [中转次数]
🎒 [行李]
🏢 销售商: [名称]

[Repeat for 3 flights]

💡 备注: [任何重要的注意事项]
"""
    prompt = prompt_template.format(json_flights_data=json.dumps(top_3_flights, indent=2, ensure_ascii=False))

    gemini_api_endpoint = os.getenv("GEMINI_API_ENDPOINT")
    if gemini_api_endpoint:
        genai.configure(client_options={"api_endpoint": gemini_api_endpoint})

    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.3, google_api_key=os.getenv("GEMINI_API_KEY"))
    
    message = HumanMessage(content=prompt)
    
    try:
        response = llm.invoke(message)
        print("\n--- LLM Report ---")
        print(response.content)
        print("--- End of Report ---\n")
    except Exception as e:
        print(f"Error generating report: {e}")

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

def scrape_flights():
    """Scrapes flight data from the website."""
    load_dotenv()

    origin = os.getenv("ORIGIN")
    destinations = os.getenv("DESTINATIONS", "").split(',')
    departure_dates = os.getenv("DEPARTURE_DATES", "").split(',')
    air_type = os.getenv("AIR_TYPE", "0")

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
    load_dotenv()
    use_cache = os.getenv("USE_CACHE", "false").lower() == "true"

    flights = None
    if use_cache:
        flights = get_flights_from_cache()
    else:
        flights = scrape_flights()

    if flights:
        generate_report(flights)

if __name__ == "__main__":
    main()
