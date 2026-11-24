from backend.database.base import Base
from backend.database.session import engine

# Import all models so SQLAlchemy registers their tables
from backend.database.models import (
    User,
    Execution,
    Task,
    TaskDependency,
    TaskAttempt,
    OutboxEvent,
    TaskResults,
    ExecutionResults,
    InboxEvent
)

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")