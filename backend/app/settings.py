import os
import dotenv


dotenv.load_dotenv()


def _get_env_raise(env_name: str) -> str:
    value = os.getenv(env_name)
    if value is None:
        raise ValueError(f'{env_name} is not set')
    return value


DATABASE_CONFIG = {
    'user': _get_env_raise('MYSQL_USER'),
    'password': _get_env_raise('MYSQL_PASSWORD'),
    'host': _get_env_raise('MYSQL_HOST'),
    'database': _get_env_raise('MYSQL_DATABASE'),
    # 'raise_on_warnings': True
}
