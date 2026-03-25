"""Tournament organizer router."""

import json
import logging
import math
import random

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import Tournament, TournamentCreate, TournamentMatch, TournamentParticipant
from app.repositories import tournament as tournament_repo
from app.services.db import get_conn, _generate_id, _now_iso

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tournament", tags=["tournament"])


@router.get("")
async def list_tournaments(channel: str = "", session: dict = Depends(require_auth)) -> list[Tournament]:
    if channel:
        require_channel_owner(session, channel)
    rows = await tournament_repo.list_tournaments(channel)
    return [Tournament(**row) for row in rows]


@router.post("/create")
async def create_tournament(data: TournamentCreate, session: dict = Depends(require_auth)) -> dict:
    require_channel_owner(session, data.channel)
    result = await tournament_repo.create(
        name=data.name, channel=data.channel, game=data.game,
        max_participants=data.max_participants, fmt=data.format,
        keyword=data.keyword,
    )
    logger.info("Tournament '%s' created in channel=%s", data.name, data.channel)
    return result


@router.get("/{tournament_id}")
async def get_tournament(tournament_id: str, session: dict = Depends(require_auth)) -> Tournament:
    t = await tournament_repo.get_by_id(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    require_channel_owner(session, t["channel"])
    return Tournament(**t)


@router.post("/{tournament_id}/register")
async def register_participant(tournament_id: str, participant: TournamentParticipant, session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()

        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        require_channel_owner(session, t["channel"])
        if t["status"] != "registration":
            raise HTTPException(status_code=400, detail="Registration is closed")

        participants = t["participants"] if isinstance(t["participants"], list) else json.loads(t["participants"])

        if len(participants) >= t["max_participants"]:
            raise HTTPException(status_code=400, detail="Tournament is full")
        if any(p["username"].lower() == participant.username.lower() for p in participants):
            raise HTTPException(status_code=409, detail="Already registered")

        p_data = {"username": participant.username, "seed": len(participants) + 1, "eliminated": False}
        participants.append(p_data)

        await conn.execute(
            "UPDATE tournaments SET participants = %s WHERE id = %s",
            (json.dumps(participants), tournament_id),
        )
        await conn.commit()

    return {"status": "registered", "participant": p_data, "total_participants": len(participants)}


@router.post("/{tournament_id}/register-batch")
async def register_batch(tournament_id: str, usernames: list[str], session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()

        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        require_channel_owner(session, t["channel"])

        participants = t["participants"] if isinstance(t["participants"], list) else json.loads(t["participants"])
        registered = []
        skipped = []

        for username in usernames:
            if len(participants) >= t["max_participants"]:
                skipped.append({"username": username, "reason": "Tournament full"})
                continue
            if any(p["username"].lower() == username.lower() for p in participants):
                skipped.append({"username": username, "reason": "Already registered"})
                continue
            p_data = {"username": username, "seed": len(participants) + 1, "eliminated": False}
            participants.append(p_data)
            registered.append(p_data)

        await conn.execute(
            "UPDATE tournaments SET participants = %s WHERE id = %s",
            (json.dumps(participants), tournament_id),
        )
        await conn.commit()

    return {"registered": registered, "skipped": skipped, "total_participants": len(participants)}


def _advance_byes(matches: list[dict], current_round: int):
    current_matches = [m for m in matches if m["round"] == current_round]
    next_matches = [m for m in matches if m["round"] == current_round + 1]
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


@router.post("/{tournament_id}/start")
async def start_tournament(tournament_id: str, session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        require_channel_owner(session, t["channel"])
        if t["status"] != "registration":
            raise HTTPException(status_code=400, detail="Tournament already started")
        participants = t["participants"] if isinstance(t["participants"], list) else json.loads(t["participants"])
        if len(participants) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 participants")
        random.shuffle(participants)
        for i, p in enumerate(participants):
            p["seed"] = i + 1
        num_players = len(participants)
        bracket_size = 2 ** math.ceil(math.log2(num_players))
        matches = []
        match_num = 0
        for i in range(0, bracket_size, 2):
            match_num += 1
            p1 = participants[i]["username"] if i < num_players else None
            p2 = participants[i + 1]["username"] if i + 1 < num_players else None
            match = {"id": _generate_id(), "round": 1, "match_number": match_num, "player1": p1, "player2": p2, "winner": None, "status": "pending"}
            if p1 and not p2:
                match["winner"] = p1
                match["status"] = "completed"
            elif p2 and not p1:
                match["winner"] = p2
                match["status"] = "completed"
            matches.append(match)
        total_rounds = math.ceil(math.log2(bracket_size))
        matches_in_round = bracket_size // 2
        for round_num in range(2, total_rounds + 1):
            matches_in_round = matches_in_round // 2
            for mn in range(1, matches_in_round + 1):
                matches.append({"id": _generate_id(), "round": round_num, "match_number": mn, "player1": None, "player2": None, "winner": None, "status": "pending"})
        _advance_byes(matches, 1)
        now = _now_iso()
        await conn.execute(
            """UPDATE tournaments SET status = 'in_progress', participants = %s, matches = %s, current_round = 1, started_at = %s WHERE id = %s""",
            (json.dumps(participants), json.dumps(matches), now, tournament_id),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        updated = await row.fetchone()
    logger.info("Tournament %s started", tournament_id)
    return Tournament(**dict(updated))


@router.post("/{tournament_id}/match/{match_id}/winner")
async def set_match_winner(tournament_id: str, match_id: str, winner: str, session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        require_channel_owner(session, t["channel"])
        matches = t["matches"] if isinstance(t["matches"], list) else json.loads(t["matches"])
        participants = t["participants"] if isinstance(t["participants"], list) else json.loads(t["participants"])
        match = next((m for m in matches if m["id"] == match_id), None)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        if winner not in [match["player1"], match["player2"]]:
            raise HTTPException(status_code=400, detail="Winner must be one of the match players")
        match["winner"] = winner
        match["status"] = "completed"
        loser = match["player1"] if winner == match["player2"] else match["player2"]
        for p in participants:
            if p["username"] == loser:
                p["eliminated"] = True
        current_round_matches = [m for m in matches if m["round"] == match["round"]]
        next_round_matches = [m for m in matches if m["round"] == match["round"] + 1]
        if next_round_matches:
            match_idx = current_round_matches.index(match)
            next_match_idx = match_idx // 2
            if next_match_idx < len(next_round_matches):
                next_match = next_round_matches[next_match_idx]
                if match_idx % 2 == 0:
                    next_match["player1"] = winner
                else:
                    next_match["player2"] = winner
        current_round = t["current_round"]
        tournament_status = t["status"]
        tournament_winner = t["winner"]
        ended_at = t["ended_at"]
        all_complete = all(m["status"] == "completed" for m in current_round_matches)
        if all_complete and next_round_matches:
            current_round = match["round"] + 1
        elif all_complete and not next_round_matches:
            tournament_status = "completed"
            tournament_winner = winner
            ended_at = _now_iso()
        await conn.execute(
            """UPDATE tournaments SET matches = %s, participants = %s, current_round = %s, status = %s, winner = %s, ended_at = %s WHERE id = %s""",
            (json.dumps(matches), json.dumps(participants), current_round, tournament_status, tournament_winner, ended_at, tournament_id),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        updated = await row.fetchone()
    return {"match": TournamentMatch(**match), "tournament": Tournament(**dict(updated))}


@router.delete("/{tournament_id}")
async def delete_tournament(tournament_id: str, session: dict = Depends(require_auth)) -> dict:
    t = await tournament_repo.get_by_id(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    require_channel_owner(session, t["channel"])
    await tournament_repo.delete(tournament_id)
    logger.info("Tournament %s deleted", tournament_id)
    return {"status": "deleted"}


@router.post("/{tournament_id}/reset")
async def reset_tournament(tournament_id: str, session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        require_channel_owner(session, t["channel"])
        participants = t["participants"] if isinstance(t["participants"], list) else json.loads(t["participants"])
        for p in participants:
            p["eliminated"] = False
            p["seed"] = None
        await conn.execute(
            """UPDATE tournaments SET status = 'registration', matches = '[]', current_round = 0, winner = NULL, started_at = NULL, ended_at = NULL, participants = %s WHERE id = %s""",
            (json.dumps(participants), tournament_id),
        )
        await conn.commit()
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        updated = await row.fetchone()
    return Tournament(**dict(updated))
