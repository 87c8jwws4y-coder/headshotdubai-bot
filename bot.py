import os
import json
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5132148605"))

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "data.json"

TIMES = ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30"]


def default_data():
    return {
        "group_id": None,
        "games": [],
        "players": {},
        "rules": "🎲 Правила HeadShotDubai\n\nСтоимость игры: 100 AED\n\nСемья — это не главное. Семья — это всё."
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key, value in default_data().items():
        if key not in data:
            data[key] = value
    return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def admin_only(message):
    return message.from_user and message.from_user.id == ADMIN_ID


def norm(name):
    return name.strip().lower()


def get_player(data, name):
    key = norm(name)
    if key not in data["players"]:
        data["players"][key] = {
            "name": name.strip(),
            "nick": name.strip(),
            "status": "",
            "telegram_id": None
        }
    return data["players"][key]


def display_player(player):
    status = player.get("status", "")
    nick = player.get("nick") or player.get("name")
    return f"{nick} {status}".strip()


def render_game(data, game):
    lines = [
        f"🎲 Игра #{game['id']}",
        f"📅 {game['date']}",
        "",
        "👥 Список игроков:"
    ]

    if not game["players"]:
        lines.append("Пока никто не записан.")
    else:
        for i, p in enumerate(game["players"], 1):
            player = get_player(data, p["name"])
            lines.append(f"{i}. {display_player(player)} — {p['time']}")

    lines.append(f"\nМест: {len(game['players'])}/10")
    return "\n".join(lines)


def game_keyboard(game_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Записаться", callback_data=f"join_{game_id}"))
    kb.add(types.InlineKeyboardButton("❌ Отменить запись", callback_data=f"cancel_{game_id}"))
    kb.add(types.InlineKeyboardButton("📜 Правила и стоимость", callback_data="rules"))
    return kb


def update_game_message(data, game):
    if game.get("chat_id") and game.get("message_id"):
        bot.edit_message_text(
            render_game(data, game),
            game["chat_id"],
            game["message_id"],
            reply_markup=game_keyboard(game["id"])
        )


@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(message, """
🎲 HeadShotDubai Bot

Команды админа:
/setgroup
/say текст
/newgame дата
/deletegame номер
/clear_games
/addplayer номер имя время
/removeplayer номер имя
/setnick имя новый_ник
/resident имя
/vip имя
/master имя
/setrules текст

Команды игроков:
/games
/mygames
/rules
""")


@bot.message_handler(commands=["setgroup"])
def setgroup(message):
    if not admin_only(message):
        return
    data = load_data()
    data["group_id"] = message.chat.id
    save_data(data)
    bot.reply_to(message, "Группа привязана ✅")


@bot.message_handler(commands=["say"])
def say(message):
    if not admin_only(message):
        return

    text = message.text.replace("/say", "", 1).strip()
    if not text:
        bot.reply_to(message, "Формат: /say текст")
        return

    data = load_data()
    group_id = data.get("group_id")

    if not group_id:
        bot.reply_to(message, "Сначала напиши /setgroup в группе.")
        return

    bot.send_message(group_id, text)
    bot.reply_to(message, "Отправил ✅")


@bot.message_handler(commands=["newgame"])
def newgame(message):
    if not admin_only(message):
        return

    date = message.text.replace("/newgame", "", 1).strip()
    if not date:
        bot.reply_to(message, "Формат: /newgame 18 июня")
        return

    data = load_data()
    game_id = len(data["games"]) + 1

    game = {
        "id": game_id,
        "date": date,
        "players": [],
        "chat_id": message.chat.id,
        "message_id": None
    }

    msg = bot.send_message(
        message.chat.id,
        render_game(data, game),
        reply_markup=game_keyboard(game_id)
    )

    game["message_id"] = msg.message_id
    data["games"].append(game)
    save_data(data)


@bot.message_handler(commands=["deletegame"])
def deletegame(message):
    if not admin_only(message):
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Формат: /deletegame 1")
        return

    game_id = int(parts[1])
    data = load_data()
    data["games"] = [g for g in data["games"] if g["id"] != game_id]
    save_data(data)

    bot.reply_to(message, f"Игра #{game_id} удалена ✅")


@bot.message_handler(commands=["clear_games"])
def clear_games(message):
    if not admin_only(message):
        return

    data = load_data()
    data["games"] = []
    save_data(data)
    bot.reply_to(message, "Все игры удалены ✅")


@bot.message_handler(commands=["addplayer"])
def addplayer(message):
    if not admin_only(message):
        return

    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        bot.reply_to(message, "Формат: /addplayer 1 Адам 20:00")
        return

    game_id = int(parts[1])
    name_time = parts[2:]
    name = name_time[0]
    time = name_time[1]

    if time not in TIMES:
        bot.reply_to(message, f"Время только: {', '.join(TIMES)}")
        return

    data = load_data()
    game = next((g for g in data["games"] if g["id"] == game_id), None)

    if not game:
        bot.reply_to(message, "Игра не найдена.")
        return

    if len(game["players"]) >= 10:
        bot.reply_to(message, "Мест уже 10/10.")
        return

    get_player(data, name)

    if any(norm(p["name"]) == norm(name) for p in game["players"]):
        bot.reply_to(message, "Игрок уже записан.")
        return

    game["players"].append({"name": name, "time": time})
    update_game_message(data, game)
    save_data(data)

    bot.reply_to(message, "Игрок добавлен ✅")


@bot.message_handler(commands=["removeplayer"])
def removeplayer(message):
    if not admin_only(message):
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат: /removeplayer 1 Адам")
        return

    game_id = int(parts[1])
    name = parts[2]

    data = load_data()
    game = next((g for g in data["games"] if g["id"] == game_id), None)

    if not game:
        bot.reply_to(message, "Игра не найдена.")
        return

    game["players"] = [p for p in game["players"] if norm(p["name"]) != norm(name)]
    update_game_message(data, game)
    save_data(data)

    bot.reply_to(message, "Игрок удалён ✅")


@bot.message_handler(commands=["setnick"])
def setnick(message):
    if not admin_only(message):
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат: /setnick Адам Adam")
        return

    old_name = parts[1]
    new_nick = parts[2]

    data = load_data()
    player = get_player(data, old_name)
    player["nick"] = new_nick
    save_data(data)

    bot.reply_to(message, "Ник изменён ✅")


def set_status(message, status):
    if not admin_only(message):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, f"Формат: /{status.lower()} Адам")
        return

    name = parts[1]
    data = load_data()
    player = get_player(data, name)
    player["status"] = status
    save_data(data)

    for game in data["games"]:
        update_game_message(data, game)

    bot.reply_to(message, f"Статус выдан: {status} ✅")


@bot.message_handler(commands=["resident"])
def resident(message):
    set_status(message, "🔵 Резидент")


@bot.message_handler(commands=["vip"])
def vip(message):
    set_status(message, "🟣 VIP")


@bot.message_handler(commands=["master"])
def master(message):
    set_status(message, "🏆 Мастер")


@bot.message_handler(commands=["setrules"])
def setrules(message):
    if not admin_only(message):
        return

    text = message.text.replace("/setrules", "", 1).strip()
    if not text:
        bot.reply_to(message, "Формат: /setrules текст правил")
        return

    data = load_data()
    data["rules"] = text
    save_data(data)

    bot.reply_to(message, "Правила обновлены ✅")


@bot.message_handler(commands=["rules"])
def rules(message):
    data = load_data()
    bot.reply_to(message, data["rules"])


@bot.message_handler(commands=["games"])
def games(message):
    data = load_data()

    if not data["games"]:
        bot.reply_to(message, "Активных игр нет.")
        return

    text = "\n\n".join(render_game(data, g) for g in data["games"])
    bot.reply_to(message, text)


@bot.callback_query_handler(func=lambda call: call.data == "rules")
def rules_button(call):
    data = load_data()
    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, data["rules"])


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def join_start(call):
    game_id = int(call.data.replace("join_", ""))

    kb = types.InlineKeyboardMarkup()
    for t in TIMES:
        kb.add(types.InlineKeyboardButton(t, callback_data=f"time_{game_id}_{t}"))

    bot.answer_callback_query(call.id)
    bot.send_message(call.from_user.id, "Выбери время:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def join_time(call):
    _, game_id, time = call.data.split("_")
    game_id = int(game_id)

    data = load_data()
    game = next((g for g in data["games"] if g["id"] == game_id), None)

    if not game:
        bot.answer_callback_query(call.id, "Игра не найдена")
        return

    if len(game["players"]) >= 10:
        bot.answer_callback_query(call.id, "Мест нет")
        return

    name = call.from_user.first_name or call.from_user.username or str(call.from_user.id)
    player = get_player(data, name)
    player["telegram_id"] = call.from_user.id

    if any(p.get("telegram_id") == call.from_user.id or norm(p["name"]) == norm(name) for p in game["players"]):
        bot.answer_callback_query(call.id, "Ты уже записан")
        return

    game["players"].append({
        "name": name,
        "time": time,
        "telegram_id": call.from_user.id
    })

    update_game_message(data, game)
    save_data(data)

    bot.answer_callback_query(call.id, "Ты записан ✅")
    bot.send_message(call.from_user.id, f"Ты записан на игру #{game_id} в {time} ✅")


@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel(call):
    game_id = int(call.data.replace("cancel_", ""))

    data = load_data()
    game = next((g for g in data["games"] if g["id"] == game_id), None)

    if not game:
        bot.answer_callback_query(call.id, "Игра не найдена")
        return

    before = len(game["players"])
    game["players"] = [
        p for p in game["players"]
        if p.get("telegram_id") != call.from_user.id
    ]

    if len(game["players"]) == before:
        bot.answer_callback_query(call.id, "Ты не был записан")
        return

    update_game_message(data, game)
    save_data(data)

    bot.answer_callback_query(call.id, "Запись отменена ✅")
    bot.send_message(call.from_user.id, f"Запись на игру #{game_id} отменена ✅")


bot.infinity_polling()