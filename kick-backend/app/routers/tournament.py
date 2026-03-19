"""Tournament organizer router."""

import random
import math
from fastapi import APIRouter
from app.models.schemas import TournamentCreate, TournamentParticipant
from app.services.database import tournaments, generate_id, now_iso

router = APIRouter(prefix="/api/tournament", tags=["tournament"])


@router.get("")
async def list_tournaments(channel: str = "") -> list[dict]:
    result = list(tournaments.values())
    if channel:
        result = [t for t in result if t["channel"] == channel]
    return sorted(result, key=lambda x: x["created_at"], reverse=True)


@router.post("/create")
async def create_tournament(data: TournamentCreate) -> dict:
    t_id = generate_id()
    tournament = {
        "id": t_id,
        **data.model_dump(),
        "status": "registration",
        "participants": [],
        "matches": [],
        "current_round": 0,
        "winner": None,
        "created_at": now_iso(),
        "started_at": None,
        "ended_at": None,
    }
    tournaments[t_id] = tournament
    return tournament


@router.get("/{tournament_id}")
async def get_tournament(tournament_id: str) -> dict:
    if tournament_id in tournaments:
        return tournaments[tournament_id]
    return {"error": "Tournament not found"}


@router.post("/{tournament_id}/register")
async def register_participant(tournament_id: str, participant: TournamentParticipant) -> dict:
    if tournament_id not in tournaments:
        return {"error": "Tournament not found"}

    t = tournaments[tournament_id]
    if t["status"] != "registration":
        return {"error": "Registration is closed"}

    if len(t["participants"]) >= t["max_participants"]:
        return {"error": "Tournament is full"}

    existing = [p for p in t["participants"] if p["username"].lower() == participant.username.lower()]
    if existing:
        return {"error": "Already registered"}

    p_data = {
        "username": participant.username,
        "seed": len(t["participants"]) + 1,
        "eliminated": False,
    }
    t["participants"].append(p_data)
    return {"status": "registered", "participant": p_data, "total_participants": len(t["participants"])}


@router.post("/{tournament_id}/register-batch")
async def register_batch(tournament_id: str, usernames: list[str]) -> dict:
    """Register multiple participants at once (from keyword collection)."""
    if tournament_id not in tournaments:
        return {"error": "Tournament not found"}

    t = tournaments[tournament_id]
    registered = []
    skipped = []

    for username in usernames:
        if len(t["participants"]) >= t["max_participants"]:
            skipped.append({"username": username, "reason": "Tournament full"})
            continue

        existing = [p for p in t["participants"] if p["username"].lower() == username.lower()]
        if existing:
            skipped.append({"username": username, "reason": "Already registered"})
            continue

        p_data = {
            "username": username,
            "seed": len(t["participants"]) + 1,
            "eliminated": False,
        }
        t["participants"].append(p_data)
        registered.append(p_data)

    return {"registered": registered, "skipped": skipped, "total_participants": len(t["participants"])}


@router.post("/{tournament_id}/start")
async def start_tournament(tournament_id: str) -> dict:
    if tournament_id not in tournaments:
        return {"error": "Tournament not found"}

    t = tournaments[tournament_id]
    if t["status"] != "registration":
        return {"error": "Tournament already started"}

    if len(t["participants"]) < 2:
        return {"error": "Need at least 2 participants"}

    # Shuffle and seed participants
    random.shuffle(t["participants"])
    for i, p in enumerate(t["participants"]):
        p["seed"] = i + 1

    # Pad to nearest power of 2
    num_players = len(t["participants"])
    bracket_size = 2 ** math.ceil(math.log2(num_players))

    # Generate bracket matches
    matches = []
    match_num = 0
    for i in range(0, bracket_size, 2):
        match_num += 1
        p1 = t["participants"][i]["username"] if i < num_players else None
        p2 = t["participants"][i + 1]["username"] if i + 1 < num_players else None

        match = {
            "id": generate_id(),
            "round": 1,
            "match_number": match_num,
            "player1": p1,
            "player2": p2,
            "winner": None,
            "status": "pending",
        }

        # Auto-advance byes
        if p1 and not p2:
            match["winner"] = p1
            match["status"] = "completed"
        elif p2 and not p1:
            match["winner"] = p2
            match["status"] = "completed"

        matches.append(match)

    # Generate future round placeholders
    total_rounds = math.ceil(math.log2(bracket_size))
    matches_in_round = bracket_size // 2
    for round_num in range(2, total_rounds + 1):
        matches_in_round = matches_in_round // 2
        for mn in range(1, matches_in_round + 1):
            matches.append({
                "id": generate_id(),
                "round": round_num,
                "match_number": mn,
                "player1": None,
                "player2": None,
                "winner": None,
                "status": "pending",
            })

    t["matches"] = matches
    t["current_round"] = 1
    t["status"] = "in_progress"
    t["started_at"] = now_iso()

    # Auto-advance byes to next round
    _advance_byes(t)

    return t


