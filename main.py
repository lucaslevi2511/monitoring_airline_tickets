from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from state import FlightState

from nodes import (
    search_flights,
    filter_flights,
    rank_flights,
    review_flights,
)



builder = StateGraph(FlightState)


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
    "origin": "Fortaleza",
    "destination": "São Paulo",
    "departure_date": "2026-12-10",

    "max_price": 800,
    "max_stops": 1,
    "max_duration_minutes": 420,

    "flights": [],
    "filtered_flights": [],
    "ranked_flights": [],

    "approved": False,
    "review_feedback": "",
    "review_attempts": 0,
    "review_interpretation": "",
})


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

print("\n--- INTERPRETATION ---")
print(result["review_interpretation"])

print(
    "\nReview attempts:",
    result["review_attempts"]
)