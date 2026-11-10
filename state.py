from typing import TypedDict


class Flight(TypedDict):
    airline: str
    origin: str
    destination: str
    departure: str
    arrival: str
    price: float
    duration_minutes: int
    stops: int


class RankedFlight(Flight):
    score: float


class FlightState(TypedDict):
    user_request: str
    origin: str
    destination: str
    departure_date: str

    max_price: float
    max_stops: int
    max_duration_minutes: int

    flights: list[Flight]
    filtered_flights: list[Flight]
    ranked_flights: list[RankedFlight]

    price_weight: float 
    duration_weight: float 
    stops_weight: float

    approved: bool

    review_feedback: str
    review_interpretation: str

    review_attempts: int