from os import getenv
import dotenv

# Load secrets from environment
dotenv.load_dotenv()

# Load environment variables
TELEGRAM_TOKEN = getenv("TELEGRAM_TOKEN")
WEBHOOK_DOMAIN = getenv("WEBHOOK_DOMAIN")
ADMIN_IDS = getenv("ADMIN_IDS")
FIREBASE_URL = getenv("FIREBASE_URL")
FIREBASE_SERVICE_ACCOUNT_KEY = getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
EMAIL_DOMAIN = getenv("EMAIL_DOMAIN")