import os
import httpx
import yaml
from typing import List, Any
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

            for member in ws.get('members', []):
                if str(member['user_id']) == str(ws['owner_id']):
                    owner_name = member['full_name']
                else:
                    collaborators_info.append(f"{member['full_name']} ({member['role']})")
            
            output += f"- **{ws['name']}** (ID: {ws['id']}): Owned by {owner_name}. Your role: {ws['user_role']}. Contains {len(ws['tenders'])} tenders.\n"
            
            if collaborators_info:
                output += f"  Collaborators: {', '.join(collaborators_info)}.\n"
        return output


    async def _make_request(self, method: str, endpoint: str) -> dict | List:
        """Helper to make authenticated async requests to the backend."""
        headers = {"Authorization": f"Bearer {self.token}"}
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.request(method, f"{BACKEND_URL}{endpoint}", headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise

    async def list_my_workspaces(self) -> str:
        """
        Retrieves a list of all workspaces the current user is a member of.
        """
        workspaces = await self._make_request("GET", "/workspaces/detailed")
        return self._format_workspaces(workspaces)

    async def list_all_tenders(self, tender_name: str | None = None) -> str:
        """
        Retrieves a list of all tenders across all workspaces that the user has access to.
        """
        endpoint = "/tenders/all_for_user"
        if tender_name:
            endpoint += f"?name={tender_name}"

        tenders = await self._make_request("GET", endpoint)

        if not tenders:
            if tender_name:
                return f"No tenders found matching the name '{tender_name}'."
            return "You do not have any tenders across your workspaces."
        
        output = "Here are the tenders across your workspaces:\n"
        for tender in tenders:
            output += f"- **{tender['name']}** in workspace **{tender['workspace_name']}** (ID: {tender['id']})\n"
        return output

    def _format_tenders_in_workspace(self, tenders: List[dict], workspace_name: str) -> str:
        """Formats a list of tenders from a specific workspace into a human-readable string."""
        if not tenders:
            return f"No tenders found in the workspace '{workspace_name}'."
        
        output = f"Here are the tenders in workspace '**{workspace_name}**':\n"
        for tender in tenders:
            output += f"- **{tender['name']}** (ID: {tender['id']}) - Created on: {tender['created_at']}\n"
        return output

    async def list_tenders_in_workspace(self, workspace_name: str) -> str:
        """
        Lists all tenders within a specific workspace by its name.
        """
        all_workspaces = await self._make_request("GET", "/workspaces/detailed")
        
        target_workspace = None
        for ws in all_workspaces:
            if ws['name'].lower() == workspace_name.lower():
                target_workspace = ws
                break
        
        if not target_workspace:
            return f"Workspace '{workspace_name}' not found or you don't have access."

        workspace_id = target_workspace['id']
        tenders = await self._make_request("GET", f"/tenders/workspace/{workspace_id}")
        
        return self._format_tenders_in_workspace(tenders, target_workspace['name'])

    def _format_any_data(self, data: Any, level: int = 1) -> str:
        """Recursively formats any dictionary or list into a Markdown string."""
        indent = "  " * level
        output = ""
        if isinstance(data, dict):
            for key, value in data.items():
                key_str = f"**{str(key).replace('_', ' ').capitalize()}**"
                if isinstance(value, (dict, list)):
                    output += f"{indent}- {key_str}:\n"
                    output += self._format_any_data(value, level + 1)
                elif value is not None:
                    output += f"{indent}- {key_str}: {value}\n"
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    output += f"{indent}-\n"
                    output += self._format_any_data(item, level + 1)
                elif item is not None:
                    output += f"{indent}- {item}\n"
        else:
            if data is not None:
                output += f"{indent}{data}\n"
        return output

    async def _format_analysis_results(self, tender_name: str, analysis_results: List[dict]) -> str:
        """Formats a list of analysis results into a human-readable string."""
        if not analysis_results:
            return f"No analysis results found for tender '{tender_name}'."

        output = f"Analysis results for tender '**{tender_name}**':\n"
        for i, result in enumerate(analysis_results):
            output += f"\n--- Analysis {i+1} ---\n"
            output += f"- **Name:** {result.get('name', 'N/A')}\n"
            output += f"- **Status:** {result.get('status', 'N/A')}\n"
            
            if result.get('status', '').lower() == 'completed':
                analysis_id = result.get('id')
                if analysis_id:
                    try:
                        full_data = await self._make_request("GET", f"/analysis-results/{analysis_id}")
                        output += "- **Result Data:**\n"
                        data = full_data.get('data')
                        if not data:
                            output += "  - No detailed data available.\n"
                        else:
                            output += self._format_any_data(data, level=1)
                    except Exception as e:
                        output += "  - Could not retrieve full analysis data.\n"
            elif result.get('status', '').lower() == 'failed':
                output += f"- **Error:** {result.get('error_message', 'No error details provided.')}\n"
        return output

    async def get_tender_analysis_details(self, tender_name: str, analysis_name: str | None = None) -> str:
        """
        Retrieves analysis results for a specific tender, optionally filtered by analysis name.
        """
        matching_tenders = await self._make_request("GET", f"/tenders/find_by_name?name={tender_name}")
        
        if not matching_tenders:
            return f"No tender found with the name '{tender_name}'."
        
        if len(matching_tenders) > 1:
            id_list = ", ".join([f"'{t['name']}' (ID: {t['id']})" for t in matching_tenders])
            return f"Multiple tenders found matching '{tender_name}'. Please be more specific. Found: {id_list}"

        tender_id = matching_tenders[0]['id']
        tender_details = await self._make_request("GET", f"/tenders/{tender_id}")
        
        all_results = tender_details.get('analysis_results', [])
        
        if analysis_name:
            filtered_results = [r for r in all_results if r.get('name', '').lower() == analysis_name.lower()]
            if not filtered_results:
                return f"No analysis named '{analysis_name}' found in tender '{tender_name}'."
            return await self._format_analysis_results(tender_details['name'], filtered_results)

        return await self._format_analysis_results(tender_details['name'], all_results)

    def _format_single_analysis_result(self, result_data: dict) -> str:
        """Formats a single, detailed analysis result into a human-readable string."""
        output = f"Details for analysis '**{result_data.get('name', 'N/A')}**':\n"
        output += f"- **Status:** {result_data.get('status', 'N/A')}\n"
        output += f"- **Procedure:** {result_data.get('procedure_name', 'N/A')}\n"
        output += f"- **Created At:** {result_data.get('created_at', 'N/A')}\n"

        if result_data.get('status', '').lower() == 'completed':
            output += "\n- **Result Data:**\n"
            data = result_data.get('data')
            if not data:
                output += "  - No detailed data available.\n"
            else:
                output += self._format_any_data(data, level=1)
        elif result_data.get('status', '').lower() == 'failed':
            output += f"- **Error:** {result_data.get('error_message', 'No error details provided.')}\n"
        else:
            output += "This analysis is not yet complete. Only full data for 'COMPLETED' analyses can be shown.\n"
        
        return output

    async def get_analysis_result_by_name(self, analysis_name: str) -> str:
        """
        Finds a specific analysis result by name and shows its detailed information.
        """
        matching_results = await self._make_request("GET", f"/analysis-results/all_for_user?name={analysis_name}")
        
        if not matching_results:
            return f"No analysis result found with the name '{analysis_name}'."
        
        if len(matching_results) > 1:
            id_list = ", ".join([f"'{r['name']}' (ID: {r['id']})" for r in matching_results])
            return f"Multiple analysis results found. Please be more specific. Found: {id_list}"
        
        analysis_summary = matching_results[0]
        analysis_id = analysis_summary['id']
        
        if analysis_summary.get('status', '').lower() == 'completed':
            try:
                full_details = await self._make_request("GET", f"/analysis-results/{analysis_id}")
                return self._format_single_analysis_result(full_details)
            except Exception:
                return f"Found completed analysis '{analysis_name}', but could not retrieve its full details."
        else:
            return self._format_single_analysis_result(analysis_summary)

    def get_tools(self) -> List[FunctionTool]:
        """
        Exposes the agent's capabilities as a list of tools for an LLM to use.
        """
        return [
            FunctionTool.from_defaults(self.list_my_workspaces, description="Get a list of all of the user's workspaces and their basic details."),
            FunctionTool.from_defaults(self.list_all_tenders, description="Retrieve a list of all tenders the user has access to, across all workspaces."),
            FunctionTool.from_defaults(self.list_tenders_in_workspace, description="List all tenders within a specific workspace. The user must provide the name of the workspace."),
            FunctionTool.from_defaults(self.get_tender_analysis_details, description="Get analysis results for a specific tender. You must provide the tender's name. If the user also specifies an analysis name, provide that too."),
            FunctionTool.from_defaults(self.get_analysis_result_by_name, description="Find a specific analysis result by its name and get its detailed information."),
        ]

    def get_system_prompt(self) -> str:
        """
        Returns the system prompt that defines the agent's behavior by loading it from a YAML file.
        """
        prompt_file = "backend/chatbot/prompts.yml"
        try:
            with open(prompt_file, "r") as f:
                prompts = yaml.safe_load(f)
                return prompts.get("review_agent_instructions", "You are a helpful assistant.")
        except (IOError, yaml.YAMLError) as e:
            print(f"Warning: Could not read or parse {prompt_file}. Error: {e}. Using default prompt.")
            return "You are a helpful assistant."
