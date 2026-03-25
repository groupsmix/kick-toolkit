"""Tournament organizer router."""

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


async def _load_tournament_full(conn, tournament_id: str) -> dict | None:
    """Load a tournament row and attach its participants & matches from normalized tables."""
    row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
    t = await row.fetchone()
    if not t:
        return None
    t = dict(t)

    p_cur = await conn.execute(
        "SELECT username, seed, eliminated FROM tournament_participants WHERE tournament_id = %s ORDER BY seed ASC NULLS LAST",
        (tournament_id,),
    )
    t["participants"] = [dict(r) for r in await p_cur.fetchall()]

    m_cur = await conn.execute(
        "SELECT id, round, match_number, player1, player2, winner, status FROM tournament_matches WHERE tournament_id = %s ORDER BY round, match_number",
        (tournament_id,),
    )
    t["matches"] = [dict(r) for r in await m_cur.fetchall()]

    return t


@router.get("")
async def list_tournaments(channel: str, session: dict = Depends(require_auth)) -> list[Tournament]:
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
    async with get_conn() as conn:
        t = await _load_tournament_full(conn, tournament_id)
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

        # Atomic count check — no race condition
        count_row = await conn.execute(
            "SELECT count(*) AS cnt FROM tournament_participants WHERE tournament_id = %s",
            (tournament_id,),
        )
        count = (await count_row.fetchone())["cnt"]
        if count >= t["max_participants"]:
            raise HTTPException(status_code=400, detail="Tournament is full")

        p_id = _generate_id()
        try:
            await conn.execute(
                """INSERT INTO tournament_participants (id, tournament_id, username, seed, eliminated)
                   VALUES (%s, %s, %s, %s, FALSE)""",
                (p_id, tournament_id, participant.username.lower(), count + 1),
            )
            await conn.commit()
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise HTTPException(status_code=409, detail="Already registered")
            raise

    p_data = {"username": participant.username.lower(), "seed": count + 1, "eliminated": False}
    return {"status": "registered", "participant": p_data, "total_participants": count + 1}


