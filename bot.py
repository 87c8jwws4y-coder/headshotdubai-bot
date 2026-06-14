import os
import json
from datetime import datetime
from telebot import TeleBot, types

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
bot = TeleBot(TOKEN)

GAMES_FILE = "games.json"
USERS_FILE = "users.json"
CONFIG_FILE = "config.json"
HISTORY_FILE = "history.json"

DEFAULT_TIMES = ["18:00", "18:30", "19:30", "20:00", "20:30", "21:00"]
DEFAULT_LIMIT = 10


def load_file(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_games(): return load_file(GAMES_FILE, {})
def save_games(data): save_file(GAMES_FILE, data)
def load_users(): return load_file(USERS_FILE, {})
def save_users(data): save_file(USERS_FILE, data)
def load_config(): return load_file(CONFIG_FILE, {})
def save_config(data): save_file(CONFIG_FILE, data)
def load_history(): return load_file(HISTORY_FILE, [])
def save_history(data): save_file(HISTORY_FILE, data)


def is_admin(message):
    return message.from_user and message.from_user.id == ADMIN_ID


def is_admin_user(user):
    return user and user.id == ADMIN_ID


def register_user(user, nick=None):
    users = load_users()
    uid = str(user.id)

    if uid not in users:
        users[uid] = {
            "nick": nick or "",
            "username": user.username or "",
            "first_name": user.first_name or "",
            "score": 0,
            "status": "Гость",
            "visits": 0,
            "games_played": 0,
            "wins": 0
        }
    else:
        users[uid]["username"] = user.username or users[uid].get("username", "")
        users[uid]["first_name"] = user.first_name or users[uid].get("first_name", "")
        if nick:
            users[uid]["nick"] = nick
        users[uid].setdefault("score", 0)
        users[uid].setdefault("status", "Гость")
        users[uid].setdefault("visits", 0)
        users[uid].setdefault("games_played", 0)
        users[uid].setdefault("wins", 0)

    save_users(users)
    return uid, users[uid]


def add_manual_player(nick):
    users = load_users()
    key = "manual_" + nick.lower().replace(" ", "_")

    if key not in users:
        users[key] = {
            "nick": nick,
            "username": "",
            "first_name": nick,
            "score": 0,
            "status": "Гость",
            "visits": 0,
            "games_played": 0,
            "wins": 0
        }

    save_users(users)
    return key


def find_user(name):
    users = load_users()
    target = name.strip().lower().replace("@", "")

    for uid, u in users.items():
        if u.get("nick", "").lower() == target:
            return uid, u
        if u.get("username", "").lower() == target:
            return uid, u

    return None, None


def get_player_key(user):
    register_user(user)
    return "uid:" + str(user.id)


def get_status_icon(status):
    if status == "VIP":
        return "👑"
    if status == "Резидент клуба":
        return "⭐"
    if status == "Судья":
        return "⚖️"
    if status == "Ведущий":
        return "🎤"
    if status == "Masters":
        return "🏆"
    return ""


def show_player(key_or_nick):
    users = load_users()

    if isinstance(key_or_nick, str) and key_or_nick.startswith("uid:"):
        uid = key_or_nick.replace("uid:", "")
        u = users.get(uid, {})
        nick = u.get("nick") or u.get("first_name") or u.get("username") or "Игрок"
        icon = get_status_icon(u.get("status", "Гость"))
        return f"{icon} {nick}".strip()

    uid, u = find_user(key_or_nick)
    if u:
        icon = get_status_icon(u.get("status", "Гость"))
        nick = u.get("nick") or u.get("first_name") or key_or_nick
        return f"{icon} {nick}".strip()

    return key_or_nick


def player_status_from_key(key):
    users = load_users()
    if key.startswith("uid:"):
        uid = key.replace("uid:", "")
        return users.get(uid, {}).get("status", "Гость")
    _, u = find_user(key)
    return u.get("status", "Гость") if u else "Гость"


def parse_title_limit(raw):
    if "|" in raw:
        title, limit_text = raw.rsplit("|", 1)
        try:
            limit = int(limit_text.strip())
        except ValueError:
            limit = DEFAULT_LIMIT
    else:
        title = raw
        limit = DEFAULT_LIMIT
    return title.strip(), max(1, limit)


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎮 Записаться на игру", "❌ Отменить запись")
    kb.add("📋 Список игр", "⏳ Лист ожидания")
    kb.add("🏆 Рейтинг клуба", "📜 Правила клуба")
    kb.add("ℹ️ Информация")
    return kb


def rules_text():
    return (
        "📜 Устав HeadShotDubai\n\n"
        "💳 Стоимость участия:\n"
        "• ⭐ Резидент клуба — 75 AED\n"
        "• Гость клуба — 100 AED\n\n"
        "1. Уважение ко всем игрокам обязательно.\n"
        "2. Решения ведущего и судьи не обсуждаются во время игры.\n"
        "3. Оскорбления, токсичность и конфликты запрещены.\n"
        "4. Опоздание более чем на 10 минут может привести к замене игрока.\n"
        "5. Телефон во время игры использовать нельзя.\n"
        "6. Нельзя подсказывать, мешать игре или раскрывать роли вне регламента.\n"
        "7. Игрок обязан соблюдать атмосферу клуба.\n"
        "8. Администрация может отказать в участии без объяснения причин.\n"
        "9. Закрытые столы доступны VIP и резидентам сразу, гостям — после подтверждения.\n"
        "10. Капитанский стол формирует только администратор.\n\n"
        "PS. Семья — это не главное. Семья — это всё. 🖤"
    )


def help_text():
    return (
        "📖 Команды HeadShotDubai Bot\n\n"
        "Игрок:\n"
        "/start\n/setnick Ник\n/profile\n/rating\n/rules\n\n"
        "Админ:\n"
        "/setgroup\n"
        "/newgame 18 июня - Открытый стол | 10\n"
        "/closedgame 18 июня - Закрытый стол | 10\n"
        "/newcaptain 20 июня - Капитанский стол | 10\n"
        "/postgame ID\n/delgame ID\n/deleteallgames\n"
        "/addplayer Ник\n/setnickuser @username Ник\n/rename СтарыйНик НовыйНик\n"
        "/addtogame ID 19:30 Ник\n/removefromgame ID Ник\n"
        "/pending ID\n/approve ID Ник\n/reject ID Ник\n"
        "/players\n/allplayers\n"
        "/score Ник 5\n/result ID Ник 5\n/history\n"
        "/vip Ник\n/unvip Ник\n/resident Ник\n/unresident Ник\n/status Ник Статус\n"
        "/broadcast текст\n/remindgame ID\n/myid"
    )


def create_game(message, game_type, command_name, title_prefix):
    if not is_admin(message):
        return

    raw = message.text.replace(command_name, "").strip()
    if not raw:
        bot.reply_to(message, f"Формат:\n{command_name} 18 июня - {title_prefix} | 10")
        return

    title, limit = parse_title_limit(raw)
    games = load_games()
    game_id = str(max([int(x) for x in games.keys()] + [0]) + 1)

    games[game_id] = {
        "title": title,
        "type": game_type,
        "limit": limit,
        "slots": [{"time": t, "players": [], "waitlist": [], "pending": []} for t in DEFAULT_TIMES],
        "chat_id": None,
        "message_id": None
    }

    save_games(games)
    bot.reply_to(message, f"Игра создана ✅\nID: {game_id}\n{title}\nТип: {game_type}\nЛимит: {limit}\n\n/postgame {game_id}")


def can_self_signup(game, key):
    game_type = game.get("type", "")

    if game_type == "Капитанский стол":
        return False, "Капитанский стол формирует только администратор."

    if game_type == "Закрытый стол":
        status = player_status_from_key(key)
        if status in ["VIP", "Резидент клуба"]:
            return True, ""
        return None, "Заявка отправлена ✅ Ожидайте подтверждения администратора."

    return True, ""


def already_in_game(game, key):
    for slot in game["slots"]:
        if key in slot["players"] or key in slot["waitlist"] or key in slot.get("pending", []):
            return True
    return False


def game_keyboard(game_id):
    games = load_games()
    kb = types.InlineKeyboardMarkup()

    if game_id not in games:
        return kb

    game = games[game_id]
    limit = game.get("limit", DEFAULT_LIMIT)

    if game.get("type") != "Капитанский стол":
        for index, slot in enumerate(game["slots"]):
            kb.add(types.InlineKeyboardButton(
                f"⏰ {slot['time']} ({len(slot['players'])}/{limit})",
                callback_data=f"join_{game_id}_{index}"
            ))

        kb.add(types.InlineKeyboardButton("❌ Отменить мою запись", callback_data=f"cancel_{game_id}"))

    return kb


def all_games_keyboard(for_signup=False):
    games = load_games()
    kb = types.InlineKeyboardMarkup()

    for game_id, game in games.items():
        if for_signup and game.get("type") == "Капитанский стол":
            continue
        kb.add(types.InlineKeyboardButton(f"🎭 {game['title']}", callback_data=f"show_{game_id}"))

    return kb


def game_card(game_id):
    games = load_games()
    if game_id not in games:
        return "Игра не найдена."

    game = games[game_id]
    limit = game.get("limit", DEFAULT_LIMIT)
    text = "🎭 HeadShotDubai\n\n"
    text += f"ID {game_id}: {game['title']}\n"
    text += f"Тип: {game['type']}\n"
    text += f"Лимит: {limit} игроков\n\n"

    for slot in game["slots"]:
        players = slot["players"]
        waitlist = slot["waitlist"]
        pending = slot.get("pending", [])
        free = limit - len(players)

        text += f"⏰ {slot['time']} — {len(players)}/{limit}, свободно: {free}\n"

        if players:
            for i, p in enumerate(players, 1):
                text += f"{i}. {show_player(p)}\n"
        else:
            text += "Пока никто не записался\n"

        if waitlist:
            text += "⏳ Лист ожидания:\n"
            for i, p in enumerate(waitlist, 1):
                text += f"{i}. {show_player(p)}\n"

        if pending:
            text += "📝 Ожидают подтверждения:\n"
            for i, p in enumerate(pending, 1):
                text += f"{i}. {show_player(p)}\n"

        text += "\n"

    text += "PS. Семья — это не главное. Семья — это всё."
    return text


def all_games_text():
    games = load_games()
    if not games:
        return "📋 Пока игр нет."

    text = "📋 Активные игры HeadShotDubai\n\n"

    for game_id, game in games.items():
        limit = game.get("limit", DEFAULT_LIMIT)
        text += f"🎭 ID {game_id}: {game['title']}\n"
        text += f"Тип: {game['type']}\n"
        text += f"Лимит: {limit}\n"

        for slot in game["slots"]:
            text += f"⏰ {slot['time']} — {len(slot['players'])}/{limit}\n"

        text += f"Удалить: /delgame {game_id}\n\n"

    return text


def waitlist_text():
    games = load_games()
    found = False
    text = "⏳ Лист ожидания\n\n"

    for game_id, game in games.items():
        for slot in game["slots"]:
            if slot["waitlist"]:
                found = True
                text += f"🎭 {game['title']} — {slot['time']}\n"
                for i, p in enumerate(slot["waitlist"], 1):
                    text += f"{i}. {show_player(p)}\n"
                text += "\n"

    return text if found else "Лист ожидания пуст."


def update_group_card(game_id):
    games = load_games()
    if game_id not in games:
        return

    chat_id = games[game_id].get("chat_id")
    message_id = games[game_id].get("message_id")

    if not chat_id or not message_id:
        return

    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=game_card(game_id),
            reply_markup=game_keyboard(game_id)
        )
    except Exception:
        pass


