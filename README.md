# ShadowTrailers

A small game-themed web application: explore, solve riddles, play arcade challenges, earn coins and spend them in the store. Suitable for ages +12.

## Game idea and objective
Sign in as an explorer, solve riddles and play arcade challenges to earn coins and score, then spend the coins in the store on items. The player's actions change the game state (coins, score, inventory), and everything is saved on the server.


## Main features
- Create an account and sign in (passwords are hashed, never stored as plain text)
- Riddle game: a correct answer gives +10 coins
- Arcade game: the score is saved and gives coins (1 coin per 10 points)
- Store: buy items with coins (Health potion 10, Magic shield 20, Neon sword 50)
- Player data (coins, score, inventory) is saved in `data/players.json`

## Technologies used
- HTML, CSS (responsive, mobile-first, colour themes)
- Vanilla JavaScript (no React or other frameworks)
- Python + Flask (backend), Flask-CORS
- JSON files for server-side storage
- Communication: fetch requests with JSON (HTTP API)
- Git and GitHub

## Team members and division of work
| Member | Role | Main files |
|---|---|---|
| Sandali | Backend: Flask routes, JSON storage | `app.py`, `data/players.json` |
| Abdulla | HTML structure and JavaScript screens | `index.html`, `script.js` |
| Ishara | CSS design, API link, README | `style.css`, `README.md` |

All members helped plan the game, test it and prepare the presentation.




## Git workflow
Each member works on their own branch (`feature-backend`, `feature-screens`, `feature-design`) and the team merges into `main` together. Commit messages are short and say what and why. Everyone pulls `main` before starting.

