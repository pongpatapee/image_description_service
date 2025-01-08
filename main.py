from io import BytesIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, File, HTTPException, UploadFile

app = FastAPI()

BUCKET_NAME = "wh1fty-test"
s3 = boto3.client("s3")


@app.get("/")
async def root():
    return {"Hello": "World"}


@app.post("/upload")
async def upload_file(file_name: str, file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        file_obj = BytesIO(file_content)

        s3_key = f"uploads/{file_name}"
        s3.upload_fileobj(file_obj, BUCKET_NAME, s3_key)

    except (BotoCoreError, ClientError) as e:
        # Handle S3 errors
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
    except Exception as e:
        # Handle general errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
