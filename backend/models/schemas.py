from pydantic import BaseModel, Field


class OAuthCallbackRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ServerSyncRequest(BaseModel):
    discord_server_id: str
    owner_id: str


class TicketConfigIn(BaseModel):
    ticket_name: str
    ticket_description: str
    ticket_category_channel: str
    staff_role: str
    panel_message: str
    panel_channel: str


class TicketCreateIn(BaseModel):
    discord_server_id: str
    type: str
    user_id: str
    channel_id: str | None = None


class ApplicationTypeIn(BaseModel):
    application_name: str
    questions: list[str] = Field(default_factory=list)
    category_channel: str
    staff_role: str


class ApplicationSubmitIn(BaseModel):
    discord_server_id: str
    type: str
    user_id: str
    answers: dict


class PanelIn(BaseModel):
    panel_type: str
    channel_id: str
    title: str
    description: str
    buttons: list[dict]


class LogEventIn(BaseModel):
    discord_server_id: str
    event_type: str
    details: dict
