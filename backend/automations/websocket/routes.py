from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from .connection_manager import ConnectionManager, get_connection_manager

router = APIRouter()

@router.websocket("/ws/analysis/{analysis_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    analysis_id: str,
    manager: ConnectionManager = Depends(get_connection_manager)
):
    await manager.connect(websocket, analysis_id)
    try:
        while True:
            # Keep the connection alive to receive updates from the server
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Client disconnected, which is a normal part of the lifecycle
        pass
    finally:
        # Ensure the connection is always cleaned up
        manager.disconnect(websocket, analysis_id)
