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
        "no dia 20 de novembro de 2026 e voltar dia 25 de novembro de 2026 "
        "Quero gastar no máximo 4000 reais, "
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
print("Tipo de viagem:", result["trip_type"])
print("Data de ida:", result["departure_date"])

if result["return_date"]:
    print("Data de volta:", result["return_date"])

print("Preço máximo:", result["max_price"])
print("Máximo de escalas:", result["max_stops"])
print(
    "Duração máxima:",
    result["max_duration_minutes"],
    "minutos",
)

print("IATA origem:", result["origin_iata"])
print("IATA destino:", result["destination_iata"])

print("\n--- RANKING ---")

for position, flight in enumerate(
    result["ranked_flights"],
    start=1,
):

    print(f"\n{position}. {flight['airline']}")

    print(
        "Voo(s):",
        ", ".join(
            flight["flight_numbers"]
        ),
    )

    print(
        "Classe:",
        flight["travel_class"],
    )

    print(
        f"Horário: "
        f"{flight['departure']} -> "
        f"{flight['arrival']}"
    )

    print(
        f"Rota: "
        f"{flight['origin']} -> "
        f"{flight['destination']}"
    )

    if flight["connection_airports"]:
        print(
            "Conexões:",
            ", ".join(
                flight["connection_airports"]
            ),
        )
    else:
        print("Conexões: Direto")

    print(
        f"Preço: R$ {flight['price']:.2f}"
    )

    print(
        f"Duração: "
        f"{flight['duration_minutes']} min"
    )

    print(
        f"Escalas: "
        f"{flight['stops']}"
    )

    print(
        f"Score: "
        f"{flight['score']}"
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