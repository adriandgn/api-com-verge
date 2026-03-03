from datetime import datetime
from typing import List, Literal, Optional, Union, Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


class SponsorInquiryPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    company: str = Field(..., min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=50)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=2000)


class SponsorInquiryResponse(BaseModel):
    success: bool
    message: str
    sponsor_id: Optional[str] = None


class CreatorRegistration(BaseModel):
    profile: Literal["creator"]
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    studio_brand: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    links: Optional[str] = Field(None, max_length=500)
    practice_description: str = Field(..., min_length=10, max_length=1000)
    podcast_interest: bool = False
    suggested_topics: Optional[str] = Field(None, max_length=500)

    @field_validator("links")
    @classmethod
    def validate_links(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith(("http://", "https://")):
            raise ValueError("Links must be valid URLs")
        return value


class ExpertRegistration(BaseModel):
    profile: Literal["expert"]
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    organization: Optional[str] = Field(None, max_length=100)
    field_expertise: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    proposed_topic: Optional[str] = Field(None, max_length=500)
    preferred_format: Optional[Literal["talk", "panel", "workshop", "demo"]] = None
    bio_links: str = Field(..., min_length=10, max_length=1000)

    @field_validator("bio_links")
    @classmethod
    def validate_bio_links(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("Bio links must be valid URLs")
        return value


class EventHostRegistration(BaseModel):
    profile: Literal["event-host"]
    organization_name: str = Field(..., min_length=2, max_length=100)
    type: Optional[str] = Field(None, max_length=100)
    city_country: str = Field(..., min_length=2, max_length=100)
    event_type: str = Field(..., min_length=5, max_length=200)
    audience_size: str = Field(..., max_length=50)
    contact_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class ParticipantRegistration(BaseModel):
    profile: Literal["participant"]
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    city_country: str = Field(..., min_length=2, max_length=100)
    interests: List[str] = Field(default_factory=list)

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, value: List[str]) -> List[str]:
        allowed = {
            "Craft Innovation",
            "Tech Applications",
            "Markets Regulation",
            "Impact Culture"
        }
        if not all(interest in allowed for interest in value):
            raise ValueError(f"Interests must be one of {sorted(allowed)}")
        return value


class VolunteerRegistration(BaseModel):
    profile: Literal["volunteer"]
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    city_country: str = Field(..., min_length=2, max_length=100)
    skills_idea: str = Field(..., min_length=10, max_length=500)
    availability: Optional[str] = Field(None, max_length=200)
    motivation: str = Field(..., min_length=10, max_length=1000)


class RegistrationResponse(BaseModel):
    success: bool
    message: str
    registration_id: Optional[str] = None


class RegistrationDetail(BaseModel):
    id: int
    uuid: str
    profile: str
    data: dict
    email: Optional[str]
    status: str
    created_at: datetime


RegistrationPayload = Annotated[
    Union[
        CreatorRegistration,
        ExpertRegistration,
        EventHostRegistration,
        ParticipantRegistration,
        VolunteerRegistration
    ],
    Field(discriminator="profile")
]
