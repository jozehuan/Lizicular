from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, analysis_id: str):
        await websocket.accept()
        if analysis_id not in self.active_connections:
            self.active_connections[analysis_id] = []
        self.active_connections[analysis_id].append(websocket)

    def disconnect(self, websocket: WebSocket, analysis_id: str):
        if analysis_id in self.active_connections:
            self.active_connections[analysis_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection_list in self.active_connections.values():
            for connection in connection_list:
                await connection.send_text(message)

    async def send_to_analysis_id(self, message: dict, analysis_id: str):
        if analysis_id in self.active_connections:
            for connection in self.active_connections[analysis_id]:
                await connection.send_json(message)

def get_connection_manager() -> ConnectionManager:
    return ConnectionManager()