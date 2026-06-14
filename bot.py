import os, json
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
    return users[uid]


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


def player_name(user):
    profile = register_user(user)
    if profile.get("nick"):
        return profile["nick"]
    if user.username:
        return "@" + user.username
    return user.first_name or "Игрок"


def find_user(name):
    users = load_users()
    target = name.strip().lower().replace("@", "")

    for uid, user in users.items():
        if user.get("nick", "").lower() == target:
            return uid, user
        if user.get("username", "").lower() == target:
            return uid, user

    return None, None


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

    return title, limit if limit > 0 else DEFAULT_LIMIT


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
        "• Резидент клуба — 75 AED\n"
        "• Гость клуба — 100 AED\n\n"
        "1. Уважение ко всем игрокам обязательно.\n"
        "2. Решения ведущего и судьи не обсуждаются во время игры.\n"
        "3. Оскорбления, токсичность и конфликты запрещены.\n"
        "4. Опоздание более чем на 10 минут может привести к замене игрока.\n"
        "5. Телефон во время игры использовать нельзя.\n"
        "6. Нельзя подсказывать, мешать игре или раскрывать роли вне регламента.\n"
        "7. Игрок обязан соблюдать атмосферу клуба.\n"
        "8. Администрация может отказать в участии без объяснения причин.\n"
        "9. VIP / капитанские столы доступны по приглашению или через отбор.\n"
        "10. Masters Dubai — финальный турнир для лучших игроков сезона.\n\n"
        "PS. Семья — это не главное. Семья — это всё. 🖤"
    )


def help_text():
    return (
        "📖 Команды HeadShotDubai Bot\n\n"
        "Игрок:\n"
        "/start — меню\n"
        "/setnick Ник — задать ник\n"
        "/profile — профиль\n"
        "/rating — рейтинг клуба\n"
        "/rules — правила клуба\n\n"
        "Админ:\n"
        "/setgroup — сохранить группу\n"
        "/newgame 18 июня - Открытый стол | 10\n"
        "/newcaptain 20 июня - Капитанский стол | 12\n"
        "/postgame ID — опубликовать карточку\n"
        "/delgame ID — удалить игру\n"
        "/addplayer Ник — добавить игрока в базу\n"
        "/setnickuser @username Ник — поменять ник игроку\n"
        "/addtogame ID 19:30 Ник — записать игрока\n"
        "/removefromgame ID Ник — убрать игрока\n"
        "/players — игроки по играм\n"
        "/allplayers — все игроки\n"
        "/score Ник 5 — изменить рейтинг\n"
        "/result ID Ник 5 — результат игры\n"
        "/history — история рейтинга\n"
        "/vip Ник — выдать VIP\n"
        "/unvip Ник — снять VIP\n"
        "/status Ник Статус — задать статус\n"
        "/broadcast текст — рассылка всем\n"
        "/remindgame ID — напомнить участникам\n"
        "/myid — узнать ID"
    )


def game_keyboard(game_id):
    games = load_games()
    kb = types.InlineKeyboardMarkup()

    if game_id not in games:
        return kb

    game = games[game_id]
    limit = game.get("limit", DEFAULT_LIMIT)

    for index, slot in enumerate(game["slots"]):
        kb.add(types.InlineKeyboardButton(
            f"⏰ {slot['time']} ({len(slot['players'])}/{limit})",
            callback_data=f"join_{game_id}_{index}"
        ))

    kb.add(types.InlineKeyboardButton(
        "❌ Отменить мою запись",
        callback_data=f"cancel_{game_id}"
    ))

    return kb


def all_games_keyboard():
    games = load_games()
    kb = types.InlineKeyboardMarkup()

    for game_id, game in games.items():
        kb.add(types.InlineKeyboardButton(
            f"🎭 {game['title']}",
            callback_data=f"show_{game_id}"
        ))

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
        free = limit - len(players)

        text += f"⏰ {slot['time']} — {len(players)}/{limit}, свободно: {free}\n"

        if players:
            for i, p in enumerate(players, 1):
                text += f"{i}. {p}\n"
        else:
            text += "Пока никто не записался\n"

        if waitlist:
            text += "⏳ Лист ожидания:\n"
            for i, p in enumerate(waitlist, 1):
                text += f"{i}. {p}\n"

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
                    text += f"{i}. {p}\n"
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
        add_manual_player(nick)
        uid, user = find_user(nick)

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
    bot.reply_to(message, f"Игровой ник сохранён ✅\nТеперь ты: {nick}")


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
    if not is_admin(message):
        return

    raw = message.text.replace("/newgame", "").strip()

    if not raw:
        bot.reply_to(message, "Формат:\n/newgame 18 июня - Открытый стол | 10")
        return

    title, limit = parse_title_limit(raw)
    games = load_games()
    game_id = str(max([int(x) for x in games.keys()] + [0]) + 1)

    games[game_id] = {
        "title": title,
        "type": "Открытый стол",
        "limit": limit,
        "slots": [{"time": t, "players": [], "waitlist": []} for t in DEFAULT_TIMES],
        "chat_id": None,
        "message_id": None
    }

    save_games(games)
    bot.reply_to(
        message,
        f"Игра создана ✅\nID: {game_id}\n{title}\nЛимит: {limit}\n\n/postgame {game_id}"
    )


