"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Quiz(Base):
    """Quiz model - bevat metadata van een quiz."""
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    game_sessions = relationship("GameSession", back_populates="quiz")


class Question(Base):
    """Vraag model - bevat een enkele vraag."""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    time_limit = Column(Integer, default=30)  # Seconden
    order = Column(Integer, default=0)  # Volgorde in quiz
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    """Antwoord model - bevat antwoordopties voor een vraag."""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    answer_text = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, default=0)  # Volgorde (A, B, C, D)
    
    # Relationships
    question = relationship("Question", back_populates="answers")


class GameSession(Base):
    """Game sessie model - actieve of voltooide game."""
    __tablename__ = "game_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    game_code = Column(String(6), unique=True, nullable=False, index=True)
    status = Column(String(20), default="waiting")  # waiting, active, finished
    current_question = Column(Integer, default=0)  # Index van huidige vraag
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="game_sessions")
    players = relationship("Player", back_populates="game_session", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="game_session", cascade="all, delete-orphan")


class Player(Base):
    """Speler model - deelnemer aan een game sessie."""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    player_name = Column(String(100), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_connected = Column(Boolean, default=True)
    
    # Relationships
    game_session = relationship("GameSession", back_populates="players")
    scores = relationship("Score", back_populates="player", cascade="all, delete-orphan")


class Score(Base):
    """Score model - individuele antwoorden en scores."""
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    game_session_id = Column(Integer, ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=True)
    is_correct = Column(Boolean, default=False)
    points = Column(Integer, default=0)
    time_taken = Column(Integer, default=0)  # Milliseconden
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game_session = relationship("GameSession", back_populates="scores")
    player = relationship("Player", back_populates="scores")
    question = relationship("Question")
    answer = relationship("Answer")