"""FastAPI hoofdapplicatie voor Quiz Game."""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn
import os

from app.database import init_db, get_db
from app import models
from app.routers import admin, game, websocket

# Initialiseer FastAPI app
app = FastAPI(
    title="Quiz Game API",
    description="Realtime multiplayer quiz applicatie (Kahoot-style)",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(admin.router)
app.include_router(game.router)
app.include_router(websocket.router)


@app.on_event("startup")
def startup_event():
    """Initialiseer database bij opstarten."""
    print("🚀 Quiz Game App wordt opgestart...")
    init_db()
    print("✅ Database geïnitialiseerd")
    print("🎮 Server draait op http://localhost:8000")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Homepage voor spelers om te joinen."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    """Admin panel voor quiz beheer."""
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/lobby/{game_code}", response_class=HTMLResponse)
def lobby(request: Request, game_code: str):
    """Lobby wachtruimte voor spelers."""
    return templates.TemplateResponse("lobby.html", {
        "request": request,
        "game_code": game_code
    })


@app.get("/game/{game_code}", response_class=HTMLResponse)
def play_game(request: Request, game_code: str):
    """Spel interface tijdens het spelen."""
    return templates.TemplateResponse("game.html", {
        "request": request,
        "game_code": game_code
    })


@app.get("/results/{game_code}", response_class=HTMLResponse)
def results(request: Request, game_code: str):
    """Resultaten pagina na afloop."""
    return templates.TemplateResponse("results.html", {
        "request": request,
        "game_code": game_code
    })


@app.get("/host/{game_code}", response_class=HTMLResponse)
def host_game(request: Request, game_code: str):
    """Host interface om spel te besturen."""
    return templates.TemplateResponse("host.html", {
        "request": request,
        "game_code": game_code
    })


@app.get("/health")
def health_check():
    """Health check endpoint voor monitoring."""
    return {"status": "healthy", "service": "quiz-game-app"}


if __name__ == "__main__":
    # Start server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Auto-reload bij code changes (dev only)
        log_level="info"
    )