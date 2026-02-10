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
            # We can receive messages from the client if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, analysis_id)
