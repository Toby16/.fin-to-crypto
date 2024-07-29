from FIN_TO_CRYPTO import app
from fastapi import status, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dropbox.files import WriteMode
from dropbox import Dropbox, exceptions
from dropbox.exceptions import ApiError
from FIN_TO_CRYPTO.pydantic_models import (
    FileRequest, initialize_transfer_model
)

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


# Handling Bitcoin (BTC) Transfers
from bitcoinlib.wallets import Wallet
from bitcoinlib.transactions import Transaction

# Handling USDT (on Ethereum) Transfers to Bitcoin
from web3 import Web3

@app.post("/transfer", status_code=status.HTTP_200_OK, tags=["File"])
@app.post("/transfer/", status_code=status.HTTP_200_OK, tags=["File"])
def initialize_transfer(data: initialize_transfer_model):
    data = data.dict()

    # explicitly validate user input
    if data["sender_address"] is None:
        raise HTTPException(status_code=400, detail="Sender Address Not Found! Example: 0xYourSenderAddress")

    if data["sender_private_key"] is None:
        raise HTTPException(status_code=400, detail="Sender Private Key Noe Found! Example: [ hidden ]")

    if data["recipient_address"] is None:
        raise HTTPException(status_code=400, detail="Recipient Address Not Found! Example: 0xRecipientAddress")

    if data["amount_to_transfer"] is None:
        raise HTTPException(status_code=400, detail="Kindly input amount to transfer from {x} to {y}".format(x=data["sender_address"], y=data["recipient_address"]))

    if data["currency"] is None:
        # defaults to BTC
        data["currency"] = "BTC"
    elif data["currency"] not in ["BTC", "USDT"]:
        raise HTTPException(status_code=400, detail="Only accepting `BTC` or `USDT`!")



    # Handle BTC -> BTC
    if data["currency"] == "BTC":
        try:
            # Initialize a wallet (for example purpose, use Wallet API or self-hosted wallet)
            wallet = Wallet.create(
                data["sender_address"],
                keys=data["sender_private_key"],
                network='bitcoin'
            )

            # Create and sign the transaction
            tx = wallet.send_to(
                data["recipient_address"],
                data["amount_to_transfer"],
                network='bitcoin'
            )


            # Broadcast the transaction
            tx_hex = tx.as_hex()
            tx_hash = wallet.network.sendrawtransaction(tx_hex)

            return {
                "statusCode": 200,
                "message": "Transaction successful with hash: {tx_hash}".format(txt_hash=txt_hash)
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif data["currency"] == "USDT":
        try:
            pass

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


    return {
        "statusCode": 200,
        "message": "success!"
    }
