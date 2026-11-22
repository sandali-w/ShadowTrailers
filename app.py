import json
import os
import random
from pathlib import Path
from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

DATA_DIR = Path("data")
PLAYERS_FILE = DATA_DIR / "players.json"

QUESTS = {
    "jungle": {
        "id": "jungle",
        "place": "Jungle",
        "relic": "Lantern",
        "sdg": "SDG 7 (Clean Energy)",
        "riddle": "I shine without burning coal or oil, powered by wind and sun to light the jungle trail. What am I?",
        "answers": ["renewable energy", "solar", "clean energy", "wind"],
    },
    "temple": {
        "id": "temple",
        "place": "Temple",
        "relic": "Coin",
        "sdg": "SDG 12 (Responsible Consumption)",
        "riddle": "Use only what you need, repair before you throw away, and keep waste low. Which habit am I?",
        "answers": ["recycle", "reuse", "reduce", "responsible consumption", "sustainability"],
    },
    "cave": {
        "id": "cave",
        "place": "Cave",
        "relic": "Key",
        "sdg": "SDG 6 (Clean Water)",
        "riddle": "Clear and safe to drink, protected from pollution so every villager stays healthy. What am I?",
        "answers": ["clean water", "fresh water", "water", "pure water"],
    },
}

STORE_ITEMS = {
    "clothes": {
        "starter": 0,
        "neon-jacket": 20,
        "explorer-hoodie": 35,
        "cyber-cloak": 50,
    },
    "themes": {
        "neon-default": 0,
        "emerald-grid": 25,
        "sunset-arcade": 40,
        "ocean-pulse": 45,
    },
}

WORD_HEIST_WORDS = [
    {"word": "SOLAR", "hint": "SDG 7: Energy from the sun"},
    {"word": "RECYCLE", "hint": "SDG 12: Turn waste into new materials"},
    {"word": "AQUIFER", "hint": "SDG 6: Underground layer holding clean water"},
]


def load_players():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PLAYERS_FILE.exists():
        PLAYERS_FILE.write_text("{}", encoding="utf-8")
    with PLAYERS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_players(players):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PLAYERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(players, file, indent=2)


def current_user(players):
    username = session.get("username")
    if not username or username not in players:
        return None, None
    return username, players[username]


