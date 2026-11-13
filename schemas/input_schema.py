from pydantic import BaseModel


class FlightRequest(BaseModel):
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