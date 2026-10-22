from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from app.database import Base

class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), nullable=True, index=True)
    agent_name = Column(String(64), nullable=False) # SA-01, SA-02, SA-11, etc.
    prompt_snapshot = Column(Text, nullable=True)
    tool_calls_json = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    sanitized_output = Column(Text, nullable=True)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    status = Column(String(32), default="SUCCESS")
    created_at = Column(DateTime, default=datetime.utcnow)


class AskBluePillQuery(Base):
    __tablename__ = "ask_bluepill_queries"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
