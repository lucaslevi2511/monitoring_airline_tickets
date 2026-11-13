from typing import Literal
from pydantic import BaseModel, Field

class PreferenceResult(BaseModel):
    price_priority: Literal[ "low", "medium", "high",]

    duration_priority: Literal[ "low", "medium", "high",]

    stops_priority: Literal[ "low", "medium", "high",]

    class_priority: Literal[ "low", "medium", "high",]

    reasoning: str = Field(description=("Explicação curta em português sobre a interpretação."))