@bot.message_handler(commands=["newcaptain"])
def newcaptain(message):
    if not is_admin(message):
        return

    raw = message.text.replace("/newcaptain", "").strip()

    if not raw:
        bot.reply_to(message, "Формат:\n/newcaptain 20 июня - Капитанский стол | 12")
        return

    title, limit = parse_title_limit(raw)
    games = load_games()
    game_id = str(max([int(x) for x in games.keys()] + [0]) + 1)

    games[game_id] = {
        "title": title,
        "type": "VIP / Капитанский стол",
        "limit": limit,
        "slots": [{"time": t, "players": [], "waitlist": []} for t in DEFAULT_TIMES],
        "chat_id": None,
        "message_id": None
    }

    save_games(games)
    bot.reply_to(
        message,
        f"Капитанский стол создан 👑\nID: {game_id}\n{title}\nЛимит: {limit}\n\n/postgame {game_id}"
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
        bot.pin_chat_message(sent.chat.id, sent.message_id, disable_notification=True)
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

    bot.reply_to(message, f"Игра удалена ✅\nID: {game_id}\n{title}")


@bot.message_handler(commands=["games"])
@bot.message_handler(func=lambda m: m.text == "📋 Список игр")
def games_list(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, all_games_text(), reply_markup=all_games_keyboard())


@bot.message_handler(func=lambda m: m.text == "🎮 Записаться на игру")
def signup_button(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id, "Выбери игру:", reply_markup=all_games_keyboard())


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
        )


@bot.callback_query_handler(func=lambda c: c.data.startswith("join_"))
def join_game(call):
    register_user(call.from_user)

    _, game_id, slot_index = call.data.split("_")
    slot_index = int(slot_index)

    games = load_games()
    player = player_name(call.from_user)

    if game_id not in games:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return

    game = games[game_id]
    limit = game.get("limit", DEFAULT_LIMIT)

    for g in games.values():
        for s in g["slots"]:
            if player in s["players"] or player in s["waitlist"]:
                bot.answer_callback_query(call.id, "Ты уже записан.")
                return

    slot = game["slots"][slot_index]

    if len(slot["players"]) < limit:
        slot["players"].append(player)
        bot.answer_callback_query(call.id, "Ты записан ✅")
    else:
        slot["waitlist"].append(player)
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
    register_user(call.from_user)

    game_id = call.data.split("_")[1]
    games = load_games()
    player = player_name(call.from_user)
    removed = False

    if game_id not in games:
        bot.answer_callback_query(call.id, "Игра не найдена.")
        return

    for slot in games[game_id]["slots"]:
        if player in slot["players"]:
            slot["players"].remove(player)
            removed = True
            if slot["waitlist"]:
                slot["players"].append(slot["waitlist"].pop(0))

        if player in slot["waitlist"]:
            slot["waitlist"].remove(player)
            removed = True

    save_games(games)
    update_group_card(game_id)

    bot.answer_callback_query(call.id, "Запись отменена ✅" if removed else "Ты не был записан.")

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
            bot.reply_to(message, f"Ник изменён ✅\n@{username} → {new_nick}")
            return

    bot.reply_to(message, "Игрок не найден. Он должен нажать /start или записаться.")


@bot.message_handler(commands=["addtogame"])
def addtogame(message):
    if not is_admin(message):
        return

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
            bot.reply_to(message, "Игрок уже записан на эту игру.")
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
    if not is_admin(message):
        return

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
        if nick in slot["players"]:
            slot["players"].remove(nick)
            removed = True
            if slot["waitlist"]:
                slot["players"].append(slot["waitlist"].pop(0))

        if nick in slot["waitlist"]:
            slot["waitlist"].remove(nick)
            removed = True

    save_games(games)
    update_group_card(game_id)

    bot.reply_to(message, "Игрок удалён ✅" if removed else "Игрок не найден в игре.")


