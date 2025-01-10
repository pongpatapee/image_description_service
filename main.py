import mimetypes
from io import BytesIO
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, File, HTTPException, UploadFile

from database import ImageTable, SessionDep, UserImageTable, UserTable
from mock_descripton_service import get_image_description
from models import User, UserCreate

app = FastAPI()

BUCKET_NAME = "wh1fty-test"
s3 = boto3.client("s3")


@app.get("/")
async def root():
    return {"Hello": "World"}


# TODO: Get user's images and implement redis caching


# File operations
@app.post("/upload/{user_id}")
async def upload_image(user_id: str, db: SessionDep, file: UploadFile = File(...)):
    try:

        # Upload to s3
        file_content = await file.read()
        file_obj = BytesIO(file_content)
        content_type = mimetypes.guess_type(file.filename)
        if not content_type:
            content_type = "application/octet-stream"
        else:
            content_type = content_type[0]

        image_id = str(uuid4())

        s3_key = f"{user_id}/{image_id}"
        s3.upload_fileobj(
            file_obj, BUCKET_NAME, s3_key, ExtraArgs={"ContentType": content_type}
        )

        public_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        # Upload to DB
        desc = get_image_description()

        image_entry = ImageTable(id=image_id, url=public_url, desc=desc)
        user_image_relation = UserImageTable(user_id=user_id, image_id=image_id)
        db.add(image_entry)
        db.add(user_image_relation)
        db.commit()

        return {"message": "File uploaded successfully", "url": public_url}

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
