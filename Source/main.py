from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from dotenv import load_dotenv
import os
import firebase_adm

load_dotenv()
telegram_token = os.getenv("TELEGRAM_TOKEN")
admin_ids_str = os.getenv("ADMIN_IDS")

# Safely split the string, strip whitespace, and filter out any empty strings before converting to integers
admIDs = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().isdigit()]
admin_only = lambda message: message.from_user.id in admIDs

storage = MemoryStorage()
bot = Bot(token=telegram_token)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])  # Run after /start command
async def start_message(message: types.Message):
    if message.from_user.id in admIDs:
        await message.answer("☑️ Панель администратора запущена. "
                             "Отправьте /help для получения дополнительной информации")
    else:
        await message.answer("🚫 Вы не являетесь администратором")


@dp.message_handler(admin_only, commands=['help'])  # Run after /help command
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


@dp.message_handler(admin_only, commands=['revoke'])
async def revoke_player_id(message: types.Message):
    ids = message.get_args().strip().split('\n')  # Split the command arguments by newlines to get individual IDs

    results = []  # To store the result for each ID

    for device_id in ids:
        device_id = device_id.strip()  # Remove any leading or trailing whitespace

        if len(device_id) == 6:
            result = firebase_adm.DeleteUser(device_id)
            results.append(result)
        elif len(device_id) != 0:
            results.append(f"🚫 Ошибка. Player ID `{device_id}` должен состоять из 6 символов")

    # Send the results back to the user
    await message.reply('\n\n'.join(results), parse_mode="Markdown")


class RevokeTokensState(StatesGroup):
    waiting_for_confirmation = State()


@dp.message_handler(admin_only, commands=['revoke_all'])
async def revoke_all_tokens(message: types.Message, state: FSMContext):
    amount = firebase_adm.CountUsers()
    await message.answer(f"⚠️ *Вы действительно хотите отозвать {amount} токенов?*\n"
                         "\n"
                         "Отправьте в чат, чтобы подтвердить:\n"
                         "\n"
                         f"`Да, я понимаю, что хочу безвозвратно отозвать все {amount} токенов`",
                         parse_mode="Markdown")
    await state.update_data(amount=amount)  # Save the amount to state data
    await RevokeTokensState.waiting_for_confirmation.set()  # Set the state


@dp.message_handler(admin_only, commands=['list_all'])  # Run after /list_all command
async def list_all(message: types.Message):
    await message.reply(firebase_adm.ListUsers(), parse_mode="HTML")


@dp.message_handler(admin_only, state=RevokeTokensState.waiting_for_confirmation, commands=['cancel'])
async def cancel_command_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()  # Check if there is an active state
    if current_state is not None:  # If a state is set
        await state.finish()  # Finish the state
        await message.answer("❌ Процесс отозвания токенов был отменен.")
    else:
        await message.answer("❓ Нет активного процесса для отмены.")


@dp.message_handler(admin_only, state=RevokeTokensState.waiting_for_confirmation, content_types=types.ContentTypes.TEXT)
async def confirm_revoke_tokens(message: types.Message, state: FSMContext):
    # Get the amount from state data
    data = await state.get_data()
    amount = data.get('amount')

    # Check if the user provided the correct confirmation message
    expected_confirmation = f"Да, я понимаю, что хочу безвозвратно отозвать все {amount} токенов"

    if message.text == expected_confirmation:
        await firebase_adm.RevokeAll()
        await state.finish()  # Finish the state
    else:
        await message.answer("❌ Подтверждение не совпадает. Попробуйте еще раз или отправьте /cancel для отмены.")


@dp.message_handler(admin_only, content_types=types.ContentTypes.TEXT)
async def player_id_handler(message: types.Message):
    ids = message.text.strip().split('\n')  # Split the message by newlines to get individual IDs

    results = []  # To store the result for each ID

    for device_id in ids:
        device_id = device_id.strip()  # Remove any leading or trailing whitespace

        if len(device_id) == 6:
            result = firebase_adm.CreateUser(device_id)
            results.append(result)
        elif len(device_id) != 0:
            results.append(f"🚫 Ошибка. Player ID `{device_id}` должен состоять из 6 символов")

    # Send the results back to the user
    await message.reply('\n\n'.join(results), parse_mode="Markdown")


if __name__ == '__main__':
    executor.start_polling(dp)
