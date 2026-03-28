import requests
import pandas as pd
import streamlit as st


def american_to_decimal(odds: float) -> float:
    if odds is None:
        return None
    odds = float(odds)
    if odds > 0:
        return 1 + (odds / 100)
    return 1 + (100 / abs(odds))


def american_to_implied_prob(odds: float) -> float:
    if odds is None:
        return None
    odds = float(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def remove_vig_two_way(prob_a: float, prob_b: float):
    total = prob_a + prob_b
    if total <= 0:
        return None, None
    return prob_a / total, prob_b / total


def expected_value_per_dollar(fair_prob: float, american_odds: float) -> float:
    dec = american_to_decimal(american_odds)
    if fair_prob is None or dec is None:
        return None
    profit_if_win = dec - 1
    return (fair_prob * profit_if_win) - (1 - fair_prob)


def fmt_pct(x):
    return f"{x * 100:.1f}%" if x is not None and pd.notna(x) else "—"


def fmt_ev(x):
    return f"{x * 100:.1f}%" if x is not None and pd.notna(x) else "—"


def fmt_american(x):
    if x is None or pd.isna(x):
        return "—"
    x = int(round(float(x)))
    return f"+{x}" if x > 0 else str(x)


def safe_get(url: str, params: dict):
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp


@st.cache_data(ttl=1800)
def get_sports(api_key: str):
    url = "https://api.the-odds-api.com/v4/sports"
    resp = safe_get(url, {"apiKey": api_key})
    return resp.json()


@st.cache_data(ttl=120)
def get_odds(api_key: str, sport_key: str, markets: str, regions: str = "us"):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": "american",
        "dateFormat": "iso",
    }
    resp = safe_get(url, params)
    remaining = resp.headers.get("x-requests-remaining", "?")
    used = resp.headers.get("x-requests-used", "?")
    return resp.json(), remaining, used


def get_opposite_outcome_name(market_key: str, all_outcomes: list, outcome: dict):
    if market_key == "h2h":
        names = [o["name"] for o in all_outcomes if o["name"] != outcome["name"]]
        return names[0] if names else None

    if market_key == "spreads":
        for o in all_outcomes:
            if (
                o["name"] != outcome["name"]
                and float(o.get("point", 0)) == -float(outcome.get("point", 0))
            ):
                return o["name"]
        others = [o["name"] for o in all_outcomes if o["name"] != outcome["name"]]
        return others[0] if others else None

    if market_key == "totals":
        target = "Over" if outcome["name"] == "Under" else "Under"
        for o in all_outcomes:
            if (
                o["name"] == target
                and float(o.get("point", 0)) == float(outcome.get("point", 0))
            ):
                return o["name"]
        others = [o["name"] for o in all_outcomes if o["name"] != outcome["name"]]
        return others[0] if others else None

    return None


def build_event_title(event):
    away = event.get("away_team", "Away")
    home = event.get("home_team", "Home")
    return f"{away} @ {home}"


def extract_value_rows(events, dk_key="draftkings"):
    rows = []

    for event in events:
        event_title = build_event_title(event)
        commence = event.get("commence_time")
        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            continue

        market_book_map = {}
        for book in bookmakers:
            book_key = book.get("key")
            for market in book.get("markets", []):
                market_key = market.get("key")
                market_book_map.setdefault(market_key, {})[book_key] = market

        for market_key, books_for_market in market_book_map.items():
            if dk_key not in books_for_market:
                continue

            dk_market = books_for_market[dk_key]
            dk_outcomes = dk_market.get("outcomes", [])

            for dk_outcome in dk_outcomes:
                dk_price = dk_outcome.get("price")
                if dk_price is None:
                    continue

                dk_implied = american_to_implied_prob(dk_price)
                fair_probs = []
                opposite_name = get_opposite_outcome_name(
                    market_key, dk_outcomes, dk_outcome
                )

                for book_key, market in books_for_market.items():
                    if book_key == dk_key:
                        continue

                    outcomes = market.get("outcomes", [])
                    match_outcome = None
                    opp_outcome = None

                    for o in outcomes:
                        same_name = o.get("name") == dk_outcome.get("name")
                        same_point = float(o.get("point", 0)) == float(
                            dk_outcome.get("point", 0)
                        )
                        if same_name and same_point:
                            match_outcome = o

                        if opposite_name is not None:
                            opp_same_name = o.get("name") == opposite_name
                            opp_same_point = (
                                float(o.get("point", 0))
                                == float(dk_outcome.get("point", 0))
                                if market_key == "totals"
                                else float(o.get("point", 0))
                                == -float(dk_outcome.get("point", 0))
                                if market_key == "spreads"
                                else True
                            )
                            if opp_same_name and opp_same_point:
                                opp_outcome = o

                    if (
                        match_outcome
                        and opp_outcome
                        and match_outcome.get("price") is not None
                        and opp_outcome.get("price") is not None
                    ):
                        p1 = american_to_implied_prob(match_outcome["price"])
                        p2 = american_to_implied_prob(opp_outcome["price"])
                        fair_p1, _ = remove_vig_two_way(p1, p2)
                        if fair_p1 is not None:
                            fair_probs.append(fair_p1)

                if fair_probs:
                    consensus_fair_prob = sum(fair_probs) / len(fair_probs)
                    ev = expected_value_per_dollar(consensus_fair_prob, dk_price)
                    edge = consensus_fair_prob - dk_implied
                    comparison_books_used = len(fair_probs)
                else:
                    consensus_fair_prob = dk_implied
                    ev = 0.0
                    edge = 0.0
                    comparison_books_used = 1

                point = dk_outcome.get("point")
                leg_label = dk_outcome.get("name")
                if point is not None:
                    if market_key == "spreads":
                        sign = "+" if float(point) > 0 else ""
                        leg_label = f"{leg_label} {sign}{point}"
                    elif market_key == "totals":
                        leg_label = f"{leg_label} {point}"

                rows.append(
                    {
                        "event_id": event.get("id"),
                        "event": event_title,
                        "commence_time": commence,
                        "market": market_key,
                        "selection": leg_label,
                        "draftkings_odds": dk_price,
                        "draftkings_implied_prob": dk_implied,
                        "consensus_fair_prob": consensus_fair_prob,
                        "edge": edge,
                        "ev_per_dollar": ev,
                        "comparison_books_used": comparison_books_used,
                        "home_team": event.get("home_team"),
                        "away_team": event.get("away_team"),
                    }
                )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["commence_time"] = pd.to_datetime(
            df["commence_time"], utc=True, errors="coerce"
        )
        df = df.sort_values(
            ["ev_per_dollar", "edge"], ascending=False
        ).reset_index(drop=True)

    return df
