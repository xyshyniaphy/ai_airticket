
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def parse_flight_data(soup: BeautifulSoup) -> list[dict]:
    """Parses the flight data from the BeautifulSoup object."""
    flight_areas = soup.find_all('div', class_='flight-area')
    parsed_flights = []

    for flight in flight_areas:
        # Basic info
        provider_name_tag = flight.find('div', class_='flight-summary-hdg')
        provider_name = provider_name_tag.text.strip() if provider_name_tag else 'N/A'

        price_tag = flight.find('span', class_='price')
        price = price_tag.text.strip() if price_tag else 'N/A'

        # Schedule
        sch_header_tag = flight.find('div', class_='sch-header')
        trip_type = sch_header_tag.find('span').text.strip() if sch_header_tag else 'N/A'

        going_area = flight.find('div', class_='going-area')
        dpt_time = going_area.find('div', class_='dpt-time').text.strip()
        dpt_airport = going_area.find('div', class_='dpt-airport').text.strip()
        arr_time = going_area.find('div', class_='arr-time').text.strip()
        arr_airport = going_area.find('div', class_='arr-airport').text.strip()

        flt_term_tag = flight.find('div', class_='flt-term')
        duration = flt_term_tag.find('span', class_='hour').text.strip()
        transfers = flt_term_tag.find('span', class_='transfer').text.strip()


        flight_data = {
            "provider_name": provider_name,
            "price": price,
            "schedule": {
                "trip_type": trip_type,
                "departure_time": dpt_time,
                "departure_airport": dpt_airport,
                "arrival_time": arr_time,
                "arrival_airport": arr_airport,
                "duration": duration,
                "transfers": transfers,
            },
        }
        parsed_flights.append(flight_data)

    return parsed_flights


def main():
    """Main function to scrape flight data."""
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


    with webdriver.Chrome(options=chrome_options) as driver:
        for dest in destinations:
            for date in departure_dates:
                print(f"Scraping for {origin} -> {dest} on {date}...")
                slice_info = f"{origin}-{dest}"
                url = f"https://www.tour.ne.jp/w_air/list/?air_type={air_type}&slice_info={slice_info}#dpt_date={date}&page_from=index"

                driver.get(url)

                try:
                    # Wait for the flight area to be present
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "flight-area"))
                    )
                    # Additional wait for dynamic content
                    time.sleep(5)

                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    flights = parse_flight_data(soup)

                    if not flights:
                        print("No flight data found.")
                        continue

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


if __name__ == "__main__":
    main()
