
import keyring
from yandex_music import Client

SERVICE_NAME = "YandexMusicExporter"
TOKEN_KEY = "yandex_music_token"


def save_token(token: str) -> None:
    keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)


def get_token() -> str | None:
    return keyring.get_password(SERVICE_NAME, TOKEN_KEY)


def connect() -> Client:
    token = get_token()

    if not token:
        raise RuntimeError("Учётная запись ещё не подключена.")

    return Client(token).init()


def authorize(on_code):
    client = Client()
    result = client.device_auth(on_code=on_code, timeout=300)

    if not result or not result.access_token:
        raise RuntimeError("Не удалось получить токен авторизации.")

    save_token(result.access_token)
    return result.access_token
