from state import FlightState
from flight_service import (search_api_flights,)

TRAVEL_CLASSES = [
    "economy",
    "premium_economy",
    "business",
    "first",
]


def search_flights(state: FlightState):
    
    if state["travel_class"] is not None:

        flights = search_api_flights(
            origin=state["origin_iata"],
            destination=state["destination_iata"],
            departure_date=state["departure_date"],
            trip_type=state["trip_type"],
            return_date=state["return_date"],
            travel_class=state["travel_class"],
        )

    else:

        flights = []

        for travel_class in TRAVEL_CLASSES:

            class_flights = search_api_flights(
                origin=state["origin_iata"],
                destination=state["destination_iata"],
                departure_date=state["departure_date"],
                trip_type=state["trip_type"],
                return_date=state["return_date"],
                travel_class=travel_class,
            )

            flights.extend(class_flights)

    return {
        "flights": flights
    }