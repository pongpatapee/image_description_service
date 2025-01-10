from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import Column, ForeignKey, String, create_engine

# from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "sqlite:///./data/storage.db"  # SQLite DB file
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    # email = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False)

    # images = relationship("UserImageTable", back_populates="user")


class ImageTable(Base):
    __tablename__ = "images"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    url = Column(String, nullable=False)
    desc = Column(String, nullable=False)

    # users = relationship("UserImageTable", back_populates="image")


class UserImageTable(Base):
    __tablename__ = "users_images"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    image_id = Column(String, ForeignKey("images.id"), nullable=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
