from pydantic import BaseModel


class Alert(BaseModel):
    id: str
    station_id: str
    station_name: str
    parameter: str
    value: float
    threshold: float
    unit: str
    severity: str               # critical | warning | info
    message: str
    raised_at: str
    status: str                 # active | acknowledged | resolved
    sampling_triggered: bool    # IoT alert -> event-based LC-HRMS sampling
