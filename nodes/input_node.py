from state import FlightState

from config import llm
from schemas.input_schema import FlightRequest


input_llm = llm.with_structured_output(
    FlightRequest,
    method="json_schema",
)


def parse_user_request(state: FlightState):

    prompt = f"""
Você é responsável por extrair dados objetivos e restrições explícitas
de uma solicitação de busca de voos domésticos no Brasil.

Solicitação:

{state["user_request"]}

Extraia:

- cidade de origem
- cidade de destino
- código IATA do principal aeroporto da origem
- código IATA do principal aeroporto do destino
- tipo de viagem: one_way ou round_trip
- data de ida
- data de volta, se houver
- preço máximo, apenas se explicitamente informado
- número máximo de escalas, apenas se explicitamente informado
- duração máxima, apenas se explicitamente informada
- classe de viagem, apenas se explicitamente informada

Regras:

- datas devem estar no formato YYYY-MM-DD
- durações devem estar em minutos
- se não houver data de volta, use null
- se não houver limite de preço, use null
- se não houver limite de escalas, use null
- se não houver limite de duração, use null
- se não houver classe explicitamente solicitada, use null

Mapeamento de classes:

- econômica → economy
- premium economy → premium_economy
- executiva → business
- primeira classe → first

Não transforme preferências subjetivas em restrições.

Exemplos:

"quero conforto"
→ travel_class = null

"prefiro evitar conexões"
→ max_stops = null

"quero economizar"
→ max_price = null

"quero uma viagem rápida"
→ max_duration_minutes = null

Por outro lado:

"quero classe executiva"
→ travel_class = business

"não aceito escalas"
→ max_stops = 0

"até R$ 1500"
→ max_price = 1500

"no máximo 5 horas"
→ max_duration_minutes = 300

Extraia apenas o que foi explicitamente informado.
Não invente valores.
"""

    request = input_llm.invoke(prompt)

    return {
        "origin": request.origin,
        "destination": request.destination,

        "origin_iata": request.origin_iata,
        "destination_iata": request.destination_iata,

        "trip_type": request.trip_type,

        "departure_date": request.departure_date,
        "return_date": request.return_date,

        "max_price": request.max_price,
        "max_stops": request.max_stops,
        "max_duration_minutes": request.max_duration_minutes,

        "travel_class": request.travel_class,
    }