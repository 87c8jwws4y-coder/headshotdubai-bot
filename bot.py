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


def load_games():
    return load_file(GAMES_FILE, {})


def save_games(data):
    save_file(GAMES_FILE, data)


def load_users():
    return load_file(USERS_FILE, {})


def save_users(data):
    save_file(USERS_FILE, data)


def load_config():
    return load_file(CONFIG_FILE, {})


def save_config(data):
    save_file(CONFIG_FILE, data)


def load_history():
    return load_file(HISTORY_FILE, [])


def save_history(data):
    save_file(HISTORY_FILE, data)


def is_admin(message):
    return message.from_user and message.from_user.id == ADMIN_ID


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
    return uid


def add_manual_player(nick):
    users = load_users()
    uid = "manual_" + nick.lower().replace(" ", "_")

    if uid not in users:
        users[uid] = {
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
    return uid


def find_user(name):
    users = load_users()
    target = name.strip().lower().replace("@", "")

    for uid, user in users.items():
        if user.get("nick", "").lower() == target:
            return uid

        if user.get("username", "").lower() == target:
            return uid

    return None


def ensure_player(name):
    uid = find_user(name)
    if uid:
        return uid
    return add_manual_player(name)


def player_key_from_telegram(user):
    register_user(user)
    return str(user.id)


def status_icon(status):
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


def show_player(uid):
    users = load_users()
    user = users.get(uid, {})

    nick = user.get("nick") or user.get("first_name") or user.get("username") or uid
    icon = status_icon(user.get("status", "Гость"))

    if icon:
        return f"{icon} {nick}"
    return nick


def player_status(uid):
    users = load_users()
    return users.get(uid, {}).get("status", "Гость")


def parse_title_limit(raw):
    if "|" in raw:
        title, limit_text = raw.rsplit("|", 1)
        title = title.strip()

        try:
            limit = int(limit_text.strip())
        except ValueError:
            limit = DEFAULT_LIMIT
    else:
        title = raw.strip()
        limit = DEFAULT_LIMIT

    if limit <= 0:
        limit = DEFAULT_LIMIT

    return title, limit


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎮 Записаться на игру", "❌ Отменить запись")
    kb.add("📋 Список игр", "⏳ Лист ожидания")
    kb.add("🏆 Рейтинг клуба", "📜 Правила клуба")
    kb.add("ℹ️ Информация")
    return kbdef rules_text():
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
        "9. Закрытые столы: VIP и резиденты записываются сразу, гости — после подтверждения.\n"
        "10. Капитанский стол формирует только администратор.\n\n"
        "PS. Семья — это не главное. Семья — это всё. 🖤"
    )


def help_text():
    return (
        "📖 Команды HeadShotDubai Bot\n\n"
        "Игрок:\n"
        "/start\n"
        "/setnick Ник\n"
        "/profile\n"
        "/rating\n"
        "/rules\n\n"
        "Админ:\n"
        "/setgroup\n"
        "/newgame 18 июня - Открытый стол | 10\n"
        "/closedgame 18 июня - Закрытый стол | 10\n"
        "/newcaptain 20 июня - Капитанский стол | 10\n"
        "/postgame ID\n"
        "/delgame ID\n"
        "/deleteallgames\n"
        "/addplayer Ник\n"
        "/setnickuser @username Ник\n"
        "/rename СтарыйНик НовыйНик\n"
        "/addtogame ID 19:30 Ник\n"
        "/removefromgame ID Ник\n"
        "/pending ID\n"
        "/approve ID Ник\n"
        "/reject ID Ник\n"
        "/players ID\n"
        "/allplayers\n"
        "/score Ник 5\n"
        "/result ID Ник 5\n"
        "/history\n"
        "/resident Ник\n"
        "/unresident Ник\n"
        "/vip Ник\n"
        "/unvip Ник\n"
        "/status Ник Статус\n"
        "/announcement Текст\n"
        "/pinannouncement Текст\n"
        "/broadcast Текст\n"
        "/remindgame ID\n"
        "/myid"
    )


