from communication.responses import AuthResponse
from .security import AuthBundle


def parse_auth_bundle(auth_bundle: AuthBundle) -> AuthResponse:
    return AuthResponse(
        user=auth_bundle.user.data.user_name,
        expiration_date=auth_bundle.token.data.expiration
    )
