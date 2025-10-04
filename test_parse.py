import json
from bs4 import BeautifulSoup
from parser import parse_flight_data

def main():
    """
    Parses the debug.html file and prints the extracted flight data.
    """
    try:
        with open('debug.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("debug.html not found. Please run the scraper first to generate it.")
        return

    soup = BeautifulSoup(html_content, 'lxml')
    flights = parse_flight_data(soup)

    if flights:
        print(json.dumps(flights, indent=2, ensure_ascii=False))
        print(f"Successfully parsed {len(flights)} flights.")
    else:
        print("No flight data could be parsed from debug.html.")

if __name__ == "__main__":
    main()