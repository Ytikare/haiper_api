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


@app.get("/text")
async def get_text_summary():
    return PlainTextResponse("This is a sample text response.")

@app.get("/summary")
async def get_json_summary():
    summary = {
        "title": 'Sample Summary',
        "content": 'This is a brief summary of the content.',
        "date": "2025-02-19T10:27:02.998Z"
    }
    return JSONResponse(content=summary)

@app.get("/image")
async def get_system_diagram():
    # This is a placeholder path - you'll need to add the actual image file
    image_path = "images/image.png"
    return FileResponse(image_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

