"""
Libya B2B Platform - Chat Routes
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import get_db
from models import ChatMessage, ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    from chatbot import detect_language, get_chatbot

    chatbot = get_chatbot()
    is_arabic = (
        request.is_arabic if request.is_arabic is not None else detect_language(request.message)
    )
    result = chatbot.process_message(
        session_id=request.session_id, message=request.message, is_arabic=is_arabic
    )
    db_message = ChatMessage(
        session_id=request.session_id,
        user_message=request.message,
        bot_response=result["response"],
        is_arabic=is_arabic,
    )
    db.add(db_message)
    db.commit()
    return ChatResponse(
        session_id=request.session_id,
        response=result["response"],
        is_arabic=is_arabic,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/{session_id}")
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [
        {
            "user_message": msg.user_message,
            "bot_response": msg.bot_response,
            "created_at": msg.created_at,
        }
        for msg in messages
    ]


@router.get("/{session_id}/suggestions")
def get_chat_suggestions(session_id: str):
    from chatbot import get_chatbot

    chatbot = get_chatbot()
    suggestions = chatbot.get_suggestions(session_id)
    return {"session_id": session_id, "suggestions": suggestions}


@router.delete("/{session_id}")
def clear_chat_history(session_id: str):
    from chatbot import get_chatbot

    chatbot = get_chatbot()
    cleared = chatbot.clear_chat_history(session_id)
    return {"session_id": session_id, "cleared": cleared}
