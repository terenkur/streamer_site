# Twitch Game Voting API

API-сервер на FastAPI для голосования зрителей Twitch за игры.

## Эндпоинты:
- `POST /vote` — голосование `{username, game}`
- `POST /games?game=Название` — добавить игру
- `GET /games` — список игр с голосами

## Развёртывание на Railway
1. Форкни репозиторий
2. Подключи Railway и выбери этот репо
3. Добавь PostgreSQL плагин и переменную окружения `DATABASE_URL`
