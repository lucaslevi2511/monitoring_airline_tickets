from langgraph.graph import StateGraph, START

from state import FlightState
from nodes import (parse_user_request,interpret_preferences,search_flights,filter_flights,rank_flights,review_flights,)


builder = StateGraph(FlightState)

builder.add_node("input", parse_user_request)
builder.add_node("preferences", interpret_preferences)
builder.add_node("search", search_flights)
builder.add_node("filter", filter_flights)
builder.add_node("ranking", rank_flights)
builder.add_node("review", review_flights)

builder.add_edge(START, "input")
builder.add_edge("input", "preferences")
builder.add_edge("preferences", "search")
builder.add_edge("search", "filter")
builder.add_edge("filter", "ranking")
builder.add_edge("ranking", "review")

graph = builder.compile()


result = graph.invoke({
    "user_request": (
        "Quero viajar de Fortaleza para Brasília no dia 20 de dezembro de 2026. "
        "Não me importo em pagar um pouco mais, mas quero conforto e evitar conexões."
    ),
    "flights": [],
    "filtered_flights": [],
    "ranked_flights": [],
    "approved": False,
    "review_feedback": "",
    "review_interpretation": "",
    "qualitative_reviews": [],
    "best_options": [],
    "discard_options": [],
    "review_conclusion": "",
    "review_attempts": 0,
})


# Preferências

print("\n=== PREFERÊNCIAS ===")
print(
    f"Preço: {result['price_priority']} | "
    f"Duração: {result['duration_priority']} | "
    f"Escalas: {result['stops_priority']} | "
    f"Conforto: {result['class_priority']}"
)
print(
    f"Pesos: {result['price_weight']:.2f} | "
    f"{result['duration_weight']:.2f} | "
    f"{result['stops_weight']:.2f} | "
    f"{result['class_weight']:.2f}"
)
print(result["preference_reasoning"])


# Busca

print("\n=== BUSCA ===")

trip = "Ida e volta" if result["trip_type"] == "round_trip" else "Somente ida"

route = (
    f"{result['origin']} ({result['origin_iata']}) → "
    f"{result['destination']} ({result['destination_iata']})"
)

dates = f"{trip} | Ida: {result['departure_date']}"
if result["return_date"]:
    dates += f" | Volta: {result['return_date']}"

price_limit = (
    f"R$ {result['max_price']:.2f}"
    if result["max_price"] is not None
    else "sem limite"
)

stops_limit = (
    str(result["max_stops"])
    if result["max_stops"] is not None
    else "sem limite"
)

duration_limit = (
    f"{result['max_duration_minutes']} min"
    if result["max_duration_minutes"] is not None
    else "sem limite"
)

travel_class = result["travel_class"] or "todas"

print(route)
print(dates)
print(
    f"Limites: preço {price_limit} | "
    f"escalas {stops_limit} | "
    f"duração {duration_limit}"
)
print(
    f"Classe: {travel_class} | "
    f"Encontrados: {len(result['flights'])} | "
    f"Filtrados: {len(result['filtered_flights'])}"
)


# Ranking

print("\n=== MELHORES VOOS ===")

for i, flight in enumerate(result["ranked_flights"][:5], start=1):
    numbers = ", ".join(flight["flight_numbers"])
    connections = ", ".join(flight["connection_airports"]) or "Direto"

    print(
        f"{i}. {flight['airline']} ({numbers}) | "
        f"R$ {flight['price']:.2f} | "
        f"{flight['duration_minutes']} min | "
        f"{connections} | "
        f"{flight['travel_class']} | "
        f"Score {flight['score']}"
    )
    print(f"   {flight['departure']} → {flight['arrival']}")


# Review

print("\n=== ANÁLISE ===")

for review in result["qualitative_reviews"]:
    numbers = ", ".join(review["flight_numbers"])
    positives = "; ".join(review["positives"])
    negatives = "; ".join(review["negatives"])

    print(f"\n{numbers}")
    print(f"+ {positives}")

    if negatives:
        print(f"- {negatives}")

    print(f"→ {review['observation']}")


# Conclusão

print("\n=== CONCLUSÃO ===")
print(
    "Melhores:",
    ", ".join(result["best_options"]) or "Nenhuma"
)
print(
    "Descartar:",
    ", ".join(result["discard_options"]) or "Nenhuma"
)
print(result["review_conclusion"])