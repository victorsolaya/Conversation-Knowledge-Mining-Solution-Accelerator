from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from agents.agent_factory_base import BaseAgentFactory


class ChartAgentFactory(BaseAgentFactory):
    """
    Factory class for creating Chart agents that generate chart.js compatible JSON
    based on numerical and structured data from RAG responses.
    """

    @classmethod
    async def create_agent(cls, config):
        """
        Asynchronously creates an AI agent configured to convert structured data
        into chart.js-compatible JSON using Azure AI Project.

        Args:
            config: Configuration object containing AI project and model settings.

        Returns:
            dict: A dictionary containing the created 'agent' and its associated 'client'.
        """
        instructions = '''You are an assistant that generates valid Chart.js v4.4.4 compatible JSON.
        Your goal is to produce a JSON object that includes:
        - `type` (chart type: bar, line, pie, etc.)
        - `data` (with `labels` and `datasets`)
        - `options` (to enhance rendering and clarity)
        Important Rules:
        - Combine both the user's query and the provided tabular/textual data to choose the best chart type.
        - Only generate a chart if the data contains numbers.
        - If no numbers are found, return:
        {"error": "Chart cannot be generated due to lack of numerical data."}
        - Do NOT include any explanations, markdown formatting, or tooltips — just clean JSON.
        - Remove all trailing commas.
        - Ensure the JSON can be parsed using `json.loads()` in Python.
        - Ensure axis ticks are readable (adjust `ticks.padding`, `maxWidth`, etc.).
        - Avoid bars being too narrow or cropped by setting reasonable `barPercentage` and `categoryPercentage`.
        '''

        project_client = AIProjectClient(
            endpoint=config.ai_project_endpoint,
            credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
            api_version=config.ai_project_api_version,
        )

        agent = project_client.agents.create_agent(
            model=config.azure_openai_deployment_model,
            name=f"KM-ChartAgent-{config.solution_name}",
            instructions=instructions,
        )

        return {
            "agent": agent,
            "client": project_client
        }

    @classmethod
    async def _delete_agent_instance(cls, agent_wrapper: dict):
        """
        Asynchronously deletes the specified chart agent instance from the Azure AI project.

        Args:
            agent_wrapper (dict): Dictionary containing the 'agent' and 'client' to be removed.
        """
        agent_wrapper["client"].agents.delete_agent(agent_wrapper["agent"].id)
