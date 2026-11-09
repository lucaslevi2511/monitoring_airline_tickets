import os

from typing import Literal
from pydantic import BaseModel, Field

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.types import Command
from langgraph.graph import END

from state import FlightState
from mocks import MOCK_FLIGHTS

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
    api_version="v1beta",
)

class ReviewResult(BaseModel):
    approved: bool = Field(
        description="True if the ranking is coherent and respects the user constraints."
    )

    feedback: str = Field(
        description="Short explanation of the review decision."
    )

    interpretation: str = Field(
        description="Short interpretation of the best ranked flights."
    )

review_llm = llm.with_structured_output(
    ReviewResult,
    method="json_schema",
)

def search_flights(state: FlightState):
    flights = [
        flight
        for flight in MOCK_FLIGHTS
        if (
            flight["origin"] == state["origin"]
            and flight["destination"] == state["destination"]
        )
    ]

    return {
        "flights": flights
    }

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
            - flight["duration_minutes"]
            / max_duration
        )

        stops_score = (
            1 / (flight["stops"] + 1)
        )

        score = (
            0.50 * price_score
            + 0.30 * duration_score
            + 0.20 * stops_score
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

def review_flights(
    state: FlightState
) -> Command[Literal["ranking", "__end__"]]:

    attempts = state["review_attempts"] + 1

    ranked = state["ranked_flights"]

    if not ranked:
        return Command(
            update={
                "approved": False,
                "review_feedback": (
                    "No flights satisfy the restrictions."
                ),
                "review_attempts": attempts,
            },
            goto=END,
        )

    prompt = f"""
You are a flight ranking reviewer.

The user requested a trip with these restrictions:

Maximum price: R$ {state["max_price"]}
Maximum stops: {state["max_stops"]}
Maximum duration: {state["max_duration_minutes"]} minutes

The ranking algorithm considers:

- price: 50%
- duration: 30%
- number of stops: 20%

Ranked flights:

{ranked}

Review the ranking.

Check whether:

1. all flights respect the user restrictions;
2. the ordering is reasonable considering price, duration and stops;
3. the first ranked flight is a reasonable recommendation.

Approve the ranking if it is coherent.

Provide a short interpretation explaining the strongest options.
"""

    review = review_llm.invoke(prompt)

    if review.approved:
        return Command(
            update={
                "approved": True,
                "review_feedback": review.feedback,
                "review_interpretation": (
                    review.interpretation
                ),
                "review_attempts": attempts,
            },
            goto=END,
        )

    return Command(
        update={
            "approved": False,
            "review_feedback": review.feedback,
            "review_interpretation": (
                review.interpretation
            ),
            "review_attempts": attempts,
        },
        goto="ranking",
    )