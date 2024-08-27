from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import ContentType
import app.firebase_adm as firebase_adm
from app.config import TELEGRAM_TOKEN, ADMIN_IDS


# Safely split the string, strip whitespace, and filter out any empty strings before converting to integers
admIDs = [int(x.strip()) for x in ADMIN_IDS.split(',') if x.strip().isdigit()]
admin_only = lambda message: message.from_user.id in admIDs

# Initialize bot and memory storage
storage = MemoryStorage()
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=storage)


# Run after /start command
@dp.message(CommandStart())
async def start_message(message: types.Message):
    if message.from_user.id in admIDs:
        await message.answer("☑️ Панель администратора запущена. "
                             "Отправьте /help для получения дополнительной информации")
    else:
        await message.answer("🚫 Вы не являетесь администратором")


# Run after /help command
@dp.message(admin_only, Command("help"))
async def help_message(message: types.Message):
    await message.answer(
        f"""
<b>Отправьте список токенов, чтобы авторизовать их. Пример:</b>
<blockquote>A1A1A1
B2B2B2
C3C3C3</blockquote>

/list_all - <b>вывести все авторизованные токены.</b>

/revoke - <b>отозвать список токенов. Пример:</b>
<blockquote>/revoke

A1A1A1
B2B2B2
C3C3C3</blockquote>

/revoke_all - <b>отозвать все токены</b>
""",
        parse_mode="HTML")


# Run after /revoke command
@dp.message(admin_only, Command("revoke"))
async def revoke_player_id(message: types.Message, command: CommandObject):
    command_args: str = command.args
    if not command_args:
        await message.answer(
            f"""
/revoke - <b>отозвать список токенов. Пример:</b>
<blockquote>/revoke

A1A1A1
B2B2B2
C3C3C3</blockquote>
        """,
            parse_mode="HTML")
    else:
        # Split the command arguments by newlines to get individual IDs
        tokens = command_args.strip().split('\n')

        results = []  # To store the result for each ID

        # Iterate through all tokens
        for token in tokens:
            token = token.strip()  # Remove any leading or trailing whitespace

            # Check if token length is correct
            if len(token) == 6:
                result = firebase_adm.RevokeToken(token)
                results.append(result)
            elif len(token) != 0:
                results.append(f"🚫 Ошибка. Player ID `{token}` должен состоять из 6 символов")

        # Send the results back to the user
        await message.reply('\n\n'.join(results), parse_mode="Markdown")


class RevokeTokensState(StatesGroup):
    waiting_for_confirmation = State()


# Run after /revoke_all command
@dp.message(admin_only, Command("revoke_all"))
async def revoke_all_tokens(message: types.Message, state: FSMContext):
    amount = firebase_adm.CountTokens() # Get amount of tokens

    await message.answer(f"⚠️ *Вы действительно хотите отозвать {amount} токенов?*\n"
                         "\n"
                         "Отправьте в чат, чтобы подтвердить:\n"
                         "\n"
                         f"`Да, я понимаю, что хочу безвозвратно отозвать все {amount} токенов`",
                         parse_mode="Markdown")
    await state.update_data(amount=amount)  # Save the amount to state data
    await state.set_state(RevokeTokensState.waiting_for_confirmation)


# Run after /list_all command
@dp.message(admin_only, Command("list_all"))  # Run after /list_all command
async def list_all(message: types.Message):
    await message.reply(firebase_adm.ListTokens(), parse_mode="HTML")


# Run after /cancel command
@dp.message(admin_only, Command("cancel"), RevokeTokensState.waiting_for_confirmation)
async def cancel_command_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()  # Check if there is an active state
    if current_state is not None:  # If a state is set
        await state.clear()  # Finish the state
        await message.answer("❌ Процесс отозвания токенов был отменен.")
    else:
        await message.answer("❓ Нет активного процесса для отмены.")


# Confirmation before revoking all tokens
@dp.message(admin_only, RevokeTokensState.waiting_for_confirmation, F.content_type == ContentType.TEXT)
async def confirm_revoke_tokens(message: types.Message, state: FSMContext):
    # Get the amount from state data
    data = await state.get_data()
    amount = data.get('amount')

    # Check if the user provided the correct confirmation message
    expected_confirmation = f"Да, я понимаю, что хочу безвозвратно отозвать все {amount} токенов"

    # Check if confirmation matches
    if message.text == expected_confirmation:
        await firebase_adm.RevokeAllTokens()
        await state.clear()  # Finish the state
    else:
        await message.answer("❌ Подтверждение не совпадает. Попробуйте еще раз или отправьте /cancel для отмены.")


# Run after receiving Token for authorization
@dp.message(admin_only, F.content_type == ContentType.TEXT)
async def player_id_handler(message: types.Message):
    tokens = message.text.strip().split('\n')  # Split the message by newlines to get individual IDs

    results = []  # To store the result for each ID

    # Iterate though all tokens
    for token in tokens:
        token = token.strip()  # Remove any leading or trailing whitespace

        # Check if token length is correct
        if len(token) == 6:
            result = firebase_adm.AuthorizeToken(token)
            results.append(result)
        elif len(token) != 0:
            results.append(f"🚫 Ошибка. Player ID `{token}` должен состоять из 6 символов")

    # Send the results back to the user
    await message.reply('\n\n'.join(results), parse_mode="Markdown")
