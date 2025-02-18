# This file will contain common utility functions
def format_response(data, status="success", message=None):
    return {
        "status": status,
        "message": message,
        "data": data
    }
