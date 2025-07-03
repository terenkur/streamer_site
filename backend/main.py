from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Разрешаем запросы с любых источников (или можешь указать адрес фронта)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или ["https://frontend-site-production.up.railway.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище игр и голосов
games: Dict[str, Dict[str, List[str] or int]] = {
    "Dark Souls": {"votes": 2, "voters": ["alice", "bob"]},
    "Hades": {"votes": 1, "voters": ["charlie"]},
    "Stardew Valley": {"votes": 0, "voters": []},
}

# Модель запроса на голосование
class Vote(BaseModel):
    username: str
    game: str

@app.get("/games")
def get_games():
    return [
        {"game": name, "votes": data["votes"], "voters": data["voters"]}
        for name, data in games.items()
    ]

@app.post("/vote")
def vote(vote: Vote):
    game = vote.game.strip()
    user = vote.username.strip().lower()

    if game not in games:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    if user in games[game]["voters"]:
        raise HTTPException(status_code=400, detail="Пользователь уже голосовал за эту игру")

    games[game]["votes"] += 1
    games[game]["voters"].append(user)

    return {"message": "Голос засчитан!"}