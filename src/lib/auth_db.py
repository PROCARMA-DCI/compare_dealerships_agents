from sqlmodel import Session, create_engine
from src.config import AUTH_DATABASE_URL

auth_engine = create_engine(AUTH_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def get_auth_session():
    with Session(auth_engine) as session:
        yield session
