# GOST / Kuznyechik Web Lab

Проект теперь работает как один веб-сервис:

- `frontend` собирается в `backend/dist`
- Flask сразу раздает этот собранный фронт
- API доступно по `/api/*`

## Структура

```text
backend/
  app.py
  requirements.txt
  dist/                 # появляется после npm run build
  src/services/trace_service.py
frontend/
  src/
  package.json
  vite.config.js
main.py                 # генерация HTML-отчета
Dockerfile
docker-compose.yml
```

## Локальный запуск (один процесс Flask)

1. Собрать фронт в `backend/dist`:

```powershell
cd frontend
npm install
npm run build
```

2. Запустить backend:

```powershell
cd ..\backend
python -m pip install -r requirements.txt
python app.py
```

После этого приложение открывается по `http://127.0.0.1:5000`.
Отдельно `npm run dev` не нужен.

## Docker + Traefik

В `docker-compose.yml` уже настроено:

- сеть: `proxy` (external)
- основной домен: `www.gost.strdinc.space`
- certresolver: `myresolver`
- редирект `http -> https` для `www.gost.strdinc.space`
- редирект `gost.strdinc.space` на `https://www.gost.strdinc.space`

Запуск:

```powershell
docker compose up -d --build
```

## Что важно

- Терминальный дамп убран из UI.
- Все таблицы строятся через `pandas.DataFrame` и рендерятся как HTML-таблицы.
- Пункты 7-11 разбиты на отдельные выпадающие шаги.