def add_score(nick, points, reason="Корректировка"):
    uid, user = find_user(nick)
    if not user:
        uid = add_manual_player(nick)

    users = load_users()
    users[uid]["score"] = users[uid].get("score", 0) + points
    save_users(users)

    history = load_history()
    history.append({
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "nick": users[uid]["nick"],
        "points": points,
        "reason": reason
    })
    save_history(history)

    return users[uid]["score"]


@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, "Добро пожаловать в HeadShotDubai 🎭\n\nЗадай игровой ник:\n/setnick Адам", reply_markup=main_menu())


@bot.message_handler(commands=["setnick"])
def setnick(message):
    nick = message.text.replace("/setnick", "").strip()
    if not nick:
        bot.reply_to(message, "Формат:\n/setnick Адам")
        return
    register_user(message.from_user, nick)
    bot.reply_to(message, f"Игровой ник сохранён ✅\nТеперь ты: {nick}")


@bot.message_handler(commands=["myid"])
def myid(message):
    bot.reply_to(message, f"Твой ID: {message.from_user.id}")


@bot.message_handler(commands=["setgroup"])
def setgroup(message):
    if not is_admin(message): return
    config = load_config()
    config["group_chat_id"] = message.chat.id
    save_config(config)
    bot.reply_to(message, "Группа сохранена ✅")


