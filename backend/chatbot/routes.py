from fastapi import APIRouter, Depends, HTTPException, Request
from langfuse import get_client
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.database import get_db
from ..auth.audit_utils import create_audit_log
from ..auth.models import AuditCategory, AuditAction
from ..auth.auth_utils import get_current_active_user, get_raw_token
from .chat_bot_controller import chat_bot_controller
from .models import APIResponse, QuestionRequest

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/chat", response_model=APIResponse)
async def ask(
    request: QuestionRequest,
    fastapi_req: Request, # Re-added to get IP and user-agent
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
    user_token: str = Depends(get_raw_token),
):
    """
    Receives a question and returns a response from the chatbot.
    This endpoint is protected and requires user authentication.
    """
    langfuse = get_client()
    question_content = request.messages[-1].content if request.messages else ""
    
    try:
        answer = await chat_bot_controller(messages=request.messages, token=user_token)
        
        # Audit the successful request
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            category=AuditCategory.CHATBOT,
            action=AuditAction.CHATBOT_QUESTION,
            success=True,
            payload={"question": question_content, "answer": answer},
            ip_address=fastapi_req.client.host if fastapi_req.client else None,
            user_agent=fastapi_req.headers.get("user-agent"),
        )
        
        return APIResponse(answer=answer)

    except Exception as e:
        # Audit the failed request
        await create_audit_log(
            db=db,
            user_id=current_user.id,
            category=AuditCategory.CHATBOT,
            action=AuditAction.CHATBOT_QUESTION,
            success=False,
            payload={"question": question_content, "error": str(e)},
            ip_address=fastapi_req.client.host if fastapi_req.client else None,
            user_agent=fastapi_req.headers.get("user-agent"),
        )
        
        # Log the exception with more detail and re-raise
        print(f"Error in /chat endpoint: {e}")
        langfuse.update_current_trace(metadata={"error": str(e)}, tags=["error"])
        raise HTTPException(status_code=500, detail=f"An error occurred in the chat controller: {e}")

    finally:
        # Ensure all langfuse data is sent before the response is returned
        langfuse.flush()