def create_game(message, game_type, command_name, example_title):
    if not is_admin(message):
        return

    raw = message.text.replace(command_name, "").strip()

    if not raw:
        bot.reply_to(message, f"Формат:\n{command_name} {example_title} | 10")
        return

    title, limit = parse_title_limit(raw)
    games = load_games()

    game_id = str(max([int(x) for x in games.keys()] + [0]) + 1)

    games[game_id] = {
        "title": title,
        "type": game_type,
        "limit": limit,
        "slots": [
            {
                "time": time_value,
                "players": [],
                "waitlist": [],
                "pending": []
            }
            for time_value in DEFAULT_TIMES
        ],
        "chat_id": None,
        "message_id": None
    }

    save_games(games)

    bot.reply_to(
        message,
        f"Игра создана ✅\n"
        f"ID: {game_id}\n"
        f"{title}\n"
        f"Тип: {game_type}\n"
        f"Лимит: {limit}\n\n"
        f"Опубликовать:\n/postgame {game_id}"
    )


def collect_players(game):
    result = []

    for slot in game["slots"]:
        for uid in slot["players"]:
            result.append((uid, slot["time"]))

    return result


def collect_waitlist(game):
    result = []

    for slot in game["slots"]:
        for uid in slot["waitlist"]:
            result.append((uid, slot["time"]))

    return result


def collect_pending(game):
    result = []

    for slot in game["slots"]:
        for uid in slot.get("pending", []):
            result.append((uid, slot["time"]))

    return result


def player_in_game(game, uid):
    for slot in game["slots"]:
        if uid in slot["players"]:
            return True

        if uid in slot["waitlist"]:
            return True

        if uid in slot.get("pending", []):
            return True

    return False


def game_keyboard(game_id):
    games = load_games()
    kb = types.InlineKeyboardMarkup()

    if game_id not in games:
        return kb

    game = games[game_id]

    if game["type"] == "Капитанский стол":
        return kb

    for index, slot in enumerate(game["slots"]):
        kb.add(
            types.InlineKeyboardButton(
                f"⏰ {slot['time']} ({len(slot['players'])}/{game['limit']})",
                callback_data=f"join_{game_id}_{index}"
            )
        )

    kb.add(
        types.InlineKeyboardButton(
            "❌ Отменить мою запись",
            callback_data=f"cancel_{game_id}"
        )
    )

    return kb


def all_games_keyboard(for_signup=False):
    games = load_games()
    kb = types.InlineKeyboardMarkup()

    for game_id, game in games.items():
        if for_signup and game["type"] == "Капитанский стол":
            continue

        kb.add(
            types.InlineKeyboardButton(
                f"🎭 {game['title']}",
                callback_data=f"show_{game_id}"
            )
        )

    return kb


def game_card(game_id):
    games = load_games()

    if game_id not in games:
        return "Игра не найдена."

    game = games[game_id]

    text = "🎭 HeadShotDubai\n\n"
    text += f"ID {game_id}: {game['title']}\n"
    text += f"Тип: {game['type']}\n"
    text += f"Лимит: {game['limit']} игроков\n\n"

    text += "⏰ Времена:\n"
    for slot in game["slots"]:
        text += f"{slot['time']} — {len(slot['players'])}/{game['limit']}\n"

    players = collect_players(game)
    text += "\n👥 Записанные игроки\n\n"

    if players:
        for index, item in enumerate(players, 1):
            uid, time_value = item
            text += f"{index}. {show_player(uid)} — {time_value}\n"
    else:
        text += "Пока никто не записался\n"

    waitlist = collect_waitlist(game)

    if waitlist:
        text += "\n⏳ Лист ожидания\n\n"
        for index, item in enumerate(waitlist, 1):
            uid, time_value = item
            text += f"{index}. {show_player(uid)} — {time_value}\n"

    pending = collect_pending(game)

    if pending:
        text += "\n📝 Ожидают подтверждения\n\n"
        for index, item in enumerate(pending, 1):
            uid, time_value = item
            text += f"{index}. {show_player(uid)} — {time_value}\n"

    text += "\nPS. Семья — это не главное. Семья — это всё."

    return text


