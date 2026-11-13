from state import FlightState

from flight_service import (rank_flight_options,)

def rank_flights(state: FlightState):

    ranked = rank_flight_options(
        flights=state["filtered_flights"],
        price_weight=state["price_weight"],
        duration_weight=state["duration_weight"],
        stops_weight=state["stops_weight"],
        class_weight=state["class_weight"]
    )

    return {
        "ranked_flights": ranked
    }