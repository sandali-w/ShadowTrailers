from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# JSON file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "players.json")


# Load player data
def load_players():
    with open(DATA_FILE, "r") as file:
        return json.load(file)


# Save player data
def save_players(players):
    with open(DATA_FILE, "w") as file:
        json.dump(players, file, indent=4)


# Home page
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to ShadowTrailers!",
        "status": "Backend is running successfully"
    })


# Register player
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must contain at least 6 characters"}), 400

    players = load_players()

    if username in players:
        return jsonify({"error": "Username already exists"}), 409

    players[username] = {
        "password": generate_password_hash(password),
        "coins": 0,
        "score": 0,
        "inventory": []
    }

    save_players(players)

    return jsonify({
        "message": "Registration successful!",
        "username": username
    }), 201


# Login player
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    username = data.get("username")
    password = data.get("password")

    players = load_players()

    if username not in players:
        return jsonify({"error": "Player not found"}), 404

    if not check_password_hash(players[username]["password"], password):
        return jsonify({"error": "Incorrect password"}), 401

    return jsonify({
        "message": "Login successful!",
        "username": username,
        "coins": players[username]["coins"],
        "score": players[username]["score"],
        "inventory": players[username]["inventory"]
    })


# Get player information
@app.route("/api/player/<username>", methods=["GET"])
def get_player(username):
    players = load_players()

    if username not in players:
        return jsonify({"error": "Player not found"}), 404

    player = players[username]

    return jsonify({
        "username": username,
        "coins": player["coins"],
        "score": player["score"],
        "inventory": player["inventory"]
    })


# Riddle game
@app.route("/api/riddle", methods=["POST"])
def riddle():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    username = data.get("username")
    answer = data.get("answer", "").strip().lower()

    players = load_players()

    if username not in players:
        return jsonify({"error": "Player not found"}), 404

    correct_answer = "echo"

    if answer == correct_answer:
        players[username]["coins"] += 10
        save_players(players)

        return jsonify({
            "message": "Correct answer!",
            "reward": 10,
            "coins": players[username]["coins"]
        })

    return jsonify({
        "message": "Incorrect answer. Try again!"
    })


# Arcade game
@app.route("/api/arcade", methods=["POST"])
def arcade():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    username = data.get("username")
    score = data.get("score")

    players = load_players()

    if username not in players:
        return jsonify({"error": "Player not found"}), 404

    if type(score) is not int or score < 0 or score > 10000:
        return jsonify({"error": "Invalid score"}), 400

    players[username]["score"] += score

    reward = score // 10
    players[username]["coins"] += reward

    save_players(players)

    return jsonify({
        "message": "Arcade score saved!",
        "score": players[username]["score"],
        "reward": reward,
        "coins": players[username]["coins"]
    })


# Store items
@app.route("/api/store", methods=["GET"])
def store():
    items = {
        "health_potion": 10,
        "magic_shield": 20,
        "neon_sword": 50
    }

    return jsonify(items)


# Buy store item
@app.route("/api/store/buy", methods=["POST"])
def buy_item():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    username = data.get("username")
    item = data.get("item")

    players = load_players()

    if username not in players:
        return jsonify({"error": "Player not found"}), 404

    items = {
        "health_potion": 10,
        "magic_shield": 20,
        "neon_sword": 50
    }

    if item not in items:
        return jsonify({"error": "Item not available"}), 404

    price = items[item]

    if players[username]["coins"] < price:
        return jsonify({"error": "Not enough coins"}), 400

    players[username]["coins"] -= price
    players[username]["inventory"].append(item)

    save_players(players)

    return jsonify({
        "message": "Item purchased successfully!",
        "item": item,
        "coins": players[username]["coins"],
        "inventory": players[username]["inventory"]
    })


if __name__ == "__main__":
    app.run(debug=True)