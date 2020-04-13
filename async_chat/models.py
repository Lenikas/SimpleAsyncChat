from datetime import datetime

from pydantic import BaseModel


class Message(BaseModel):
    user: str
    text: str
    date_time: datetime