def all_games_text():
    games = load_games()

    if not games:
        return "📋 Пока игр нет."

    text = "📋 Активные игры HeadShotDubai\n\n"

    for game_id, game in games.items():
        text += f"🎭 ID {game_id}: {game['title']}\n"
        text += f"Тип: {game['type']}\n"
        text += f"Игроков: {len(collect_players(game))}/{game['limit']}\n"
        text += f"Удалить: /delgame {game_id}\n\n"

    return textdef waitlist_text():
    games = load_games()
    text = "⏳ Лист ожидания\n\n"
    found = False

    for game_id, game in games.items():
        waitlist = collect_waitlist(game)

        if waitlist:
            found = True
            text += f"🎭 {game['title']}\n"

            for index, item in enumerate(waitlist, 1):
                uid, time_value = item
                text += f"{index}. {show_player(uid)} — {time_value}\n"

            text += "\n"

    if not found:
        return "Лист ожидания пуст."

    return text


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


def add_score_to_player(nick, points, reason):
    uid = ensure_player(nick)
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


def can_self_signup(game, uid):
    game_type = game["type"]

    if game_type == "Капитанский стол":
        return False, "Капитанский стол формирует только администратор."

    if game_type == "Закрытый стол":
        status = player_status(uid)

        if status in ["VIP", "Резидент клуба"]:
            return True, ""

        return None, "Заявка отправлена ✅ Ожидайте подтверждения администратора."

    return True, ""


@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.from_user)

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в HeadShotDubai 🎭\n\n"
        "Задай игровой ник:\n/setnick Адам",
        reply_markup=main_menu()
    )


@bot.message_handler(commands=["setnick"])
def setnick(message):
    nick = message.text.replace("/setnick", "").strip()

    if not nick:
        bot.reply_to(message, "Формат:\n/setnick Адам")
        return

    register_user(message.from_user, nick)

    bot.reply_to(
        message,
        f"Игровой ник сохранён ✅\nТеперь ты: {nick}"
    )


@bot.message_handler(commands=["myid"])
def myid(message):
    bot.reply_to(message, f"Твой ID: {message.from_user.id}")


@bot.message_handler(commands=["setgroup"])
def setgroup(message):
    if not is_admin(message):
        return

    config = load_config()
    config["group_chat_id"] = message.chat.id
    save_config(config)

    bot.reply_to(message, "Группа сохранена ✅")


@bot.message_handler(commands=["newgame"])
def newgame(message):
    create_game(
        message,
        "Открытый стол",
        "/newgame",
        "18 июня - Открытый стол"
    )


@bot.message_handler(commands=["closedgame"])
def closedgame(message):
    create_game(
        message,
        "Закрытый стол",
        "/closedgame",
        "18 июня - Закрытый стол"
    )


@bot.message_handler(commands=["newcaptain"])
def newcaptain(message):
    create_game(
        message,
        "Капитанский стол",
        "/newcaptain",
        "20 июня - Капитанский стол"
    )


@bot.message_handler(commands=["postgame"])
def postgame(message):
    if not is_admin(message):
        return

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

    sent = bot.send_message(
        target_chat,
        game_card(game_id),
        reply_markup=game_keyboard(game_id)
    )

    games[game_id]["chat_id"] = sent.chat.id
    games[game_id]["message_id"] = sent.message_id

    save_games(games)

    try:
        bot.pin_chat_message(
            sent.chat.id,
            sent.message_id,
            disable_notification=True
        )
    except Exception:
        pass

    bot.reply_to(message, "Карточка игры опубликована ✅")


