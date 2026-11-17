from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportGenerateRequest(BaseModel):
    task_id: int
    file_format: str = Field(default="docx", pattern="^(docx)$")


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    file_format: str
    file_name: str
    generated_at: datetime


class ReportListOut(BaseModel):
    total: int
    items: list[ReportOut]
