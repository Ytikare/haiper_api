from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
import uvicorn
from src.integration.database import get_all_workflows, get_workflow_by_id, get_db, update_workflow, create_workflow, delete_workflow, create_workflow_submission

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


@app.put("/api/workflows/{workflow_id}")
async def update_workflow_endpoint(workflow_id: str, workflow_data: dict = Body(...)):
    db = next(get_db())
    return await update_workflow(db, workflow_id, workflow_data)


@app.post("/api/workflows")
async def create_workflow_endpoint(workflow_data: dict = Body(...)):
    db = next(get_db())
    return await create_workflow(db, workflow_data)


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow_endpoint(workflow_id: str):
    db = next(get_db())
    return await delete_workflow(db, workflow_id)


@app.post("/api/workflow-feedback")
async def create_workflow_feedback(feedback_data: dict = Body(...)):
    db = next(get_db())
    return await create_workflow_submission(db, feedback_data)


@app.get("/api/summary/text")
async def get_text_summary():
    return PlainTextResponse("This is a workflow management system that handles creation, updating, and execution of workflows.")

@app.get("/api/summary/json")
async def get_json_summary():
    summary = {
        "system": "Workflow Management System",
        "features": [
            "Workflow CRUD operations",
            "Workflow execution",
            "Feedback submission"
        ],
        "endpoints": {
            "total": 7,
            "types": ["GET", "POST", "PUT", "DELETE"]
        }
    }
    return JSONResponse(content=summary)

@app.get("/api/summary/image")
async def get_system_diagram():
    # This is a placeholder path - you'll need to add the actual image file
    image_path = "src/static/system_diagram.png"
    return FileResponse(image_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