@bot.message_handler(commands=["delgame"])
def delgame(message):
    if not is_admin(message):
        return

    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/delgame 1")
        return

    game_id = parts[1]
    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    title = games[game_id]["title"]

    del games[game_id]
    save_games(games)

    bot.reply_to(
        message,
        f"Игра удалена ✅\nID: {game_id}\n{title}"
    )


@bot.message_handler(commands=["deleteallgames"])
def deleteallgames(message):
    if not is_admin(message):
        return

    save_games({})
    bot.reply_to(message, "Все игры удалены ✅")


@bot.message_handler(commands=["games"])
@bot.message_handler(func=lambda m: m.text == "📋 Список игр")
def games_list(message):
    register_user(message.from_user)

    bot.send_message(
        message.chat.id,
        all_games_text(),
        reply_markup=all_games_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🎮 Записаться на игру")
def signup_button(message):
    register_user(message.from_user)

    bot.send_message(
        message.chat.id,
        "Выбери игру:",
        reply_markup=all_games_keyboard(for_signup=True)
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("show_"))
def show_game(call):
    register_user(call.from_user)

    game_id = call.data.split("_")[1]

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=game_card(game_id),
            reply_markup=game_keyboard(game_id)
        )
    except Exception:
        bot.send_message(
            call.message.chat.id,
            game_card(game_id),
            reply_markup=game_keyboard(game_id)
        )@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def join_game(call):
    uid = player_key_from_telegram(call.from_user)

    _, game_id, slot_index = call.data.split("_")
    slot_index = int(slot_index)

    games = load_games()

    if game_id not in games:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return

    game = games[game_id]

    if player_in_game(game, uid):
        bot.answer_callback_query(call.id, "Ты уже записан.")
        return

    allowed, message_text = can_self_signup(game, uid)

    if allowed is False:
        bot.answer_callback_query(call.id, message_text)
        return

    slot = game["slots"][slot_index]

    if allowed is None:
        slot["pending"].append(uid)
        bot.answer_callback_query(call.id, message_text)
    else:
        if len(slot["players"]) < game["limit"]:
            slot["players"].append(uid)
            bot.answer_callback_query(call.id, "Ты записан ✅")
        else:
            slot["waitlist"].append(uid)
            bot.answer_callback_query(call.id, "Ты в листе ожидания ⏳")

    save_games(games)
    update_group_card(game_id)

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=game_card(game_id),
            reply_markup=game_keyboard(game_id)
        )
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def cancel_from_card(call):
    uid = player_key_from_telegram(call.from_user)

    game_id = call.data.split("_")[1]
    games = load_games()
    removed = False

    if game_id not in games:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return

    game = games[game_id]

    for slot in game["slots"]:
        for field in ["players", "waitlist", "pending"]:
            if uid in slot[field]:
                slot[field].remove(uid)
                removed = True

        if slot["waitlist"] and len(slot["players"]) < game["limit"]:
            slot["players"].append(slot["waitlist"].pop(0))

    save_games(games)
    update_group_card(game_id)

    bot.answer_callback_query(
        call.id,
        "Запись отменена ✅" if removed else "Ты не был записан."
    )

    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=game_card(game_id),
            reply_markup=game_keyboard(game_id)
        )
    except Exception:
        pass


@bot.message_handler(func=lambda m: m.text == "❌ Отменить запись")
def cancel_button(message):
    register_user(message.from_user)

    bot.send_message(
        message.chat.id,
        "Выбери игру и нажми «Отменить мою запись»:",
        reply_markup=all_games_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "⏳ Лист ожидания")
def waitlist_button(message):
    bot.send_message(message.chat.id, waitlist_text())


@bot.message_handler(commands=["addplayer"])
def addplayer(message):
    if not is_admin(message):
        return

    nick = message.text.replace("/addplayer", "").strip()

    if not nick:
        bot.reply_to(message, "Формат:\n/addplayer Adam")
        return

    add_manual_player(nick)

    bot.reply_to(message, f"Игрок добавлен ✅\n{nick}")


