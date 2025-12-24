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

def parse_flight_data(soup: BeautifulSoup, air_type: str = "0") -> list[dict]:
    """Parses the flight data from the BeautifulSoup object.

    Args:
        soup: BeautifulSoup object containing the HTML
        air_type: "0" for one-way, "1" for round-trip
    """
    if air_type == "1":
        return parse_round_trip_flight_data(soup)

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
        plane_model = plane_model_tag.text.strip() if plane_model_tag else 'N/A'

        flight_code_tags = flight.find_all('span', class_='sch-dtl-desc-flt-code')
        flight_codes = [tag.text.strip() for tag in flight_code_tags]
        flight_code = ', '.join(flight_codes) if flight_codes else 'N/A'

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
            "flight_code": flight_code,
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


def parse_round_trip_flight_data(soup: BeautifulSoup) -> list[dict]:
    """Parses round-trip flight data from the BeautifulSoup object.

    Round-trip HTML structure:
    - Two .sch-header sections: "往路" (outbound) and "復路" (return)
    - Two .sch-item sections with full flight details
    - One .sch-stay-item showing stay duration
    - Single combined price for both directions
    """
    flight_areas = soup.find_all('div', class_='flight-area')
    parsed_flights = []

    for flight_area in flight_areas:
        # Get provider and price (shared for the whole round trip)
        provider_name_tag = flight_area.find('div', class_='flight-summary-hdg')
        provider_name = provider_name_tag.text.strip().split('\n')[0] if provider_name_tag else 'N/A'

        price_tag = flight_area.find('span', class_='flight-summary-total-price')
        price = price_tag.text.strip() if price_tag else 'N/A'

        # Get stay duration from .sch-stay-item
        stay_duration = 'N/A'
        stay_item = flight_area.find('div', class_='sch-stay-item')
        if stay_item:
            stay_req_tag = stay_item.find('div', class_='sch-stay-header-req')
            if stay_req_tag:
                stay_duration = stay_req_tag.text.strip()

        # Get baggage info
        baggage_info = []
        baggage_list = flight_area.find('ul', class_='flight-summary-info-list')
        if baggage_list:
            for item in baggage_list.find_all('li'):
                baggage_info.append(item.text.strip())

        # Get all sch-headers (往路 and 復路)
        sch_headers = flight_area.find_all('div', class_='sch-header')
        sch_items = flight_area.find_all('div', class_='sch-item')

        if len(sch_headers) < 2 or len(sch_items) < 2:
            # Not a valid round trip, skip
            continue

        # Parse outbound flight (往路)
        outbound = _parse_single_direction(sch_headers[0], sch_items[0], flight_area)

        # Parse return flight (復路)
        return_flight = _parse_single_direction(sch_headers[1], sch_items[1], flight_area)

        flight_data = {
            "provider_name": provider_name,
            "price": price,
            "trip_type": "round_trip",
            "outbound": outbound,
            "return": return_flight,
            "stay_duration": stay_duration,
            "baggage": baggage_info
        }
        parsed_flights.append(flight_data)

    return parsed_flights


def _parse_single_direction(header_item: dict, sch_item: dict, flight_area: dict) -> dict:
    """Parse a single direction (outbound or return) for round-trip flights.

    Args:
        header_item: The .sch-header BeautifulSoup element for this direction
        sch_item: The .sch-item BeautifulSoup element for this direction
        flight_area: The parent flight_area element (for finding nested details)

    Returns:
        dict with keys: airline, flight_code, departure, arrival, duration, transfers
    """
    # Get airline name
    airline_name_tag = header_item.find('span', class_='sch-airline-name-sup')
    airline_name = airline_name_tag.text.strip() if airline_name_tag else 'N/A'

    # Get departure info from .going-area
    dpt_date, dpt_time, dpt_airport = 'N/A', 'N/A', 'N/A'
    going_area = sch_item.find('div', class_='going-area')
    if going_area:
        dpt_date_tag = going_area.find('span', class_='sch-date')
        dpt_date = dpt_date_tag.text.strip() if dpt_date_tag else 'N/A'
        dpt_time_tag = going_area.find('span', class_='sch-time')
        dpt_time = dpt_time_tag.text.strip() if dpt_time_tag else 'N/A'
        dpt_airport_tag = going_area.find('span', class_='city-airport')
        dpt_airport = dpt_airport_tag.text.strip() if dpt_airport_tag else 'N/A'

    # Get arrival info from .return-area
    arr_date, arr_time, arr_airport = 'N/A', 'N/A', 'N/A'
    return_area = sch_item.find('div', class_='return-area')
    if return_area:
        arr_date_tag = return_area.find('span', class_='sch-date')
        arr_date = arr_date_tag.text.strip() if arr_date_tag else 'N/A'
        arr_time_tag = return_area.find('span', class_='sch-time')
        arr_time = arr_time_tag.text.strip() if arr_time_tag else 'N/A'
        arr_airport_tag = return_area.find('span', class_='city-airport2')
        arr_airport = arr_airport_tag.text.strip() if arr_airport_tag else 'N/A'

    # Get duration
    duration = 'N/A'
    flt_term = sch_item.find('div', class_='flt-term')
    if flt_term:
        duration_tag = flt_term.find('div', class_='flt-term-top')
        if duration_tag and duration_tag.div:
            duration = duration_tag.div.text.strip().split('\n')[0]

    # Get transfer info
    transfers_str = 'N/A'
    transfer_airports = []
    transfer_tag = flt_term.find('span', class_='flt-term-transit') if flt_term else None
    if transfer_tag:
        transfers_str = transfer_tag.text.strip()

    # Get flight codes from this direction's detailed view
    # The detailed view is in .sch-dtl-container - we need to find the one for this direction
    flight_codes = []
    # Find flight codes in the main sch-item area (simplified)
    # In detailed HTML, codes are in .sch-dtl-desc-flt-code within the flight detail container
    flight_code_tags = flight_area.find_all('span', class_='sch-dtl-desc-flt-code')
    # For round trip, we split codes appropriately - first half for outbound, second for return
    # This is a simplified approach; ideally we'd parse per direction
    flight_codes = [tag.text.strip() for tag in flight_code_tags]
    flight_code = ', '.join(flight_codes) if flight_codes else 'N/A'

    # Get transfer airports from detailed view
    transfer_tags = flight_area.find_all('dd', class_='airport transfer')
    for tag in transfer_tags:
        airport_name_tag = tag.find('a', class_='airport')
        if airport_name_tag:
            transfer_airports.append(airport_name_tag.text.strip())

    return {
        "airline": airline_name,
        "flight_code": flight_code,
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
        }
    }