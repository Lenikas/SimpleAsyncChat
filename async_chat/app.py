from datetime import datetime
from typing import Any, List

import redis
from async_chat.models import Message
from fastapi import FastAPI, Request, WebSocket, websockets
from fastapi.templating import Jinja2Templates

app = FastAPI()
rd = redis.Redis.from_url('redis://0.0.0.0')
rd.lpush('messages', '')
rd.flushall()

templates = Jinja2Templates(directory='templates')

connections: List[WebSocket] = []


@app.get('/{username}')
async def get(request: Request, username: str) -> Any:
    return templates.TemplateResponse(
        'chat_page.html', {'request': request, 'username': username}
    )


@app.get('/messages/last50')
async def get_last_messages(request: Request) -> Any:
    rd.ltrim('messages', 0, 49)
    messages = rd.lrange('messages', 0, 49)
    return templates.TemplateResponse(
        'last_messages_page.html', {'request': request, 'messages': messages}
    )


async def chat_logic(websocket: WebSocket, username: str) -> None:
    try:
        while True:
            data: str = await websocket.receive_text()
            model_data = {'user': username, 'text': data, 'date_time': datetime.now()}
            message = Message(**model_data)
            rd.lpush(
                'messages',
                f'{message.user} write message: {message.text} on time: {datetime.now()}',
            )
            for connection in connections:
                await connection.send_text(f'{username}: {data}')
    except websockets.WebSocketDisconnect:
        await websocket.close()
        connections.remove(websocket)


@app.websocket('/ws/{username}')
async def websocket_endpoint(websocket: WebSocket, username: str) -> None:
    await websocket.accept()
    if websocket not in connections:
        connections.append(websocket)
    await chat_logic(websocket, username)
