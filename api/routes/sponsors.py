import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from api.database import insert_sponsor_inquiry
from api.email_service import send_sponsor_admin_notification, send_sponsor_confirmation_email
from api.models import SponsorInquiryPayload, SponsorInquiryResponse
from api.rate_limit import limiter
from api.settings import get_settings


router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/sponsors", response_model=SponsorInquiryResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def create_sponsor_inquiry(
    inquiry: SponsorInquiryPayload,
    request: Request,
    background_tasks: BackgroundTasks
):
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    data = inquiry.model_dump()

    try:
        result = await insert_sponsor_inquiry(
            data=data,
            ip=ip,
            user_agent=user_agent
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to save sponsor inquiry")
    except Exception as exc:
        logger.exception("Error saving sponsor inquiry")
        raise HTTPException(status_code=500, detail=f"Error: {str(exc)}") from exc

    try:
        background_tasks.add_task(send_sponsor_confirmation_email, data["email"], data["name"])
    except ValueError:
        logger.warning("Email config missing; sponsor confirmation email skipped")

    try:
        background_tasks.add_task(send_sponsor_admin_notification, data)
    except ValueError:
        logger.warning("Email config missing; sponsor admin notification skipped")

    return SponsorInquiryResponse(
        success=True,
        message="Sponsor inquiry submitted successfully",
        sponsor_id=result.get("uuid")
    )

