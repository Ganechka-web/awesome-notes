from passlib.context import CryptContext


class SecurityPasswordService:
    context = CryptContext(schemes=["bcrypt"])

    def generate_password_hash(self, bare_password: str) -> str:
        return self.context.hash(bare_password)

    def verify_password_hash(self, bare_password: str, password_hash: str) -> bool:
        return self.context.verify(bare_password, password_hash)
