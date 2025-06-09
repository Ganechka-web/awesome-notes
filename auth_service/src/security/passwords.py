from passlib.context import CryptContext


context = CryptContext(schemes=['bcrypt'])


def get_password_hash(password: str) -> str:
    return context.hash(password)


def check_password_hash(password: str, password_hash: str) -> bool:
    return context.verify(password, password_hash)
