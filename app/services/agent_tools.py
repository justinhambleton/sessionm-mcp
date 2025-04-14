from typing import Dict, List, Any
from datetime import datetime
from dateutil import parser

def get_soonest_campaign(context: Dict[str, Any]) -> str:
    campaigns = context.get("campaigns", [])
    if not campaigns:
        return "You have no campaigns."
    sorted_campaigns = sorted(
        campaigns,
        key=lambda c: c.get("end_date") or "9999-12-31"
    )
    first = sorted_campaigns[0]
    return (
        f'"{first["name"]}" ends on {first["end_date"]}'
        if first.get("end_date") else f'"{first["name"]}" has no end date.'
    )

def summarize_offers(context: Dict[str, Any]) -> str:
    offers = context.get("offers", [])
    if not offers:
        return "You don’t have any active offers."
    return "\n".join(f'{o["name"]} – {o["description"]}' for o in offers)

def get_point_summary(context: Dict[str, Any]) -> str:
    total = int(context.get("total_points", 0))
    tier = context.get("tier", {}).get("name", "Unknown")
    return f"You’re currently a {tier} member with {total:,} points."

def get_total_earned_points(context: Dict[str, Any]) -> str:
    audits = context.get("recent_activity", [])
    earned = sum(a["modification"] for a in audits if a["modification"] > 0)
    return f"You've earned a total of {int(earned):,} points."

def get_total_spent_points(context: Dict[str, Any]) -> str:
    audits = context.get("recent_activity", [])
    spent = sum(a["amount_spent"] for a in audits)
    return f"You’ve spent a total of {int(spent):,} points."

def get_total_points_expired(context: Dict[str, Any]) -> str:
    audits = context.get("recent_activity", [])
    expired_total = sum(a.get("amount_expired", 0) for a in audits if a.get("amount_expired", 0) > 0)
    return f"You have {expired_total:.0f} points that have expired." if expired_total else "You have no expired points."

def get_total_points_earned(context: Dict[str, Any]) -> str:
    audits = context.get("recent_activity", [])
    earned_total = sum(a.get("modification", 0) for a in audits if a.get("modification", 0) > 0)
    return f"You have earned a total of {earned_total:.0f} points recently."

def get_points_by_account(context: Dict[str, Any]) -> str:
    audits = context.get("recent_activity", [])
    by_account = {}
    for a in audits:
        acc = a.get("account_name", "Unknown")
        by_account[acc] = by_account.get(acc, 0) + a.get("modification", 0)

    lines = [f"{acc}: {pts:.0f} pts" for acc, pts in by_account.items()]
    return "Point changes by account:\n" + "\n".join(lines) if lines else "No recent point activity."

def get_most_valuable_offer(context: Dict[str, Any]) -> str:
    offers = context.get("offers", [])
    reward_offers = [
        (o["name"], int(o["name"].replace("$", "").split()[0]))
        for o in offers
        if o["name"].startswith("$") and o["name"][1:].split()[0].isdigit()
    ]
    if not reward_offers:
        return "Could not determine the most valuable offer."
    top = max(reward_offers, key=lambda x: x[1])
    return f'Your most valuable offer is "{top[0]}".'

def get_recent_purchases(context: Dict[str, Any], count: int = 3) -> str:
    timeline = context.get("timeline", [])
    purchases = [
        e for e in timeline
        if e.get("event_stream_payload", {}).get("event_type_slug") == "PURCHASE"
    ]
    sorted_purchases = sorted(purchases, key=lambda e: e.get("timestamp", 0), reverse=True)[:count]

    return "\n".join(
        f"- {e['event_stream_payload'].get('transaction_id', 'N/A')} on {e['event_stream_payload'].get('transaction_time', 'Unknown')}"
        for e in sorted_purchases
    ) if sorted_purchases else "No purchases found."

def get_points_spent_this_month(context: Dict[str, Any]) -> str:
    timeline = context.get("timeline", [])
    now = datetime.utcnow()

    def is_this_month(event):
        payload = event.get("event_stream_payload", {})
        time_str = payload.get("TimeOfOccurrence")
        try:
            return parser.parse(time_str).month == now.month
        except:
            return False

    spent_events = [
        e for e in timeline
        if e.get("event_stream_payload", {}).get("event_type_slug") == "INCENTIVES_POINT_SPEND" and is_this_month(e)
    ]
    total_spent = sum(abs(e["event_stream_payload"].get("Modification", 0)) for e in spent_events)
    return f"You’ve spent {int(total_spent)} points so far this month." if spent_events else "No points spent this month."