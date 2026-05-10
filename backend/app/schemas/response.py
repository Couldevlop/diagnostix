"""Schémas Pydantic pour les réponses au questionnaire."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ResponseIn(BaseModel):
    question_id: int
    answer_value: str  # YES | NO | PARTIAL | MANUAL | FREE_NUMERIC | valeur numérique
    answer_numeric: float | None = Field(default=None, ge=0)

    def model_post_init(self, __context: object) -> None:
        """Normalise les réponses numériques envoyées directement par le frontend."""
        VALID = {"YES", "NO", "PARTIAL", "MANUAL", "FREE_NUMERIC"}
        if self.answer_value not in VALID:
            try:
                self.answer_numeric = float(self.answer_value)
                self.answer_value = "FREE_NUMERIC"
            except ValueError:
                raise ValueError(
                    f"answer_value invalide : {self.answer_value!r}. "
                    f"Valeurs acceptées : {', '.join(sorted(VALID))} ou numérique."
                )


class ProgressOut(BaseModel):
    answered: int
    total: int
    percent: float


class ResponseSavedOut(BaseModel):
    saved: bool
    progress: ProgressOut
