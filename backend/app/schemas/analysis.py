from pydantic import BaseModel, field_validator
import re


class AnalysisRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$", v):
            raise ValueError(f"Invalid ticker format: {v}")
        return v
