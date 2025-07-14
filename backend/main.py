from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import List, Dict
import time

app = FastAPI()

SECRET_KEY = "your-very-secret-key"
ADMIN_PASSWORD = "secret123"
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 3600

security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # можно ограничить фронтом
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище
games: Dict[str, Dict[str, List[str] or int]] = {
    "Dark Souls": {"votes": 2, "voters": ["alice", "bob"]},
    "Hades": {"votes": 1, "voters": ["charlie"]},
    "Stardew Valley": {"votes": 0, "voters": []},
}

# Модели
class Vote(BaseModel):
    username: str
    game: str

class LoginData(BaseModel):
    password: str

class GameAdd(BaseModel):
    game: str

class GameEdit(BaseModel):
    old_name: str
    new_name: str
    new_votes: int
    new_voters: List[str]

class GameDelete(BaseModel):
    game: str

# Авторизация
def create_token() -> str:
    payload = {
        "sub": "admin",
        "exp": time.time() + TOKEN_EXPIRE_SECONDS
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный или просроченный токен")

# Маршруты
@app.post("/login")
def login(data: LoginData):
    if data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    token = create_token()
    return {"token": token}

@app.get("/games")
def get_games():
    return [
        {"game": name, "votes": data["votes"], "voters": data["voters"]}
        for name, data in games.items()
    ]

@app.post("/vote")
def vote(data: Vote):
    game = data.game.strip()
    user = data.username.strip().lower()

    if game not in games:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    if user in games[game]["voters"]:
        raise HTTPException(status_code=400, detail="Уже голосовал")

    games[game]["votes"] += 1
    games[game]["voters"].append(user)

    return {"message": "Голос засчитан"}

@app.post("/games")
def add_game(data: GameAdd, _: str = Depends(verify_token)):
    if data.game in games:
        raise HTTPException(status_code=400, detail="Игра уже есть")
    games[data.game] = {"votes": 0, "voters": []}
    return {"message": "Игра добавлена"}

@app.patch("/games")
def edit_game(data: GameEdit, _: str = Depends(verify_token)):
    if data.old_name not in games:
        raise HTTPException(status_code=404, detail="Старая игра не найдена")

    del games[data.old_name]
    games[data.new_name] = {
        "votes": data.new_votes,
        "voters": data.new_voters[:data.new_votes]  # обрезаем лишних
    }
    return {"message": "Игра обновлена"}

@app.delete("/games")
def delete_game(data: GameDelete, _: str = Depends(verify_token)):
    if data.game not in games:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    del games[data.game]
    return {"message": "Удалено"}

class WheelSettings(BaseModel):
    coefficient: float
    zero_votes_weight: int

# Добавляем в хранилище
wheel_settings = {
    "coefficient": 2.0,
    "zero_votes_weight": 40
}

# Новые эндпоинты
@app.get("/wheel-settings")
def get_wheel_settings(_: str = Depends(verify_token)):
    return wheel_settings

@app.patch("/wheel-settings")
def update_wheel_settings(
    settings: WheelSettings, 
    _: str = Depends(verify_token)
):
    wheel_settings["coefficient"] = settings.coefficient
    wheel_settings["zero_votes_weight"] = settings.zero_votes_weight
    return {"message": "Настройки обновлены"}
