from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI()

ADMIN_PASSWORD = "secret123"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Игры и голоса в памяти (пока без базы)
games: Dict[str, Dict[str, List[str] or int]] = {
    "Dark Souls": {"votes": 2, "voters": ["alice", "bob"]},
    "Hades": {"votes": 1, "voters": ["charlie"]},
    "Stardew Valley": {"votes": 0, "voters": []},
}

class Vote(BaseModel):
    username: str
    game: str

class GameAdd(BaseModel):
    game: str
    admin_password: str

class GameEdit(BaseModel):
    old_name: str
    new_name: str
    new_votes: int
    admin_password: str

class GameDelete(BaseModel):
    game: str
    admin_password: str

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

@app.post("/games")
def add_game(data: GameAdd):
    if data.admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Неверный пароль")
    if data.game in games:
        raise HTTPException(status_code=400, detail="Такая игра уже существует")
    games[data.game] = {"votes": 0, "voters": []}
    return {"message": "Игра добавлена"}

@app.patch("/games")
def edit_game(data: GameEdit):
    if data.admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Неверный пароль")
    if data.old_name not in games:
        raise HTTPException(status_code=404, detail="Старая игра не найдена")

    existing_voters = games[data.old_name]["voters"]
    del games[data.old_name]

    games[data.new_name] = {
        "votes": data.new_votes,
        "voters": existing_voters[:data.new_votes]  # обрезаем если нужно
    }

    return {"message": "Игра обновлена"}

@app.delete("/games")
def delete_game(data: GameDelete):
    if data.admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Неверный пароль")
    if data.game not in games:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    del games[data.game]
    return {"message": "Игра удалена"}
