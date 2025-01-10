from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str


class User(BaseModel):
    id: UUID
    name: str
    email: str


class Image(BaseModel):
    id: UUID
    url: str
    desc: str
