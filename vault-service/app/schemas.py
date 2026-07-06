from pydantic import BaseModel


class UploadRequest(BaseModel):
    filename: str

class UploadResponse(BaseModel):
    upload_url: str
    file_key: str

    