from app.core.security import verify_password, create_access_token


class AuthUseCase:

    def __init__(self, user_repo):
        self.user_repo = user_repo

    def login(self, email: str, password: str):
        user = self.user_repo.get_by_email(email)

        if not user:
            raise Exception("Usuario no existe")

        if not verify_password(password, user.password):
            raise Exception("Credenciales incorrectas")

        token = create_access_token({
            "sub": user.id,
            "roles": [user_role.role.name for user_role in user.user_roles]  # ✅
        })

        return {
            "access_token": token,
            "token_type": "bearer"
        }