import os
import json
from telebot import TeleBot, types

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = TeleBot(TOKEN)
DATA_FILE = "games.json"


def load():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎮 Записаться на игру", "❌ Отменить запись")
    kb.add("📋 Список игр", "⏳ Лист ожидания")
    kb.add("👑 VIP / Капитанские")
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в HeadShotDubai 🖤\n\nВыбери действие:",
        reply_markup=menu()
    )


@bot.message_handler(commands=["newgame"])
def new_game(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/newgame", "").strip()
    if not text:
        bot.reply_to(message, "Формат: /newgame 20 июня 20:00 | Открытый стол")
        return

    data = load()
    game_id = str(len(data) + 1)
    data[game_id] = {
        "title": text,
        "players": [],
        "waitlist": [],
        "limit": 10
    }
    save(data)
    bot.reply_to(message, f"Игра создана ✅\nID: {game_id}\n{text}")


@bot.message_handler(func=lambda m: m.text == "📋 Список игр")
def games_list(message):
    data = load()
    if not data:
        bot.send_message(message.chat.id, "Пока игр нет.")
        return

    text = "📋 Ближайшие игры:\n\n"
    for gid, g in data.items():
        text += f"{gid}. {g['title']}\nМест: {len(g['players'])}/{g['limit']}\n\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "🎮 Записаться на игру")
def signup_menu(message):
    data = load()
    if not data:
        bot.send_message(message.chat.id, "Пока нет активных игр.")
        return

    kb = types.InlineKeyboardMarkup()
    for gid, g in data.items():
        kb.add(types.InlineKeyboardButton(
            f"{g['title']} ({len(g['players'])}/{g['limit']})",
            callback_data=f"join_{gid}"
        ))
    bot.send_message(message.chat.id, "Выбери игру:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def join_game(call):
    gid = call.data.split("_")[1]
    data = load()
    user = call.from_user
    name = user.username or user.first_name

    if gid not in data:
        bot.answer_callback_query(call.id, "Игра не найдена")
        return

    game = data[gid]

    if name in game["players"] or name in game["waitlist"]:
        bot.answer_callback_query(call.id, "Ты уже записан")
        return

    if len(game["players"]) < game["limit"]:
        game["players"].append(name)
        bot.send_message(call.message.chat.id, f"✅ @{name} записан на игру:\n{game['title']}")
    else:
        game["waitlist"].append(name)
        bot.send_message(call.message.chat.id, f"⏳ @{name} добавлен в лист ожидания:\n{game['title']}")

    save(data)


@bot.message_handler(func=lambda m: m.text == "❌ Отменить запись")
def cancel_signup(message):
    data = load()
    name = message.from_user.username or message.from_user.first_name
    removed = False

    for g in data.values():
        if name in g["players"]:
            g["players"].remove(name)
            removed = True
            if g["waitlist"]:
                next_player = g["waitlist"].pop(0)
                g["players"].append(next_player)
        if name in g["waitlist"]:
            g["waitlist"].remove(name)
            removed = True

    save(data)
    bot.send_message(message.chat.id, "Запись отменена ✅" if removed else "Ты не был записан.")


@bot.message_handler(commands=["players"])
def players(message):
    if message.from_user.id != ADMIN_ID:
        return

    data = load()
    text = "👥 Списки игроков:\n\n"
    for gid, g in data.items():
        text += f"{gid}. {g['title']}\n"
        text += "Игроки:\n" + "\n".join([f"- @{p}" for p in g["players"]]) + "\n"
        text += "Ожидание:\n" + "\n".join([f"- @{p}" for p in g["waitlist"]]) + "\n\n"

    bot.send_message(message.chat.id, text or "Списков нет.")


@bot.message_handler(func=lambda m: m.text == "⏳ Лист ожидания")
def waitlist(message):
    data = load()
    text = "⏳ Лист ожидания:\n\n"
    for g in data.values():
        if g["waitlist"]:
            text += f"{g['title']}:\n" + "\n".join([f"- @{p}" for p in g["waitlist"]]) + "\n\n"
    bot.send_message(message.chat.id, text if text != "⏳ Лист ожидания:\n\n" else "Лист ожидания пуст.")


@bot.message_handler(func=lambda m: m.text == "👑 VIP / Капитанские")
def vip(message):
    bot.send_message(
        message.chat.id,
        "👑 VIP / Капитанские столы\n\n"
        "Через капитанские столы лучшие игроки проходят в Masters Dubai.\n"
        "Запись открывается отдельно у администратора."
    )

@bot.message_handler(commands=["delgame"])
def delete_game(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Формат: /delgame 1")
        return

    gid = parts[1]
    data = load()

    if gid not in data:
        bot.reply_to(message, "Игра не найдена.")
        return

    title = data[gid]["title"]
    del data[gid]
    save(data)

    bot.reply_to(message, f"Игра удалена ✅\nID: {gid}\n{title}")
bot.infinity_polling()