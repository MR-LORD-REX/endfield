from pydantic import BaseModel

class User(BaseModel):
    uid: int 
    skport_id: int 
    skport_name: str
    server_id: int
    cred: str | None = None
    sign_token: str | None = None
    sk_role: str | None = None 