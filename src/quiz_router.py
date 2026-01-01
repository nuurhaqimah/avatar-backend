import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncpg

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# Database connection settings from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://homeschool_user:homeschool_pass@localhost:7000/homeschool_db")


class QuizOption(BaseModel):
    id: str
    text: str
    is_correct: bool


class QuizQuestion(BaseModel):
    id: str
    text: str
    questionType: str  # e.g., "Multiple choice", "Essay", "True/False"
    options: Optional[List[str]] = None  # Only for MCQ, True/False
    correctAnswer: Optional[int] = None  # Only for MCQ, True/False
    maxLength: Optional[int] = None  # For Essay questions


class QuizResponse(BaseModel):
    questionSetId: str
    questionSetName: str
    questions: List[QuizQuestion]


async def get_db_connection():
    """Create a database connection."""
    return await asyncpg.connect(DATABASE_URL)


@router.get("/question-set/{question_set_id}")
async def get_quiz_by_question_set(
    question_set_id: str,
    question_types: Optional[str] = None  # Comma-separated list, e.g., "Multiple choice,True/False"
) -> QuizResponse:
    """
    Fetch questions from a question set.
    By default, only returns 'Multiple choice' questions.
    Use question_types parameter to specify which types to include.
    Example: ?question_types=Multiple choice,Essay,True/False
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        # Get question set info
        question_set = await conn.fetchrow(
            """
            SELECT id, name
            FROM question_sets
            WHERE id = $1
            """,
            question_set_id
        )
        
        if not question_set:
            raise HTTPException(status_code=404, detail="Question set not found")
        
        # Parse question types filter
        if question_types:
            type_list = [t.strip() for t in question_types.split(',')]
        else:
            type_list = ['Multiple choice']  # Default to MCQ only
        
        # Get questions from the question set filtered by type
        questions_data = await conn.fetch(
            """
            SELECT 
                q.id,
                q.question,
                qt.name as question_type
            FROM questions q
            INNER JOIN question_set_units qsu ON q.id = qsu.question_id
            INNER JOIN question_types qt ON q.question_type_id = qt.id
            WHERE qsu.question_set_id = $1
            AND qt.name = ANY($2::text[])
            ORDER BY qsu.order_num
            """,
            question_set_id,
            type_list
        )
        
        quiz_questions = []
        
        # TODO: BACKEND - Implement question_options table for storing MCQ options
        # Current implementation returns sample options - frontend handles actual quiz logic
        # 
        # Future implementation options:
        # 1. Create question_options table:
        #    CREATE TABLE question_options (
        #        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        #        question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
        #        option_text TEXT NOT NULL,
        #        is_correct BOOLEAN DEFAULT FALSE,
        #        order_num INTEGER NOT NULL
        #    );
        # 
        # 2. Or add JSON columns to questions table:
        #    ALTER TABLE questions ADD COLUMN options JSONB;
        #    ALTER TABLE questions ADD COLUMN correct_answer INTEGER;
        
        for idx, question_row in enumerate(questions_data):
            question_id = question_row['id']
            question_type = question_row['question_type']
            question_text = question_row['question']
            
            # Handle different question types
            if question_type in ['Multiple choice', 'True/False', 'MCQ']:
                # TEMPORARY: Sample options - frontend will handle actual quiz logic
                sample_options = [
                    f"Option A",
                    f"Option B", 
                    f"Option C",
                    f"Option D"
                ]
                
                quiz_questions.append(
                    QuizQuestion(
                        id=str(question_id),
                        text=question_text,
                        questionType=question_type,
                        options=sample_options,
                        correctAnswer=1  # TEMPORARY: Frontend handles validation
                    )
                )
            
            elif question_type == 'Essay':
                quiz_questions.append(
                    QuizQuestion(
                        id=str(question_id),
                        text=question_text,
                        questionType=question_type,
                        maxLength=1000
                    )
                )
            
            else:
                quiz_questions.append(
                    QuizQuestion(
                        id=str(question_id),
                        text=question_text,
                        questionType=question_type
                    )
                )
        
        if not quiz_questions:
            raise HTTPException(
                status_code=404,
                detail="No MCQ questions found in this question set"
            )
        
        return QuizResponse(
            questionSetId=str(question_set['id']),
            questionSetName=question_set['name'],
            questions=quiz_questions
        )
        
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            await conn.close()


@router.get("/question-sets")
async def get_available_quiz_sets():
    """
    Get all question sets that contain MCQ questions.
    """
    conn = None
    try:
        conn = await get_db_connection()
        
        question_sets = await conn.fetch(
            """
            SELECT DISTINCT
                qs.id,
                qs.name,
                qs.instruction as description,
                COUNT(DISTINCT q.id) as question_count
            FROM question_sets qs
            INNER JOIN question_set_units qsu ON qs.id = qsu.question_set_id
            INNER JOIN questions q ON qsu.question_id = q.id
            INNER JOIN question_types qt ON q.question_type_id = qt.id
            WHERE qt.name = 'Multiple choice'
            GROUP BY qs.id, qs.name, qs.instruction
            HAVING COUNT(DISTINCT q.id) > 0
            ORDER BY qs.name
            """
        )
        
        return [
            {
                "id": str(row['id']),
                "name": row['name'],
                "description": row['description'] or "",
                "questionCount": row['question_count']
            }
            for row in question_sets
        ]
        
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            await conn.close()
