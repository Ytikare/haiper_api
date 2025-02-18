from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.integration.database import test_db_connection, get_all_workflows, get_db

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

@app.get("/test-db")
async def test_database():
    return await test_db_connection()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

