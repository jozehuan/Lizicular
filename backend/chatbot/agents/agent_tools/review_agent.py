import os
import httpx
from typing import List
from llama_index.core.tools import FunctionTool
from pydantic import Field

from ..base_agent import BaseAgent

# Get the backend URL from environment variables, with a default for local dev
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class ReviewAgent(BaseAgent):
    """
    An agent designed to interact with the application's own backend to retrieve
    information about a user's workspaces, tenders, and analysis results.
    """
    token: str = None

    def __init__(self, token: str):
        """
        Initializes the agent with the user's access token.
        """
        if not token:
            raise ValueError("An access token is required to initialize ReviewAgent.")
        self.token = token

    def _format_workspaces(self, workspaces: List[dict]) -> str:
        """Formats a list of workspaces into a human-readable string."""
        if not workspaces:
            return "You do not have any workspaces."
        
        output = "Here are your workspaces:"
        for ws in workspaces:
            output += f"- **{ws['name']}** (ID: {ws['id']}): Role: {ws['user_role']}. Contains {ws['tender_count']} tenders."
        return output

    def _format_tenders(self, tenders: List[dict]) -> str:
        """Formats a list of tenders into a human-readable string."""
        if not tenders:
            return "No tenders found in this workspace."
            
        output = "Tenders in this workspace:"
        for tender in tenders:
            output += f"- **{tender['name']}** (ID: {tender['id']}): Status: {tender['status']}. Contains {len(tender.get('documents', []))} documents."
        return output

    def _format_tender_details(self, tender: dict) -> str:
        """Formats the details of a single tender into a human-readable string."""
        if not tender:
            return "Could not retrieve tender details."
        
        doc_list = "\n  ".join([f"- {doc['filename']}" for doc in tender.get('documents', [])])
        analysis_list = "\n  ".join([f"- {res['name']} (ID: {res['id']}, Status: {res['status']})" for res in tender.get('analysis_results', [])])

        output = f"""
        **Tender Details for: {tender['name']}** (ID: {tender['id']})
        - **Status:** {tender['status']}
        - **Created:** {tender['created_at']}
        
        **Documents ({len(tender.get('documents', []))}):**
          {doc_list or "No documents."}
          
        **Analysis Results ({len(tender.get('analysis_results', []))}):**
          {analysis_list or "No analysis results."}
        """
        return output.strip()

    def _format_analysis_details(self, result: dict) -> str:
        """Formats the details of a single analysis result into a human-readable string."""
        if not result:
            return "Could not retrieve analysis result details."

        status = result.get("status", "unknown").lower()
        output = f"**Analysis Result: {result.get('name', 'N/A')}** (ID: {result.get('_id')})\n- **Status:** {status.capitalize()}\n"

        if status == "completed" and result.get("data"):
            # Simple formatting of the data payload for the LLM
            output += "- **Result Data:**\n"
            for key, value in result["data"].items():
                if isinstance(value, list) and len(value) > 0:
                    output += f"  - {key.replace('_', ' ').capitalize()}: {len(value)} items\n"
                elif isinstance(value, dict):
                    output += f"  - {key.replace('_', ' ').capitalize()}: [Complex object]\n"
                else:
                    output += f"  - {key.replace('_', ' ').capitalize()}: {value}\n"
        elif status == "failed":
            output += f"- **Error:** {result.get('error_message', 'No details provided.')}\n"
        
        return output.strip()

    async def _make_request(self, method: str, endpoint: str) -> dict | List:
        """Helper to make authenticated async requests to the backend."""
        headers = {"Authorization": f"Bearer {self.token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, f"{BACKEND_URL}{endpoint}", headers=headers)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                return response.json()
            except httpx.HTTPStatusError as e:
                # Provide more context on HTTP errors
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise

    async def list_my_workspaces(self) -> str:
        """
        Retrieves a list of all workspaces the current user is a member of,
        including the user's role and the number of tenders in each workspace.
        """
        workspaces = await self._make_request("GET", "/workspaces/detailed/")
        return self._format_workspaces(workspaces)

    async def list_tenders_in_workspace(self, workspace_id: str = Field(description="The UUID of the workspace.", examples=["7f015cc9-51bd-471c-beca-dfe3850fd208"])) -> str:
        """
        Retrieves a list of all tenders within a specific workspace, identified by its ID.
        """
        tenders = await self._make_request("GET", f"/tenders/workspace/{workspace_id}")
        return self._format_tenders(tenders)

    async def get_tender_details(self, tender_id: str = Field(description="The UUID of the tender.", examples=["d8d8f8d8-f8d8-f8d8-f8d8-d8d8f8d8f8d8"])) -> str:
        """
        Retrieves the full details for a specific tender, including its documents and analysis results.
        """
        tender = await self._make_request("GET", f"/tenders/{tender_id}")
        return self._format_tender_details(tender)

    async def get_analysis_result_details(self, analysis_id: str = Field(description="The UUID of the analysis result.", examples=["a1b2c3d4-e5f6-a1b2-c3d4-e5f6a1b2c3d4"])) -> str:
        """
        Retrieves the status and data for a specific analysis result. If the analysis is complete,
        it will return the summarized data, which can then be used to answer questions.
        """
        result = await self._make_request("GET", f"/analysis-results/{analysis_id}")
        return self._format_analysis_details(result)

    def get_tools(self) -> List[FunctionTool]:
        """
        Exposes the agent's capabilities as a list of tools for an LLM to use.
        """
        return [
            FunctionTool.from_defaults(
                self.list_my_workspaces,
                description="Use this tool to get a list of all of the user's workspaces and their basic details."
            ),
            FunctionTool.from_defaults(
                self.list_tenders_in_workspace,
                description="Use this tool to list all tenders within a specific workspace. You must provide the workspace_id."
            ),
            FunctionTool.from_defaults(
                self.get_tender_details,
                description="Use this tool to get all the details about a single tender, including its documents and analysis results. You must provide the tender_id."
            ),
            FunctionTool.from_defaults(
                self.get_analysis_result_details,
                description="Use this tool to check the status of an analysis and get the results if it is complete. You must provide the analysis_id."
            ),
        ]
