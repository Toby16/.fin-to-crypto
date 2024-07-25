from FIN_TO_CRYPTO import app
from fastapi import status, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dropbox.files import WriteMode
from dropbox import Dropbox, exceptions
from dropbox.exceptions import ApiError
from FIN_TO_CRYPTO.pydantic_models import FileRequest

import dropbox
import json
import os

DROPBOX_API_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
FIN_FOLDER = os.getenv("FIN_FOLDER")


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


@app.post("/file_fetch", status_code=status.HTTP_200_OK, tags=["File"])
@app.post("/file_fetch/", status_code=status.HTTP_200_OK, tags=["File"])
async def fetch_file(file_request: FileRequest):
    """
    Endpoint to only accept .fin files
    ... and download from dropox to server storage
    """

    # Validate .fin file extension
    if not file_request.filename.endswith(".fin"):
        raise HTTPException(status_code=400, detail="Only .fin files are allowed")


    # Initialize Dropbox client
    dropbox_client = dropbox.Dropbox(DROPBOX_API_TOKEN)

    # Handle file destination in storage server
    filename = file_request.filename

    if filename.startswith("/"):
        # filename.replace("/", "", 1)
        filename = filename.lstrip("/")

    local_folder = FIN_FOLDER
    os.makedirs(local_folder, exist_ok=True)
    local_path = os.path.join(local_folder, filename)

    
    try:
        search_result = dropbox_client.files_search(
            path="",  # Search from the root directory
            query=filename,
            mode=dropbox.files.SearchMode.filename,
            max_results=5
        )

        if not search_result.matches:
            # print(search_result.matches)
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found in Dropbox")


        dropbox_path = search_result.matches[0].metadata.path_lower


        with open(local_path, "wb") as f:
            metadata, res = dropbox_client.files_download(path=dropbox_path)
            f.write(res.content)
    except dropbox.exceptions.ApiError as err:
        raise HTTPException(status_code=400, detail=f"Dropbox API error: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

    return {
        "message": f"File '{filename}' downloaded successfully.",
        "path": "{}".format(local_path),
        "filename": filename
    }


@app.post("/get_file_details", status_code=status.HTTP_200_OK, tags=["File"])
@app.post("/get_file_details/", status_code=status.HTTP_200_OK, tags=["File"])
def fetch_file(data: FileRequest):
    """
    Endpoint to only accept .fin files
    ... and download from dropox to server storage
    """

    # Validate .fin file extension
    if not data.filename.endswith(".fin"):
        raise HTTPException(status_code=400, detail="Only .fin files are allowed")


    filename = data.filename

    if filename.startswith("/"):
        # filename.replace("/", "", 1)
        filename = filename.lstrip("/")

    local_folder = FIN_FOLDER

    try:
        # Construct the full file path
        # file+path = local_folder + "/" + filename
        file_path = os.path.join(local_folder, filename)


        with open(file_path, "r") as f:
            data = f.read()

        # Convert JSON data to a dictionary
        data_dict = json.loads(data)
        # return data_dict

    except Exception as e:
        if (str(e)).startswith("[Errno 2] No such file or directory:"):
            raise HTTPException(status_code=400, detail="[Errno 2] No such file or directory!")


    details_ = {
        "recipient": {},
        "sender": {},
        "transfer_info": {}
    }

    # SENDER
    details_["sender"]["account_name"] = data_dict["message_header"]["rcvd_senders_account_name"]
    details_["sender"]["account_number"] = data_dict["message_header"]["rcvd_senders_account_number"]
    details_["sender"]["bank_name"] = data_dict["message_header"]["rcvd_senders_bank"]
    details_["sender"]["swift_code"] = data_dict["message_header"]["rcvd_senders_swift_code"]
    details_["sender"]["bank_address"] = data_dict["message_header"]["rcvd_senders_bank_address"]

    # RECIPIENT
    details_["recipient"]["bank_name"] = data_dict["recipient_bank"]

    # INFO
    details_["transfer_info"]["country"] = data_dict["account_country"]
    details_["transfer_info"]["amount"] = str(data_dict["transfer_amount"])
    details_["transfer_info"]["currency"] = data_dict["currency"]

    return {
        "statusCode": 200,
        "data": details_
    }
