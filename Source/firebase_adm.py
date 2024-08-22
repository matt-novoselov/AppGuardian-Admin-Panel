from dotenv import load_dotenv
import os
import json
import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

load_dotenv()
firebase_url = os.getenv("FIREBASE_URL")
email_domain = os.getenv("EMAIL_DOMAIN")
firebase_api_key_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")

# Convert Firebase certificate back to a dictionary
firebase_api_key = json.loads(firebase_api_key_str)
cred = credentials.Certificate(firebase_api_key)

firebase_admin.initialize_app(cred, {
    'databaseURL': firebase_url,
})

token_state_dict = {True: "Активирован", False: "Не активирован"}


def CreateUser(deviceID_upper):
    try:
        token = deviceID_upper.lower()
        email = GenerateEmail(token)

        # Attempt to create a user
        auth.create_user(
            email=email,
            password=token,
        )

        print(f"[v] New token was authorized: {token.upper()}")
        return f'️✅ Токен *{token.upper()}* был успешно авторизован'

    except FirebaseError as e:
        # Check if the error is due to the email already existing
        if 'EMAIL_EXISTS' in str(e):
            return f"❌ Пользователь с этим токеном уже существует: *{token.upper()}*"
        else:
            print(f"[!] There was an error: {e}")
            return f"There was an error: {e}"

    except Exception as e:
        print(f"[!] There was an error: {e}")
        return f"There was an error: {e}"


def DeleteUser(token):
    try:
        composed_email = GenerateEmail(token)
        uid = auth.get_user_by_email(composed_email).uid
        auth.delete_user(uid)

        print(f"[v] Token {token.upper()} was revoked")
        return f"🗑 Токен *{token.upper()}* был успешно отозван"
    except:
        return f"❓ Токен *{token.upper()}* не был найден"


def ListUsers():
    message = "Все авторизованные токены:\n\n"
    try:
        for user in auth.list_users().iterate_all():
            extracted_token = str(user.email).split("@")[0]
            message += f"<b>{extracted_token.upper()}</b>\n"

        message += "\n/revoke [TOKEN] - отозвать определенный токен\n/revoke_all - отозвать все токены"
        return message
    except Exception as e:
        print(f"[!] There was an error: {e}")
        return f"There was an error: {e}"


def CountUsers() -> int:
    try:
        amount = 0
        page = auth.list_users()  # Initialize the ListUsersPage
        while page:
            amount += len(page.users)  # Count the users on the current page
            page = page.get_next_page()  # Move to the next page
        return amount
    except Exception as e:
        print(f"[!] There was an error: {e}")
        return 0


def RevokeAll():
    try:
        count = 0
        for user in auth.list_users().iterate_all():
            uid = user.uid
            auth.delete_user(uid)
            count += 1
            print(f'[v] Token {str(user.email).split("@")[0]} was revoked using /revoke_all')

        return f"🗑️ Было успешно отозвано {count} токенов"

    except Exception as e:
        print(f"[!] There was an error: {e}")
        return f"There was an error: {e}"


def GenerateEmail(token: str) -> str:
    composed_email = f'{token}@{email_domain}'
    return composed_email
