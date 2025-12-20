"""FastAPI server for MACSDK chatbot web interface.

Provides a WebSocket endpoint for real-time streaming chat interactions
with the multi-agent chatbot system.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketState

from ..._version import __version__
from ...core.config import config
from ...core.state import ChatbotState

if TYPE_CHECKING:
    from langgraph.graph.graph import CompiledGraph

# Configure logging
logger = logging.getLogger(__name__)

# WebSocket configuration constants
MESSAGE_MAX_LENGTH = config.message_max_length

# Warmup configuration
WARMUP_QUERY = "Hello"


class WebSocketMessage(BaseModel):
    """Model for incoming WebSocket messages."""

    message: str = Field(
        ..., min_length=1, max_length=MESSAGE_MAX_LENGTH, description="User message"
    )


class WebSocketResponse(BaseModel):
    """Model for outgoing WebSocket responses."""

    type: str = Field(..., description="Message type")
    content: str | None = Field(None, description="Message content")


async def safe_send_json(websocket: WebSocket, data: dict) -> None:
    """Safely send JSON data through WebSocket.

    Checks connection state before sending and silently handles errors.

    Args:
        websocket: The WebSocket connection.
        data: Dictionary to send as JSON.
    """
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(data)
    except Exception:  # nosec B110
        pass  # WebSocket may be closed, safe to ignore


def create_initial_state() -> ChatbotState:
    """Create initial chatbot state."""
    return {
        "messages": [],
        "user_query": "",
        "chatbot_response": "",
        "workflow_step": "query",
    }


def create_web_app(
    graph: "CompiledGraph",
    title: str = "MACSDK Chatbot",
    static_dir: Path | None = None,
) -> FastAPI:
    """Create a FastAPI app for the chatbot.

    Args:
        graph: The compiled chatbot graph to use.
        title: Title for the API.
        static_dir: Optional path to static files directory.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(title=title, version=__version__)

    # Mount static files if provided
    if static_dir and static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    async def warmup_graph() -> None:
        """Warm up the chatbot graph with a test query."""
        try:
            logger.info("Warming up chatbot graph...")
            test_state: ChatbotState = {
                "messages": [HumanMessage(content=WARMUP_QUERY)],
                "user_query": WARMUP_QUERY,
                "chatbot_response": "",
                "workflow_step": "processing",
            }
            try:
                async with asyncio.timeout(config.warmup_timeout):
                    async for _ in graph.astream(test_state, stream_mode=["updates"]):
                        pass
            except TimeoutError:
                logger.warning(f"Graph warmup timed out after {config.warmup_timeout}s")
                return
            logger.info("Chatbot graph warmed up successfully")
        except Exception as e:
            logger.warning(f"Graph warmup failed: {e}")

    @app.on_event("startup")
    async def startup_event() -> None:
        """Execute startup tasks."""
        logger.info("Running startup tasks...")
        await warmup_graph()
        logger.info("Startup tasks completed")

    @app.get("/", response_class=HTMLResponse)
    async def root() -> HTMLResponse:
        """Serve the main HTML page."""
        if static_dir:
            html_file = static_dir / "index.html"
            if html_file.exists():
                return HTMLResponse(content=html_file.read_text())
        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <h1>{title}</h1>
                    <p>Connect via WebSocket at /ws</p>
                </body>
            </html>
            """
        )

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time chat streaming."""
        await websocket.accept()
        state = create_initial_state()

        try:
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    validated_message = WebSocketMessage(**message_data)
                    user_message = validated_message.message.strip()
                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                    raise
                except json.JSONDecodeError:
                    await safe_send_json(
                        websocket, {"type": "error", "content": "Invalid JSON"}
                    )
                    continue
                except Exception as e:
                    await safe_send_json(
                        websocket, {"type": "error", "content": str(e)}
                    )
                    continue

                if not user_message:
                    continue

                state.update(
                    {
                        "messages": state.get("messages", [])
                        + [HumanMessage(content=user_message)],
                        "user_query": user_message,
                        "workflow_step": "processing",
                    }
                )

                await safe_send_json(
                    websocket, {"type": "user_message", "content": user_message}
                )

                try:
                    # Use same stream modes as CLI for consistency
                    stream = graph.astream(state, stream_mode=["values", "custom"])
                    async for chunk in stream:
                        if websocket.client_state != WebSocketState.CONNECTED:
                            break

                        if isinstance(chunk, tuple) and len(chunk) == 2:
                            stream_mode_type, stream_data = chunk

                            if stream_mode_type == "custom":
                                if isinstance(stream_data, str):
                                    await safe_send_json(
                                        websocket,
                                        {"type": "progress", "content": stream_data},
                                    )
                                elif isinstance(stream_data, dict):
                                    for value in stream_data.values():
                                        if isinstance(value, str):
                                            await safe_send_json(
                                                websocket,
                                                {"type": "progress", "content": value},
                                            )
                            elif stream_mode_type == "values":
                                # Update state with final values
                                if isinstance(stream_data, dict):
                                    state.update(stream_data)  # type: ignore

                    final_response = state.get("chatbot_response", "")
                    if final_response:
                        await safe_send_json(
                            websocket,
                            {"type": "bot_response", "content": final_response},
                        )

                    await safe_send_json(websocket, {"type": "complete"})

                except asyncio.CancelledError:
                    logger.info("Graph execution cancelled")
                    raise
                except Exception as e:
                    await safe_send_json(
                        websocket, {"type": "error", "content": str(e)}
                    )
                    logger.error(f"Error processing message: {e}")

        except (WebSocketDisconnect, asyncio.CancelledError):
            logger.info("Client disconnected or cancelled")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await safe_send_json(websocket, {"type": "error", "content": str(e)})

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


def run_web_server(
    graph: "CompiledGraph",
    title: str = "MACSDK Chatbot",
    static_dir: Path | None = None,
    host: str | None = None,
    port: int | None = None,
) -> None:
    """Run the FastAPI web server.

    Args:
        graph: The compiled chatbot graph to use.
        title: Title for the API.
        static_dir: Path to static files directory for custom UI.
        host: Host to bind to (defaults to config value).
        port: Port to bind to (defaults to config value).
    """
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = create_web_app(graph, title, static_dir)

    host = host or config.server_host
    port = port or config.server_port

    logger.info(f"Starting {title} Web Server...")
    logger.info(f"Server running on http://{host}:{port}")
    logger.info(f"Open your browser at http://localhost:{port}")

    uvicorn.run(app, host=host, port=port)
