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
        super().__init__()
        if not token:
            raise ValueError("An access token is required to initialize ReviewAgent.")
        self.token = token

    def _format_workspaces(self, workspaces: List[dict]) -> str:
        """Formats a list of workspaces into a human-readable string."""
        if not workspaces:
            return "You do not have any workspaces."
        
        output = "Here are your workspaces:\n"
        for ws in workspaces:
            owner_name = "Unknown Owner"
            collaborators_info = []

            # Find owner and other members
            for member in ws.get('members', []):
                if str(member['user_id']) == str(ws['owner_id']): # Compare UUIDs as strings
                    owner_name = member['full_name']
                else:
                    collaborators_info.append(f"{member['full_name']} ({member['role']})")
            
            output += f"- **{ws['name']}** (ID: {ws['id']}): Owned by {owner_name}. Your role: {ws['user_role']}. Contains {len(ws['tenders'])} tenders."
            
            if collaborators_info:
                output += f" Collaborators: {', '.join(collaborators_info)}."
            
            output += "\n"
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
        async with httpx.AsyncClient(follow_redirects=True) as client:
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
        workspaces = await self._make_request("GET", "/workspaces/detailed")
        return self._format_workspaces(workspaces)

    async def list_tenders_in_workspace(self, workspace_id: str) -> str:
        """
        Retrieves a list of all tenders within a specific workspace, identified by its ID.
        """
        tenders = await self._make_request("GET", f"/tenders/workspace/{workspace_id}")
        return self._format_tenders(tenders)

    async def get_tender_details(self, tender_id: str) -> str:
        """
        Retrieves the full details for a specific tender, including its documents and analysis results.
        """
        tender = await self._make_request("GET", f"/tenders/{tender_id}")
        return self._format_tender_details(tender)

    async def get_analysis_result_details(self, analysis_id: str) -> str:
        """
        Retrieves the status and data for a specific analysis result. If the analysis is complete,
        it will return the summarized data, which can then be used to answer questions.
        """
        result = await self._make_request("GET", f"/analysis-results/{analysis_id}")
        return self._format_analysis_details(result)

    async def find_tender_by_name(self, tender_name: str) -> str:
        """
        Searches for tenders by name across all workspaces the user has access to.
        Returns a list of matching tenders with their IDs, names, and creation dates.
        If multiple tenders with the same name exist, all will be returned.
        """
        tenders = await self._make_request("GET", f"/tenders/find_by_name?name={tender_name}")
        
        if not tenders:
            return f"No tenders found with the name '{tender_name}'."
        
        output = f"Found {len(tenders)} tender(s) matching '{tender_name}':\n"
        for tender in tenders:
            output += f"- **{tender['name']}** (ID: {tender['id']}) created on {tender['created_at']}.\n"
        return output

    async def list_all_tenders(self, tender_name: str | None = None) -> str:
        """
        Retrieves a list of all tenders across all workspaces that the user has access to,
        with an optional filter by tender name. This is useful for answering general questions
        about tenders or when the user asks to filter tenders by a specific criteria (e.g., name, status).
        """
        endpoint = "/tenders/all_for_user"
        if tender_name:
            endpoint += f"?name={tender_name}"

        tenders = await self._make_request("GET", endpoint)

        if not tenders:
            if tender_name:
                return f"No tenders found matching the name '{tender_name}'."
            return "You do not have any tenders across your workspaces."
        
        output = f"Here are the tenders across your workspaces:\n"
        for tender in tenders:
            output += f"- **{tender['name']}** (ID: {tender['id']}) created on {tender['created_at']}.\n"
        return output

    async def list_all_analysis_results(self, analysis_name: str | None = None) -> str:
        """
        Retrieves a list of all analysis results across all tenders and workspaces that the user has access to,
        with an optional filter by analysis result name. This is useful for answering general questions
        about analysis results or when the user asks to filter analysis results by a specific criteria.
        """
        endpoint = "/analysis-results/all_for_user"
        if analysis_name:
            endpoint += f"?name={analysis_name}"

        results = await self._make_request("GET", endpoint)

        if not results:
            if analysis_name:
                return f"No analysis results found matching the name '{analysis_name}'."
            return "You do not have any analysis results across your tenders and workspaces."
        
        output = f"Found {len(results)} analysis result(s):\n"
        for res in results:
            output += f"- **{res['name']}** (ID: {res['id']}) Status: {res['status']} created on {res['created_at']}.\n"
        return output


    def get_tools(self) -> List[FunctionTool]:
        """
        Exposes the agent's capabilities as a list of tools for an LLM to use.
        """
        return [
            FunctionTool.from_defaults(
                self.list_my_workspaces,
                description="Use this tool to get a list of all of the user's workspaces and their basic details, including owner, your role, and number of tenders."
            ),
            FunctionTool.from_defaults(
                self.list_tenders_in_workspace,
                description="Use this tool to list all tenders within a specific workspace. You must provide the workspace_id (UUID format)."
            ),
            FunctionTool.from_defaults(
                self.list_all_tenders,
                description="Use this tool to retrieve a comprehensive list of all tenders the user has access to, across all their workspaces. You can optionally filter by a tender name. Use this when the user asks general questions about tenders or to filter them by name."
            ),
            FunctionTool.from_defaults(
                self.find_tender_by_name,
                description="Use this tool to search for tenders by name across all user's workspaces. This is useful when the user only provides a tender name and you need to find its ID. Provide the full tender name for best results."
            ),
            FunctionTool.from_defaults(
                self.list_all_analysis_results,
                description="Use this tool to retrieve a comprehensive list of all analysis results the user has access to, across all their tenders and workspaces. You can optionally filter by an analysis name. Use this when the user asks general questions about analysis results or to filter them by name."
            ),
            FunctionTool.from_defaults(
                self.get_tender_details,
                description="Use this tool to get all the details about a single tender, including its documents and analysis results. You must provide the tender_id (UUID format)."
            ),
            FunctionTool.from_defaults(
                self.get_analysis_result_details,
                description="Use this tool to check the status of an analysis and get the results if it is complete. You must provide the analysis_id (UUID format)."
            ),
        ]

    def get_system_prompt(self) -> str:
        """
        Returns the system prompt that defines the agent's behavior.
        """
        return (
            "You are a specialized assistant for retrieving and filtering information about a user's professional data related to tenders and workspaces. "
            "Your primary function is to answer questions by utilizing the provided tools. "
            "If a question falls outside the scope of managing tenders, workspaces, or analysis results, politely decline to answer and remind the user that your purpose is to assist only with application-related data. Do not engage in general conversation or provide information unrelated to the application's context. "
            "Respond in a concise and clear manner, adapting the information to the user's specific question and context. "
            "Only provide the necessary details, avoiding unnecessary verbosity. "
            "Always format your responses using Markdown for clarity, including line breaks, bold text (e.g., **important**), and italics (e.g., *example*), to make them easy to read for the user. "
            "Follow these steps to answer questions about tenders and analysis results: "
            "1. If the user asks a general question about **tenders** (e.g., 'list all tenders', 'what tenders do I have?') or asks to filter tenders by name, ALWAYS use the 'list_all_tenders' tool first. "
            "2. If the user asks a general question about **analysis results** (e.g., 'list all analysis results', 'what analysis do I have?') or asks to filter analysis results by name, ALWAYS use the 'list_all_analysis_results' tool first. "
            "3. Once you receive a list of tenders or analysis results, you are responsible for filtering this information based on the user's query and providing a concise summary. "
            "4. If the user refers to a **tender** by name (e.g., 'TICKET22'), but doesn't explicitly ask to list *all* matching tenders, you should first use the 'find_tender_by_name' tool to get its ID. If multiple tenders match the name, clarify with the user which one they mean by ID before proceeding. "
            "5. If the user refers to an **analysis result** by name, but doesn't explicitly ask to list *all* matching analysis results, you should first use the 'find_analysis_result_by_name' tool to get its ID. If multiple analysis results match the name, clarify with the user which one they mean by ID before proceeding. "
            "6. Once you have a specific tender ID, use 'get_tender_details' to retrieve its full information. "
            "7. Once you have a specific analysis ID, use 'get_analysis_result_details' to retrieve its full information. "
            "8. For questions about workspaces, use 'list_my_workspaces' or 'list_tenders_in_workspace' as appropriate. "
            "Do not guess or make up information. Always rely on the tool outputs. Prioritize providing relevant details concisely and directly addressing the user's intent."
        )
