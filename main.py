from io import BytesIO
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, File, HTTPException, UploadFile, status

from database import SessionDep, UserTable
from models import Image, User, UserCreate

app = FastAPI()

BUCKET_NAME = "wh1fty-test"
s3 = boto3.client("s3")


@app.get("/")
async def root():
    return {"Hello": "World"}


# File operations
@app.post("/upload")
async def upload_image(user_id: str, file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        file_obj = BytesIO(file_content)

        s3_key = str(uuid4())
        s3.upload_fileobj(file_obj, BUCKET_NAME, s3_key)

    except (BotoCoreError, ClientError) as e:
        # Handle S3 errors
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
    except Exception as e:
        # Handle general errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


# User operations
@app.post("/user")
async def create_user(user_create: UserCreate, db: SessionDep):

    # Check if user alredy exists
    # user_exists = (
    #     session.query(UserTable).filter(UserTable.email == user_create.email).first()
    # )
    # if user_exists:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="User with this email already exist",
    #     )

    new_user = UserTable(name=user_create.name, email=user_create.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # refresh to get UUID

    return User(id=new_user.id, name=new_user.name, email=new_user.email)


@app.get("/user/{user_id}")
async def get_user(user_id: str, db: SessionDep):
    user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return User(id=user.id, name=user.name, email=user.email)


@app.delete("/user/{user_id}")
async def delete_user(user_id: str, db: SessionDep):
    user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user)
    db.commit()
    return {"message": f"User {id} deleted successfully."}
