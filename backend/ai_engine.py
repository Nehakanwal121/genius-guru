
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import os
import json
from dotenv import load_dotenv
import logging

# ✅ Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Function to initialize ChatOpenAI
def get_llm():
    try:
        return ChatOpenAI(
            temperature=0.7,
            model_name="gpt-3.5-turbo",
            openai_api_key=OPENAI_API_KEY
        )
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        raise Exception(f"Failed to initialize AI model: {str(e)}")

# ✅ Tutoring Prompt Generator
def generate_tutoring_response(subject, level, question, learning_style, background, language):
    try:
        prompt = _create_tutoring_prompt(subject, level, question, learning_style, background, language)
        logger.info(f"Generating tutoring response for subject: {subject}, level: {level}")
        
        llm = get_llm()
        response = llm([HumanMessage(content=prompt)])

        # ✅ Extract response content safely
        content = None
        if hasattr(response, "content"):
            content = response.content
        elif hasattr(response, "generations"):
            content = response.generations[0][0].text
        elif isinstance(response, list) and hasattr(response[0], "content"):
            content = response[0].content

        if not content:
            raise Exception("LLM returned no usable response content.")

        logger.info("LLM response extracted successfully")
        return format_tutoring_response(content, learning_style)

    except Exception as e:
        logger.error(f"Error generating tutoring response: {str(e)}")
        raise Exception(f"Failed to generate tutoring response: {str(e)}")

def _create_tutoring_prompt(subject, level, question, learning_style, background, language):
    return f"""
Subject: {subject}
Learning Level: {level}
Background Knowledge: {background}
Learning Style Preference: {learning_style}
Language Preference: {language}

QUESTION:
{question}

INSTRUCTIONS:
1. Provide a clear, educational explanation that directly addresses the question
2. Tailor your explanation to a {background} student at {level} level
3. Use {language} as the primary language
4. Format your response with appropriate markdown for readability

LEARNING STYLE ADAPTATIONS:
- For Visual learners: Include descriptions of visual concepts, diagrams, or mental models
- For Text-based learners: Provide clear, structured explanations with defined concepts
- For Hands-on learners: Include practical examples, exercises, or applications

Your explanation should be educational, accurate, and engaging.
"""

def format_tutoring_response(content, learning_style):
    if learning_style == "Visual":
        return content + "\n\n📝 *Note: Visualize these concepts as you read for better retention.*"
    elif learning_style == "Hands-on":
        return content + "\n\n🛠️ *Tip: Try working through the examples yourself to reinforce your learning.*"
    else:
        return content

# ✅ Quiz Generation Section
def _create_quiz_prompt(subject, level, num_questions):
    return f"""
You are a quiz generator.

Generate a quiz on the subject **{subject}** at **{level}** level.

Instructions:
1. Generate **{num_questions}** multiple-choice questions (MCQs).
2. Each question must have exactly 4 answer options (A, B, C, D).
3. Clearly indicate the correct answer.
4. Cover diverse aspects of {subject}.

FORMAT YOUR RESPONSE AS JSON:
[
    {{
        "question": "Question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Option A",
        "explanation": "Brief explanation of why this answer is correct"
    }},
    ...
]

IMPORTANT:
- Make sure to return valid JSON that can be parsed.
- Do not include any text outside the JSON array.
- Include a brief explanation for each correct answer.
"""

def _create_fallback_quiz(subject, num_questions):
    logger.warning(f"Using fallback quiz for {subject}")
    return [
        {
            "question": f"Sample {subject} question {i+1}",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "This is a fallback explanation."
        }
        for i in range(num_questions)
    ]

def _validate_quiz_data(quiz_data):
    for question in quiz_data:
        if not all(key in question for key in ["question", "options", "correct_answer"]):
            raise ValueError("Each quiz item must have question, options, and correct_answer")
        if not isinstance(question["options"], list) or len(question["options"]) != 4:
            raise ValueError("Each question must have exactly 4 options")
        if question["correct_answer"] not in question["options"]:
            raise ValueError("The correct answer must be one of the options")