def check_arcade_unlock(user):
    required_relics = {"Lantern", "Coin", "Key"}
    if required_relics.issubset(set(user.get("relics", []))):
        user["arcade_unlocked"] = True


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    players = load_players()
    if username in players:
        return jsonify({"error": "User already exists"}), 409

    players[username] = {
        "password_hash": generate_password_hash(password),
        "coins": 0,
        "clues": [],
        "relics": [],
        "arcade_unlocked": False,
        "clothes": ["starter"],
        "themes": ["neon-default"],
        "equipped_clothes": "starter",
        "equipped_theme": "neon-default",
    }
    save_players(players)
    session["username"] = username
    return jsonify({"message": "Registered", "username": username}), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    players = load_players()
    user = players.get(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["username"] = username
    return jsonify({"message": "Logged in", "username": username})


@app.post("/api/logout")
def logout():
    session.pop("username", None)
    return jsonify({"message": "Logged out"})


@app.get("/api/me")
def me():
    players = load_players()
    username, user = current_user(players)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    profile = {key: val for key, val in user.items() if key != "password_hash"}
    return jsonify({"username": username, "profile": profile})


@app.post("/api/clue/<place>")
def collect_clue(place):
    players = load_players()
    _, user = current_user(players)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    place_key = place.lower()
    if place_key not in QUESTS:
        return jsonify({"error": "Unknown place"}), 404

    if place_key not in user["clues"]:
        user["clues"].append(place_key)
        save_players(players)

    return jsonify({"place": place_key, "clues": user["clues"]})


@app.get("/api/quest/<quest_id>")
@app.post("/api/quest/<quest_id>")
def handle_quest(quest_id):
    players = load_players()
    _, user = current_user(players)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    quest = QUESTS.get(quest_id.lower())
    if not quest:
        return jsonify({"error": "Quest not found"}), 404

    if request.method == "GET":
        return jsonify({
            "id": quest["id"],
            "place": quest["place"],
            "sdg": quest["sdg"],
            "riddle": quest["riddle"],
            "relic": quest["relic"],
            "solved": quest["relic"] in user["relics"],
        })

    data = request.get_json(silent=True) or {}
    guess = (data.get("answer") or "").strip().lower()
    correct = guess in quest["answers"]

    if correct and quest["relic"] not in user["relics"]:
        user["relics"].append(quest["relic"])
        check_arcade_unlock(user)
        save_players(players)

    return jsonify({
        "correct": correct,
        "relics": user["relics"],
        "arcade_unlocked": user["arcade_unlocked"],
    })


@app.post("/api/play/start")
def play_start():
    players = load_players()
    _, user = current_user(players)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    game = (data.get("game") or "").strip().lower()

    if game == "number_guesser":
        target = random.randint(1, 10)
        session["minigame"] = {"game": "number_guesser", "target": target, "attempts": 0}
        return jsonify({"game": game, "prompt": "Guess a number between 1 and 10"})

    if game == "word_heist":
        entry = random.choice(WORD_HEIST_WORDS)
        session["minigame"] = {"game": "word_heist", "word": entry["word"]}
        return jsonify({
            "game": game,
            "hint": entry["hint"],
            "length": len(entry["word"]),
        })

    if game == "math_blitz":
        a = random.randint(2, 12)
        b = random.randint(2, 12)
        op = random.choice(["+", "-", "*"])
        answer = a + b if op == "+" else (a - b if op == "-" else a * b)
        session["minigame"] = {"game": "math_blitz", "answer": answer}
        return jsonify({"game": game, "question": f"{a} {op} {b}"})

    return jsonify({"error": "Invalid game name"}), 400


@app.post("/api/play/guess")
def play_guess():
    players = load_players()
    _, user = current_user(players)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    state = session.get("minigame")
    if not state:
        return jsonify({"error": "No active mini-game. Call /api/play/start first"}), 400

    data = request.get_json(silent=True) or {}
    guess = data.get("guess")
    game = state.get("game")
    won = False
    message = "Try again"

    if game == "number_guesser":
        state["attempts"] = state.get("attempts", 0) + 1
        session["minigame"] = state
        try:
            num_guess = int(guess)
        except (TypeError, ValueError):
            return jsonify({"error": "Enter a valid number"}), 400

        if num_guess == state["target"]:
            won = True
            message = "Correct number!"
            session.pop("minigame", None)
        elif num_guess < state["target"]:
            message = "Too low"
        else:
            message = "Too high"

    elif game == "word_heist":
        word_guess = str(guess or "").strip().upper()
        if word_guess == state["word"]:
            won = True
            message = "Word solved!"
            session.pop("minigame", None)
        else:
            message = "Incorrect word"

    elif game == "math_blitz":
        try:
            ans_guess = int(guess)
        except (TypeError, ValueError):
            return jsonify({"error": "Enter a valid integer answer"}), 400

        if ans_guess == state["answer"]:
            won = True
            message = "Math Blitz cleared!"
            session.pop("minigame", None)
        else:
            message = "Wrong calculation"

    if won:
        user["coins"] = user.get("coins", 0) + 10
        save_players(players)

    return jsonify({
        "won": won,
        "message": message,
        "reward": 10 if won else 0,
        "coins": user["coins"],
    })


@app.post("/api/buy")
def buy_item():
    players = load_players()
    _, user = current_user(players)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip().lower()
    item_id = (data.get("item") or "").strip()

    if category not in STORE_ITEMS or item_id not in STORE_ITEMS[category]:
        return jsonify({"error": "Invalid store item"}), 404

    price = STORE_ITEMS[category][item_id]
    inventory_key = "clothes" if category == "clothes" else "themes"

    if item_id in user[inventory_key]:
        return jsonify({"error": "Already owned", "coins": user["coins"]}), 400

    if user["coins"] < price:
        return jsonify({"error": "Not enough coins", "coins": user["coins"]}), 400

    user["coins"] -= price
    user[inventory_key].append(item_id)
    save_players(players)

    return jsonify({
        "message": "Purchased",
        "category": category,
        "item": item_id,
        "coins": user["coins"],
        inventory_key: user[inventory_key],
    })


@app.post("/api/equip")
def equip_item():
    players = load_players()
    _, user = current_user(players)
    if not user:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    category = (data.get("category") or "").strip().lower()
    item_id = (data.get("item") or "").strip()

    if category == "clothes":
        if item_id not in user["clothes"]:
            return jsonify({"error": "Clothes item not owned"}), 400
        user["equipped_clothes"] = item_id
    elif category == "themes":
        if item_id not in user["themes"]:
            return jsonify({"error": "Theme not owned"}), 400
        user["equipped_theme"] = item_id
    else:
        return jsonify({"error": "Invalid category"}), 400

    save_players(players)
    return jsonify({
        "message": "Equipped",
        "equipped_clothes": user["equipped_clothes"],
        "equipped_theme": user["equipped_theme"],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)