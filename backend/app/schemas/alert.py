from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime
import re


class AlertCreate(BaseModel):
    ticker: str
    alert_type: Literal["price_above", "price_below", "earnings_date", "re_analyze", "custom"]
    target_price: Optional[float] = None
    cron_expression: Optional[str] = None
    event_description: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$", v):
            raise ValueError(f"Invalid ticker: {v}")
        return v

    @model_validator(mode="after")
    def validate_fields_by_type(self) -> "AlertCreate":
        if self.alert_type in ("price_above", "price_below") and self.target_price is None:
            raise ValueError("target_price is required for price alerts")
        if self.alert_type == "re_analyze" and not self.cron_expression:
            # Default: weekly on Monday at 8am
            self.cron_expression = "0 8 * * 1"
        if self.alert_type == "custom" and not self.event_description:
            raise ValueError("event_description is required for custom alerts")
        return self


class AlertUpdate(BaseModel):
    is_active: Optional[bool] = None
    target_price: Optional[float] = None
    cron_expression: Optional[str] = None
    event_description: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    ticker: str
    alert_type: str
    target_price: Optional[float] = None
    cron_expression: Optional[str] = None
    event_description: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0

    class Config:
        from_attributes = True


class AlertTriggerResponse(BaseModel):
    id: str
    alert_id: str
    triggered_at: datetime
    trigger_value: str
    action_taken: str

    class Config:
        from_attributes = True
