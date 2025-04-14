from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class PointAccount(BaseModel):
    account_name: str
    available_balance: float
    life_time_value: float

class TierInfo(BaseModel):
    name: str
    system: Optional[str]
    entered_at: Optional[str]
    resets_at: Optional[str]

class OfferMedia(BaseModel):
    uri: Optional[str]
    category_name: Optional[str]

class Offer(BaseModel):
    id: str
    name: str
    description: Optional[str]
    offer_type: Optional[str]
    is_redeemable: bool
    start_date: Optional[str]
    expiration_date: Optional[str]
    media: List[OfferMedia] = []

class Campaign(BaseModel):
    campaign_id: int
    name: str
    type: Optional[str]
    status: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    header: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    template_type: Optional[str]

class PointAuditLog(BaseModel):
    id: str
    account_name: str
    point_account_id: str
    user_point_account_id: str
    modification: float
    amount_spent: float
    amount_expired: float
    audit_type: int
    modification_type: Optional[str]
    modification_entity_id: Optional[str]
    point_source_id: Optional[str]
    point_source_name: Optional[str]
    time_of_occurrence: str
    request_id: Optional[str]
    transaction_id: Optional[str]

class TimelineEvent(BaseModel):
    event_stream_stream_id: str
    event_stream_event_category_id: int
    event_stream_event_type_id: int
    target_id: int
    timestamp: int
    created_at: int
    event_stream_payload: Dict[str, Any]
    contexts: List[Dict[str, Any]]

class MemberContext(BaseModel):
    member_id: str
    external_id: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    tier: Optional[TierInfo]
    total_points: float
    life_time_points: float
    reward_dollars: float
    tier_qualifying_points: float
    redeemable_points: float
    point_accounts: List[PointAccount]
    recent_activity: List[PointAuditLog] = []
    offers: List[Offer]
    campaigns: List[Campaign] = []
    timeline: List[TimelineEvent] = []