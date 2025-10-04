from bs4 import BeautifulSoup

def parse_flight_data(soup: BeautifulSoup) -> list[dict]:
    """Parses the flight data from the BeautifulSoup object."""
    flight_areas = soup.find_all('div', class_='flight-area')
    parsed_flights = []

    for flight in flight_areas:
        provider_name_tag = flight.find('div', class_='flight-summary-hdg')
        provider_name = provider_name_tag.text.strip() if provider_name_tag else 'N/A'

        price_tag = flight.find('span', class_='price')
        price = price_tag.text.strip() if price_tag else 'N/A'

        sch_header_tag = flight.find('div', class_='sch-header')
        trip_type = 'N/A'
        if sch_header_tag:
            span_tag = sch_header_tag.find('span')
            if span_tag:
                trip_type = span_tag.text.strip()

        going_area = flight.find('div', class_='going-area')
        dpt_time, dpt_airport, arr_time, arr_airport = 'N/A', 'N/A', 'N/A', 'N/A'
        if going_area:
            dpt_time_tag = going_area.find('div', class_='dpt-time')
            dpt_time = dpt_time_tag.text.strip() if dpt_time_tag else 'N/A'

            dpt_airport_tag = going_area.find('div', class_='dpt-airport')
            dpt_airport = dpt_airport_tag.text.strip() if dpt_airport_tag else 'N/A'

            arr_time_tag = going_area.find('div', class_='arr-time')
            arr_time = arr_time_tag.text.strip() if arr_time_tag else 'N/A'

            arr_airport_tag = going_area.find('div', class_='arr-airport')
            arr_airport = arr_airport_tag.text.strip() if arr_airport_tag else 'N/A'

        flt_term_tag = flight.find('div', class_='flt-term')
        duration, transfers = 'N/A', 'N/A'
        if flt_term_tag:
            hour_tag = flt_term_tag.find('span', class_='hour')
            duration = hour_tag.text.strip() if hour_tag else 'N/A'

            transfer_tag = flt_term_tag.find('span', class_='transfer')
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