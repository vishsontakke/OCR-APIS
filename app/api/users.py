from fastapi import APIRouter
from app.schemas.user_schema import User

router = APIRouter()

fake_users_db = [
    {"id": 1, "name": "Test User", "email": "test@example.com"},
    {"id": 2, "name": "Alice", "email": "alice@example.com"},
    {"id": 3, "name": "Bob", "email": "bob@example.com"},
]

@router.get("/", response_model=list[User])
def get_users():
    """Fetch all users"""
    return fake_users_db