import json
import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError
from app.config import FIREBASE_URL, FIREBASE_SERVICE_ACCOUNT_KEY, EMAIL_DOMAIN


# Convert Firebase certificate back to a dictionary
firebase_api_key = json.loads(FIREBASE_SERVICE_ACCOUNT_KEY)
cred = credentials.Certificate(firebase_api_key)

# Initialize Firebase app
firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_URL,
})


# Function to authorize new Token by device ID
def AuthorizeToken(deviceID_upper):
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



# Function to revoke token
def RevokeToken(token):
    try:
        # Compose email by token
        composed_email = GenerateEmail(token)

        # Get User ID
        uid = auth.get_user_by_email(composed_email).uid

        # Try to delete user by User ID
        auth.delete_user(uid)

        print(f"[v] Token {token.upper()} was revoked")
        return f"🗑 Токен *{token.upper()}* был успешно отозван"
    except:
        return f"❓ Токен *{token.upper()}* не был найден"



# Function to list all authorized tokens
def ListTokens():
    message = "Все авторизованные токены:\n\n"
    try:
        # Iterate through all users in database
        for user in auth.list_users().iterate_all():
            extracted_token = str(user.email).split("@")[0]
            message += f"<b>{extracted_token.upper()}</b>\n"

        message += "\n/revoke [TOKEN] - отозвать определенный токен\n/revoke_all - отозвать все токены"
        return message
    except Exception as e:
        print(f"[!] There was an error: {e}")
        return f"There was an error: {e}"


# Function to count all authorized tokens
def CountTokens() -> int:
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



# Function to revoke all authorized tokens
def RevokeAllTokens():
    try:
        count = CountTokens() # Count users before deletion

        # Iterate through authorized users and delete each
        for user in auth.list_users().iterate_all():
            uid = user.uid
            auth.delete_user(uid)
            print(f'[v] Token {str(user.email).split("@")[0]} was revoked using /revoke_all')

        return f"🗑️ Было успешно отозвано {count} токенов"

    except Exception as e:
        print(f"[!] There was an error: {e}")
        return f"There was an error: {e}"


# Generate unique email based on token
def GenerateEmail(token: str) -> str:
    composed_email = f'{token}@{EMAIL_DOMAIN}'
    return composed_email