def _advance_byes(tournament: dict):
    """Advance bye winners to the next round."""
    current_round = tournament["current_round"]
    current_matches = [m for m in tournament["matches"] if m["round"] == current_round]
    next_matches = [m for m in tournament["matches"] if m["round"] == current_round + 1]

    if not next_matches:
        return

    for i, match in enumerate(current_matches):
        if match["winner"] and match["status"] == "completed":
            next_match_idx = i // 2
            if next_match_idx < len(next_matches):
                next_match = next_matches[next_match_idx]
                if i % 2 == 0:
                    next_match["player1"] = match["winner"]
                else:
                    next_match["player2"] = match["winner"]


@router.post("/{tournament_id}/match/{match_id}/winner")
async def set_match_winner(tournament_id: str, match_id: str, winner: str) -> dict:
    if tournament_id not in tournaments:
        return {"error": "Tournament not found"}

    t = tournaments[tournament_id]
    match = next((m for m in t["matches"] if m["id"] == match_id), None)
    if not match:
        return {"error": "Match not found"}

    if winner not in [match["player1"], match["player2"]]:
        return {"error": "Winner must be one of the match players"}

    match["winner"] = winner
    match["status"] = "completed"

    # Mark loser as eliminated
    loser = match["player1"] if winner == match["player2"] else match["player2"]
    for p in t["participants"]:
        if p["username"] == loser:
            p["eliminated"] = True

    # Advance winner to next round
    current_round_matches = [m for m in t["matches"] if m["round"] == match["round"]]
    next_round_matches = [m for m in t["matches"] if m["round"] == match["round"] + 1]

    if next_round_matches:
        match_idx = current_round_matches.index(match)
        next_match_idx = match_idx // 2
        if next_match_idx < len(next_round_matches):
            next_match = next_round_matches[next_match_idx]
            if match_idx % 2 == 0:
                next_match["player1"] = winner
            else:
                next_match["player2"] = winner

    # Check if round is complete
    all_complete = all(m["status"] == "completed" for m in current_round_matches)
    if all_complete and next_round_matches:
        t["current_round"] = match["round"] + 1
    elif all_complete and not next_round_matches:
        t["status"] = "completed"
        t["winner"] = winner
        t["ended_at"] = now_iso()

    return {"match": match, "tournament": t}


@router.delete("/{tournament_id}")
async def delete_tournament(tournament_id: str) -> dict:
    if tournament_id in tournaments:
        del tournaments[tournament_id]
    return {"status": "deleted"}


@router.post("/{tournament_id}/reset")
async def reset_tournament(tournament_id: str) -> dict:
    if tournament_id not in tournaments:
        return {"error": "Tournament not found"}

    t = tournaments[tournament_id]
    t["status"] = "registration"
    t["matches"] = []
    t["current_round"] = 0
    t["winner"] = None
    t["started_at"] = None
    t["ended_at"] = None
    for p in t["participants"]:
        p["eliminated"] = False
        p["seed"] = None

    return t
