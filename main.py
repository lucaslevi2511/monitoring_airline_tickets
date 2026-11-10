from langgraph.graph import (
    StateGraph,
    START,
)

from state import FlightState

from nodes import (
    parse_user_request,
    search_flights,
    filter_flights,
    rank_flights,
    review_flights,
)

builder = StateGraph(FlightState)

builder.add_node(
    "input",
    parse_user_request,
)

builder.add_node(
    "search",
    search_flights,
)

builder.add_node(
    "filter",
    filter_flights,
)

builder.add_node(
    "ranking",
    rank_flights,
)

builder.add_node(
    "review",
    review_flights,
)

builder.add_edge(
    START,
    "input",
)

builder.add_edge(
    "input",
    "search",
)

builder.add_edge(
    "search",
    "filter",
)

builder.add_edge(
    "filter",
    "ranking",
)

builder.add_edge(
    "ranking",
    "review",
)

graph = builder.compile()

result = graph.invoke({

    "user_request": (
        "Quero viajar de Fortaleza para São Paulo "
        "no dia 20 de dezembro de 2026 e voltar dia 25 de dezembro de 2026 "
        "Quero gastar no máximo 4000 reais, "
        "aceito no máximo uma escala "
        "e não quero viagens com mais de 7 horas."
    ),

    "flights": [],
    "filtered_flights": [],
    "ranked_flights": [],

    "price_weight": 0.40,
    "duration_weight": 0.25,
    "stops_weight": 0.20,
    "class_weight": 0.15,

    "approved": False,
    "review_feedback": "",
    "qualitative_reviews": [],
    "best_options": [],
    "discard_options": [],
    "review_conclusion": "",
    "review_attempts": 0,
})

print("\n=== BUSCA ===")

trip_label = (
    "Ida e volta"
    if result["trip_type"] == "round_trip"
    else "Somente ida"
)

print(
    f"{result['origin']} ({result['origin_iata']}) "
    f"→ {result['destination']} ({result['destination_iata']})"
)

print(
    f"{trip_label} | "
    f"Ida: {result['departure_date']}"
    + (
        f" | Volta: {result['return_date']}"
        if result["return_date"]
        else ""
    )
)

print(
    f"Limites: R$ {result['max_price']:.2f} | "
    f"{result['max_stops']} escala(s) | "
    f"{result['max_duration_minutes']} min"
)


print("\n=== MELHORES VOOS ===")

for position, flight in enumerate(
    result["ranked_flights"][:10],
    start=1,
):

    flight_numbers = ", ".join(
        flight["flight_numbers"]
    )

    connections = (
        ", ".join(flight["connection_airports"])
        if flight["connection_airports"]
        else "Direto"
    )

    print(
        f"\n{position}. {flight['airline']} "
        f"({flight_numbers})"
    )

    print(
        f"   R$ {flight['price']:.2f} | "
        f"{flight['duration_minutes']} min | "
        f"{connections} | "
        f"Score {flight['score']}"
    )

    print(
        f"   {flight['departure']} "
        f"→ {flight['arrival']} | "
        f"{flight['travel_class']}"
    )


print("\n=== ANÁLISE ===")

for review in result["qualitative_reviews"]:

    flight_numbers = ", ".join(
        review["flight_numbers"]
    )

    positives = "; ".join(
        review["positives"]
    )

    negatives = "; ".join(
        review["negatives"]
    )

    print(f"\n{flight_numbers}")

    print(
        f"   + {positives}"
    )

    if negatives:
        print(
            f"   - {negatives}"
        )

    print(
        f"   → {review['observation']}"
    )


print("\n=== CONCLUSÃO ===")

print(
    "Melhores:",
    ", ".join(result["best_options"])
    if result["best_options"]
    else "Nenhuma destacada",
)

print(
    "Descartar:",
    ", ".join(result["discard_options"])
    if result["discard_options"]
    else "Nenhuma",
)

print(
    "\n",
    result["review_conclusion"],
    sep="",
)