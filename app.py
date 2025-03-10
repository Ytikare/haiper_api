from fastapi import FastAPI, Body, File, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
import uvicorn
import os
import json
import PyPDF2
from io import BytesIO
from typing import Optional
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
    async for db in get_db():
        return await get_all_workflows(db)


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    async for db in get_db():
        return await get_workflow_by_id(db, workflow_id)


@app.put("/api/workflows/{workflow_id}")
async def update_workflow_endpoint(workflow_id: str, workflow_data: dict = Body(...)):
    async for db in get_db():
        return await update_workflow(db, workflow_id, workflow_data)


@app.post("/api/workflows")
async def create_workflow_endpoint(workflow_data: dict = Body(...)):
    async for db in get_db():
        return await create_workflow(db, workflow_data)


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow_endpoint(workflow_id: str):
    async for db in get_db():
        return await delete_workflow(db, workflow_id)


@app.post("/api/workflow-feedback")
async def create_workflow_feedback(feedback_data: dict = Body(...)):
    async for db in get_db():
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

@app.post("/api/workflow/rfil")
async def process_rfil_workflow(
    request: Request,
    rfil: UploadFile = File(...),
):
    """
    RFIL workflow endpoint that processes a PDF file submission.
    
    Workflow steps:
    1. Obtain and validate the PDF
    2. Store valid PDFs as temporary files
    3. Process the file with a mockup function
    4. Return combined results
    5. Delete the temporary file
    """
    # Access the complete form data to get any additional fields
    form = await request.form()
    
    # Process additional form fields if needed
    additional_data = {}
    for field_name, field_value in form.items():
        if field_name == "rfil" or isinstance(field_value, UploadFile):
            continue
            
        if isinstance(field_value, str):
            try:
                parsed_value = json.loads(field_value)
                additional_data[field_name] = parsed_value
            except json.JSONDecodeError:
                additional_data[field_name] = field_value
    
    # Check if the file is a PDF
    if not rfil.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        # Read the file content
        contents = await rfil.read()
        
        # Validate PDF structure
        try:
            pdf_file = BytesIO(contents)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Check if PDF has at least one page
            if len(pdf_reader.pages) < 1:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "The PDF file is empty or corrupt"}
                )
                
            # Check if file is readable
            _ = pdf_reader.pages[0].extract_text()
            
            # If we get here, the PDF is valid
            # ---------- NEW CODE STARTS HERE ----------
            
            # 1. Generate a unique ID for this file
            import uuid
            import tempfile
            file_id = str(uuid.uuid4())
            
            # 2. Create a temporary directory if it doesn't exist
            temp_dir = os.path.join(os.getcwd(), "temp_files")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 3. Save the file to the temporary directory
            temp_file_path = os.path.join(temp_dir, f"{file_id}.pdf")
            with open(temp_file_path, "wb") as temp_file:
                # Reset file pointer to beginning
                pdf_file.seek(0)
                temp_file.write(pdf_file.read())
            
            # 4. Mockup process function
            def process_rfil_file(file_path):
                """Mockup processing function for RFIL files"""
                # Simulate some processing time
                import time
                time.sleep(1)
                
                # Mock analysis results
                return {
                    "process_result": "success",
                    "analysis": {
                        "compliance_score": 0.87,
                        "risk_factors": ["section_3.2", "appendix_B"],
                        "regulatory_matches": 5,
                        "processing_time": "1.2s"
                    }
                }
            
            # 5. Process the file
            process_results = process_rfil_file(temp_file_path)
            
            # 6. Prepare the response with combined results
            response_data = {
                "status": "success", 
                "message": "PDF file has been processed successfully", 
                "filename": rfil.filename,
                "file_id": file_id,
                "pages": len(pdf_reader.pages),
                "process_results": process_results
            }
            
            # Include any additional data in the response if needed
            if additional_data:
                response_data["additional_data"] = additional_data
            
            # 7. Delete the temporary file (optional - you may want to keep it for a while)
            os.remove(temp_file_path)
            
            return JSONResponse(content=response_data)
            # ---------- NEW CODE ENDS HERE ----------
            
        except PyPDF2.errors.PdfReadError:
            return JSONResponse(
                status_code=400, 
                content={"status": "error", "message": "The file is not a valid PDF"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An error occurred: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

