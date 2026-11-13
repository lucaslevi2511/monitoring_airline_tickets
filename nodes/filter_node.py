from state import FlightState

from flight_service import (filter_flight_options,)

def filter_flights(state: FlightState):

    filtered = filter_flight_options(
        flights=state["flights"],
        max_price=state["max_price"],
        max_stops=state["max_stops"],
        max_duration_minutes=state["max_duration_minutes"],
    )

    return {
        "filtered_flights": filtered
    }