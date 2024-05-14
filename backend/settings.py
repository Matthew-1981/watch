import os


def _get_env_raise(env_name: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        raise ValueError(f'{env_name} is not set')
    return value


SERVER_HOST = _get_env_raise('SERVER_HOST')
SERVER_PORT = int(_get_env_raise('SERVER_PORT'))

ORIGINS = _get_env_raise('ORIGINS').split(';')

DATABASE_CONFIG = {
    'user': _get_env_raise('DB_USER'),
    'password': _get_env_raise('DB_PASSWORD'),
    'host': _get_env_raise('DB_HOST'),
    'database': _get_env_raise('DB_NAME'),
    # 'raise_on_warnings': True
}
