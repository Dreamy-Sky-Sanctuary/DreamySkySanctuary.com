from datetime import timedelta
import os
import dotenv

dotenv.load_dotenv()

VERSION: str = '0.0.1'
APP_NAME: str = 'DreamySkySanctuary'
DESCRIPTION: str = 'The website of the Dreamy Sky Sanctuary, a discord server about the game Sky: Children of the Light.'

CLIENT_ORIGIN: list[str] = [
    "http://localhost",
    "http://dreamyskysanctuary.com",
]

BASE_DIR: str = os.getcwd()
TEMPLATES_DIR: str = os.path.join(BASE_DIR, "templates")
PUBLIC_DIR: str = os.path.join(BASE_DIR, "public")
STATIC_DIR: str = os.path.join(BASE_DIR, "static")
UPLOAD_DIR: str = os.path.join(BASE_DIR, "upload")

UPLOAD_EXPIRE_TIME: int = 60 * 60 * 24 * 31  # 31 days / 1 month
TEAM_EXPIRE_TIME: int = 60 * 60 * 2 # 24 hours / 1 day
ACCESS_TOKEN_EXPIRE_MINUTES: timedelta = timedelta(hours=6)
CHECK_INTERVAL: int = 60 * 60 * 24  # 24 hours


ENV_FILE: str = os.path.join(BASE_DIR, ".env")
TOKEN: str = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN")

SERVER_SECRET: str = os.getenv("SERVER_SECRET", "123supersecretkey123")
ALGORITHM: str = "HS256"
OTP_WINDOW: int = 2

DISCORD_OWNER_ID: int = int(os.getenv("DISCORD_OWNER_ID", "DEFAULT_OWNER_ID"))

SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.example.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", 645))
SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "root")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "root")


ALLOWED_FILE_TYPES: dict[str, str] = {
    "image/jpeg": "jpg", 
    "image/jpg": "jpg", 
    "image/png": "png", 
    "image/gif": "gif",	
    "image/gifv": "gifv",
    "video/webm": "webm",
    "video/mp4": "mp4",
    "video/wav": "wav",
    "audio/mp3": "mp3",
    "video/ogg": "ogg",}