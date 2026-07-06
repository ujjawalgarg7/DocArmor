from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models import Document
from app.s3 import s3_client
from app.config import settings
from app.schemas import UploadRequest, UploadResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/upload-url", response_model=UploadResponse)
def generate_upload_url(file: UploadRequest,
                        user = Depends(get_current_user)
                        ,db: Session = Depends(get_db)):

    key = f"uploads/{uuid.uuid4()}_{file.filename}"

    document = Document(
        owner_email=user["sub"],   
        filename=file.filename,
        s3_key=key,
        status="Pending"
    )

    db.add(document)
    db.commit()

    upload_url = s3_client.generate_presigned_url(
    "put_object",
    Params={
        "Bucket": settings.AWS_BUCKET,
        "Key": key
    },
    ExpiresIn=300
)
    
    print(upload_url)
    
    return {
        "upload_url": upload_url,
        "file_key": key
    }