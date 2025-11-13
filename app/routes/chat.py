from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, ErrorResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - receives user message and returns AI response.
    Currently returns a mock response.
    """
    try:
        user_message = request.message.strip()
        
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        # Mock AI response
        mock_response = f"I understand you're facing: {user_message}. Let me help you brainstorm some solutions and ideas. What specific aspect would you like to explore further?"
        
        return ChatResponse(
            success=True,
            data={"response": mock_response},
            message="Chat response generated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