@bot.message_handler(commands=["newgame"])
def newgame(message):
    create_game(message, "Открытый стол", "/newgame", "Открытый стол")


@bot.message_handler(commands=["closedgame"])
def closedgame(message):
    create_game(message, "Закрытый стол", "/closedgame", "Закрытый стол")


@bot.message_handler(commands=["newcaptain"])
def newcaptain(message):
    create_game(message, "Капитанский стол", "/newcaptain", "Капитанский стол")


@bot.message_handler(commands=["postgame"])
def postgame(message):
    if not is_admin(message): return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/postgame 1")
        return

    game_id = parts[1]
    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    config = load_config()
    target_chat = config.get("group_chat_id", message.chat.id)

    sent = bot.send_message(target_chat, game_card(game_id), reply_markup=game_keyboard(game_id))
    games[game_id]["chat_id"] = sent.chat.id
    games[game_id]["message_id"] = sent.message_id
    save_games(games)

    try:
        bot.pin_chat_message(sent.chat.id, sent.message_id, disable_notification=True)
    except Exception:
        pass

    bot.reply_to(message, "Карточка игры опубликована ✅")


@bot.message_handler(commands=["delgame"])
def delgame(message):
    if not is_admin(message): return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/delgame 1")
        return
    games = load_games()
    game_id = parts[1]
    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return
    title = games[game_id]["title"]
    del games[game_id]
    save_games(games)
    bot.reply_to(message, f"Игра удалена ✅\nID: {game_id}\n{title}")


