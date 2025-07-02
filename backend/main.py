from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from ai_engine import generate_tutoring_response, generate_quiz

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="AI_TUTOR_API",
    description="API for generating personalized tutoring content and quizzes",
    version="1.0.0"
)

# ✅ Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Data models
class TutorRequest(BaseModel):
    subject: str = Field(..., description="Academic subject")
    level: str = Field(..., description="Learning level (Beginner, Intermediate, Advanced)")
    question: str = Field(..., description="User's question")
    learning_style: str = Field("Text-Based", description="Preferred learning style")
    background: str = Field("Unknown", description="Background knowledge level")
    language: str = Field("English", description="Preferred language")

class QuizRequest(BaseModel):
    subject: str = Field(..., description="Academic subject")
    level: str = Field(..., description="Learning level")
    num_questions: int = Field(5, description="Number of quiz questions", ge=1, le=10)
    reveal_format: Optional[bool] = Field(True, description="Whether to return formatted HTML")

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None

class TutorResponse(BaseModel):
    response: str

class QuizResponse(BaseModel):
    quiz: List[Dict[str, Any]]
    formatted_quiz: Optional[str] = None

# ✅ /tutor endpoint
@app.post("/tutor", response_model=TutorResponse)
async def get_tutoring_response(data: TutorRequest):
    try:
        explanation = generate_tutoring_response(
            data.subject,
            data.level,
            data.question,
            data.learning_style,
            data.background,
            data.language
        )
        return {"response": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

# ✅ /quiz endpoint
@app.post("/quiz", response_model=QuizResponse)
async def generate_quiz_api(data: QuizRequest):
    try:
        quiz_result = generate_quiz(
            data.subject,
            data.level,
            data.num_questions,
            reveal_answer=data.reveal_format
        )

        if data.reveal_format:
            return {
                "quiz": quiz_result["quiz_data"],
                "formatted_quiz": quiz_result["formatted_quiz"]
            }
        else:
            return {
                "quiz": quiz_result["quiz_data"]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

# ✅ /quiz-html endpoint
@app.get("/quiz-html/{subject}/{level}/{num_questions}", response_class=HTMLResponse)
async def get_quiz_html(subject: str, level: str, num_questions: int = 5):
    try:
        quiz_result = generate_quiz(subject, level, num_questions, reveal_answer=True)
        return quiz_result["formatted_quiz"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz HTML: {str(e)}")

# ✅ /health endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
