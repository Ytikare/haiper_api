from abc import ABC, abstractmethod
from typing import Any, Dict
from src.functions.utils import format_response
from src.integration.database import Database

class BaseWorkflow(ABC):
    def __init__(self):
        self.db = Database()

    @abstractmethod
    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method that must be implemented by all workflow classes
        Args:
            request_data: Dictionary containing the request data
        Returns:
            Dictionary with the response data
        """
        pass

    async def run(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to run the workflow
        Args:
            request_data: Dictionary containing the request data
        Returns:
            Formatted response with the workflow results
        """
        try:
            # Execute the specific workflow implementation
            result = await self.execute(request_data)
            
            # Log the successful execution
            await self.log_execution(request_data, result, success=True)
            
            return format_response(
                data=result,
                status="success",
                message="Workflow executed successfully"
            )
            
        except Exception as e:
            # Log the failed execution
            await self.log_execution(request_data, str(e), success=False)
            
            return format_response(
                data=None,
                status="error",
                message=str(e)
            )

    async def log_execution(self, request_data: Dict[str, Any], result: Any, success: bool) -> None:
        """
        Log the workflow execution to the database
        Args:
            request_data: The original request data
            result: The execution result or error message
            success: Boolean indicating if the execution was successful
        """
        log_data = {
            "workflow_name": self.__class__.__name__,
            "request_data": request_data,
            "result": result,
            "success": success,
            "timestamp": "CURRENT_TIMESTAMP"  # This should be handled by your database
        }
        
        await self.db.insert("workflow_logs", log_data)
