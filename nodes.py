import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END
from langgraph.types import Command
from state import FlightState
from mocks import MOCK_FLIGHTS

# CONFIGURATION
MAX_REVIEW_ATTEMPTS = 3

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
    api_version="v1beta",
)

# STRUCTURED OUTPUT SCHEMAS

class FlightRequest(BaseModel):
    origin: str = Field(description="Brazilian origin city.")

    destination: str = Field(description="Brazilian destination city.")

    departure_date: str = Field(description="Departure date in YYYY-MM-DD format.")

    max_price: float = Field(description="Maximum price in Brazilian reais.")

    max_stops: int = Field(description="Maximum number of stops accepted.")

    max_duration_minutes: int = Field(description="Maximum total flight duration in minutes.")


class ReviewResult(BaseModel):
    approved: bool = Field(description="Whether the current ranking should be approved.")

    feedback: str = Field(description="Explanation of the review decision.")

    interpretation: str = Field(description="Short interpretation of the ranked flights.")

    price_weight: float = Field(description="Suggested importance of price, between 0 and 1.")

    duration_weight: float = Field(description="Suggested importance of duration, between 0 and 1.")

    stops_weight: float = Field(description="Suggested importance of number of stops, between 0 and 1.")

# STRUCTURED LLMs

input_llm = llm.with_structured_output(
    FlightRequest,
    method="json_schema",
)

review_llm = llm.with_structured_output(
    ReviewResult,
    method="json_schema",
)

# INPUT NODE

def parse_user_request(state: FlightState):

    prompt = f"""
You are responsible for extracting structured flight search information.

The user wants to search for a domestic flight in Brazil.

User request:

{state["user_request"]}

Extract:

- origin city
- destination city
- departure date
- maximum price
- maximum number of stops
- maximum total flight duration

Convert durations to minutes.

Convert the departure date to YYYY-MM-DD.

Do not invent information.
"""

    request = input_llm.invoke(prompt)

    return {
        "origin": request.origin,
        "destination": request.destination,
        "departure_date": request.departure_date,
        "max_price": request.max_price,
        "max_stops": request.max_stops,
        "max_duration_minutes": request.max_duration_minutes,
    }

# SEARCH NODE

def search_flights(state: FlightState):

    flights = [
        flight
        for flight in MOCK_FLIGHTS
        if (flight["origin"] == state["origin"] and flight["destination"] == state["destination"])
    ]

    return {
        "flights": flights
    }

# FILTER NODE

def filter_flights(state: FlightState):

    filtered = []

    for flight in state["flights"]:

        if flight["price"] > state["max_price"]:
            continue

        if flight["stops"] > state["max_stops"]:
            continue

        if (
            flight["duration_minutes"]
            > state["max_duration_minutes"]
        ):
            continue

        filtered.append(flight)

    return {
        "filtered_flights": filtered
    }

# RANKING NODE

def rank_flights(state: FlightState):

    flights = state["filtered_flights"]

    if not flights:
        return {
            "ranked_flights": []
        }

    ranked = []

    max_price = max(
        flight["price"]
        for flight in flights
    )

    max_duration = max(
        flight["duration_minutes"]
        for flight in flights
    )

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

        score = (
            state["price_weight"] * price_score
            + state["duration_weight"] * duration_score
            + state["stops_weight"] * stops_score
        )

        ranked.append({
            **flight,
            "score": round(score, 3),
        })

    ranked.sort(
        key=lambda flight: flight["score"],
        reverse=True,
    )

    return {
        "ranked_flights": ranked
    }

# REVIEW NODE

def review_flights(
    state: FlightState
) -> Command[Literal["ranking", "__end__"]]:

    attempts = state["review_attempts"] + 1
    ranked = state["ranked_flights"]

    # No valid flights
    if not ranked:
        return Command(
            update={
                "approved": False,
                "review_feedback": (
                    "No flights satisfy the restrictions."
                ),
                "review_interpretation": (
                    "No valid flight options were available for review."
                ),
                "review_attempts": attempts,
            },
            goto=END,
        )

    prompt = f"""
You are a flight ranking reviewer.

User restrictions:

Maximum price: R$ {state["max_price"]}
Maximum stops: {state["max_stops"]}
Maximum duration: {state["max_duration_minutes"]} minutes

Current ranking weights:

Price: {state["price_weight"]}
Duration: {state["duration_weight"]}
Stops: {state["stops_weight"]}

Ranked flights:

{ranked}

Review the ranking.

Evaluate whether:

1. all flights respect the restrictions;
2. the ranking is coherent;
3. the best flight represents a reasonable trade-off;
4. the current ranking weights produce a sensible result.

If the ranking is not satisfactory, suggest new weights.

The three weights MUST sum to 1.0.

If the ranking is satisfactory, keep the current weights.

Return:

- approval decision;
- feedback;
- interpretation;
- price weight;
- duration weight;
- stops weight.
"""

    review = review_llm.invoke(prompt)

    # Ranking approved
    if review.approved:
        return Command(
            update={
                "approved": True,
                "review_feedback": review.feedback,
                "review_interpretation": review.interpretation,
                "review_attempts": attempts,
            },
            goto=END,
        )

    # Maximum number of review attempts reached
    if attempts >= MAX_REVIEW_ATTEMPTS:
        return Command(
            update={
                "approved": False,
                "review_feedback": (
                    f"Maximum review attempts reached. "
                    f"Last review: {review.feedback}"
                ),
                "review_interpretation": review.interpretation,
                "review_attempts": attempts,
            },
            goto=END,
        )

    # Normalize new ranking weights
    total_weight = (
        review.price_weight
        + review.duration_weight
        + review.stops_weight
    )

    if total_weight > 0:
        price_weight = (
            review.price_weight / total_weight
        )

        duration_weight = (
            review.duration_weight / total_weight
        )

        stops_weight = (
            review.stops_weight / total_weight
        )

    else:
        # Keep previous weights if the LLM returns invalid values
        price_weight = state["price_weight"]
        duration_weight = state["duration_weight"]
        stops_weight = state["stops_weight"]

    # Retry ranking with updated weights
    return Command(
        update={
            "approved": False,
            "review_feedback": review.feedback,
            "review_interpretation": review.interpretation,

            "price_weight": price_weight,
            "duration_weight": duration_weight,
            "stops_weight": stops_weight,

            "review_attempts": attempts,
        },
        goto="ranking",
    )