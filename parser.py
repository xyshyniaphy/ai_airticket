from bs4 import BeautifulSoup, Comment

def clean_html(html: str) -> str:
    """Removes script and style tags, and comments from the HTML."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.decompose()
    
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr != 'id' and attr != 'class':
                del tag[attr]
    return str(soup)

def parse_flight_data(soup: BeautifulSoup) -> list[dict]:
    """Parses the flight data from the BeautifulSoup object."""
    flight_areas = soup.find_all('div', class_='flight-area')
    parsed_flights = []

    for flight in flight_areas:
        provider_name_tag = flight.find('div', class_='flight-summary-hdg')
        provider_name = provider_name_tag.text.strip().split('\n')[0] if provider_name_tag else 'N/A'

        price_tag = flight.find('span', class_='flight-summary-total-price')
        price = price_tag.text.strip() if price_tag else 'N/A'

        trip_type_tag = flight.find('div', class_='sch-header-sup')
        trip_type = trip_type_tag.text.strip() if trip_type_tag else 'N/A'

        dpt_time, dpt_airport, arr_time, arr_airport = 'N/A', 'N/A', 'N/A', 'N/A'
        going_area = flight.find('div', class_='going-area')
        if going_area:
            dpt_time_tag = going_area.find('span', class_='sch-time')
            dpt_time = dpt_time_tag.text.strip() if dpt_time_tag else 'N/A'

            dpt_airport_tag = going_area.find('span', class_='city-airport')
            dpt_airport = dpt_airport_tag.text.strip() if dpt_airport_tag else 'N/A'

        return_area = flight.find('div', class_='return-area')
        if return_area:
            arr_time_tag = return_area.find('span', class_='sch-time')
            arr_time = arr_time_tag.text.strip() if arr_time_tag else 'N/A'

            arr_airport_tag = return_area.find('span', class_='city-airport2')
            arr_airport = arr_airport_tag.text.strip() if arr_airport_tag else 'N/A'

        duration, transfers = 'N/A', 'N/A'
        flt_term = flight.find('div', class_='flt-term')
        if flt_term:
            duration_tag = flt_term.find('div', class_='flt-term-top')
            if duration_tag and duration_tag.div:
                duration = duration_tag.div.text.strip().split('\n')[0]

            transfer_tag = flt_term.find('span', class_='flt-term-transit')
            transfers = transfer_tag.text.strip() if transfer_tag else 'N/A'

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