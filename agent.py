"""
LangGraph agent setup and execution.
Manages the agentic workflow with model and tool nodes.
"""

import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage
from langchain_tavily import TavilySearch

from models import State
from config import Settings

logger = logging.getLogger(__name__)


class ToolFactory:
    """Factory for creating and managing tools."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._tools = None

    @property
    def tools(self) -> list:
        """Lazily initialize and return tools list."""
        if self._tools is None:
            self._tools = [TavilySearch(
                max_results=self.settings.tavily_max_results, tavily_api_key=self.settings.tavily_api_key)]
        return self._tools

    @property
    def search_tool(self) -> TavilySearch:
        """Get the search tool."""
        return self.tools[0]


class LLMFactory:
    """Factory for creating and managing LLM instances."""

    def __init__(self, settings: Settings):
        """Initialize LLM factory."""
        self.settings = settings
        self._llm = None

    @property
    def llm(self):
        """Lazily initialize and return LLM instance."""
        if self._llm is None:
            try:
                self._llm = init_chat_model(
                    model=self.settings.llm_model,
                    model_provider=self.settings.llm_provider,
                    api_key=self.settings.groq_api_key
                )
                logger.info(f"LLM initialized: {self.settings.llm_model}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise

        return self._llm

    def get_llm_with_tools(self, tool_factory: ToolFactory):
        """Get LLM bound with tools."""
        return self.llm.bind_tools(tool_factory.tools)


class GraphBuilder:
    """Builds and manages the LangGraph agent workflow."""

    NODE_MODEL = "model"
    NODE_TOOL = "tool_node"

    def __init__(self, llm_with_tools, tool_factory: ToolFactory):
        """Initialize graph builder."""
        self.llm_with_tools = llm_with_tools
        self.tool_factory = tool_factory
        self._graph = None
        self._memory = InMemorySaver()

    async def model_node(self, state: State) -> dict:
        """
        Model node: Process messages with LLM.

        Args:
            state: Current graph state

        Returns:
            Updated state with model response
        """
        try:
            result = await self.llm_with_tools.ainvoke(state["messages"])
            return {"messages": [result]}
        except Exception as e:
            logger.error(f"Error in model node: {e}")
            raise

    async def tool_router(self, state: State) -> str:
        """
        Route based on tool calls in last message.

        Args:
            state: Current graph state

        Returns:
            Next node name
        """
        last_msg = state["messages"][-1]

        if hasattr(last_msg, "tool_calls") and len(last_msg.tool_calls) > 0:
            return self.NODE_TOOL
        return END

    async def tool_node(self, state: State) -> dict:
        tool_calls = state["messages"][-1].tool_calls
        tool_map = {
            tool.name: tool for tool in self.tool_factory.tools
        }
        tool_messages = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args")
            tool_id = tool_call.get("id")

            tool = tool_map.get(tool_name)
            if tool is None:
                tool_messages.append(ToolMessage(
                    content=f"Unknown tool: {tool_name}",
                    tool_call_id=tool_id,
                    name=tool_name
                ))
                continue

            try:
                result = await tool.ainvoke(tool_args)
                tool_messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_id,
                    name=tool_name
                ))
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tool_messages.append(ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_id,
                    name=tool_name
                ))

        return {"messages": tool_messages}

    def build(self) -> "CompiledGraph":
        """
        Build the compiled graph.

        Returns:
            Compiled graph instance
        """
        if self._graph is not None:
            return self._graph

        try:
            builder = StateGraph(State)
            builder.add_node(self.NODE_MODEL, self.model_node)
            builder.add_node(self.NODE_TOOL, self.tool_node)

            builder.add_edge(START, self.NODE_MODEL)
            builder.add_conditional_edges(self.NODE_MODEL, self.tool_router)
            builder.add_edge(self.NODE_TOOL, self.NODE_MODEL)

            self._graph = builder.compile(checkpointer=self._memory)
            logger.info("Graph built successfully")

        except Exception as e:
            logger.error(f"Failed to build graph: {e}")
            raise

        return self._graph


class AgentFactory:
    """Factory for creating configured agent instances."""

    def __init__(self, settings: Settings):
        """Initialize agent factory."""
        self.settings = settings
        self.tool_factory = ToolFactory(settings)
        self.llm_factory = LLMFactory(settings)

    def create_graph_builder(self) -> GraphBuilder:
        """Create and return configured graph builder."""
        llm_with_tools = self.llm_factory.get_llm_with_tools(self.tool_factory)
        return GraphBuilder(llm_with_tools, self.tool_factory)

    async def get_compiled_graph(self):
        """Get compiled graph for execution."""
        graph_builder = self.create_graph_builder()
        return graph_builder.build()
