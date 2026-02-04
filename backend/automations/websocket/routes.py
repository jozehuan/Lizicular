"""
Endpoint WebSocket para notificaciones en tiempo real.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import jwt, JWTError
import logging

from backend.auth.auth_utils import SECRET_KEY, ALGORITHM
from backend.automations.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


async def get_user_from_token(token: str) -> str:
    """
    Extraer user_id del token JWT.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise ValueError("user_id not found in token")
        return user_id
    except JWTError:
        raise ValueError("Invalid token")


@router.websocket("/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    Endpoint WebSocket para recibir notificaciones en tiempo real.
    
    El cliente debe conectarse con:
    ws://localhost:8000/ws/notifications?token=<JWT_TOKEN>
    
    Mensajes que recibirá:
    - analysis_status_update: Cuando cambia el estado de un análisis
    - analysis_completed: Cuando un análisis termina
    - system_notification: Notificaciones del sistema
    """
    try:
        # Autenticar al usuario
        user_id = await get_user_from_token(token)
    except ValueError as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008)  # Policy Violation
        return
    
    # Conectar el WebSocket
    await websocket_manager.connect(websocket, user_id)
    
    try:
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connection_established",
            "message": "Conectado a notificaciones en tiempo real",
            "user_id": user_id
        })
        
        # Mantener la conexión abierta
        while True:
            # Recibir mensajes del cliente (si los hay)
            data = await websocket.receive_text()
            
            # Puedes implementar comandos del cliente aquí
            # Por ejemplo: ping/pong, suscripciones específicas, etc.
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        websocket_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(websocket, user_id)