def _parse_quiz_response(response_content, subject, num_questions):
    try:
        quiz_data = json.loads(response_content)
        _validate_quiz_data(quiz_data)
        if len(quiz_data) > num_questions:
            quiz_data = quiz_data[:num_questions]
        for question in quiz_data:
            if "explanation" not in question:
                question["explanation"] = f"The correct answer is {question['correct_answer']}."
        return quiz_data
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing quiz response: {str(e)}")
        return _create_fallback_quiz(subject, num_questions)

def generate_quiz_data(subject, level, num_questions):
    prompt = _create_quiz_prompt(subject, level, num_questions)
    llm = get_llm()
    response = llm([HumanMessage(content=prompt)])
    return _parse_quiz_response(response.content, subject, num_questions)

def generate_quiz(subject, level, num_questions=5, reveal_answer=False):
    try:
        quiz_data = generate_quiz_data(subject, level, num_questions)
        if reveal_answer:
            formatted_quiz = _format_quiz_with_reveal(quiz_data)
            return {
                "quiz_data": quiz_data,
                "formatted_quiz": formatted_quiz
            }
        else:
            return {
                "quiz_data": quiz_data
            }
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise Exception(f"Failed to generate quiz: {str(e)}")

def _format_quiz_with_reveal(quiz_data):
    html = """
    <html>
    <head>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f2f4f8;
                color: #333;
                padding: 20px;
            }

            .quiz-card {
                background-color: #fff;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                margin: 20px auto;
                padding: 20px;
                max-width: 700px;
                transition: transform 0.3s;
            }

            .quiz-card:hover {
                transform: scale(1.01);
            }

            .question {
                font-size: 18px;
                font-weight: bold;
            }

            .option {
                padding: 10px 14px;
                margin: 8px 0;
                border-radius: 8px;
                border: 1px solid #ccc;
                cursor: pointer;
                transition: background-color 0.3s, transform 0.2s;
            }

            .option:hover {
                background-color: #f0f0f0;
                transform: scale(1.02);
            }

            .selected-correct {
                background-color: #c8f7c5;
                border-color: #28a745;
                font-weight: bold;
            }

            .selected-incorrect {
                background-color: #f8d7da;
                border-color: #dc3545;
            }

            .answer {
                margin-top: 12px;
                padding: 12px;
                background-color: #e9ecef;
                border-left: 5px solid #007bff;
                display: none;
                border-radius: 8px;
            }
        </style>
        <script>
            function handleAnswerSelection(isCorrect, selectedOption, questionNum) {
                if (isCorrect) {
                    selectedOption.className += ' selected-correct';
                } else {
                    selectedOption.className += ' selected-incorrect';
                    revealAnswer(questionNum);
                }
            }

            function revealAnswer(questionNum) {
                const answerDiv = document.getElementById("answer-" + questionNum);
                answerDiv.style.display = 'block';
                answerDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

                answerDiv.animate([
                    { transform: 'scale(1.05)', opacity: 1 },
                    { transform: 'scale(1)', opacity: 1 }
                ], {
                    duration: 800,
                    iterations: 1
                });
            }
        </script>
    </head>
    <body>
    <h2>🧠 Interactive Quiz</h2>
    """

    for i, question in enumerate(quiz_data):
        html += f"""
        <div class='quiz-card'>
            <div class='question'>Q{i+1}: {question['question']}</div>
            <div class='options'>
        """
        for option in question['options']:
            is_correct = str(option == question['correct_answer']).lower()
            html += f"""
                <div class='option' onclick="handleAnswerSelection({is_correct}, this, {i+1})">
                    {option}
                </div>
            """
        html += f"""
            </div>
            <div class='answer' id='answer-{i+1}'>
                <strong>✅ Correct Answer:</strong> {question['correct_answer']}<br>
                <em>💡 Explanation:</em> {question['explanation']}
            </div>
        </div>
        """

    html += """
    </body>
    </html>
    """
    return html

