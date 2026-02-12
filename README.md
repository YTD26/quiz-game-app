# Quiz Game App 🎮

Een realtime multiplayer quiz applicatie (Kahoot-style) gebouwd met FastAPI, WebSockets en SQLite.

## Features ✨

- 🎯 Realtime multiplayer quiz gameplay
- 🏆 Live scoreboard met snelheidsbonus
- 👥 Host en speler rollen
- 📝 Quiz maken en beheren
- ⚡ WebSocket communicatie
- 💾 SQLite database
- 🚀 Cloud-ready (Render deployment)

## Technologie Stack

- **Backend**: FastAPI + WebSockets
- **Database**: SQLite + SQLAlchemy
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Render-ready

## Lokale Installatie 🛠️

### Vereisten
- Python 3.9+
- pip

### Stappen

1. **Clone de repository**
```bash
git clone https://github.com/YTD26/quiz-game-app.git
cd quiz-game-app
```

2. **Maak virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Installeer dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
```

5. **Start de applicatie**
```bash
python -m app.main
```

6. **Open in browser**
```
http://localhost:8000
```

## Gebruik 📖

### Als Host
1. Ga naar `/admin`
2. Maak een nieuwe quiz aan
3. Voeg vragen toe met 4 antwoordopties
4. Start de quiz → ontvang game code
5. Deel code met spelers
6. Start het spel wanneer iedereen klaar is

### Als Speler
1. Ga naar homepage
2. Voer game code + naam in
3. Wacht in lobby
4. Beantwoord vragen binnen tijdslimiet
5. Bekijk je score na elke vraag

## Database Schema 📊

- **quizzes**: Quiz metadata
- **questions**: Vragen per quiz
- **answers**: Antwoordopties
- **game_sessions**: Actieve games
- **players**: Spelers per sessie
- **scores**: Score tracking

## Score Berekening 🎯

```
Score = 1000 × (resterende_tijd / totale_tijd)
```

- Correct antwoord: tot 1000 punten
- Sneller = meer punten
- Fout antwoord: 0 punten

## Deployment naar Render 🚀

### Automatische Deployment

1. Login bij [Render](https://render.com)
2. Klik "New +" → "Web Service"
3. Connect deze GitHub repo
4. Configuratie:
   - **Name**: quiz-game-app
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Deploy!

### Environment Variables op Render

Voeg toe in Render dashboard:
```
DATABASE_URL=sqlite:///./quiz_app.db
SECRET_KEY=[genereer-sterke-key]
DEBUG=False
```

## Project Structuur 📁

```
quiz-game-app/
├── app/
│   ├── main.py              # FastAPI app + WebSocket
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/
│   │   ├── admin.py         # Admin routes
│   │   ├── game.py          # Game logic
│   │   └── websocket.py     # WebSocket handler
│   ├── templates/
│   │   ├── index.html       # Speler homepage
│   │   ├── admin.html       # Quiz beheer
│   │   ├── lobby.html       # Wachtruimte
│   │   ├── game.html        # Quiz interface
│   │   └── results.html     # Scoreboard
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── lobby.js
│           ├── game.js
│           └── admin.js
├── requirements.txt
├── .env.example
└── README.md
```

## API Endpoints 🔌

### REST API
- `GET /` - Homepage (speler)
- `GET /admin` - Admin panel
- `POST /api/quiz` - Maak quiz
- `GET /api/quiz/{id}` - Haal quiz op
- `POST /api/game/start` - Start game sessie
- `GET /api/game/{code}` - Game details

### WebSocket
- `/ws/{game_code}/{player_name}` - Game verbinding

## Uitbreidingen 🔧

Toekomstige features:
- [ ] User authentication
- [ ] Quiz categorieën
- [ ] Afbeeldingen in vragen
- [ ] Team mode
- [ ] Statistieken dashboard
- [ ] CSV export van scores
- [ ] Quiz dupliceren functie

## Troubleshooting 🔍

### Database errors
```bash
# Reset database
rm quiz_app.db
python -m app.main
```

### Port al in gebruik
```bash
# Verander port in main.py of:
uvicorn app.main:app --port 8001
```

## Licentie

MIT License - zie LICENSE bestand

## Contact

Vragen? Open een issue op GitHub!