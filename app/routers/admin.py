"""Admin routes voor quiz beheer."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/quiz", response_model=schemas.QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(quiz: schemas.QuizCreate, db: Session = Depends(get_db)):
    """Maak een nieuwe quiz aan met vragen en antwoorden."""
    # Maak quiz
    db_quiz = models.Quiz(
        title=quiz.title,
        description=quiz.description
    )
    db.add(db_quiz)
    db.flush()  # Get quiz ID
    
    # Voeg vragen toe
    for q_idx, question in enumerate(quiz.questions):
        db_question = models.Question(
            quiz_id=db_quiz.id,
            question_text=question.question_text,
            time_limit=question.time_limit,
            order=q_idx
        )
        db.add(db_question)
        db.flush()  # Get question ID
        
        # Valideer: precies 1 correct antwoord
        correct_count = sum(1 for a in question.answers if a.is_correct)
        if correct_count != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vraag '{question.question_text}' moet precies 1 correct antwoord hebben, niet {correct_count}"
            )
        
        # Voeg antwoorden toe
        for a_idx, answer in enumerate(question.answers):
            db_answer = models.Answer(
                question_id=db_question.id,
                answer_text=answer.answer_text,
                is_correct=answer.is_correct,
                order=a_idx
            )
            db.add(db_answer)
    
    db.commit()
    db.refresh(db_quiz)
    return db_quiz


@router.get("/quiz", response_model=List[schemas.QuizListItem])
def list_quizzes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Haal alle quizzen op (zonder vragen)."""
    quizzes = db.query(models.Quiz).offset(skip).limit(limit).all()
    
    result = []
    for quiz in quizzes:
        question_count = db.query(models.Question).filter(models.Question.quiz_id == quiz.id).count()
        result.append(
            schemas.QuizListItem(
                id=quiz.id,
                title=quiz.title,
                description=quiz.description,
                created_at=quiz.created_at,
                question_count=question_count
            )
        )
    return result


@router.get("/quiz/{quiz_id}", response_model=schemas.QuizResponse)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Haal een specifieke quiz op met alle vragen en antwoorden."""
    quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz niet gevonden")
    return quiz


@router.put("/quiz/{quiz_id}", response_model=schemas.QuizResponse)
def update_quiz(quiz_id: int, quiz_update: schemas.QuizCreate, db: Session = Depends(get_db)):
    """Update een bestaande quiz."""
    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz niet gevonden")
    
    # Update quiz metadata
    db_quiz.title = quiz_update.title
    db_quiz.description = quiz_update.description
    
    # Verwijder oude vragen (cascade verwijdert ook antwoorden)
    db.query(models.Question).filter(models.Question.quiz_id == quiz_id).delete()
    
    # Voeg nieuwe vragen toe
    for q_idx, question in enumerate(quiz_update.questions):
        db_question = models.Question(
            quiz_id=db_quiz.id,
            question_text=question.question_text,
            time_limit=question.time_limit,
            order=q_idx
        )
        db.add(db_question)
        db.flush()
        
        # Valideer correct antwoord
        correct_count = sum(1 for a in question.answers if a.is_correct)
        if correct_count != 1:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Elke vraag moet precies 1 correct antwoord hebben"
            )
        
        # Voeg antwoorden toe
        for a_idx, answer in enumerate(question.answers):
            db_answer = models.Answer(
                question_id=db_question.id,
                answer_text=answer.answer_text,
                is_correct=answer.is_correct,
                order=a_idx
            )
            db.add(db_answer)
    
    db.commit()
    db.refresh(db_quiz)
    return db_quiz


@router.delete("/quiz/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """Verwijder een quiz."""
    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz niet gevonden")
    
    db.delete(db_quiz)
    db.commit()
    return None