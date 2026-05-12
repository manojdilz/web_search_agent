"""
Main application entry point.
Initializes and configures the FastAPI application.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Settings, get_settings, setup_logging
from agent import AgentFactory
from services import ChatStreamService
from routes import create_chat_routes


# Global instances
logger: logging.Logger = None
settings: Settings = None
app: FastAPI = None
agent_factory: AgentFactory = None
chat_service: ChatStreamService = None


def init_logging() -> logging.Logger:
    global logger
    settings = get_settings()
    logger = setup_logging(settings.log_level)
    logger.info("Logging initialized")
    return logger


def init_config() -> Settings:
    global settings
    settings = get_settings()
    logger.info(f"Configuration loaded: {settings.llm_model}")
    return settings


async def init_agent() -> AgentFactory:
    global agent_factory
    agent_factory = AgentFactory(settings)
    logger.info("Agent factory initialized")
    return agent_factory


async def init_services() -> ChatStreamService:
    global chat_service
    graph = await agent_factory.get_compiled_graph()
    chat_service = ChatStreamService(graph)
    logger.info("Chat stream service initialized")
    return chat_service


def setup_routes(app: FastAPI) -> FastAPI:
    router = create_chat_routes(chat_service)
    app.include_router(router)
    logger.info("Routes configured")
    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Perplexity 2.0 Backend")
    await init_agent()
    await init_services()
    setup_routes(app)
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Perplexity 2.0 Backend")


def create_app() -> FastAPI:
    init_logging()
    init_config()

    app = FastAPI(
        title="Perplexity 2.0 Backend",
        description="AI-powered search and response streaming backend",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
        expose_headers=["Content-Type"],
    )

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
