from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

app = FastAPI()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///../db.sqlite3")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    vote = relationship("Vote", back_populates="user", uselist=False)

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    votes = relationship("Vote", back_populates="game")

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('users.username'))
    game_id = Column(Integer, ForeignKey('games.id'))
    user = relationship("User", back_populates="vote")
    game = relationship("Game", back_populates="votes")

Base.metadata.create_all(engine)

class VoteInput(BaseModel):
    username: str
    game: str

@app.post("/vote")
def vote(data: VoteInput):
    db = SessionLocal()
    user = db.query(User).filter_by(username=data.username).first()
    game = db.query(Game).filter_by(name=data.game).first()
    if not game:
        db.close()
        raise HTTPException(status_code=404, detail="Игра не найдена")

    if not user:
        user = User(username=data.username)
        db.add(user)
        db.commit()

    existing_vote = db.query(Vote).filter_by(username=data.username).first()
    if existing_vote:
        existing_vote.game = game
    else:
        vote = Vote(username=data.username, game=game)
        db.add(vote)

    db.commit()
    db.close()
    return {"status": "ok"}

@app.get("/games")
def get_games():
    db = SessionLocal()
    games = db.query(Game.name, func.count(Vote.id).label('votes')).join(Vote, isouter=True).group_by(Game.id).all()
    db.close()
    return [{"game": g[0], "votes": g[1]} for g in games]

@app.post("/games")
def add_game(game: str = Query(...)):
    db = SessionLocal()
    if db.query(Game).filter_by(name=game).first():
        db.close()
        raise HTTPException(status_code=400, detail="Такая игра уже есть")
    db.add(Game(name=game))
    db.commit()
    db.close()
    return {"status": "добавлено"}
