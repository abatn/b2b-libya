"""
Libya B2B Platform - Messaging Routes
Conversations and messages with WebSocket support.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from config import get_db
from models import Conversation, Message, MessageCreate, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/api/b2b/messages", tags=["messages"])


# ── WebSocket Connection Manager ──────────────────────────────
class ConnectionManager:
    """Manages WebSocket connections per conversation."""

    def __init__(self):
        # {conversation_id: [websocket, ...]}
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: int):
        await websocket.accept()
        if conversation_id not in self.active:
            self.active[conversation_id] = []
        self.active[conversation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: int):
        if conversation_id in self.active:
            self.active[conversation_id] = [
                ws for ws in self.active[conversation_id] if ws != websocket
            ]
            if not self.active[conversation_id]:
                del self.active[conversation_id]

    async def broadcast(self, conversation_id: int, message: dict):
        """Send message to all connected clients in a conversation."""
        if conversation_id in self.active:
            dead = []
            for ws in self.active[conversation_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            # Clean up dead connections
            for ws in dead:
                self.active[conversation_id] = [w for w in self.active[conversation_id] if w != ws]

    async def broadcast_to_user(self, user_id: int, message: dict):
        """Send message to all conversations a user participates in."""
        for conv_id, sockets in list(self.active.items()):
            dead = []
            for ws in sockets:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active[conv_id] = [w for w in self.active[conv_id] if w != ws]


manager = ConnectionManager()


@router.post("")
def create_conversation(
    buyer_id: int = 1,
    supplier_id: int = 1,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = Conversation(buyer_id=buyer_id, supplier_id=supplier_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {
        "id": conv.id,
        "buyer_id": conv.buyer_id,
        "supplier_id": conv.supplier_id,
        "created_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
    }


@router.get("")
def list_conversations(
    buyer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Conversation)
    if buyer_id:
        query = query.filter(Conversation.buyer_id == buyer_id)
    query = query.order_by(Conversation.last_message_at.desc())
    convs = query.offset(skip).limit(limit).all()
    total = query.count()

    return {
        "conversations": [
            {
                "id": c.id,
                "buyer_id": c.buyer_id,
                "supplier_id": c.supplier_id,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "last_message_text": c.last_message_text,
                "unread_count": c.unread_count,
            }
            for c in convs
        ],
        "total": total,
    }


@router.get("/{conversation_id}")
def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "conversation": {
            "id": conv.id,
            "buyer_id": conv.buyer_id,
            "supplier_id": conv.supplier_id,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
        },
        "messages": [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "sender_type": m.sender_type,
                "sender_id": m.sender_id,
                "text": m.text,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.post("/{conversation_id}")
def send_message(
    conversation_id: int,
    msg: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = Message(
        conversation_id=conversation_id,
        sender_type=msg.sender_type,
        sender_id=msg.sender_id,
        text=msg.text,
    )
    db.add(message)

    conv.last_message_at = datetime.now(timezone.utc)
    conv.last_message_text = msg.text[:200] if msg.text else None
    conv.unread_count += 1

    db.commit()
    db.refresh(message)

    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_type": message.sender_type,
        "text": message.text,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


# ── WebSocket Endpoint ────────────────────────────────────────
@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int):
    """WebSocket endpoint for realtime messaging in a conversation."""
    await manager.connect(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            if payload.get("type") == "message":
                # Broadcast to all clients in this conversation
                await manager.broadcast(
                    conversation_id,
                    {
                        "type": "message",
                        "conversation_id": conversation_id,
                        "sender_type": payload.get("sender_type", "buyer"),
                        "sender_id": payload.get("sender_id", 0),
                        "text": payload.get("text", ""),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            elif payload.get("type") == "typing":
                # Broadcast typing indicator
                await manager.broadcast(
                    conversation_id,
                    {
                        "type": "typing",
                        "sender_type": payload.get("sender_type", "buyer"),
                        "conversation_id": conversation_id,
                    },
                )
            elif payload.get("type") == "read":
                # Broadcast read receipt
                await manager.broadcast(
                    conversation_id,
                    {
                        "type": "read",
                        "conversation_id": conversation_id,
                        "reader": payload.get("sender_type", "buyer"),
                    },
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
    except Exception:
        manager.disconnect(websocket, conversation_id)
