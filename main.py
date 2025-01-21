import json
import mimetypes
import time
from io import BytesIO
from uuid import uuid4

import boto3
import redis
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, File, HTTPException, Request, UploadFile

from database import ImageTable, SessionDep, UserImageTable, UserTable
from mock_descripton_service import get_image_description
from models import Image, User, UserCreate

app = FastAPI()
redis_client = redis.Redis(host="localhost", port=6379, db=0)

BUCKET_NAME = "wh1fty-test"
DEFAULT_EXPIRATION = 3600

s3 = boto3.client("s3")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.2f} ms"
    return response


@app.get("/")
async def root():
    return {"Hello": "World"}


@app.get("/images/{user_id}")
async def get_all_user_images(user_id: str, db: SessionDep):
    try:
        img_data = redis_client.get(f"img:{user_id}")

        if img_data:
            print("cache hit")
            return json.loads(img_data.decode("utf-8"))
        else:
            print("cache miss")
            img_data = (
                db.query(ImageTable)
                .join(UserImageTable, ImageTable.id == UserImageTable.image_id)
                .filter(UserImageTable.user_id == user_id)
                .all()
            )

            img_respose = [
                Image(id=img_item.id, url=img_item.url, desc=img_item.desc).model_dump()
                for img_item in img_data
            ]

            redis_client.setex(
                f"img:{user_id}",
                DEFAULT_EXPIRATION,
                json.dumps(img_respose),
            )

            return img_data

    except Exception as e:
        print(f"Error occured: {e}")


# File operations
@app.post("/images/upload/{user_id}")
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

        # invalidate cache
        redis_client.delete(f"img:{user_id}")

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
