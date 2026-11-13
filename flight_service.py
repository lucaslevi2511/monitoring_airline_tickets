from state import Flight, RankedFlight
import serpapi
import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

# Normalizacao dos dados da API

def normalize_serpapi_flights(
    results: dict,
    departure_date: str,
) -> list[Flight]:

    options = (
        results.get("best_flights", [])
        + results.get("other_flights", [])
    )

    normalized_flights = []

    for option in options:

        segments = option.get(
            "flights",
            []
        )

        if not segments:
            continue

        first_segment = segments[0]
        last_segment = segments[-1]

        departure_airport = (
            first_segment["departure_airport"]
        )

        arrival_airport = (
            last_segment["arrival_airport"]
        )

        flight_numbers = [segment["flight_number"]
            for segment in segments
        ]

        travel_class = first_segment.get("travel_class", "Unknown",)

        connection_airports = [layover["id"]
            for layover in option.get("layovers", [])
        ]
        
        flight = {
            "airline": first_segment["airline"],

            "origin": departure_airport["id"],
            "destination": arrival_airport["id"],

            "departure_date": departure_date,

            "departure": departure_airport["time"],
            "arrival": arrival_airport["time"],

            "price": float(option["price"]),

            "duration_minutes": int(option["total_duration"]),

            "stops": max(len(segments) - 1,0,),

           "flight_numbers": flight_numbers,

            "travel_class": travel_class,

            "connection_airports": connection_airports,
        }

        normalized_flights.append(flight)

    return normalized_flights

# Busca

TRAVEL_CLASS_MAP = {
    "economy": "1",
    "premium_economy": "2",
    "business": "3",
    "first": "4",
}

def search_api_flights(
    origin: str,
    destination: str,
    departure_date: str,
    trip_type: str,
    travel_class: str,
    return_date: str | None = None,
) -> list[Flight]:

    client = serpapi.Client(
        api_key=SERPAPI_KEY
    )
    travel_class_code = TRAVEL_CLASS_MAP.get(travel_class)

    if not travel_class_code:
        raise ValueError(f"Classe de viagem inválida: {travel_class}")
    
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "currency": "BRL",
        "hl": "pt-BR",
        "gl": "br",
        "travel_class": travel_class_code,
    }
    if trip_type == "round_trip":

        if not return_date:
            raise ValueError("Round trip requires a return date.")

        params["type"] = "1"
        params["return_date"] = return_date
    else:
        params["type"] = "2"

    results = client.search(params)
    return normalize_serpapi_flights(results= results, departure_date=departure_date)
# Filtragem

def filter_flight_options(flights: list[Flight], max_price: float | None, max_stops: int | None, max_duration_minutes: int | None,) -> list[Flight]:

    filtered = []

    for flight in flights:

        if (max_price is not None and flight["price"] > max_price):
            continue

        if (max_stops is not None and flight["stops"] > max_stops):
            continue

        if (max_duration_minutes is not None and flight["duration_minutes"] > max_duration_minutes):
            continue

        filtered.append(flight)

    return filtered

# Ranqueamento

def rank_flight_options(
    flights: list[Flight],
    price_weight: float,
    duration_weight: float,
    stops_weight: float,
    class_weight: float,
) -> list[RankedFlight]:

    if not flights:
        return []

    ranked = []

    max_price = max(
        flight["price"]
        for flight in flights
    )

    max_duration = max(
        flight["duration_minutes"]
        for flight in flights
    )
    CLASS_SCORES = {"Economy": 0.25, "Premium Economy": 0.50, "Business": 0.75, "First": 1.00,}
    for flight in flights:

        price_score = (
            1 - flight["price"] / max_price
        )

        duration_score = (
            1
            - flight["duration_minutes"] / max_duration
        )

        stops_score = (
            1 / (flight["stops"] + 1)
        )

        class_score = CLASS_SCORES.get(flight["travel_class"], 0.25,)

        score = (
            price_weight * price_score
            + duration_weight * duration_score
            + stops_weight * stops_score
            + class_weight * class_score
        )

        ranked.append({
            **flight,
            "score": round(score, 3),
        })

    ranked.sort(
        key=lambda flight: flight["score"],
        reverse=True,
    )

    return ranked