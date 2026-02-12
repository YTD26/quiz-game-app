"""WebSocket handler voor realtime game communicatie."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime

from app.database import get_db, SessionLocal
from app import models

router = APIRouter()

# Globale connection manager
class ConnectionManager:
    def __init__(self):
        # game_code -> set van WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_code: str):
        await websocket.accept()
        if game_code not in self.active_connections:
            self.active_connections[game_code] = set()
        self.active_connections[game_code].add(websocket)
    
    def disconnect(self, websocket: WebSocket, game_code: str):
        if game_code in self.active_connections:
            self.active_connections[game_code].discard(websocket)
            if not self.active_connections[game_code]:
                del self.active_connections[game_code]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, game_code: str):
        if game_code in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[game_code]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # Verwijder disconnected websockets
            for conn in disconnected:
                self.active_connections[game_code].discard(conn)

manager = ConnectionManager()


@router.websocket("/ws/{game_code}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, game_code: str, player_name: str):
    """WebSocket verbinding voor een speler in een game."""
    await manager.connect(websocket, game_code)
    
    db = SessionLocal()
    
    try:
        # Valideer game en speler
        game = db.query(models.GameSession).filter(
            models.GameSession.game_code == game_code
        ).first()
        
        if not game:
            await websocket.send_json({"type": "error", "message": "Game niet gevonden"})
            await websocket.close()
            return
        
        player = db.query(models.Player).filter(
            models.Player.game_session_id == game.id,
            models.Player.player_name == player_name
        ).first()
        
        if not player:
            await websocket.send_json({"type": "error", "message": "Speler niet gevonden"})
            await websocket.close()
            return
        
        # Update speler status
        player.is_connected = True
        db.commit()
        
        # Broadcast dat speler is gejoined
        player_count = db.query(models.Player).filter(
            models.Player.game_session_id == game.id
        ).count()
        
        await manager.broadcast({
            "type": "player_joined",
            "data": {
                "player_name": player_name,
                "player_count": player_count
            }
        }, game_code)
        
        # Luister naar berichten
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "start_game":
                # Host start het spel
                game.status = "active"
                game.started_at = datetime.utcnow()
                game.current_question = 0
                db.commit()
                
                # Stuur eerste vraag
                await send_question(game_code, game.quiz_id, 0, db)
            
            elif message_type == "next_question":
                # Host gaat naar volgende vraag
                game.current_question += 1
                db.commit()
                
                questions = db.query(models.Question).filter(
                    models.Question.quiz_id == game.quiz_id
                ).order_by(models.Question.order).all()
                
                if game.current_question < len(questions):
                    await send_question(game_code, game.quiz_id, game.current_question, db)
                else:
                    # Spel afgelopen
                    game.status = "finished"
                    game.finished_at = datetime.utcnow()
                    db.commit()
                    
                    await manager.broadcast({
                        "type": "game_finished",
                        "data": {"game_code": game_code}
                    }, game_code)
            
            elif message_type == "answer_submitted":
                # Speler heeft antwoord gegeven - broadcast update
                await manager.broadcast({
                    "type": "answer_received",
                    "data": {"player_name": player_name}
                }, game_code)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_code)
        
        # Update speler status
        if player:
            player.is_connected = False
            db.commit()
        
        await manager.broadcast({
            "type": "player_left",
            "data": {"player_name": player_name}
        }, game_code)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, game_code)
    
    finally:
        db.close()


async def send_question(game_code: str, quiz_id: int, question_index: int, db: Session):
    """Stuur een vraag naar alle spelers."""
    questions = db.query(models.Question).filter(
        models.Question.quiz_id == quiz_id
    ).order_by(models.Question.order).all()
    
    if question_index >= len(questions):
        return
    
    question = questions[question_index]
    
    # Format antwoorden (zonder correcte antwoord indicator)
    answers = []
    for answer in question.answers:
        answers.append({
            "id": answer.id,
            "answer_text": answer.answer_text,
            "order": answer.order
        })
    
    await manager.broadcast({
        "type": "question_start",
        "data": {
            "question": {
                "id": question.id,
                "question_text": question.question_text,
                "time_limit": question.time_limit,
                "answers": answers
            },
            "question_number": question_index + 1,
            "total_questions": len(questions)
        }
    }, game_code)


@router.get("/ws/test")
async def websocket_test():
    """Test endpoint voor WebSocket connectiviteit."""
    return {"message": "WebSocket endpoint beschikbaar", "active_games": len(manager.active_connections)}