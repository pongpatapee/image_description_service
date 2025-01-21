from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str


class User(BaseModel):
    id: str
    name: str
    email: str


class Image(BaseModel):
    id: str
    url: str
    desc: str
