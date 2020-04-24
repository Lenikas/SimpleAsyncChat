from datetime import datetime
from typing import Any, List

import redis
from async_chat.models import Message
from fastapi import FastAPI, HTTPException, Request, WebSocket, websockets
from fastapi.templating import Jinja2Templates

app = FastAPI()

rd = redis.Redis()
rd.lpush('messages', '')

templates = Jinja2Templates(directory='templates')

connections: List[WebSocket] = []


@app.get('/{username}')
async def get(request: Request, username: str) -> Any:
    return templates.TemplateResponse(
        'chat_page.html', {'request': request, 'username': username}
    )


@app.get('/messages/last/{count}')
async def get_last_messages(request: Request, count: str) -> Any:
    try:
        count_messages = int(count)
    except ValueError:
        raise HTTPException(
            status_code=404, detail={'Error': 'Count of last messages must be a number'}
        )
    if count_messages > 50 or count_messages < 0:
        raise HTTPException(
            status_code=404,
            detail={'Error': 'Count of last messages must be less that 50 and more 0'},
        )

    messages = rd.lrange('messages', 0, count_messages - 1)
    return templates.TemplateResponse(
        'last_messages_page.html', {'request': request, 'messages': messages}
    )


async def chat_logic(websocket: WebSocket, username: str) -> None:
    try:
        while True:
            data: str = await websocket.receive_text()
            message = Message(user=username, text=data, date_time=datetime.utcnow())
            rd.lpush(
                'messages',
                f'{message.user} write message: {message.text} on time: {message.date_time}',
            )
            rd.ltrim('messages', 0, 49)
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
