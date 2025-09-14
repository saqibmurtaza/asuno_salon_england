from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict, Any

class SessionHistory(SQLModel, table=True):
    __tablename__ = "session_history"

    session_id: str = Field(primary_key=True, index=True)
    history: Dict[str, Any] = Field(..., sa_column=Column(JSONB, nullable=False))
