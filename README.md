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
- В блоке «Финальная сводка» есть кнопка «Скачать в PDF».
- Для PDF-экспорта на сервере нужен `pandoc` (кнопка использует backend endpoint `/api/report/pdf`).
  В Docker-образе зависимости для PDF уже устанавливаются автоматически (`pandoc + weasyprint`).

## Скрипт полного отчета (MD -> PDF)

Скрипт: `backend/scripts/generate_report.py`

Пример:

```powershell
python backend/scripts/generate_report.py `
  --source-bytes "55 65 51 33 4D 95 59 C7 93 8C BD E3 D6 AB 2F 79" `
  --a-mapping "3 13 14 11 4 10 15 9 1 0 12 2 5 8 6 7" `
  --b-mapping "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15" `
  --key-bytes "88 99 AA BB CC DD EE FF 00 11 22 33 44 55 66 77" `
  --output-dir reports
```

Сначала всегда создается `.md`, затем скрипт пытается собрать `.pdf` через `pandoc`.
Если `pandoc` не установлен, остается только `.md` (с понятным сообщением).
