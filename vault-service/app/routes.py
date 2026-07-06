from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models import AuditLog, Document
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

    audit_log = AuditLog(
        user_email=user["sub"],
        action="UPLOAD",
        filename=file.filename
    )
    db.add(audit_log)
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

@router.get("/download-url/{document_id}")
def download_file(
    document_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_email != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    download_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_BUCKET,
            "Key": document.s3_key.replace("uploads/", "processed/")
        },
        ExpiresIn=300
    )

    log = AuditLog(
    user_email=user["sub"],
    action="DOWNLOAD",
    filename=document.filename
)

    db.add(log)
    db.commit()
    
    return {
        "download_url": download_url
    }
    
    
@router.put("/complete/{file_key:path}")
def complete_upload(file_key: str, db: Session = Depends(get_db)):
    
    document = db.query(Document).filter(
        Document.s3_key == file_key
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    document.status = "Processed"

    db.commit()

    return {
        "message": "Updated"
    }
    
@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).all()

@router.get("/download/{doc_id}")
def download_document(doc_id: int, db: Session = Depends(get_db)):

    document = db.query(Document).filter(
        Document.id == doc_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    processed_key = document.s3_key.replace(
        "uploads/",
        "processed/"
    )

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_BUCKET,
            "Key": processed_key
        },
        ExpiresIn=300
    )

    return {
        "download_url": url
    }