@bot.message_handler(commands=["deleteallgames"])
def deleteallgames(message):
    if not is_admin(message): return
    save_games({})
    bot.reply_to(message, "Все игры удалены ✅")


@bot.message_handler(commands=["games"])
@bot.message_handler(func=lambda m: m.text == "📋 Список игр")
def games_list(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, all_games_text(), reply_markup=all_games_keyboard())


@bot.message_handler(func=lambda m: m.text == "🎮 Записаться на игру")
def signup_button(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, "Выбери игру:", reply_markup=all_games_keyboard(for_signup=True))


@bot.callback_query_handler(func=lambda c: c.data.startswith("show_"))
def show_game(call):
    register_user(call.from_user)
    game_id = call.data.split("_")[1]
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=game_card(game_id), reply_markup=game_keyboard(game_id))
    except Exception:
        bot.send_message(call.message.chat.id, game_card(game_id), reply_markup=game_keyboard(game_id))


@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def join_game(call):
    key = get_player_key(call.from_user)
    _, game_id, slot_index = call.data.split("_")
    slot_index = int(slot_index)

    games = load_games()
    if game_id not in games:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return

    game = games[game_id]
    allowed, msg = can_self_signup(game, key)

    if allowed is False:
        bot.answer_callback_query(call.id, msg)
        return

    if already_in_game(game, key):
        bot.answer_callback_query(call.id, "Ты уже записан.")
        return

    slot = game["slots"][slot_index]

    if allowed is None:
        slot.setdefault("pending", []).append(key)
        bot.answer_callback_query(call.id, msg)
    else:
        if len(slot["players"]) < game.get("limit", DEFAULT_LIMIT):
            slot["players"].append(key)
            bot.answer_callback_query(call.id, "Ты записан ✅")
        else:
            slot["waitlist"].append(key)
            bot.answer_callback_query(call.id, "Ты в листе ожидания ⏳")

    save_games(games)
    update_group_card(game_id)

    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=game_card(game_id), reply_markup=game_keyboard(game_id))
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def cancel_from_card(call):
    key = get_player_key(call.from_user)
    game_id = call.data.split("_")[1]
    games = load_games()
    removed = False

    if game_id not in games:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return

    for slot in games[game_id]["slots"]:
        for field in ["players", "waitlist", "pending"]:
            if key in slot.get(field, []):
                slot[field].remove(key)
                removed = True

        if removed and slot["waitlist"] and len(slot["players"]) < games[game_id].get("limit", DEFAULT_LIMIT):
            slot["players"].append(slot["waitlist"].pop(0))

    save_games(games)
    update_group_card(game_id)

    bot.answer_callback_query(call.id, "Запись отменена ✅" if removed else "Ты не был записан.")

    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=game_card(game_id), reply_markup=game_keyboard(game_id))
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "❌ Отменить запись")
def cancel_button(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, "Выбери игру и нажми «Отменить мою запись»:", reply_markup=all_games_keyboard())


