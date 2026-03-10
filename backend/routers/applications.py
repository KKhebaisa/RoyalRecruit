from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.entities import ApplicationType, Question
from backend.models.schemas import ApplicationSubmitIn, ApplicationTypeIn
from backend.services.application_service import create_application_type, submit_application
from backend.services.server_service import get_server_by_discord_id

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/types/{discord_server_id}")
def create_type(discord_server_id: str, payload: ApplicationTypeIn, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    app_type = create_application_type(db, server, payload)
    return {"id": app_type.id}


@router.get("/types/{discord_server_id}")
def list_types(discord_server_id: str, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    types = db.query(ApplicationType).filter(ApplicationType.server_id == server.id).all()
    response = []
    for app_type in types:
        questions = db.query(Question).filter(Question.application_type == app_type.id).order_by(Question.order_index).all()
        response.append({
            "id": app_type.id,
            "application_name": app_type.application_name,
            "category_channel": app_type.category_channel,
            "staff_role": app_type.staff_role,
            "questions": [q.question_text for q in questions],
        })
    return response


@router.post("/submit")
def submit(payload: ApplicationSubmitIn, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, payload.discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    app = submit_application(db, server, payload)
    return {"id": app.id, "status": app.status}
