from typing import TypedDict


class Flight(TypedDict):
    airline: str
    origin: str
    destination: str

    departure_date: str
    departure: str
    arrival: str

    price: float
    duration_minutes: int
    stops: int

    flight_numbers: list[str]
    travel_class: str
    connection_airports: list[str]


class RankedFlight(Flight):
    score: float


class FlightState(TypedDict):

    user_request: str

    # INPUT
    origin: str
    destination: str
    origin_iata: str
    destination_iata: str

    trip_type: str
    departure_date: str
    return_date: str | None

    max_price: float | None
    max_stops: int | None
    max_duration_minutes: int | None
    travel_class: str | None

    # PREFERENCES
    price_priority: str
    duration_priority: str
    stops_priority: str
    class_priority: str

    preference_reasoning: str

    price_weight: float
    duration_weight: float
    stops_weight: float
    class_weight: float

    # FLIGHTS
    flights: list[Flight]
    filtered_flights: list[Flight]
    ranked_flights: list[RankedFlight]

    # REVIEW
    approved: bool
    review_feedback: str
    review_interpretation: str
    review_attempts: int

    qualitative_reviews: list[dict]
    best_options: list[str]
    discard_options: list[str]
    review_conclusion: str