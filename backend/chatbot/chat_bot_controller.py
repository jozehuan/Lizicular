import uuid
from typing import List
from datetime import datetime

from .models import Message, BotSettings
from .bot_manager import BotManager

from llama_index.core.llms import ChatMessage
from langfuse import observe, get_client, propagate_attributes

def remove_empty_messages(request_content: List[Message]) -> List[Message]:
    """Removes messages with None content."""
    return [
        Message(role=i.role, content=i.content)
        for i in request_content
        if i.content is not None
    ]

@observe(name="chat_bot_controller_logic")
async def chat_bot_controller(messages: List[Message], token: str = None):
    """
    Main controller to handle an incoming chat request.
    """
    bot_settings = BotSettings(user_token=token) if token else None
    messages = remove_empty_messages(messages)

    if not messages:
        raise ValueError("No messages provided")

    bot_manager = BotManager(bot_settings)
    question = messages[-1]
    
    # Langfuse configuration check
    import os
    langfuse_enabled = os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    langfuse = get_client() if langfuse_enabled else None
    
    timestamp = datetime.now().isoformat()

    # Prepare chat history, keeping the last 2 messages
    history_send = [
        ChatMessage(role=i.role.value, content=i.content) for i in messages[:-1]
    ] if len(messages) > 1 else []

    if len(history_send) > 2:
        history_send = history_send[-2:]

    if not langfuse:
        # Simple path without Langfuse tracing
        return await bot_manager.run_agent(question.content, chat_history=history_send)

    # Path with Langfuse observation
    # Propagate attributes for Langfuse observation
    with propagate_attributes(
        metadata={
            "timestamp": timestamp,
            "question": question.content,
            "total_messages": len(messages),
        }
    ):
        # Start a generation observation in Langfuse
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="agent_response",
            input={
                "question": question.content,
                "history_length": len(history_send),
                "timestamp": timestamp,
            },
        ) as generation:
            try:
                # The actual agent call
                response = await bot_manager.run_agent(
                    question.content, chat_history=history_send
                )
                generation.update(
                    output={"status": "OK"}, level="SUCCESS", tags=["response"]
                )
            except Exception as e:
                generation.update(
                    output={"error": str(e)},
                    level="ERROR",
                    status_message=str(e),
                    tags=["error"],
                )
                raise

    # Update the current trace in Langfuse
    langfuse.update_current_trace(
        name=str(uuid.uuid4()),
        input={"user_question": question.content},
        metadata={
            "request_timestamp": timestamp,
            "history_messages": len(history_send),
        },
    )

    return response