@router.post("/{tournament_id}/register-batch")
async def register_batch(tournament_id: str, usernames: list[str], session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()

        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        require_channel_owner(session, t["channel"])

        count_row = await conn.execute(
            "SELECT count(*) AS cnt FROM tournament_participants WHERE tournament_id = %s",
            (tournament_id,),
        )
        current_count = (await count_row.fetchone())["cnt"]

        registered = []
        skipped = []

        for username in usernames:
            if current_count >= t["max_participants"]:
                skipped.append({"username": username, "reason": "Tournament full"})
                continue

            p_id = _generate_id()
            try:
                await conn.execute(
                    """INSERT INTO tournament_participants (id, tournament_id, username, seed, eliminated)
                       VALUES (%s, %s, %s, %s, FALSE)""",
                    (p_id, tournament_id, username.lower(), current_count + 1),
                )
                p_data = {"username": username.lower(), "seed": current_count + 1, "eliminated": False}
                registered.append(p_data)
                current_count += 1
            except Exception as e:
                if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                    skipped.append({"username": username, "reason": "Already registered"})
                else:
                    raise

        await conn.commit()

    return {"registered": registered, "skipped": skipped, "total_participants": current_count}


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

        # Load participants from normalized table
        p_cur = await conn.execute(
            "SELECT id, username, seed, eliminated FROM tournament_participants WHERE tournament_id = %s",
            (tournament_id,),
        )
        participants = [dict(r) for r in await p_cur.fetchall()]

        if len(participants) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 participants")

        random.shuffle(participants)
        for i, p in enumerate(participants):
            p["seed"] = i + 1
            await conn.execute(
                "UPDATE tournament_participants SET seed = %s WHERE id = %s",
                (i + 1, p["id"]),
            )

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

        # Insert matches into normalized table
        for m in matches:
            await conn.execute(
                """INSERT INTO tournament_matches (id, tournament_id, round, match_number, player1, player2, winner, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (m["id"], tournament_id, m["round"], m["match_number"], m["player1"], m["player2"], m["winner"], m["status"]),
            )

        now = _now_iso()
        await conn.execute(
            "UPDATE tournaments SET status = 'in_progress', current_round = 1, started_at = %s WHERE id = %s",
            (now, tournament_id),
        )
        await conn.commit()

        updated = await _load_tournament_full(conn, tournament_id)

    logger.info("Tournament %s started", tournament_id)
    return Tournament(**updated)


@router.post("/{tournament_id}/match/{match_id}/winner")
async def set_match_winner(tournament_id: str, match_id: str, winner: str, session: dict = Depends(require_auth)) -> dict:
    async with get_conn() as conn:
        row = await conn.execute("SELECT * FROM tournaments WHERE id = %s", (tournament_id,))
        t = await row.fetchone()
        if not t:
            raise HTTPException(status_code=404, detail="Tournament not found")
        require_channel_owner(session, t["channel"])

        # Load the target match
        m_row = await conn.execute(
            "SELECT * FROM tournament_matches WHERE id = %s AND tournament_id = %s",
            (match_id, tournament_id),
        )
        match = await m_row.fetchone()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        match = dict(match)

        if winner not in [match["player1"], match["player2"]]:
            raise HTTPException(status_code=400, detail="Winner must be one of the match players")

        # Update match winner
        await conn.execute(
            "UPDATE tournament_matches SET winner = %s, status = 'completed' WHERE id = %s",
            (winner, match_id),
        )

        # Mark loser as eliminated
        loser = match["player1"] if winner == match["player2"] else match["player2"]
        if loser:
            await conn.execute(
                "UPDATE tournament_participants SET eliminated = TRUE WHERE tournament_id = %s AND username = %s",
                (tournament_id, loser),
            )

        # Advance winner to next round
        cur_round_cur = await conn.execute(
            "SELECT * FROM tournament_matches WHERE tournament_id = %s AND round = %s ORDER BY match_number",
            (tournament_id, match["round"]),
        )
        current_round_matches = [dict(r) for r in await cur_round_cur.fetchall()]

        next_round_cur = await conn.execute(
            "SELECT * FROM tournament_matches WHERE tournament_id = %s AND round = %s ORDER BY match_number",
            (tournament_id, match["round"] + 1),
        )
        next_round_matches = [dict(r) for r in await next_round_cur.fetchall()]

        if next_round_matches:
            match_idx = next((i for i, m in enumerate(current_round_matches) if m["id"] == match_id), 0)
            next_match_idx = match_idx // 2
            if next_match_idx < len(next_round_matches):
                next_match = next_round_matches[next_match_idx]
                if match_idx % 2 == 0:
                    await conn.execute(
                        "UPDATE tournament_matches SET player1 = %s WHERE id = %s",
                        (winner, next_match["id"]),
                    )
                else:
                    await conn.execute(
                        "UPDATE tournament_matches SET player2 = %s WHERE id = %s",
                        (winner, next_match["id"]),
                    )

        # Check if round is complete
        current_round = t["current_round"]
        tournament_status = t["status"]
        tournament_winner = t["winner"]
        ended_at = t["ended_at"]

        # Re-fetch current round matches after our update
        cur_round_cur2 = await conn.execute(
            "SELECT * FROM tournament_matches WHERE tournament_id = %s AND round = %s",
            (tournament_id, match["round"]),
        )
        updated_round_matches = [dict(r) for r in await cur_round_cur2.fetchall()]
        all_complete = all(m["status"] == "completed" for m in updated_round_matches)

        if all_complete and next_round_matches:
            current_round = match["round"] + 1
        elif all_complete and not next_round_matches:
            tournament_status = "completed"
            tournament_winner = winner
            ended_at = _now_iso()

        await conn.execute(
            "UPDATE tournaments SET current_round = %s, status = %s, winner = %s, ended_at = %s WHERE id = %s",
            (current_round, tournament_status, tournament_winner, ended_at, tournament_id),
        )
        await conn.commit()

        updated = await _load_tournament_full(conn, tournament_id)

        # Get the updated match for response
        um_row = await conn.execute(
            "SELECT id, round, match_number, player1, player2, winner, status FROM tournament_matches WHERE id = %s",
            (match_id,),
        )
        updated_match = dict(await um_row.fetchone())

    return {"match": TournamentMatch(**updated_match), "tournament": Tournament(**updated)}


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

        # Reset participants (clear seeds/eliminated)
        await conn.execute(
            "UPDATE tournament_participants SET eliminated = FALSE, seed = NULL WHERE tournament_id = %s",
            (tournament_id,),
        )

        # Delete all matches
        await conn.execute(
            "DELETE FROM tournament_matches WHERE tournament_id = %s",
            (tournament_id,),
        )

        await conn.execute(
            "UPDATE tournaments SET status = 'registration', current_round = 0, winner = NULL, started_at = NULL, ended_at = NULL WHERE id = %s",
            (tournament_id,),
        )
        await conn.commit()

        updated = await _load_tournament_full(conn, tournament_id)

    return Tournament(**updated)
