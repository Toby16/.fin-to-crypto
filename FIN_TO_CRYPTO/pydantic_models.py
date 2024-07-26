from typing import Optional
from pydantic import BaseModel, Field


class FileRequest(BaseModel):
    # Only pass .fin files
    filename: str = Field(examples=["test.fin"])


class initialize_transfer_model(BaseModel):
    sender_address: Optional[str] = Field(default=None,examples=["0xYourSenderAddress"])
    sender_private_key: Optional[str] = Field(default=None, examples=["YourPrivateKey"])
    recipient_address: Optional[str] = Field(default=None, examples=["0xRecipientAddress"])
    amount_to_transfer: Optional[float] = Field(default=None, examples=[0.01])
    currency: Optional[str] = Field(default=None, examples=["BTC", "USDT"])