@bot.message_handler(func=lambda m: m.text == "⏳ Лист ожидания")
def waitlist_button(message):
    bot.send_message(message.chat.id, waitlist_text())


@bot.message_handler(commands=["addplayer"])
def addplayer(message):
    if not is_admin(message): return
    nick = message.text.replace("/addplayer", "").strip()
    if not nick:
        bot.reply_to(message, "Формат:\n/addplayer Adam")
        return
    add_manual_player(nick)
    bot.reply_to(message, f"Игрок добавлен ✅\n{nick}")


@bot.message_handler(commands=["setnickuser"])
def setnickuser(message):
    if not is_admin(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/setnickuser @username НовыйНик")
        return
    username = parts[1].replace("@", "").lower()
    new_nick = parts[2].strip()
    users = load_users()
    for uid, u in users.items():
        if u.get("username", "").lower() == username:
            users[uid]["nick"] = new_nick
            save_users(users)
            bot.reply_to(message, f"Ник изменён ✅\n@{username} → {new_nick}")
            return
    bot.reply_to(message, "Игрок не найден. Он должен нажать /start или записаться.")


@bot.message_handler(commands=["rename"])
def rename(message):
    if not is_admin(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/rename СтарыйНик НовыйНик")
        return
    old, new = parts[1], parts[2]
    uid, u = find_user(old)
    if not u:
        bot.reply_to(message, "Игрок не найден.")
        return
    users = load_users()
    users[uid]["nick"] = new
    save_users(users)
    bot.reply_to(message, f"Ник изменён ✅\n{old} → {new}")


@bot.message_handler(commands=["addtogame"])
def addtogame(message):
    if not is_admin(message): return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        bot.reply_to(message, "Формат:\n/addtogame 1 19:30 Adam")
        return

    game_id, time_value, nick = parts[1], parts[2], parts[3]
    add_manual_player(nick)
    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    game = games[game_id]
    limit = game.get("limit", DEFAULT_LIMIT)

    for slot in game["slots"]:
        if nick in slot["players"] or nick in slot["waitlist"]:
            bot.reply_to(message, "Игрок уже записан.")
            return

    for slot in game["slots"]:
        if slot["time"] == time_value:
            if len(slot["players"]) < limit:
                slot["players"].append(nick)
                result = "Игрок записан ✅"
            else:
                slot["waitlist"].append(nick)
                result = "Игрок добавлен в лист ожидания ⏳"
            save_games(games)
            update_group_card(game_id)
            bot.reply_to(message, result)
            return

    bot.reply_to(message, "Такого времени нет.")


@bot.message_handler(commands=["removefromgame"])
def removefromgame(message):
    if not is_admin(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/removefromgame 1 Adam")
        return

    game_id, nick = parts[1], parts[2]
    games = load_games()
    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    removed = False
    for slot in games[game_id]["slots"]:
        for field in ["players", "waitlist", "pending"]:
            if nick in slot.get(field, []):
                slot[field].remove(nick)
                removed = True
        if removed and slot["waitlist"] and len(slot["players"]) < games[game_id].get("limit", DEFAULT_LIMIT):
            slot["players"].append(slot["waitlist"].pop(0))

    save_games(games)
    update_group_card(game_id)
    bot.reply_to(message, "Игрок удалён ✅" if removed else "Игрок не найден.")


@bot.message_handler(commands=["pending"])
def pending(message):
    if not is_admin(message): return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/pending 1")
        return
    game_id = parts[1]
    games = load_games()
    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    text = f"📝 Заявки на игру ID {game_id}\n\n"
    found = False
    for slot in games[game_id]["slots"]:
        if slot.get("pending"):
            found = True
            text += f"⏰ {slot['time']}\n"
            for p in slot["pending"]:
                text += f"- {show_player(p)}\n"
            text += "\n"
    bot.reply_to(message, text if found else "Заявок нет.")


@bot.message_handler(commands=["approve"])
def approve(message):
    if not is_admin(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/approve 1 Adam")
        return
    game_id, nick = parts[1], parts[2]
    games = load_games()
    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    for slot in games[game_id]["slots"]:
        for p in list(slot.get("pending", [])):
            if show_player(p).replace("👑", "").replace("⭐", "").strip().lower() == nick.lower() or p == nick:
                slot["pending"].remove(p)
                if len(slot["players"]) < games[game_id].get("limit", DEFAULT_LIMIT):
                    slot["players"].append(p)
                else:
                    slot["waitlist"].append(p)
                save_games(games)
                update_group_card(game_id)
                bot.reply_to(message, "Заявка одобрена ✅")
                return
    bot.reply_to(message, "Заявка не найдена.")


@bot.message_handler(commands=["reject"])
def reject(message):
    if not is_admin(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/reject 1 Adam")
        return
    game_id, nick = parts[1], parts[2]
    games = load_games()
    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    for slot in games[game_id]["slots"]:
        for p in list(slot.get("pending", [])):
            if show_player(p).replace("👑", "").replace("⭐", "").strip().lower() == nick.lower() or p == nick:
                slot["pending"].remove(p)
                save_games(games)
                update_group_card(game_id)
                bot.reply_to(message, "Заявка отклонена ✅")
                return
    bot.reply_to(message, "Заявка не найдена.")


@bot.message_handler(commands=["players"])
def players(message):
    if not is_admin(message): return
    games = load_games()
    text = ""
    for game_id in games.keys():
        text += game_card(game_id) + "\n\n"
    bot.send_message(message.chat.id, text if text else "Игр пока нет.")


@bot.message_handler(commands=["allplayers"])
def allplayers(message):
    if not is_admin(message): return
    users = load_users()
    if not users:
        bot.send_message(message.chat.id, "База игроков пустая.")
        return

    text = "👥 Все игроки HeadShotDubai\n\n"
    for i, u in enumerate(users.values(), 1):
        icon = get_status_icon(u.get("status", "Гость"))
        nick = u.get("nick") or u.get("first_name") or "Игрок"
        username = u.get("username", "")
        text += f"{i}. {icon} {nick} — {u.get('score', 0)} очков | {u.get('status', 'Гость')}".strip()
        if username:
            text += f" (@{username})"
        text += "\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["score"])
def score(message):
    if not is_admin(message): return
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/score Adam 5")
        return
    nick = parts[1]
    try:
        points = int(parts[2])
    except ValueError:
        bot.reply_to(message, "Баллы должны быть числом.")
        return
    total = add_score(nick, points, "Ручная корректировка")
    bot.reply_to(message, f"Рейтинг обновлён ✅\n{nick}: {total} очков")


@bot.message_handler(commands=["result"])
def result(message):
    if not is_admin(message): return
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "Формат:\n/result 1 Adam 5")
        return
    game_id, nick = parts[1], parts[2]
    try:
        points = int(parts[3])
    except ValueError:
        bot.reply_to(message, "Баллы должны быть числом.")
        return
    total = add_score(nick, points, f"Результат игры ID {game_id}")
    bot.reply_to(message, f"Результат внесён ✅\n{nick}: {total} очков")


@bot.message_handler(commands=["history"])
def history(message):
    if not is_admin(message): return
    data = load_history()
    if not data:
        bot.send_message(message.chat.id, "История рейтинга пустая.")
        return
    text = "📈 История рейтинга\n\n"
    for h in data[-30:]:
        sign = "+" if h["points"] > 0 else ""
        text += f"{h['date']} — {h['nick']} {sign}{h['points']} ({h['reason']})\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["rating"])
@bot.message_handler(func=lambda m: m.text == "🏆 Рейтинг клуба")
def rating(message):
    register_user(message.from_user)
    users = load_users()
    if not users:
        bot.send_message(message.chat.id, "Рейтинг пока пуст.")
        return
    sorted_users = sorted(users.values(), key=lambda u: u.get("score", 0), reverse=True)
    text = "🏆 Рейтинг клуба HeadShotDubai\n\n"
    for i, u in enumerate(sorted_users, 1):
        icon = get_status_icon(u.get("status", "Гость"))
        nick = u.get("nick") or u.get("first_name") or "Игрок"
        text += f"{i}. {icon} {nick} — {u.get('score', 0)} очков | {u.get('status', 'Гость')}\n".strip() + "\n"
    bot.send_message(message.chat.id, text)


def set_player_status(message, new_status):
    if not is_admin(message): return
    nick = message.text.split(maxsplit=1)[1].strip() if len(message.text.split(maxsplit=1)) > 1 else ""
    uid, u = find_user(nick)
    if not u:
        bot.reply_to(message, "Игрок не найден.")
        return
    users = load_users()
    users[uid]["status"] = new_status
    save_users(users)
    bot.reply_to(message, f"Статус обновлён ✅\n{show_player(nick)}: {new_status}")


@bot.message_handler(commands=["vip"])
def vip(message): set_player_status(message, "VIP")


@bot.message_handler(commands=["unvip"])
def unvip(message): set_player_status(message, "Гость")


@bot.message_handler(commands=["resident"])
def resident(message): set_player_status(message, "Резидент клуба")


@bot.message_handler(commands=["unresident"])
def unresident(message): set_player_status(message, "Гость")


@bot.message_handler(commands=["status"])
def status(message):
    if not is_admin(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/status Adam Судья")
        return
    nick, new_status = parts[1], parts[2]
    uid, u = find_user(nick)
    if not u:
        bot.reply_to(message, "Игрок не найден.")
        return
    users = load_users()
    users[uid]["status"] = new_status
    save_users(users)
    bot.reply_to(message, f"Статус обновлён ✅\n{nick}: {new_status}")


@bot.message_handler(commands=["profile"])
def profile(message):
    _, u = register_user(message.from_user)
    icon = get_status_icon(u.get("status", "Гость"))
    nick = u.get("nick") or u.get("first_name") or "Игрок"
    gp = u.get("games_played", 0)
    wins = u.get("wins", 0)
    winrate = round((wins / gp) * 100, 1) if gp else 0
    bot.send_message(message.chat.id, f"🎭 {icon} {nick}\n\nРейтинг: {u.get('score', 0)}\nСтатус: {u.get('status', 'Гость')}\nПосещений: {u.get('visits', 0)}\nИгр сыграно: {gp}\nПобед: {wins}\nПроцент побед: {winrate}%")


@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if not is_admin(message): return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(message, "Формат:\n/broadcast Завтра игра в 19:30")
        return
    count = 0
    for uid in load_users().keys():
        if uid.startswith("manual_"):
            continue
        try:
            bot.send_message(int(uid), text)
            count += 1
        except Exception:
            pass
    bot.reply_to(message, f"Рассылка отправлена ✅\nПолучателей: {count}")


@bot.message_handler(commands=["remindgame"])
def remindgame(message):
    if not is_admin(message): return
    bot.reply_to(message, "Напоминание подготовлено ✅")


@bot.message_handler(commands=["rules"])
@bot.message_handler(func=lambda m: m.text == "📜 Правила клуба")
def rules(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, rules_text())


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(message.chat.id, help_text())


@bot.message_handler(func=lambda m: m.text == "ℹ️ Информация")
def info(message):
    bot.send_message(message.chat.id, "HeadShotDubai 🎭\n\nСпортивная мафия в Дубае.\nОткрытые, закрытые и капитанские столы.\n\nСтоимость:\n• ⭐ Резидент клуба — 75 AED\n• Гость клуба — 100 AED\n\nPS. Семья — это не главное. Семья — это всё.")


bot.infinity_polling()