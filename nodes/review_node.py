from typing import Literal
from langgraph.graph import END
from langgraph.types import Command
from config import llm
from state import FlightState
from schemas.review_schema import (
    ReviewResult,
)


MAX_REVIEW_ATTEMPTS = 3


review_llm = llm.with_structured_output(
    ReviewResult,
    method="json_schema",
)

def review_flights(
    state: FlightState
) -> Command[Literal["ranking", "__end__"]]:

    attempts = state["review_attempts"] + 1
    ranked = state["ranked_flights"]

    # Nenhum voo válido disponível
    if not ranked:
        return Command(
            update={
                "approved": False,
                "review_feedback": (
                    "Nenhum voo satisfaz as restrições informadas."
                ),
                "review_interpretation": (
                    "Não há opções válidas disponíveis para análise."
                ),
                "review_attempts": attempts,
            },
            goto=END,
        )

    # Analisa os 10 melhores voos
    top_flights = ranked[:5]

    flight_text = ""

    for position, flight in enumerate(
        top_flights,
        start=1,
    ):
        flight_text += f"""
Voo {position}

Número(s) do voo:
{", ".join(flight["flight_numbers"])}

Companhia aérea:
{flight["airline"]}

Classe:
{flight["travel_class"]}

Rota:
{flight["origin"]} -> {flight["destination"]}

Partida:
{flight["departure"]}

Chegada:
{flight["arrival"]}

Preço:
R$ {flight["price"]:.2f}

Duração:
{flight["duration_minutes"]} minutos

Escalas:
{flight["stops"]}

Conexões:
{", ".join(flight["connection_airports"])
if flight["connection_airports"]
else "Voo direto"}

Score do ranking:
{flight["score"]}

---
"""

    prompt = f"""
Você é um agente revisor especializado em recomendações de voos.

Um algoritmo determinístico já realizou o ranqueamento utilizando
as preferências interpretadas anteriormente do usuário.

Os critérios utilizados foram:

- preço
- duração
- número de escalas
- classe/conforto

Pesos atuais:

Preço:
{state["price_weight"]}

Duração:
{state["duration_weight"]}

Escalas:
{state["stops_weight"]}

Classe/conforto:
{state["class_weight"]}

O ranking numérico deve ser tratado como a ordenação principal.

Seu papel NÃO é substituir arbitrariamente o ranking.

Seu objetivo é analisar qualitativamente os resultados e verificar
se o ranking é coerente com as características reais dos voos.

Analise:

{flight_text}

Para cada voo:

1. Identifique seus principais pontos positivos.

2. Identifique seus principais pontos negativos ou trade-offs.

3. Considere:
   - preço
   - duração
   - número de escalas
   - classe
   - aeroportos de conexão
   - horário de partida
   - horário de chegada

4. Considere os pesos utilizados no ranking.

5. Compare o voo com alternativas próximas na classificação.

6. Identifique quando um voo é claramente dominado por outro.

Exemplos de observações relevantes:

- preço menor, mas horário inconveniente
- preço maior compensado por classe superior
- voo direto que justifica preço maior
- conexão que reduz a atratividade da opção
- duração significativamente menor
- voo claramente dominado por outra alternativa
- boa relação entre preço, conforto e duração

Não invente informações que não estejam presentes nos dados.

Depois da análise:

- identifique os voos que apresentam melhor valor geral
- identifique os voos que podem ser descartados
- apresente uma conclusão justificando essas escolhas

Só coloque um voo em discard_options quando existir outra opção
claramente melhor ou equivalente com menos desvantagens.

AVALIAÇÃO DO RANKING:

Se o ranking estiver coerente com os pesos e com as características
dos voos, use:

approved = true

Nesse caso, mantenha os pesos atuais aproximadamente como estão.

Se existir uma inconsistência relevante entre as prioridades
do usuário e o resultado produzido pelo ranking, use:

approved = false

Nesse caso, sugira novos valores para:

- price_weight
- duration_weight
- stops_weight
- class_weight

Os novos pesos devem refletir melhor as preferências do usuário.

IMPORTANTE:

Todas as respostas textuais devem ser escritas em português brasileiro.

Não utilize inglês nos campos de análise, feedback,
observações ou conclusão.
"""

    review = review_llm.invoke(prompt)

    if review.approved:
        return Command(
            update={
                "approved": True,

                "review_feedback":
                    review.feedback,

                "qualitative_reviews": [
                    item.model_dump()
                    for item in review.flight_reviews
                ],

                "best_options":
                    review.best_options,

                "discard_options":
                    review.discard_options,

                "review_conclusion":
                    review.final_conclusion,

                "review_interpretation":
                    review.final_conclusion,

                "review_attempts":
                    attempts,
            },
            goto=END,
        )

    if attempts >= MAX_REVIEW_ATTEMPTS:
        return Command(
            update={
                "approved": False,

                "review_feedback": (
                    "Número máximo de revisões atingido. "
                    f"Última avaliação: {review.feedback}"
                ),

                "review_interpretation":
                    review.final_conclusion,

                "review_conclusion":
                    review.final_conclusion,

                "qualitative_reviews": [
                    item.model_dump()
                    for item in review.flight_reviews
                ],

                "best_options":
                    review.best_options,

                "discard_options":
                    review.discard_options,

                "review_attempts":
                    attempts,
            },
            goto=END,
        )

    total_weight = (
        review.price_weight
        + review.duration_weight
        + review.stops_weight
        + review.class_weight
    )

    if total_weight > 0:

        price_weight = (
            review.price_weight
            / total_weight
        )

        duration_weight = (
            review.duration_weight
            / total_weight
        )

        stops_weight = (
            review.stops_weight
            / total_weight
        )

        class_weight = (
            review.class_weight
            / total_weight
        )

    else:

        # Caso o Reviewer retorne pesos inválidos,
        # mantém os pesos anteriores.

        price_weight = (
            state["price_weight"]
        )

        duration_weight = (
            state["duration_weight"]
        )

        stops_weight = (
            state["stops_weight"]
        )

        class_weight = (
            state["class_weight"]
        )

    # ==========================
    # RETORNA PARA O RANKING
    # ==========================

    return Command(
        update={
            "approved": False,

            "review_feedback":
                review.feedback,

            "review_interpretation":
                review.final_conclusion,

            "review_conclusion":
                review.final_conclusion,

            "qualitative_reviews": [
                item.model_dump()
                for item in review.flight_reviews
            ],

            "best_options":
                review.best_options,

            "discard_options":
                review.discard_options,

            "price_weight":
                price_weight,

            "duration_weight":
                duration_weight,

            "stops_weight":
                stops_weight,

            "class_weight":
                class_weight,

            "review_attempts":
                attempts,
        },

        goto="ranking",
    )