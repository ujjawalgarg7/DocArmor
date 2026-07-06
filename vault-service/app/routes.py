from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models import AuditLog, Document, SharedDocument
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
def list_documents(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    owned_docs = db.query(Document).filter(
        Document.owner_email == user["sub"]
    ).all()

    shared_rows = db.query(SharedDocument).filter(
        SharedDocument.shared_with_email == user["sub"]
    ).all()

    shared_doc_ids = [row.document_id for row in shared_rows]

    shared_docs = []

    if shared_doc_ids:
        shared_docs = db.query(Document).filter(
            Document.id.in_(shared_doc_ids)
        ).all()

    return {
        "owned": owned_docs,
        "shared": shared_docs
    }

@router.get("/download/{doc_id}")
def download_document(
    doc_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == doc_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    is_owner = document.owner_email == user["sub"]

    is_shared = db.query(SharedDocument).filter(
        SharedDocument.document_id == doc_id,
        SharedDocument.shared_with_email == user["sub"]
    ).first()

    if not is_owner and not is_shared:
        raise HTTPException(status_code=403, detail="Access denied")

    processed_key = document.s3_key.replace("uploads/", "processed/")

    download_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_BUCKET,
            "Key": processed_key
        },
        ExpiresIn=300
    )
    log = AuditLog(
    user_email=user["sub"],
    action="DOWNLOAD",
    filename=document.filename)

    db.add(log)
    db.commit()
    return {"download_url": download_url}
    
    
@router.post("/share/{document_id}")
def share_document(
    document_id: int,
    shared_with_email: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(404, "Document not found")

    if document.owner_email != user["sub"]:
        raise HTTPException(403, "Only owner can share this document")

    share = SharedDocument(
        document_id=document_id,
        owner_email=user["sub"],
        shared_with_email=shared_with_email
    )

    db.add(share)
    db.commit()

    return {"message": "Document shared successfully"}


@router.post("/share/{document_id}")
def share_document(
    document_id: int,
    shared_with_email: str = Query(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_email != user["sub"]:
        raise HTTPException(status_code=403, detail="Only owner can share this document")

    shared = SharedDocument(
        document_id=document.id,
        owner_email=user["sub"],
        shared_with_email=shared_with_email
    )

    db.add(shared)
    db.commit()

    return {"message": "Document shared successfully"}


@router.get("/logs")
def get_logs(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logs = db.query(AuditLog).filter(
        AuditLog.user_email == user["sub"]
    ).order_by(
        AuditLog.created_at.desc()
    ).all()

    return logs



@router.get("/document-logs/{document_id}")
def get_document_logs(
    document_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_email != user["sub"]:
        raise HTTPException(status_code=403, detail="Only owner can view document logs")

    logs = db.query(AuditLog).filter(
        AuditLog.filename == document.filename,
        AuditLog.action == "DOWNLOAD"
    ).order_by(
        AuditLog.created_at.desc()
    ).all()

    return logs