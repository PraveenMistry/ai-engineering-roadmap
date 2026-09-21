"""
Day 12 — Exercise 1: The message contract

Every message any agent sends goes through this one shape. This is A2A
(agent-to-agent communication) in miniature: agents don't need to know
HOW another agent works internally, only that messages between them
follow this contract — same idea as MCP's tool contract from Day 11,
just between two agents instead of an agent and a tool.
"""

import uuid
import time
from typing import TypedDict, Literal

MessageType = Literal["proposal", "counter_proposal", "accept", "reject", "terminate"]


class Message(TypedDict):
    message_id: str
    conversation_id: str
    sender: str
    receiver: str
    type: MessageType
    payload: dict
    timestamp: float


def create_message(
    conversation_id: str,
    sender: str,
    receiver: str,
    msg_type: MessageType,
    payload: dict,
) -> Message:
    return {
        "message_id": f"msg-{uuid.uuid4().hex[:8]}",
        "conversation_id": conversation_id,
        "sender": sender,
        "receiver": receiver,
        "type": msg_type,
        "payload": payload,
        "timestamp": time.time(),
    }
