"""
Gestor de WebSockets para notificaciones en tiempo real.
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import logging, json

from backend.auth.auth_utils import get_current_active_user
from backend.auth.models import User

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Gestor de conexiones WebSocket para notificaciones en tiempo real.
    """
    
    def __init__(self):
        # Diccionario: user_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Conectar un nuevo WebSocket para un usuario.
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket conectado para usuario {user_id}. Total conexiones: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Desconectar un WebSocket de un usuario.
        """
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"WebSocket desconectado para usuario {user_id}")
                
                # Si no quedan conexiones, eliminar la entrada
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            except ValueError:
                pass
    
    async def send_to_user(self, user_id: str, message: dict):
        """
        Enviar un mensaje a todas las conexiones de un usuario específico.
        """
        if user_id not in self.active_connections:
            logger.warning(f"Usuario {user_id} no tiene conexiones WebSocket activas")
            return
        
        # Enviar a todas las conexiones del usuario
        disconnected = []
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error enviando mensaje a usuario {user_id}: {e}")
                disconnected.append(connection)
        
        # Limpiar conexiones muertas
        for conn in disconnected:
            self.disconnect(conn, user_id)
    
    async def broadcast(self, message: dict):
        """
        Enviar un mensaje a todos los usuarios conectados.
        """
        for user_id, connections in self.active_connections.items():
            await self.send_to_user(user_id, message)
    
    async def send_to_workspace(self, workspace_id: str, message: dict):
        """
        Enviar un mensaje a todos los usuarios de un workspace.
        (Necesitarías tener un mapeo workspace -> users)
        """
        # TODO: Implementar si necesitas notificaciones a nivel de workspace
        pass


# Instancia global del gestor
websocket_manager = WebSocketManager()