@bot.message_handler(commands=["setnickuser"])
def setnickuser(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/setnickuser @username НовыйНик")
        return

    username = parts[1].replace("@", "").lower()
    new_nick = parts[2].strip()

    users = load_users()

    for uid, user in users.items():
        if user.get("username", "").lower() == username:
            users[uid]["nick"] = new_nick
            save_users(users)

            bot.reply_to(
                message,
                f"Ник изменён ✅\n@{username} → {new_nick}"
            )
            return

    bot.reply_to(
        message,
        "Игрок не найден. Он должен нажать /start или записаться."
    )


@bot.message_handler(commands=["rename"])
def rename(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/rename СтарыйНик НовыйНик")
        return

    old_nick = parts[1]
    new_nick = parts[2]

    uid = ensure_player(old_nick)
    users = load_users()
    users[uid]["nick"] = new_nick
    save_users(users)

    bot.reply_to(
        message,
        f"Ник изменён ✅\n{old_nick} → {new_nick}"
    )


@bot.message_handler(commands=["addtogame"])
def addtogame(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=3)

    if len(parts) < 4:
        bot.reply_to(message, "Формат:\n/addtogame 1 19:30 Adam")
        return

    game_id = parts[1]
    time_value = parts[2]
    nick = parts[3]

    uid = ensure_player(nick)
    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    game = games[game_id]

    if player_in_game(game, uid):
        bot.reply_to(message, "Игрок уже записан на эту игру.")
        return

    for slot in game["slots"]:
        if slot["time"] == time_value:
            if len(slot["players"]) < game["limit"]:
                slot["players"].append(uid)
                result = "Игрок записан ✅"
            else:
                slot["waitlist"].append(uid)
                result = "Игрок добавлен в лист ожидания ⏳"

            save_games(games)
            update_group_card(game_id)
            bot.reply_to(message, result)
            return

    bot.reply_to(message, "Такого времени нет.")


@bot.message_handler(commands=["removefromgame"])
def removefromgame(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/removefromgame 1 Adam")
        return

    game_id = parts[1]
    nick = parts[2]

    uid = ensure_player(nick)
    games = load_games()
    removed = False

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    game = games[game_id]

    for slot in game["slots"]:
        for field in ["players", "waitlist", "pending"]:
            if uid in slot[field]:
                slot[field].remove(uid)
                removed = True

        if slot["waitlist"] and len(slot["players"]) < game["limit"]:
            slot["players"].append(slot["waitlist"].pop(0))

    save_games(games)
    update_group_card(game_id)

    bot.reply_to(
        message,
        "Игрок удалён ✅" if removed else "Игрок не найден в игре."
    )


@bot.message_handler(commands=["pending"])
def pending(message):
    if not is_admin(message):
        return

    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/pending 1")
        return

    game_id = parts[1]
    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    game = games[game_id]
    pending_list = collect_pending(game)

    if not pending_list:
        bot.reply_to(message, "Заявок нет.")
        return

    text = f"📝 Заявки на игру ID {game_id}\n\n"

    for index, item in enumerate(pending_list, 1):
        uid, time_value = item
        text += f"{index}. {show_player(uid)} — {time_value}\n"

    bot.reply_to(message, text)


@bot.message_handler(commands=["approve"])
def approve(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/approve 1 Adam")
        return

    game_id = parts[1]
    nick = parts[2].lower()

    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    game = games[game_id]

    for slot in game["slots"]:
        for uid in list(slot["pending"]):
            if show_player(uid).replace("👑", "").replace("⭐", "").strip().lower() == nick:
                slot["pending"].remove(uid)

                if len(slot["players"]) < game["limit"]:
                    slot["players"].append(uid)
                else:
                    slot["waitlist"].append(uid)

                save_games(games)
                update_group_card(game_id)

                bot.reply_to(message, "Заявка одобрена ✅")
                return

    bot.reply_to(message, "Заявка не найдена.")


@bot.message_handler(commands=["reject"])
def reject(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/reject 1 Adam")
        return

    game_id = parts[1]
    nick = parts[2].lower()

    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    game = games[game_id]

    for slot in game["slots"]:
        for uid in list(slot["pending"]):
            if show_player(uid).replace("👑", "").replace("⭐", "").strip().lower() == nick:
                slot["pending"].remove(uid)
                save_games(games)
                update_group_card(game_id)

                bot.reply_to(message, "Заявка отклонена ✅")
                return

    bot.reply_to(message, "Заявка не найдена.")


@bot.message_handler(commands=["players"])
def players(message):
    if not is_admin(message):
        return

    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/players ID")
        return

    game_id = parts[1]
    games = load_games()

    if game_id not in games:
        bot.reply_to(message, "Игра не найдена.")
        return

    game = games[game_id]
    players_list = collect_players(game)

    text = "👥 Записанные игроки\n\n"

    if players_list:
        for index, item in enumerate(players_list, 1):
            uid, time_value = item
            text += f"{index}. {show_player(uid)} — {time_value}\n"
    else:
        text += "Пока никто не записался."

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["allplayers"])
def allplayers(message):
    if not is_admin(message):
        return

    users = load_users()

    if not users:
        bot.send_message(message.chat.id, "База игроков пустая.")
        return

    text = "👥 Все игроки HeadShotDubai\n\n"

    for index, uid in enumerate(users.keys(), 1):
        user = users[uid]
        text += (
            f"{index}. {show_player(uid)} — "
            f"{user.get('score', 0)} очков | "
            f"{user.get('status', 'Гость')}\n"
        )

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["score"])
def score(message):
    if not is_admin(message):
        return

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

    total = add_score_to_player(
        nick,
        points,
        "Ручная корректировка"
    )

    bot.reply_to(
        message,
        f"Рейтинг обновлён ✅\n{nick}: {total} очков"
    )


@bot.message_handler(commands=["result"])
def result(message):
    if not is_admin(message):
        return

    parts = message.text.split()

    if len(parts) < 4:
        bot.reply_to(message, "Формат:\n/result 1 Adam 5")
        return

    game_id = parts[1]
    nick = parts[2]

    try:
        points = int(parts[3])
    except ValueError:
        bot.reply_to(message, "Баллы должны быть числом.")
        return

    total = add_score_to_player(
        nick,
        points,
        f"Результат игры ID {game_id}"
    )

    bot.reply_to(
        message,
        f"Результат внесён ✅\n{nick}: {total} очков"
    )


@bot.message_handler(commands=["history"])
def history(message):
    if not is_admin(message):
        return

    data = load_history()

    if not data:
        bot.send_message(message.chat.id, "История рейтинга пустая.")
        return

    text = "📈 История рейтинга\n\n"

    for item in data[-30:]:
        sign = "+" if item["points"] > 0 else ""
        text += f"{item['date']} — {item['nick']} {sign}{item['points']} ({item['reason']})\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["rating"])
@bot.message_handler(func=lambda m: m.text == "🏆 Рейтинг клуба")
def rating(message):
    register_user(message.from_user)

    users = load_users()

    if not users:
        bot.send_message(message.chat.id, "Рейтинг пока пуст.")
        return

    sorted_users = sorted(
        users.keys(),
        key=lambda uid: users[uid].get("score", 0),
        reverse=True
    )

    text = "🏆 Рейтинг клуба HeadShotDubai\n\n"

    for index, uid in enumerate(sorted_users, 1):
        text += (
            f"{index}. {show_player(uid)} — "
            f"{users[uid].get('score', 0)} очков | "
            f"{users[uid].get('status', 'Гость')}\n"
        )

    bot.send_message(message.chat.id, text)


def set_status_for_player(message, status_value):
    if not is_admin(message):
        return

    nick = message.text.split(maxsplit=1)[1].strip() if len(message.text.split(maxsplit=1)) > 1 else ""

    if not nick:
        bot.reply_to(message, "Укажи ник игрока.")
        return

    uid = ensure_player(nick)
    users = load_users()
    users[uid]["status"] = status_value
    save_users(users)

    bot.reply_to(
        message,
        f"Статус обновлён ✅\n{show_player(uid)}: {status_value}"
    )


@bot.message_handler(commands=["resident"])
def resident(message):
    set_status_for_player(message, "Резидент клуба")


@bot.message_handler(commands=["unresident"])
def unresident(message):
    set_status_for_player(message, "Гость")


@bot.message_handler(commands=["vip"])
def vip(message):
    set_status_for_player(message, "VIP")


@bot.message_handler(commands=["unvip"])
def unvip(message):
    set_status_for_player(message, "Гость")


@bot.message_handler(commands=["status"])
def status(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/status Adam Судья")
        return

    nick = parts[1]
    status_value = parts[2]

    uid = ensure_player(nick)
    users = load_users()
    users[uid]["status"] = status_value
    save_users(users)

    bot.reply_to(
        message,
        f"Статус обновлён ✅\n{show_player(uid)}: {status_value}"
    )


@bot.message_handler(commands=["profile"])
def profile(message):
    uid = register_user(message.from_user)
    users = load_users()
    user = users[uid]

    games_played = user.get("games_played", 0)
    wins = user.get("wins", 0)
    winrate = round((wins / games_played) * 100, 1) if games_played else 0

    bot.send_message(
        message.chat.id,
        f"🎭 {show_player(uid)}\n\n"
        f"Рейтинг: {user.get('score', 0)}\n"
        f"Статус: {user.get('status', 'Гость')}\n"
        f"Посещений: {user.get('visits', 0)}\n"
        f"Игр сыграно: {games_played}\n"
        f"Побед: {wins}\n"
        f"Процент побед: {winrate}%"
    )


@bot.message_handler(commands=["announcement"])
def announcement(message):
    if not is_admin(message):
        return

    text = message.text.replace("/announcement", "").strip()

    if not text:
        bot.reply_to(message, "Формат:\n/announcement Текст")
        return

    group_id = load_config().get("group_chat_id")

    if not group_id:
        bot.reply_to(message, "Сначала выполни /setgroup в группе.")
        return

    bot.send_message(
        group_id,
        f"📢 Официальное объявление HeadShotDubai\n\n{text}"
    )

    bot.reply_to(message, "Объявление опубликовано ✅")


@bot.message_handler(commands=["pinannouncement"])
def pinannouncement(message):
    if not is_admin(message):
        return

    text = message.text.replace("/pinannouncement", "").strip()

    if not text:
        bot.reply_to(message, "Формат:\n/pinannouncement Текст")
        return

    group_id = load_config().get("group_chat_id")

    if not group_id:
        bot.reply_to(message, "Сначала выполни /setgroup в группе.")
        return

    sent = bot.send_message(
        group_id,
        f"📌 Важное объявление HeadShotDubai\n\n{text}"
    )

    try:
        bot.pin_chat_message(
            group_id,
            sent.message_id,
            disable_notification=True
        )
    except Exception:
        pass

    bot.reply_to(message, "Важное объявление опубликовано и закреплено ✅")


@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if not is_admin(message):
        return

    text = message.text.replace("/broadcast", "").strip()

    if not text:
        bot.reply_to(message, "Формат:\n/broadcast Текст")
        return

    users = load_users()
    count = 0

    for uid in users:
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
    if not is_admin(message):
        return

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
    bot.send_message(
        message.chat.id,
        "HeadShotDubai 🎭\n\n"
        "Спортивная мафия в Дубае.\n"
        "Открытые, закрытые и капитанские столы.\n\n"
        "Стоимость:\n"
        "• ⭐ Резидент клуба — 75 AED\n"
        "• Гость клуба — 100 AED\n\n"
        "PS. Семья — это не главное. Семья — это всё."
    )


bot.infinity_polling()