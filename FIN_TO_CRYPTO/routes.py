from FIN_TO_CRYPTO import app
from fastapi import status, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dropbox.files import WriteMode
from dropbox import Dropbox, exceptions
from dropbox.exceptions import ApiError

import dropbox

import os

DROPBOX_API_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

@app.get("/", status_code=status.HTTP_200_OK)
def index():
    return {
        "statusCode": 200,
        "message": "nothing to see here!"
        # "DROPBOX_API_TOKEN": DROPBOX_API_TOKEN
    }


@app.post("/file_upload", status_code=status.HTTP_200_OK, tags=["File"])
@app.post("/file_upload/", status_code=status.HTTP_200_OK, tags=["File"])
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to only accept .fin files
    ... and upload to dropox.
    """

    # Validate .fin file extension
    if not file.filename.endswith(".fin"):
        raise HTTPException(status_code=400, detail="Only .fin files are allowed")


    # Initialize Dropbox client
    dropbox_client = dropbox.Dropbox(DROPBOX_API_TOKEN)
    """
    # Save the file to a temporary location
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, 'wb') as out_file:
        content = file.file.read()
        out_file.write(content)
    """


    try:
        # Read the file contents
        file_contents = await file.read()

        # Define the Dropbox path
        dropbox_path = f'/{file.filename}'

        # Upload the file to Dropbox
        dropbox_client.files_upload(file_contents, dropbox_path, mode=WriteMode('overwrite'))

        return {"message": "File uploaded successfully", "file_path": dropbox_path}

    except exceptions.ApiError as e:
        raise HTTPException(status_code=500, detail=f"Dropbox API error: {e.error}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

