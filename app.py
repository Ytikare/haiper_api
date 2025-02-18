from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.integration.database import get_all_workflows, get_workflow_by_id, get_db

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/workflows")
async def root():
    db = next(get_db())
    return await get_all_workflows(db)


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    db = next(get_db())
    return await get_workflow_by_id(db, workflow_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