@bot.message_handler(commands=["players"])
def players(message):
    if not is_admin(message):
        return

    games = load_games()
    text = ""

    for game_id in games.keys():
        text += game_card(game_id) + "\n\n"

    bot.send_message(message.chat.id, text if text else "Игр пока нет.")


@bot.message_handler(commands=["allplayers"])
def allplayers(message):
    if not is_admin(message):
        return

    users = load_users()
    text = "👥 Все игроки HeadShotDubai\n\n"

    if not users:
        bot.send_message(message.chat.id, "База игроков пустая.")
        return

    for i, user in enumerate(users.values(), 1):
        nick = user.get("nick") or user.get("first_name") or "Игрок"
        username = user.get("username", "")
        score = user.get("score", 0)
        status = user.get("status", "Гость")

        text += f"{i}. {nick} — {score} очков | {status}"
        if username:
            text += f" (@{username})"
        text += "\n"

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

    total = add_score(nick, points, "Ручная корректировка")
    bot.reply_to(message, f"Рейтинг обновлён ✅\n{nick}: {total} очков")


@bot.message_handler(commands=["result"])
def result(message):
    if not is_admin(message):
        return

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
    if not is_admin(message):
        return

    history_data = load_history()

    if not history_data:
        bot.send_message(message.chat.id, "История рейтинга пустая.")
        return

    text = "📈 История рейтинга\n\n"

    for h in history_data[-30:]:
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

    for i, user in enumerate(sorted_users, 1):
        nick = user.get("nick") or user.get("first_name") or "Игрок"
        score = user.get("score", 0)
        status = user.get("status", "Гость")
        text += f"{i}. {nick} — {score} очков | {status}\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["vip"])
def vip(message):
    if not is_admin(message):
        return

    nick = message.text.replace("/vip", "").strip()
    uid, user = find_user(nick)

    if not user:
        bot.reply_to(message, "Игрок не найден.")
        return

    users = load_users()
    users[uid]["status"] = "VIP"
    save_users(users)

    bot.reply_to(message, f"{nick} получил статус VIP ✅")


@bot.message_handler(commands=["unvip"])
def unvip(message):
    if not is_admin(message):
        return

    nick = message.text.replace("/unvip", "").strip()
    uid, user = find_user(nick)

    if not user:
        bot.reply_to(message, "Игрок не найден.")
        return

    users = load_users()
    users[uid]["status"] = "Гость"
    save_users(users)

    bot.reply_to(message, f"Статус VIP снят с {nick} ✅")


@bot.message_handler(commands=["status"])
def status(message):
    if not is_admin(message):
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(message, "Формат:\n/status Adam Резидент клуба")
        return

    nick, new_status = parts[1], parts[2]
    uid, user = find_user(nick)

    if not user:
        bot.reply_to(message, "Игрок не найден.")
        return

    users = load_users()
    users[uid]["status"] = new_status
    save_users(users)

    bot.reply_to(message, f"Статус обновлён ✅\n{nick}: {new_status}")


@bot.message_handler(commands=["profile"])
def profile(message):
    user = register_user(message.from_user)
    nick = user.get("nick") or user.get("first_name") or "Игрок"
    games_played = user.get("games_played", 0)
    wins = user.get("wins", 0)
    winrate = round((wins / games_played) * 100, 1) if games_played else 0

    bot.send_message(
        message.chat.id,
        f"🎭 {nick}\n\n"
        f"Рейтинг: {user.get('score', 0)}\n"
        f"Статус: {user.get('status', 'Гость')}\n"
        f"Посещений: {user.get('visits', 0)}\n"
        f"Игр сыграно: {games_played}\n"
        f"Побед: {wins}\n"
        f"Процент побед: {winrate}%"
    )


@bot.message_handler(commands=["broadcast"])
def broadcast(message):
    if not is_admin(message):
        return

    text = message.text.replace("/broadcast", "").strip()

    if not text:
        bot.reply_to(message, "Формат:\n/broadcast Завтра игра в 19:30")
        return

    users = load_users()
    count = 0

    for uid in users.keys():
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

    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "Формат:\n/remindgame 1")
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
        "Открытые игры, капитанские столы, рейтинг клуба и путь в Masters Dubai.\n\n"
        "Стоимость:\n"
        "• Резидент клуба — 75 AED\n"
        "• Гость клуба — 100 AED\n\n"
        "PS. Семья — это не главное. Семья — это всё."
    )


bot.infinity_polling()