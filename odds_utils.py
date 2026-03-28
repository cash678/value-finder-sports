import requests
import pandas as pd
import streamlit as st


def american_to_decimal(odds):
    if odds > 0:
        return 1 + (odds / 100)
    return 1 + (100 / abs(odds))


def american_to_implied_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def remove_vig_two_way(prob_a, prob_b):
    total = prob_a + prob_b
    return prob_a / total, prob_b / total


def expected_value_per_dollar(prob, odds):
    dec = american_to_decimal(odds)
    return (prob * (dec - 1)) - (1 - prob)


@st.cache_data(ttl=60)
def get_sports(api_key):
    url = "https://api.the-odds-api.com/v4/sports"
    return requests.get(url, params={"apiKey": api_key}).json()


@st.cache_data(ttl=60)
def get_odds(api_key, sport, markets):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": markets,
        "oddsFormat": "american",
    }
    res = requests.get(url, params=params)
    return res.json(), "?", "?"


def extract_value_rows(events):
    rows = []

    for event in events:
        for book in event.get("bookmakers", []):
            if book["key"] != "draftkings":
                continue

            for market in book["markets"]:
                for outcome in market["outcomes"]:
                    odds = outcome["price"]
                    prob = american_to_implied_prob(odds)

                    rows.append({
                        "event": f"{event['away_team']} @ {event['home_team']}",
                        "market": market["key"],
                        "selection": outcome["name"],
                        "draftkings_odds": odds,
                        "draftkings_implied_prob": prob,
                        "consensus_fair_prob": prob,
                        "edge": 0,
                        "ev_per_dollar": 0,
                        "comparison_books_used": 1,
                    })

    return pd.DataFrame(rows)


def fmt_pct(x):
    return f"{x*100:.1f}%"


def fmt_ev(x):
    return f"{x*100:.1f}%"


def fmt_american(x):
    return f"+{x}" if x > 0 else str(x)
