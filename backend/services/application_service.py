from sqlalchemy.orm import Session

from backend.models.entities import Application, ApplicationType, Question, Server
from backend.models.schemas import ApplicationSubmitIn, ApplicationTypeIn


def create_application_type(db: Session, server: Server, payload: ApplicationTypeIn) -> ApplicationType:
    app_type = ApplicationType(
        server_id=server.id,
        application_name=payload.application_name,
        category_channel=payload.category_channel,
        staff_role=payload.staff_role,
    )
    db.add(app_type)
    db.flush()
    for index, question in enumerate(payload.questions):
        db.add(Question(application_type=app_type.id, question_text=question, order_index=index))
    db.commit()
    db.refresh(app_type)
    return app_type


def submit_application(db: Session, server: Server, payload: ApplicationSubmitIn) -> Application:
    application = Application(
        server_id=server.id,
        type=payload.type,
        user_id=payload.user_id,
        answers=payload.answers,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application
