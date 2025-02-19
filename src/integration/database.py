from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ..functions.utils import assign_new_values

# You'll need to modify these according to your PostgreSQL setup
SQLALCHEMY_DATABASE_URL = "postgresql://MIIvanov:@localhost:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy.orm import Session
from .models import WorkflowFormStructure, WorkflowStructure

async def get_all_workflows(db: Session):
    try:
        workflows = db.query( WorkflowStructure).all()
        
        # Convert SQLAlchemy objects to dictionaries
        workflow_list = []
        for workflow in workflows:
            workflow_dict = {
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
            workflow_list.append(workflow_dict)
            
        return workflow_list
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_workflow_by_id(db: Session, workflow_id: str):
    try:
        workflow = db.query(WorkflowFormStructure).filter(WorkflowFormStructure.id == workflow_id).first()
        
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

async def update_workflow(db: Session, workflow_id: str, workflow_data: dict):
    try:
        # Find the workflow by id
        workflow = db.query(WorkflowStructure).filter(WorkflowStructure.id == workflow_id).first()
        
        if not workflow:
            return {"status": "error", "message": f"Workflow with id {workflow_id} not found"}

        assign_new_values(workflow, workflow_data)
        
        # Commit the changes to the database
        db.commit()
        
        # Return the updated workflow
        return {
            "status": "success",
            "message": "Workflow updated successfully",
        }
    except Exception as e:
        db.rollback()  # Rollback changes in case of error
        return {"status": "error", "message": str(e)}
