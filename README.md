# Workflow Management API

A FastAPI-based service for managing configurable workflows with PostgreSQL backend.

## Features

- CRUD operations for workflow management
- Workflow submission/feedback tracking
- Database integration with SQLAlchemy
- CORS support for frontend integration

## Prerequisites

- Python 3.7+
- PostgreSQL database

## Installation

1. Ensure that python is installed on your device
2. Clone the repository
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with:

```
DATABASE_CONNECTION=postgresql://user:password@localhost:5432/dbname
```
This is the connection string for your database. 

Change values depending on your database settings

The project assumes that you are using postgreSQL as a database.


## Database Schema

The system uses three main models:

### WorkflowStructure
- Used for storing workflow's structure
- Fields: id, name, description, status, is_published, fields, api_config, category, version, created_at, updated_at, created_by, is_deleted

### WorkflowSubmission
- Tracks workflow feedback
- Fields: id, workflow_id, is_positive, submitted_at

## API Endpoints

### Workflows
- GET `/api/workflows` - List all workflows
- GET `/api/workflows/{workflow_id}` - Get specific workflow
- POST `/api/workflows` - Create new workflow
- PUT `/api/workflows/{workflow_id}` - Update workflow
- DELETE `/api/workflows/{workflow_id}` - Delete workflow

### User Feedback
- POST `/api/workflow-feedback` - Submit workflow feedback

### Test Endpoints
- GET `/text` - Sample text response
- GET `/summary` - Sample JSON response
- GET `/image` - Sample image response

## Running the Application

Start the server:
```bash
uvicorn app:app --workers X
```
`--workers X` - used to specify the number of worker processes that should handle incoming requests. Assign according to system resources

The API will be available at `http://localhost:8000`

## Development

The project uses:
- FastAPI for API framework
- SQLAlchemy for ORM
- Pydantic for data validation
- uvicorn for ASGI server

## Error Handling

All database operations include error handling with:
- Transaction rollback on errors
- Detailed error messages in responses
- Success/error status in response format
