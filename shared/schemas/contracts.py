from pydantic import BaseModel


class TicketPanelButton(BaseModel):
    label: str
    value: str


class PanelContract(BaseModel):
    panel_type: str
    title: str
    description: str
    buttons: list[TicketPanelButton]
