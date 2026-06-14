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
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def username(user):
    if user.username:
        return f"@{user.username}"
    return user.first_name or "Игрок"


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


@bot.message_handler(commands=["myid"])
def myid(message):
    bot.reply_to(message, f"Твой ID: {message.from_user.id}")


@bot.message_handler(commands=["newgame"])
def new_game(message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/newgame", "").strip()

    if not text:
        bot.reply_to(message, "Формат:\n/newgame 15 июня 19:30 - Открытый стол")
        return

    data = load()
    game_id = str(max([int(x) for x in data.keys()] + [0]) + 1)

    data[game_id] = {
        "title": text,
        "players": [],
        "waitlist": [],
        "limit": 10
    }

    save(data)

    bot.reply_to(message, f"Игра создана ✅\nID: {game_id}\n{text}")


@bot.message_handler(commands=["delgame"])
def delete_game(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/delgame 1")
        return

    gid = parts[1]
    data = load()

    if gid not in data:
        bot.reply_to(message, "Игра с таким ID не найдена.")
        return

    title = data[gid]["title"]
    del data[gid]
    save(data)

    bot.reply_to(message, f"Игра удалена ✅\nID: {gid}\n{title}")


@bot.message_handler(commands=["players"])
def players(message):
    if message.from_user.id != ADMIN_ID:
        return

    data = load()

    if not data:
        bot.send_message(message.chat.id, "Пока игр нет.")
        return

    text = "👥 Списки игроков:\n\n"

    for gid, g in data.items():
        text += f"🎭 ID {gid}: {g['title']}\n"
        text += f"Мест: {len(g['players'])}/{g['limit']}\n\n"

        if g["players"]:
            text += "✅ Игроки:\n"
            for i, p in enumerate(g["players"], 1):
                text += f"{i}. {p}\n"
        else:
            text += "✅ Игроки: пока нет\n"

        if g["waitlist"]:
            text += "\n⏳ Лист ожидания:\n"
            for i, p in enumerate(g["waitlist"], 1):
                text += f"{i}. {p}\n"

        text += "\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "📋 Список игр")
def games_list(message):
    data = load()

    if not data:
        bot.send_message(message.chat.id, "Пока игр нет.")
        return

    text = "📋 Ближайшие игры:\n\n"

    for gid, g in data.items():
        free = g["limit"] - len(g["players"])
        text += f"🎭 ID {gid}: {g['title']}\n"
        text += f"Мест занято: {len(g['players'])}/{g['limit']}\n"
        text += f"Свободно мест: {free}\n\n"

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
    player = username(call.from_user)

    if gid not in data:
        bot.answer_callback_query(call.id, "Игра не найдена")
        return

    game = data[gid]

    if player in game["players"] or player in game["waitlist"]:
        bot.answer_callback_query(call.id, "Ты уже записан")
        return

    if len(game["players"]) < game["limit"]:
        game["players"].append(player)
        save(data)

        bot.send_message(
            call.message.chat.id,
            f"✅ {player} записан на игру:\n{game['title']}"
        )

        bot.send_message(
            ADMIN_ID,
            f"Новая запись ✅\n{player}\n\nИгра:\n{game['title']}"
        )

    else:
        game["waitlist"].append(player)
        save(data)

        bot.send_message(
            call.message.chat.id,
            f"⏳ {player} добавлен в лист ожидания:\n{game['title']}"
        )

        bot.send_message(
            ADMIN_ID,
            f"Новый игрок в листе ожидания ⏳\n{player}\n\nИгра:\n{game['title']}"
        )


@bot.message_handler(func=lambda m: m.text == "❌ Отменить запись")
def cancel_signup(message):
    data = load()
    player = username(message.from_user)
    removed = False
    promoted = []

    for gid, g in data.items():
        if player in g["players"]:
            g["players"].remove(player)
            removed = True

            if g["waitlist"]:
                next_player = g["waitlist"].pop(0)
                g["players"].append(next_player)
                promoted.append((next_player, g["title"]))

        if player in g["waitlist"]:
            g["waitlist"].remove(player)
            removed = True

    save(data)

    if removed:
        bot.send_message(message.chat.id, "Запись отменена ✅")
        bot.send_message(ADMIN_ID, f"Игрок отменил запись ❌\n{player}")

        for p, title in promoted:
            bot.send_message(
                ADMIN_ID,
                f"Игрок из листа ожидания перешёл в основной состав ✅\n{p}\n\nИгра:\n{title}"
            )
    else:
        bot.send_message(message.chat.id, "Ты не был записан.")


@bot.message_handler(func=lambda m: m.text == "⏳ Лист ожидания")
def waitlist(message):
    data = load()
    text = "⏳ Лист ожидания:\n\n"

    found = False

    for gid, g in data.items():
        if g["waitlist"]:
            found = True
            text += f"🎭 {g['title']}:\n"
            for i, p in enumerate(g["waitlist"], 1):
                text += f"{i}. {p}\n"
            text += "\n"

    bot.send_message(message.chat.id, text if found else "Лист ожидания пуст.")


@bot.message_handler(func=lambda m: m.text == "👑 VIP / Капитанские")
def vip(message):
    bot.send_message(
        message.chat.id,
        "👑 VIP / Капитанские столы\n\n"
        "Через капитанские столы лучшие игроки проходят в Masters Dubai.\n"
        "Запись открывается отдельно у администратора."
    )


bot.infinity_polling()