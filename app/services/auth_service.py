"""Authentication service."""
import uuid

from app.core.config import settings
from app.core.exceptions import DuplicateResourceError
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.repositories.wallet_repo import WalletRepository
from app.schemas.auth import RegisterRequest


class AuthService:
    def __init__(self, db):
        self.db = db
        self.user_repo = UserRepository(db)
        self.wallet_repo = WalletRepository(db)

    async def register_user(self, data: RegisterRequest) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise DuplicateResourceError("Email already registered")
        existing_phone = await self.user_repo.get_by_phone(data.phone)
        if existing_phone:
            raise DuplicateResourceError("Phone number already registered")
        user = await self.user_repo.create({
            "email": data.email,
            "phone": data.phone,
            "full_name": data.full_name,
            "password_hash": get_password_hash(data.password),
            "role": UserRole.CUSTOMER,
        })
        await self.wallet_repo.get_or_create_for_user(user.id)
        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        from app.core.security import verify_password

        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if user.status.value != "active":
            return None
        return user

    def _oauth_phone(self, provider: str, email: str, sub: str) -> str:
        """Generate unique placeholder phone for OAuth users (required by schema)."""
        h = abs(hash(f"{provider}:{email}:{sub}"))
        return "+233" + str(h % 10**9).zfill(9)

    async def authenticate_google(self, id_token: str) -> User | None:
        """Verify Google ID token and return/create user."""
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests
        except ImportError:
            return None
        if not settings.GOOGLE_CLIENT_ID:
            return None
        try:
            payload = id_token.verify_oauth2_token(
                id_token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except Exception:
            return None
        email = payload.get("email")
        sub = payload.get("sub", "")
        name = payload.get("name") or email or "User"
        if not email:
            return None
        user = await self.user_repo.get_by_email(email)
        if user:
            return user
        phone = self._oauth_phone("google", email, sub)
        while True:
            existing = await self.user_repo.get_by_phone(phone)
            if not existing:
                break
            phone = "+233" + str(uuid.uuid4().int % 10**9).zfill(9)
        user = await self.user_repo.create({
            "email": email,
            "phone": phone,
            "full_name": name,
            "password_hash": get_password_hash(uuid.uuid4().hex),
            "role": UserRole.CUSTOMER,
        })
        await self.wallet_repo.get_or_create_for_user(user.id)
        return user

    async def authenticate_apple(self, id_token: str) -> User | None:
        """Verify Apple ID token and return/create user."""
        if not settings.APPLE_CLIENT_ID:
            return None
        try:
            payload = self._verify_apple_token(id_token)
        except Exception:
            return None
        if not payload:
            return None
        sub = payload.get("sub", "")
        email = payload.get("email") or f"{sub}@privaterelay.appleid.com"
        name = payload.get("name", {}).get("firstName", "") or "User"
        if payload.get("name", {}).get("lastName"):
            name = f"{name} {payload['name']['lastName']}".strip()
        user = await self.user_repo.get_by_email(email)
        if user:
            return user
        phone = self._oauth_phone("apple", email, sub)
        while True:
            existing = await self.user_repo.get_by_phone(phone)
            if not existing:
                break
            phone = "+233" + str(uuid.uuid4().int % 10**9).zfill(9)
        user = await self.user_repo.create({
            "email": email,
            "phone": phone,
            "full_name": name or "User",
            "password_hash": get_password_hash(uuid.uuid4().hex),
            "role": UserRole.CUSTOMER,
        })
        await self.wallet_repo.get_or_create_for_user(user.id)
        return user

    def _verify_apple_token(self, token: str) -> dict | None:
        """Verify Apple ID token using Apple's public keys."""
        import httpx
        from jose import jwt, jwk

        try:
            resp = httpx.get("https://appleid.apple.com/auth/keys")
            resp.raise_for_status()
            jwks = resp.json()
        except Exception:
            return None
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                try:
                    public_key = jwk.construct(key)
                    payload = jwt.decode(
                        token,
                        public_key,
                        algorithms=["RS256"],
                        audience=settings.APPLE_CLIENT_ID,
                        issuer="https://appleid.apple.com",
                    )
                    return payload
                except Exception:
                    return None
        return None
