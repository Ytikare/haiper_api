from sqlalchemy import create_engine, select, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime

from ..functions.utils import assign_new_values

load_dotenv()

# Database connection
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_CONNECTION")

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"ssl": False}
)

SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency to get DB session
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

from .models import WorkflowFormStructure, WorkflowStructure, WorkflowSubmission

async def get_all_workflows(db: AsyncSession):
    try:
        result = await db.execute(
            select(WorkflowStructure)
            .where(WorkflowStructure.is_deleted == False)
        )
        workflows = result.scalars().all()
        
        workflow_list = [
            {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status,
                "fields": workflow.fields,
                "apiConfig": workflow.api_config,
                "category": workflow.category,
                "version": workflow.version,
                "isPublished": workflow.is_published,
                "createdAt": workflow.created_at.isoformat(),
                "updatedAt": workflow.updated_at.isoformat(),
                "createdBy": workflow.created_by
            }
            for workflow in workflows
        ]
        
        return workflow_list
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_workflow_by_id(db: AsyncSession, workflow_id: str):
    try:
        # Use async query instead of sync query
        result = await db.execute(
            select(WorkflowFormStructure)
            .where(WorkflowFormStructure.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            return {"status": "error", "message": f"Workflow with id {workflow_id} not found"}
            
        workflow_dict = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status,
            "fields": workflow.fields,
            "apiConfig": workflow.api_config,
            "isPublished": workflow.is_published,
        }
        
        return workflow_dict
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def update_workflow(db: AsyncSession, workflow_id: str, workflow_data: dict):
    try:
        # Create a dictionary for all the values to update
        update_values = {}
        
        # Process each field from workflow_data
        for key, value in workflow_data.items():
            if key == "fields":
                update_values["fields"] = value
            elif key == "name":
                update_values["name"] = value
            elif key == "description":
                update_values["description"] = value
            elif key == "status":
                update_values["status"] = value
            elif key == "apiConfig":
                update_values["api_config"] = value
            elif key == "category":
                update_values["category"] = value
            elif key == "version":
                update_values["version"] = value
            elif key == "isPublished":
                update_values["is_published"] = value
            elif key == "createdBy":
                update_values["created_by"] = value
            elif key == "updatedAt":
                # Handle datetime conversion
                if isinstance(value, str):
                    try:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        # Convert to naive datetime
                        update_values["updated_at"] = datetime(
                            dt.year, dt.month, dt.day, 
                            dt.hour, dt.minute, dt.second, dt.microsecond
                        )
                    except ValueError:
                        update_values["updated_at"] = datetime.utcnow()
                else:
                    update_values["updated_at"] = value
            # Skip 'id' as it's the primary key and can't be updated
        
        # Always update updated_at if not already set
        if "updated_at" not in update_values:
            update_values["updated_at"] = datetime.utcnow()
        
        # Execute the update statement
        update_stmt = update(WorkflowStructure).where(
            WorkflowStructure.id == workflow_id
        ).values(**update_values)
        
        # Execute the statement
        await db.execute(update_stmt)
        
        # Explicitly commit the transaction
        await db.commit()
        
        return {
            "status": "success",
            "message": "Workflow updated successfully",
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in update_workflow: {str(e)}")
        await db.rollback()
        return {"status": "error", "message": str(e)}

async def create_workflow(db: AsyncSession, workflow_data: dict):
    try:
        # Create new WorkflowStructure instance
        new_workflow = WorkflowStructure(
            id=workflow_data.get('id'),
            name=workflow_data.get('name'),
            description=workflow_data.get('description'),
            status=workflow_data.get('status'),
            fields=workflow_data.get('fields'),
            api_config=workflow_data.get('apiConfig'),
            category=workflow_data.get('category'),
            version=workflow_data.get('version', 1),
            is_published=workflow_data.get('isPublished', False),
            created_by=workflow_data.get('createdBy')
        )
        
        # Add to database with async methods
        db.add(new_workflow)
        await db.commit()
        
        return {
            "status": "success",
            "message": "Workflow created successfully",
        }
        
    except Exception as e:
        await db.rollback()  # Use async rollback
        return {"status": "error", "message": str(e)}

async def delete_workflow(db: AsyncSession, workflow_id: str):
    try:
        # Find the workflow using async methods
        result = await db.execute(
            select(WorkflowStructure)
            .where(WorkflowStructure.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            return {"status": "error", "message": f"Workflow with id {workflow_id} not found"}
        
        # Set is_deleted to True
        workflow.is_deleted = True
        
        # Commit using async methods
        await db.commit()
        
        return {
            "status": "success",
            "message": "Workflow deleted successfully"
        }
        
    except Exception as e:
        await db.rollback()  # Use async rollback
        return {"status": "error", "message": str(e)}

async def create_workflow_submission(db: AsyncSession, submission_data: dict):
    try:
        # Create new WorkflowSubmission instance
        new_submission = WorkflowSubmission(
            workflow_id=submission_data.get('workflowId'),
            is_positive= True if submission_data.get('feedback') == "positive" else False
        )
        
        # Add to database with async methods
        db.add(new_submission)
        await db.commit()
        
        return {
            "status": "success",
            "message": "Workflow submission created successfully",
        }
        
    except Exception as e:
        await db.rollback()  # Use async rollback
        return {"status": "error", "message": str(e)}