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

        airline_name_tag = flight.find('span', class_='sch-airline-name-sup')
        airline_name = airline_name_tag.text.strip() if airline_name_tag else 'N/A'

        dpt_date, dpt_time, dpt_airport = 'N/A', 'N/A', 'N/A'
        going_area = flight.find('div', class_='going-area')
        if going_area:
            dpt_date_tag = going_area.find('span', class_='sch-date')
            dpt_date = dpt_date_tag.text.strip() if dpt_date_tag else 'N/A'
            dpt_time_tag = going_area.find('span', class_='sch-time')
            dpt_time = dpt_time_tag.text.strip() if dpt_time_tag else 'N/A'
            dpt_airport_tag = going_area.find('span', class_='city-airport')
            dpt_airport = dpt_airport_tag.text.strip() if dpt_airport_tag else 'N/A'

        arr_date, arr_time, arr_airport = 'N/A', 'N/A', 'N/A'
        return_area = flight.find('div', class_='return-area')
        if return_area:
            arr_date_tag = return_area.find('span', class_='sch-date')
            arr_date = arr_date_tag.text.strip() if arr_date_tag else 'N/A'
            arr_time_tag = return_area.find('span', class_='sch-time')
            arr_time = arr_time_tag.text.strip() if arr_time_tag else 'N/A'
            arr_airport_tag = return_area.find('span', class_='city-airport2')
            arr_airport = arr_airport_tag.text.strip() if arr_airport_tag else 'N/A'

        duration, transfers_str = 'N/A', 'N/A'
        flt_term = flight.find('div', class_='flt-term')
        if flt_term:
            duration_tag = flt_term.find('div', class_='flt-term-top')
            if duration_tag and duration_tag.div:
                duration = duration_tag.div.text.strip().split('\n')[0]

            transfer_tag = flt_term.find('span', class_='flt-term-transit')
            transfers_str = transfer_tag.text.strip() if transfer_tag else 'N/A'

        plane_model_tag = flight.find('li', class_='amenity-equipment')
        plane_model = plane_model_tag.find_all('span')[2].text.strip() if plane_model_tag and len(plane_model_tag.find_all('span')) > 2 else 'N/A'

        baggage_info = []
        baggage_list = flight.find('ul', class_='flight-summary-info-list')
        if baggage_list:
            for item in baggage_list.find_all('li'):
                baggage_info.append(item.text.strip())

        transfer_airports = []
        transfer_tags = flight.find_all('dd', class_='airport transfer')
        for tag in transfer_tags:
            airport_name_tag = tag.find('a', class_='airport')
            if airport_name_tag:
                transfer_airports.append(airport_name_tag.text.strip())

        flight_data = {
            "provider_name": provider_name,
            "price": price,
            "trip_type": trip_type,
            "airline": airline_name,
            "departure": {
                "date": dpt_date,
                "time": dpt_time,
                "airport": dpt_airport
            },
            "arrival": {
                "date": arr_date,
                "time": arr_time,
                "airport": arr_airport
            },
            "duration": duration,
            "transfers": {
                "count_str": transfers_str,
                "airports": transfer_airports
            },
            "plane_model": plane_model,
            "baggage": baggage_info
        }
        parsed_flights.append(flight_data)

    return parsed_flights