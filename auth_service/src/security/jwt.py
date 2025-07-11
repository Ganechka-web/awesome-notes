from typing import Any
from datetime import datetime

from jose import jwt

from core.settings import SECRET_KEY, ALGORITHM


def get_jwt_token(login: str) -> str:
    exp = datetime(day=1)
    return jwt.encode(
        {
            'sub': login,
            'exp': exp
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_jwt_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=ALGORITHM
    )
