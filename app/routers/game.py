"""Game logic routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import random
import string
from datetime import datetime

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/game", tags=["game"])


def generate_game_code(db: Session) -> str:
    """Genereer unieke 6-cijferige game code."""
    while True:
        code = ''.join(random.choices(string.digits, k=6))
        existing = db.query(models.GameSession).filter(
            models.GameSession.game_code == code,
            models.GameSession.status != "finished"
        ).first()
        if not existing:
            return code


@router.post("/start", response_model=schemas.GameSessionResponse, status_code=status.HTTP_201_CREATED)
def start_game_session(game_data: schemas.GameSessionCreate, db: Session = Depends(get_db)):
    """Start een nieuwe game sessie voor een quiz."""
    # Valideer quiz bestaat
    quiz = db.query(models.Quiz).filter(models.Quiz.id == game_data.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz niet gevonden")
    
    # Check of quiz vragen heeft
    question_count = db.query(models.Question).filter(models.Question.quiz_id == game_data.quiz_id).count()
    if question_count == 0:
        raise HTTPException(status_code=400, detail="Quiz heeft geen vragen")
    
    # Maak game sessie
    game_code = generate_game_code(db)
    game_session = models.GameSession(
        quiz_id=game_data.quiz_id,
        game_code=game_code,
        status="waiting"
    )
    db.add(game_session)
    db.commit()
    db.refresh(game_session)
    
    return game_session


@router.get("/{game_code}", response_model=schemas.GameSessionResponse)
def get_game_session(game_code: str, db: Session = Depends(get_db)):
    """Haal game sessie informatie op."""
    game = db.query(models.GameSession).filter(models.GameSession.game_code == game_code).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game niet gevonden")
    return game


@router.post("/join", response_model=schemas.PlayerResponse)
def join_game(player_data: schemas.PlayerJoin, db: Session = Depends(get_db)):
    """Speler joint een game sessie."""
    # Valideer game bestaat
    game = db.query(models.GameSession).filter(
        models.GameSession.game_code == player_data.game_code
    ).first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game code ongeldig")
    
    if game.status != "waiting":
        raise HTTPException(status_code=400, detail="Game is al gestart of afgelopen")
    
    # Check of naam al bestaat
    existing_player = db.query(models.Player).filter(
        models.Player.game_session_id == game.id,
        models.Player.player_name == player_data.player_name
    ).first()
    
    if existing_player:
        raise HTTPException(status_code=400, detail="Naam is al in gebruik")
    
    # Maak speler
    player = models.Player(
        game_session_id=game.id,
        player_name=player_data.player_name
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    
    return player


@router.get("/{game_code}/players", response_model=List[schemas.PlayerResponse])
def get_game_players(game_code: str, db: Session = Depends(get_db)):
    """Haal alle spelers van een game op."""
    game = db.query(models.GameSession).filter(models.GameSession.game_code == game_code).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game niet gevonden")
    
    players = db.query(models.Player).filter(models.Player.game_session_id == game.id).all()
    return players


@router.post("/answer", response_model=schemas.ScoreResponse)
def submit_answer(answer_data: schemas.AnswerSubmit, db: Session = Depends(get_db)):
    """Verwerk een antwoord van een speler."""
    # Valideer game
    game = db.query(models.GameSession).filter(
        models.GameSession.game_code == answer_data.game_code
    ).first()
    
    if not game or game.status != "active":
        raise HTTPException(status_code=400, detail="Game is niet actief")
    
    # Valideer speler
    player = db.query(models.Player).filter(
        models.Player.id == answer_data.player_id,
        models.Player.game_session_id == game.id
    ).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Speler niet gevonden")
    
    # Check of vraag al beantwoord
    existing_score = db.query(models.Score).filter(
        models.Score.game_session_id == game.id,
        models.Score.player_id == answer_data.player_id,
        models.Score.question_id == answer_data.question_id
    ).first()
    
    if existing_score:
        raise HTTPException(status_code=400, detail="Vraag al beantwoord")
    
    # Valideer antwoord
    answer = db.query(models.Answer).filter(models.Answer.id == answer_data.answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Antwoord niet gevonden")
    
    # Valideer vraag
    question = db.query(models.Question).filter(models.Question.id == answer_data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Vraag niet gevonden")
    
    # Bereken score
    is_correct = answer.is_correct
    points = 0
    
    if is_correct:
        time_limit_ms = question.time_limit * 1000
        time_taken_ms = answer_data.time_taken
        
        if time_taken_ms < time_limit_ms:
            remaining_time = time_limit_ms - time_taken_ms
            points = int(1000 * (remaining_time / time_limit_ms))
        else:
            points = 100  # Minimale punten voor correct maar te laat
    
    # Sla score op
    score = models.Score(
        game_session_id=game.id,
        player_id=answer_data.player_id,
        question_id=answer_data.question_id,
        answer_id=answer_data.answer_id,
        is_correct=is_correct,
        points=points,
        time_taken=answer_data.time_taken
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    
    return score


@router.get("/{game_code}/leaderboard", response_model=schemas.Leaderboard)
def get_leaderboard(game_code: str, db: Session = Depends(get_db)):
    """Haal het scoreboard op voor een game."""
    game = db.query(models.GameSession).filter(models.GameSession.game_code == game_code).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game niet gevonden")
    
    # Query scores per speler
    leaderboard_query = db.query(
        models.Player.player_name,
        func.sum(models.Score.points).label('total_score'),
        func.sum(func.cast(models.Score.is_correct, Integer)).label('correct_answers')
    ).join(
        models.Score, models.Player.id == models.Score.player_id
    ).filter(
        models.Player.game_session_id == game.id
    ).group_by(
        models.Player.id
    ).order_by(
        func.sum(models.Score.points).desc()
    ).all()
    
    # Maak entries met rank
    entries = []
    for idx, (name, score, correct) in enumerate(leaderboard_query, start=1):
        entries.append(schemas.LeaderboardEntry(
            player_name=name,
            total_score=score or 0,
            correct_answers=correct or 0,
            rank=idx
        ))
    
    # Tel totaal aantal vragen
    total_questions = db.query(models.Question).filter(
        models.Question.quiz_id == game.quiz_id
    ).count()
    
    return schemas.Leaderboard(
        entries=entries,
        total_questions=total_questions
    )