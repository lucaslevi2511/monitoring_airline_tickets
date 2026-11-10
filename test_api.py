from flight_service import search_api_flights


flights = search_api_flights(
    origin="FOR",
    destination="GRU",
    departure_date="2026-12-10",
)


for flight in flights:

    print(
        flight["airline"],
        "|",
        flight["origin"],
        "->",
        flight["destination"],
        "| R$",
        flight["price"],
        "|",
        flight["duration_minutes"],
        "min |",
        flight["stops"],
        "escala(s)"
    )