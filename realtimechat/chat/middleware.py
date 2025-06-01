from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async

from cryptography.fernet import fernet
key = Fernet.generate_key()
cipher = Fernet(key)
encrypted = cipher.encrypt(b'secret message')

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        return await super().__call__(scope, receive, send)
    