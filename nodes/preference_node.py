from config import llm
from state import FlightState
from schemas.preference_schema import (
    PreferenceResult,
)

PRIORITY_VALUES = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

preference_llm = llm.with_structured_output(
    PreferenceResult,
    method="json_schema",
)

def priorities_to_weights(
    price: str,
    duration: str,
    stops: str,
    travel_class: str,
) -> dict:

    price_value = PRIORITY_VALUES[price]
    duration_value = PRIORITY_VALUES[duration]
    stops_value = PRIORITY_VALUES[stops]
    class_value = PRIORITY_VALUES[travel_class]

    total = (price_value + duration_value + stops_value + class_value)

    return {
        "price_weight": price_value / total,
        "duration_weight": duration_value / total,
        "stops_weight": stops_value / total,
        "class_weight": class_value / total,
    }

# PREFERENCE NODE

def interpret_preferences(state: FlightState):

    prompt = f"""
Você é um agente responsável por interpretar as preferências subjetivas
do usuário ao escolher uma passagem aérea.

Solicitação:

{state["user_request"]}

Avalie quatro critérios:

- preço
- duração
- escalas
- classe/conforto

Para cada critério, retorne:

- low
- medium
- high

Não determine restrições obrigatórias.
Outro agente já é responsável por isso.

Seu papel é interpretar o que o usuário VALORIZA.

Exemplo 1:

"Não me importo em pagar um pouco mais,
quero conforto e prefiro evitar conexões."

Interpretação esperada:

price_priority = low
duration_priority = medium
stops_priority = high
class_priority = high


Exemplo 2:

"Quero gastar o mínimo possível.
Não me importo com conexões nem com conforto."

Interpretação esperada:

price_priority = high
duration_priority = medium
stops_priority = low
class_priority = low


Exemplo 3:

"Quero chegar o mais rápido possível
e prefiro voo direto."

Interpretação esperada:

price_priority = medium
duration_priority = high
stops_priority = high
class_priority = low


Os exemplos são apenas referências.

Interprete a solicitação atual sem copiar automaticamente
nenhum dos exemplos.

Explique brevemente sua interpretação em português brasileiro.
"""

    preferences = preference_llm.invoke(prompt)

    weights = priorities_to_weights(
        price=preferences.price_priority,
        duration=preferences.duration_priority,
        stops=preferences.stops_priority,
        travel_class=preferences.class_priority,
    )

    return {
        "price_priority": preferences.price_priority,
        "duration_priority": preferences.duration_priority,
        "stops_priority": preferences.stops_priority,
        "class_priority": preferences.class_priority,

        "preference_reasoning": preferences.reasoning,

        **weights,
    }