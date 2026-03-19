"""Viewer Heatmap service.

Computes heatmap overviews, insights, and viewer attention analytics.
"""

import logging

from app.repositories import heatmap as heatmap_repo

logger = logging.getLogger(__name__)


async def compute_overview(channel: str) -> dict:
    """Compute a full heatmap overview for a channel."""
    viewer_stats = await heatmap_repo.get_viewer_stats(channel)
    category_stats = await heatmap_repo.get_category_stats(channel)
    aggregate = await heatmap_repo.get_aggregate_heatmap(channel)

    # Find peak viewer minute
    peak_minute = 0
    peak_viewers = 0
    for snap in aggregate:
        if snap.get("avg_viewers", 0) > peak_viewers:
            peak_viewers = snap["avg_viewers"]
            peak_minute = snap["minute_offset"]

    # Determine best and worst category
    best_cat = ""
    worst_cat = ""
    if category_stats:
        sorted_cats = sorted(category_stats, key=lambda c: c.get("avg_retention", 0), reverse=True)
        best_cat = sorted_cats[0]["category"] if sorted_cats else ""
        worst_cat = sorted_cats[-1]["category"] if len(sorted_cats) > 1 else ""

    # Generate insights
    insights = _generate_insights(viewer_stats, category_stats, aggregate)

    return {
        "channel": channel,
        "total_sessions": viewer_stats.get("total_sessions", 0),
        "avg_session_duration": round(viewer_stats.get("avg_duration", 0) / 60, 1),
        "avg_retention_rate": _compute_avg_retention(category_stats),
        "peak_viewer_minute": peak_minute,
        "best_category": best_cat,
        "worst_category": worst_cat,
        "unique_viewers": viewer_stats.get("unique_viewers", 0),
        "insights": insights,
        "timeline": aggregate,
        "category_stats": category_stats,
    }


def _compute_avg_retention(category_stats: list[dict]) -> float:
    if not category_stats:
        return 0.0
    total = sum(c.get("avg_retention", 0) for c in category_stats)
    return round(total / len(category_stats), 1)


def _generate_insights(
    viewer_stats: dict,
    category_stats: list[dict],
    aggregate: list[dict],
) -> list[dict]:
    """Generate actionable insights from heatmap data."""
    insights = []

    # Viewer retention insights
    if category_stats:
        sorted_cats = sorted(category_stats, key=lambda c: c.get("avg_retention", 0), reverse=True)
        if len(sorted_cats) >= 2:
            best = sorted_cats[0]
            worst = sorted_cats[-1]
            if best["category"] != worst["category"]:
                diff = round(best.get("avg_retention", 0) - worst.get("avg_retention", 0), 1)
                insights.append({
                    "type": "retention",
                    "priority": "action",
                    "title": "Content Retention Gap",
                    "message": f"'{best['category']}' content retains {diff}% more viewers than '{worst['category']}'. Consider adjusting your content mix.",
                    "metric": f"+{diff}%",
                })

    # Peak time insights
    if aggregate:
        if len(aggregate) >= 5:
            early = aggregate[:len(aggregate)//3]
            late = aggregate[-len(aggregate)//3:]
            early_avg = sum(s.get("avg_viewers", 0) for s in early) / len(early) if early else 0
            late_avg = sum(s.get("avg_viewers", 0) for s in late) / len(late) if late else 0

            if early_avg > 0 and late_avg < early_avg * 0.5:
                drop_pct = round((1 - late_avg / early_avg) * 100)
                insights.append({
                    "type": "dropoff",
                    "priority": "warning",
                    "title": "Late-Stream Viewer Drop",
                    "message": f"You lose ~{drop_pct}% of viewers in the last third of your stream. Consider ending earlier or adding engagement hooks.",
                    "metric": f"-{drop_pct}%",
                })

    # Chat activity insights
    avg_duration = viewer_stats.get("avg_duration", 0)
    if avg_duration > 0:
        mins = round(avg_duration / 60, 1)
        if mins < 15:
            insights.append({
                "type": "engagement",
                "priority": "warning",
                "title": "Short Viewer Sessions",
                "message": f"Average viewer stays {mins} minutes. Try adding interactive elements in the first 10 minutes to hook viewers.",
                "metric": f"{mins}m",
            })
        elif mins > 60:
            insights.append({
                "type": "engagement",
                "priority": "info",
                "title": "Strong Viewer Retention",
                "message": f"Average viewer stays {mins} minutes — well above typical streams. Your content is keeping people engaged!",
                "metric": f"{mins}m",
            })

    # Unique viewers insight
    unique = viewer_stats.get("unique_viewers", 0)
    total = viewer_stats.get("total_sessions", 0)
    if unique > 0 and total > 0:
        return_rate = round((total / unique - 1) * 100, 1) if unique > 0 else 0
        if return_rate > 50:
            insights.append({
                "type": "loyalty",
                "priority": "info",
                "title": "High Return Rate",
                "message": f"{return_rate}% of your viewers come back for multiple sessions. Your community is growing!",
                "metric": f"{return_rate}%",
            })

    if not insights:
        insights.append({
            "type": "info",
            "priority": "info",
            "title": "Building Your Heatmap",
            "message": "More data needed for detailed insights. Keep streaming and the heatmap will reveal patterns in your viewer behavior.",
            "metric": "",
        })

    return insights


async def compute_session_insights(channel: str, session_id: str) -> dict:
    """Get detailed insights for a specific stream session."""
    timeline = await heatmap_repo.get_heatmap_timeline(session_id)
    segments = await heatmap_repo.get_segments(session_id)
    viewers = await heatmap_repo.get_viewer_sessions(channel, session_id)

    return {
        "session_id": session_id,
        "timeline": timeline,
        "segments": segments,
        "viewer_count": len(viewers),
        "total_messages": sum(v.get("messages_sent", 0) for v in viewers),
    }
