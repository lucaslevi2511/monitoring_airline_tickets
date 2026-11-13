from pydantic import BaseModel, Field

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

    approved: bool = Field(description=("Indica se o ranking atual é coerente."))

    feedback: str = Field(description=("Avaliação geral do ranking."))

    flight_reviews: list[FlightQualitativeReview] = Field(description=("Análise qualitativa dos voos."))

    best_options: list[str] = Field(description=("Voos que apresentam melhor valor geral."))

    discard_options: list[str] = Field(description=("Voos que podem ser descartados em favor de alternativas melhores."))

    final_conclusion: str = Field(description=("Conclusão final da análise."))

    price_weight: float = Field(description=("Importância sugerida para preço."))

    duration_weight: float = Field(description=("Importância sugerida para duração."))

    stops_weight: float = Field(description=("Importância sugerida para escalas."))

    class_weight: float = Field(description=("Importância sugerida para classe."))