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
    return df
