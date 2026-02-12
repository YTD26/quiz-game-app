"""Pydantic schemas voor request/response validation."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ===== Answer Schemas =====
class AnswerBase(BaseModel):
    answer_text: str = Field(..., max_length=500)
    is_correct: bool = False
    order: int = 0


class AnswerCreate(AnswerBase):
    pass


class AnswerResponse(AnswerBase):
    id: int
    question_id: int
    
    class Config:
        from_attributes = True


class AnswerResponsePublic(BaseModel):
    """Answer zonder is_correct - voor spelers."""
    id: int
    answer_text: str
    order: int
    
    class Config:
        from_attributes = True


# ===== Question Schemas =====
class QuestionBase(BaseModel):
    question_text: str
    time_limit: int = Field(default=30, ge=5, le=120)
    order: int = 0


class QuestionCreate(QuestionBase):
    answers: List[AnswerCreate] = Field(..., min_length=2, max_length=4)


class QuestionResponse(QuestionBase):
    id: int
    quiz_id: int
    answers: List[AnswerResponse]
    
    class Config:
        from_attributes = True


class QuestionResponsePublic(QuestionBase):
    """Question voor spelers - zonder correcte antwoorden."""
    id: int
    answers: List[AnswerResponsePublic]
    
    class Config:
        from_attributes = True


# ===== Quiz Schemas =====
class QuizBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None


class QuizCreate(QuizBase):
    questions: List[QuestionCreate] = Field(..., min_length=1)


class QuizResponse(QuizBase):
    id: int
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse]
    
    class Config:
        from_attributes = True


class QuizListItem(QuizBase):
    """Quiz list item zonder vragen."""
    id: int
    created_at: datetime
    question_count: int = 0
    
    class Config:
        from_attributes = True


# ===== Game Session Schemas =====
class GameSessionCreate(BaseModel):
    quiz_id: int


class GameSessionResponse(BaseModel):
    id: int
    quiz_id: int
    game_code: str
    status: str
    current_question: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Player Schemas =====
class PlayerJoin(BaseModel):
    game_code: str = Field(..., min_length=6, max_length=6)
    player_name: str = Field(..., min_length=1, max_length=100)


class PlayerResponse(BaseModel):
    id: int
    player_name: str
    joined_at: datetime
    is_connected: bool
    
    class Config:
        from_attributes = True


# ===== Score Schemas =====
class AnswerSubmit(BaseModel):
    game_code: str
    player_id: int
    question_id: int
    answer_id: int
    time_taken: int  # Milliseconden


class ScoreResponse(BaseModel):
    id: int
    player_id: int
    question_id: int
    is_correct: bool
    points: int
    time_taken: int
    answered_at: datetime
    
    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    player_name: str
    total_score: int
    correct_answers: int
    rank: int


class Leaderboard(BaseModel):
    entries: List[LeaderboardEntry]
    total_questions: int


# ===== WebSocket Messages =====
class WSMessage(BaseModel):
    type: str
    data: dict


class WSPlayerJoined(BaseModel):
    player_name: str
    player_count: int


class WSQuestionStart(BaseModel):
    question: QuestionResponsePublic
    question_number: int
    total_questions: int


class WSQuestionEnd(BaseModel):
    correct_answer_id: int
    leaderboard: List[LeaderboardEntry]