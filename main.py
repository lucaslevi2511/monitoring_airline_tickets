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
        "no dia 10 de dezembro de 2026. "
        "Quero gastar no máximo 800 reais, "
        "aceito no máximo uma escala "
        "e não quero viagens com mais de 7 horas."
    ),

    "flights": [],
    "filtered_flights": [],
    "ranked_flights": [],

    "price_weight": 0.50,
    "duration_weight": 0.30,
    "stops_weight": 0.20,

    "approved": False,
    "review_feedback": "",
    "review_interpretation": "",
    "review_attempts": 0,
})

print("\n--- SOLICITAÇÃO INTERPRETADA ---")

print("Origem:", result["origin"])
print("Destino:", result["destination"])
print("Data:", result["departure_date"])

print("Preço máximo:", result["max_price"])
print("Máximo de escalas:", result["max_stops"])
print(
    "Duração máxima:",
    result["max_duration_minutes"],
    "minutos",
)

print("\n--- RANKING ---")

for position, flight in enumerate(
    result["ranked_flights"],
    start=1,
):

    print(
        f"{position}. "
        f"{flight['airline']} | "
        f"R$ {flight['price']:.2f} | "
        f"{flight['duration_minutes']} min | "
        f"{flight['stops']} escala(s) | "
        f"Score: {flight['score']}"
    )


print("\n--- REVIEW ---")
print(result["review_feedback"])
print("\nPesos após review:")
print("\nPreço: ", result["price_weight"])
print("\nDuração: ", result["duration_weight"])
print("\nParadas: ", result["stops_weight"])
print("\n--- INTERPRETATION ---")
print(result["review_interpretation"])

print(
    "\nReview attempts:",
    result["review_attempts"]
)