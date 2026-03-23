"""Repository for Revenue Intelligence data access."""

from datetime import datetime, timezone

from app.services.db import get_conn, _generate_id, _now_iso


async def create_entry(
    channel: str,
    source: str,
    amount: float,
    currency: str = "USD",
    description: str = "",
    stream_session_id: str | None = None,
    date: str = "",
) -> dict:
    rid = _generate_id()
    now = _now_iso()
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO revenue_entries
               (id, channel, source, amount, currency, description,
                stream_session_id, date, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (rid, channel, source, amount, currency, description,
             stream_session_id, date, now),
        )
        await conn.commit()
    return {
        "id": rid, "channel": channel, "source": source, "amount": amount,
        "currency": currency, "description": description,
        "stream_session_id": stream_session_id, "date": date, "created_at": now,
    }


async def get_entries(channel: str, limit: int = 100) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM revenue_entries
               WHERE channel = %s ORDER BY date DESC LIMIT %s""",
            (channel, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_entry(entry_id: str) -> dict | None:
    """Fetch a single revenue entry by ID."""
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM revenue_entries WHERE id = %s", (entry_id,),
        )
        row = await cur.fetchone()
    return dict(row) if row else None



async def delete_entry(entry_id: str) -> bool:
    async with get_conn() as conn:
        cur = await conn.execute(
            "DELETE FROM revenue_entries WHERE id = %s", (entry_id,),
        )
        await conn.commit()
        return cur.rowcount > 0


async def get_summary(channel: str) -> dict:
    entries = await get_entries(channel, limit=500)

    now = datetime.now(timezone.utc)
    current_month = now.strftime("%Y-%m")
    last_month = (now.replace(day=1) - __import__("datetime").timedelta(days=1)).strftime("%Y-%m")

    total = sum(e["amount"] for e in entries)
    this_month = sum(e["amount"] for e in entries if e["date"].startswith(current_month))
    last_month_total = sum(e["amount"] for e in entries if e["date"].startswith(last_month))

    mom_change = 0.0
    if last_month_total > 0:
        mom_change = round(((this_month - last_month_total) / last_month_total) * 100, 1)

    # By source
    source_totals: dict[str, float] = {}
    for e in entries:
        src = e["source"]
        source_totals[src] = source_totals.get(src, 0) + e["amount"]
    by_source = [{"source": s, "total": round(t, 2)} for s, t in
                 sorted(source_totals.items(), key=lambda x: x[1], reverse=True)]

    # Monthly totals
    month_totals: dict[str, float] = {}
    for e in entries:
        month = e["date"][:7] if len(e["date"]) >= 7 else "unknown"
        month_totals[month] = month_totals.get(month, 0) + e["amount"]
    monthly = [{"month": m, "total": round(t, 2)} for m, t in sorted(month_totals.items())]

    # Per stream
    stream_totals: dict[str, dict] = {}
    for e in entries:
        sid = e.get("stream_session_id")
        if sid:
            if sid not in stream_totals:
                stream_totals[sid] = {"session_id": sid, "revenue": 0, "date": e["date"]}
            stream_totals[sid]["revenue"] += e["amount"]
    per_stream = sorted(stream_totals.values(), key=lambda x: x["date"], reverse=True)

    # Forecast (simple average of last 3 months)
    recent_months = sorted(month_totals.keys(), reverse=True)[:3]
    if recent_months:
        forecast = round(sum(month_totals[m] for m in recent_months) / len(recent_months), 2)
    else:
        forecast = 0.0

    return {
        "channel": channel,
        "total_revenue": round(total, 2),
        "total_this_month": round(this_month, 2),
        "total_last_month": round(last_month_total, 2),
        "month_over_month_change": mom_change,
        "by_source": by_source,
        "monthly_totals": monthly,
        "per_stream": per_stream,
        "forecast_next_month": forecast,
    }


async def export_csv(channel: str) -> str:
    """Export revenue data as CSV string for tax purposes."""
    entries = await get_entries(channel, limit=10000)
    lines = ["Date,Source,Amount,Currency,Description,Stream Session ID"]
    for e in entries:
        desc = e.get("description", "").replace(",", ";").replace('"', "'")
        lines.append(
            f"{e['date']},{e['source']},{e['amount']},{e['currency']},\"{desc}\","
            f"{e.get('stream_session_id', '')}"
        )
    return "\n".join(lines)
