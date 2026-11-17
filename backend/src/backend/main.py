from fastapi import FastAPI
from backend.api.v1.tasks import router as task_router
from backend.api.v1.executions import router as execution_router


app = FastAPI()

app.include_router(task_router, prefix="/api/v1")
app.include_router(execution_router, prefix="/api/v1")
app.get("/health")
async def health_check():
    return {"status": "ok"}
