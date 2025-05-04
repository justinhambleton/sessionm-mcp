import os
import httpx

if os.getenv("NODE_ENV", "development") != "production":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

from app.models import (
    MemberContext,
    PointAccount,
    TierInfo,
    Offer,
    OfferMedia,
    Campaign,
    PointAuditLog,
    TimelineEvent
)
from typing import List

CORE_API_BASE_URL = os.getenv("CORE_API_BASE_URL")
CORE_API_KEY = os.getenv("CORE_API_KEY")
CORE_API_SECRET = os.getenv("CORE_API_SECRET")
CONNECT_API_BASE_URL = os.getenv("CONNECT_API_BASE_URL")
CONNECT_API_KEY = os.getenv("CONNECT_API_KEY")
CONNECT_API_SECRET = os.getenv("CONNECT_API_SECRET")
RETAILER_ID = os.getenv("RETAILER_ID")

async def resolve_user_context(identifier: str, type: str = "user_id") -> MemberContext:
    if type not in ["user_id", "email", "phone"]:
        raise ValueError("Invalid identifier type")

    if type == "user_id":
        url = f"{CORE_API_BASE_URL}/priv/v1/apps/{CORE_API_KEY}/users/{identifier}"
        params = None
    else:
        url = f"{CORE_API_BASE_URL}/priv/v1/apps/{CORE_API_KEY}/users/search_users"
        params = {
            "mobile_number": identifier if type == "phone" else None,
            "advanced_search_params[user_profile]": "true"
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        if type == "email":
            params["email"] = identifier

        import base64
        userpass = f"{CORE_API_KEY}:{CORE_API_SECRET}"
        auth_header = base64.b64encode(userpass.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}"
        }
        print("SessionM request URL:", url)
        print("SessionM request params:", params)
        print("SessionM request headers:", headers)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        print("SessionM response status:", response.status_code)
        print("SessionM response body:", response.text)
        response.raise_for_status()
        data = response.json()

    players = data.get("players", [])
    if not players:
        raise ValueError("User not found")
    user = players[0]

    print("User object loaded successfully")
    print("Lookup type:", type)
    print("User ID:", user["id"])
    print("Email:", user.get("email"))
    print("Tier:", user.get("tier"))

    balances = user.get("tier_details", {}).get("point_account_balances", {})
    summary = balances.get("summary", {})
    details = balances.get("details", [])

    def extract_balance(name: str) -> float:
        for acct in details:
            if acct["account_name"] == name:
                return acct.get("available_balance", 0.0)
        return 0.0

    tier_data = user.get("tier_details", {}).get("tier_levels", [])
    tier_info = None
    if tier_data:
        t = tier_data[0]
        tier_info = TierInfo(
            name=t["tier_overview"]["name"],
            system=t.get("tier_system_id"),
            entered_at=user.get("tier_entered_at"),
            resets_at=user.get("tier_resets_at")
        )

    try:
        print("Fetching offers...")
        offers = await get_user_offers(user["user_id"])
        print(f"Offers loaded: {len(offers)}")
    except Exception as e:
        print("Error fetching offers:", e)
        offers = []

    try:
        print("Fetching campaigns...")
        campaigns = await get_user_campaigns(user["user_id"])
        print(f"Campaigns loaded: {len(campaigns)}")
    except Exception as e:
        print("Error fetching campaigns:", e)
        campaigns = []

    try:
        print("Fetching point audit logs...")
        audit_logs = await get_user_point_audit_logs(user["user_id"])
        print(f"Audit logs loaded: {len(audit_logs)}")
    except Exception as e:
        logging.error(f"Error fetching point audit logs: {e}")
        audit_logs = []

    try:
        print("Fetching timeline events...")
        timeline = await get_user_timeline_events(user["user_id"])
        print(f"Timeline events loaded: {len(timeline)}")
    except Exception as e:
        logging.error(f"Error fetching timeline events: {e}")
        timeline = []

    return MemberContext(
        member_id=user["id"],
        external_id=user.get("external_id"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        email=user.get("email"),
        tier=tier_info,
        total_points=summary.get("total_points", 0.0),
        life_time_points=summary.get("life_time_points", 0.0),
        reward_dollars=extract_balance("Reward Dollars"),
        tier_qualifying_points=extract_balance("Tier Qualifying Points"),
        redeemable_points=extract_balance("Redeemable Points"),
        point_accounts=[
            PointAccount(
                account_name=a["account_name"],
                available_balance=a["available_balance"],
                life_time_value=a["life_time_value"]
            )
            for a in details
        ],
        recent_activity=audit_logs,
        offers=offers,
        campaigns=campaigns,
        timeline=timeline
    )

async def get_user_offers(user_id: str) -> List[Offer]:
    url = f"{CONNECT_API_BASE_URL}/offers/api/2.0/offers/get_user_offers"
    payload = {
        "retailer_id": RETAILER_ID,
        "user_id": user_id,
        "skip": 0,
        "take": 1000,
        "include_pending_extended_data": True,
        "culture": "en-US"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            auth=(CONNECT_API_KEY, CONNECT_API_SECRET),
            headers={"Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()
        offers = response.json().get("payload", {}).get("user_offers", [])
        return [
            Offer(
                id=o["id"],
                name=o.get("name"),
                description=o.get("description"),
                offer_type=o.get("offer_type"),
                is_redeemable=o.get("is_redeemable", False),
                start_date=o.get("start_date"),
                expiration_date=o.get("expiration_date") or o.get("redemption_end_date"),
                media=[
                    OfferMedia(
                        uri=m.get("uri"),
                        category_name=m.get("category_name")
                    ) for m in o.get("media", [])
                ]
            )
            for o in offers
        ]

async def get_user_campaigns(user_id: str) -> List[Campaign]:
    url = f"{CORE_API_BASE_URL}/priv/v1/apps/{CORE_API_KEY}/users/{user_id}/campaigns"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, auth=(CORE_API_KEY, CORE_API_SECRET))
        response.raise_for_status()
        data = response.json()
        tiles = data.get("campaigns", {}).get("tiles", [])
        return [
            Campaign(
                campaign_id=c.get("campaign_id"),
                name=c.get("name"),
                type=c.get("custom_payload", {}).get("type"),
                status=c.get("progress", {}).get("state"),
                start_date=c.get("start_date"),
                end_date=c.get("end_date"),
                header=c.get("template", {}).get("message", {}).get("header"),
                description=c.get("template", {}).get("message", {}).get("description"),
                image_url=c.get("template", {}).get("message", {}).get("image_url"),
                template_type=c.get("template", {}).get("type")
            )
            for c in tiles
        ]

async def get_user_point_audit_logs(user_id: str) -> List[PointAuditLog]:
    url = f"{CONNECT_API_BASE_URL}/incentives/api/1.0/point_audit_logs/fetch_point_audit_logs"
    payload = {
        "retailer_id": RETAILER_ID,
        "user_id": user_id,
        "exclude_specified_modification_types": False,
        "skip": 0,
        "take": 10
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            auth=(CONNECT_API_KEY, CONNECT_API_SECRET),
            headers={"Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()
        items = response.json().get("payload", {}).get("results", [])
        return [PointAuditLog(**i) for i in items]

async def get_user_timeline_events(user_id: str) -> List[TimelineEvent]:
    url = f"{CORE_API_BASE_URL}/priv/v1/apps/{CORE_API_KEY}/users/{user_id}/timelines/ACCOUNT_AUDIT_LOG"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            auth=(CORE_API_KEY, CORE_API_SECRET),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        items = response.json().get("result", [])
        return [TimelineEvent(**item) for item in items]

def generate_summary(ctx: MemberContext) -> str:
    return (
        f"Hi {ctx.first_name}, you're a {ctx.tier.name if ctx.tier else 'member'} with "
        f"{int(ctx.total_points):,} points and {len(ctx.offers)} active offer"
        f"{'' if len(ctx.offers) == 1 else 's'}."
    )
