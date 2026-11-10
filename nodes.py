import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END
from langgraph.types import Command
from state import FlightState
from mocks import MOCK_FLIGHTS
from flight_service import search_api_flights, filter_flight_options, rank_flight_options

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

    origin_iata: str = Field(description="IATA airport code for the origin.")

    destination_iata: str = Field(description="IATA airport code for the destination.")

    trip_type: str = Field (description= "Trip type: 'one_way' or 'round_trip'.")

    departure_date: str = Field(description="Departure date in YYYY-MM-DD format.")

    return_date: str = Field(description= "Return date in YYYY-MM-DD format. " "Use null for one-way trips.")

    max_price: float = Field(description="Maximum price in Brazilian reais.")

    max_stops: int = Field(description="Maximum number of stops accepted.")

    max_duration_minutes: int = Field(description="Maximum total flight duration in minutes.")


class FlightQualitativeReview(BaseModel):
    flight_numbers: list[str] = Field(
        description="Flight numbers being reviewed."
    )

    positives: list[str] = Field(
        description="Main positive aspects of this flight."
    )

    negatives: list[str] = Field(
        description="Main negative aspects or trade-offs."
    )

    observation: str = Field(
        description=(
            "Short qualitative observation respecting "
            "the numerical ranking score."
        )
    )


class ReviewResult(BaseModel):
    approved: bool = Field(
        description="Whether the current ranking is coherent."
    )

    feedback: str = Field(
        description="General evaluation of the ranking."
    )

    flight_reviews: list[FlightQualitativeReview] = Field(
        description=(
            "Qualitative analysis of the top ranked flights."
        )
    )

    best_options: list[str] = Field(
        description=(
            "Flight numbers that provide the best overall value."
        )
    )

    discard_options: list[str] = Field(
        description=(
            "Flight numbers that offer poor value compared "
            "with better alternatives."
        )
    )

    final_conclusion: str = Field(
        description=(
            "Final recommendation explaining which flights "
            "are most worthwhile and which should be discarded."
        )
    )

    price_weight: float = Field(description="Suggested importance of price, between 0 and 1.")

    duration_weight: float = Field (description="Suggested importance of duration, between 0 and 1.")

    stops_weight: float = Field (description="Suggested importance of stops, between 0 and 1.")

    class_weight: float = Field(description="Suggested importance of travel class, between 0 and 1.")

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
- IATA code of the main airport for the origin city
- IATA code of the main airport for the destination city
- trip type: one_way or round_trip
- departure date
- return date, if the trip is round trip
- maximum price
- maximum number of stops
- maximum total flight duration

Convert dates to YYYY-MM-DD.
Convert durations to minutes.

If the user only provides a departure date, use:
trip_type = "one_way"
return_date = null

If the user explicitly requests a return trip and provides a return date, use:
trip_type = "round_trip"

For cities with multiple airports, use the main airport for now.

Do not invent information.
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
}

# SEARCH NODE

def search_flights(state: FlightState):

    flights = search_api_flights(
        origin=state["origin_iata"],
        destination=state["destination_iata"],
        departure_date=state["departure_date"],
        trip_type = state["trip_type"],
        return_date=state["return_date"]
    )

    return {
        "flights": flights
    }

# FILTER NODE

def filter_flights(state: FlightState):

    filtered = filter_flight_options(
        flights=state["flights"],
        max_price=state["max_price"],
        max_stops=state["max_stops"],
        max_duration_minutes=state["max_duration_minutes"],
    )

    return {
        "filtered_flights": filtered
    }

# RANKING NODE

def rank_flights(state: FlightState):

    ranked = rank_flight_options(
        flights=state["filtered_flights"],
        price_weight=state["price_weight"],
        duration_weight=state["duration_weight"],
        stops_weight=state["stops_weight"],
        class_weight=state["class_weight"]
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
    top_flights = state["ranked_flights"][:10]
    flight_text = ""
    for position, flight in enumerate(top_flights,start=1,):
        flight_text += f"""
Flight {position}

Flight numbers: {", ".join(flight["flight_numbers"])}
Airline: {flight["airline"]}
Class: {flight["travel_class"]}

Route:
{flight["origin"]} -> {flight["destination"]}

Departure:
{flight["departure"]}

Arrival:
{flight["arrival"]}

Price:
R$ {flight["price"]:.2f}

Duration:
{flight["duration_minutes"]} minutes

Stops:
{flight["stops"]}

Connections:
{", ".join(flight["connection_airports"]) if flight["connection_airports"] else "Direct"}

Ranking score:
{flight["score"]}
---
"""

    prompt = f"""
You are a flight recommendation reviewer.

A deterministic ranking algorithm has already ranked the flights
using price, duration and number of stops.

Current weights:

Price weight: {state["price_weight"]}
Duration weight: {state["duration_weight"]}
Stops weight: {state["stops_weight"]}
Class weight: {state["class_weight"]}

The numerical ranking must be respected as the primary ordering.

Your role is NOT to arbitrarily replace the ranking.

Your role is to provide a qualitative critical analysis that adds
context to the numerical score.

Analyze the following top-ranked flights:

{flight_text}

For each flight:

1. Identify important positive aspects.
2. Identify important negative aspects or trade-offs.
3. Consider price, duration, stops, connection airports,
   departure time and arrival time.
4. Respect the ranking score, but point out relevant caveats.

Examples of useful observations:

- very low price but inconvenient departure time
- slightly more expensive but much shorter trip
- direct flight that may justify a higher price
- connection that makes the option less attractive
- multiple flights with very similar characteristics
- flight that is dominated by another option
- poor cost-benefit compared with nearby alternatives

Do not invent information that is not present in the flight data.

After reviewing the flights:

- identify the flights that offer the best overall value
- identify flights that can reasonably be discarded
- explain the final recommendation

A flight should only be marked for discard when another option
clearly offers better value or similar benefits with fewer disadvantages.

If the ranking is already coherent, approve it.

Only reject the ranking if there is a meaningful inconsistency
between the numerical ranking and the available flight information.
"""

    review = review_llm.invoke(prompt)

    # Ranking approved
    if review.approved:
        return Command(
            update={
                "approved": True,

                "review_feedback": review.feedback,

                "qualitative_reviews": [
                    item.model_dump()
                    for item in review.flight_reviews
                ],

                "best_options": review.best_options,

                "discard_options": review.discard_options,

                "review_conclusion": review.final_conclusion,

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