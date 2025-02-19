# This file will contain common utility functions
def format_response(data, status="success", message=None):
    return {
        "status": status,
        "message": message,
        "data": data
    }


def assign_new_values(workflow:any, workflow_data: dict):
    # Update the workflow attributes
    for key, value in workflow_data.items():
        # Convert camelCase to snake_case for database columns
        if key == "apiConfig":
            setattr(workflow, "api_config", value)
        elif key == "isPublished":
            setattr(workflow, "is_published", value)
        elif key == "createdAt":
            setattr(workflow, "created_at", value)
        elif key == "updatedAt":
            setattr(workflow, "updated_at", value)
        elif key == "id":
            continue
        elif key == "createdBy":
            setattr(workflow, "created_by", value)
        else:
            setattr(workflow, key, value)