"""
Clerk webhook endpoints for user synchronization
"""

import json
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
import os
from dotenv import load_dotenv
from svix import Webhook, WebhookVerificationError

from app.database import get_db
from app.models import User

load_dotenv()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Get Clerk webhook secret from environment
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")


async def verify_clerk_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
) -> dict:
    """
    Verify Clerk webhook signature using svix.
    Returns the parsed payload if verification succeeds.
    """
    # Read request body
    body = await request.body()

    if not CLERK_WEBHOOK_SECRET:
        # In development, you might want to skip verification
        # In production, always verify webhooks
        return json.loads(body.decode("utf-8"))

    try:
        wh = Webhook(CLERK_WEBHOOK_SECRET)

        # Verify the webhook signature
        payload = wh.verify(
            body,
            {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature,
            },
        )
        # svix.verify returns a dict, so we can return it directly
        if isinstance(payload, bytes):
            return json.loads(payload.decode("utf-8"))
        return payload
    except WebhookVerificationError as e:
        raise HTTPException(
            status_code=401, detail=f"Webhook verification failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Webhook processing error: {str(e)}"
        )


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
    db: Session = Depends(get_db),
):
    """
    Handle Clerk webhook events for user CRUD operations.

    Supported events:
    - user.created: Create new user in database
    - user.updated: Update existing user in database
    - user.deleted: Delete user from database
    """
    try:
        # Verify webhook signature and get payload
        payload = await verify_clerk_webhook(
            request, svix_id, svix_timestamp, svix_signature
        )
        event_type = payload.get("type")
        data = payload.get("data", {})

        if event_type == "user.created":
            # Create new user
            user_id = data.get("id")
            if not user_id:
                raise HTTPException(status_code=400, detail="User ID is required")

            # Check if user already exists
            existing_user = db.query(User).filter(User.user_id == user_id).first()
            if existing_user:
                # Update instead of creating
                existing_user.email = data.get("email_addresses", [{}])[0].get(
                    "email_address", ""
                )
                existing_user.first_name = data.get("first_name")
                existing_user.last_name = data.get("last_name")
                db.commit()
                return {"success": True, "message": "User updated (already existed)"}

            # Extract email from email_addresses array
            email_addresses = data.get("email_addresses", [])
            email = (
                email_addresses[0].get("email_address", "") if email_addresses else ""
            )

            # Create new user
            new_user = User(
                user_id=user_id,
                email=email,
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                bio=None,  # Bio not provided by Clerk, can be updated later
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return {
                "success": True,
                "message": "User created successfully",
                "user_id": new_user.user_id,
            }

        elif event_type == "user.updated":
            # Update existing user
            user_id = data.get("id")
            if not user_id:
                raise HTTPException(status_code=400, detail="User ID is required")

            # Find user
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                # If user doesn't exist, create it
                email_addresses = data.get("email_addresses", [])
                email = (
                    email_addresses[0].get("email_address", "")
                    if email_addresses
                    else ""
                )

                new_user = User(
                    user_id=user_id,
                    email=email,
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    bio=None,
                )
                db.add(new_user)
                db.commit()
                return {
                    "success": True,
                    "message": "User created (didn't exist on update)",
                    "user_id": new_user.user_id,
                }

            # Update user fields
            email_addresses = data.get("email_addresses", [])
            if email_addresses:
                user.email = email_addresses[0].get("email_address", user.email)

            if data.get("first_name") is not None:
                user.first_name = data.get("first_name")
            if data.get("last_name") is not None:
                user.last_name = data.get("last_name")

            db.commit()
            db.refresh(user)

            return {
                "success": True,
                "message": "User updated successfully",
                "user_id": user.user_id,
            }

        elif event_type == "user.deleted":
            # Delete user
            user_id = data.get("id")
            if not user_id:
                raise HTTPException(status_code=400, detail="User ID is required")

            # Find and delete user
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return {
                    "success": True,
                    "message": "User not found (already deleted or never existed)",
                }

            db.delete(user)
            db.commit()

            return {
                "success": True,
                "message": "User deleted successfully",
                "user_id": user_id,
            }

        else:
            # Unhandled event type
            return {
                "success": True,
                "message": f"Event type '{event_type}' received but not handled",
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Webhook processing error: {str(e)}"
        )
