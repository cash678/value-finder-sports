import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from odds_utils import (
    extract_value_rows,
    fmt_american,
    fmt_ev,
    fmt_pct,
    get_odds,
    get_sports,
)
from parlay_utils import build_parlays

st.set_page_config(page_title="DraftKings Value Finder", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #0b1220 0%, #111827 55%, #0f172a 100%);
        color: #f8fafc;
    }
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        color: #f8fafc;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 1.3rem;
    }
    .hero-box {
        background: linear-gradient(135deg, rgba(34,197,94,0.18), rgba(15,23,42,0.95));
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 20px 22px;
        margin-bottom: 18px;
    }
    .metric-card {
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid rgba(148,163,184,0.16);
        border-radius: 16px;
        padding: 16px;
        min-height: 100px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 0.45rem;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.7rem;
        font-weight: 800;
    }
    .section-label {
        color: #e2e8f0;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 0.3rem;
        margin-bottom: 0.9rem;
    }
    .pick-card {
        background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(30,41,59,0.92));
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.18);
    }
    .pick-topline {
        display: inline-block;
        background: rgba(34,197,94,0.16);
        color: #86efac;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .pick-title {
        color: #f8fafc;
        font-size: 1.15rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }
    .pick-event {
        color: #cbd5e1;
        margin-bottom: 0.8rem;
    }
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-top: 10px;
    }
    .stat-pill {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(148,163,184,0.1);
        border-radius: 14px;
        padding: 10px 12px;
    }
    .stat-pill-label {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-bottom: 0.2rem;
    }
    .stat-pill-value {
        color: #f8fafc;
        font-size: 1rem;
        font-weight: 700;
    }
    .note-box {
        background: rgba(15,23,42,0.9);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 16px;
        padding: 14px 16px;
        color: #cbd5e1;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    div[data-testid="stDataFrame"] {
        background: rgba(15,23,42,0.75);
        border-radius: 16px;
        padding: 6px;
        border: 1px solid rgba(148,163,184,0.12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">DraftKings Value Finder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Compare DraftKings lines to broader market consensus, surface possible value, and build easier-to-read straight and parlay bet ideas.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Setup")

    api_key = st.text_input(
        "The Odds API key",
        value=st.secrets.get("ODDS_API_KEY", os.getenv("ODDS_API_KEY", "")),
        type="password",
        help="Get a key from The Odds API and place it here or in secrets.toml.",
    )

    st.markdown("### Filters")
    markets_selected = st.multiselect(
        "Markets",
        options=["h2h", "spreads", "totals"],
        default=["h2h", "spreads", "totals"],
        help="h2h = moneyline",
    )
    min_ev = st.slider("Minimum EV %", min_value=-10.0, max_value=25.0, value=1.0, step=0.5)
    min_edge = st.slider("Minimum edge %", min_value=-5.0, max_value=20.0, value=1.0, step=0.5)
    min_books = st.slider("Minimum comparison books", min_value=1, max_value=15, value=3, step=1)
    max_parlay_legs = st.slider("Max parlay legs", min_value=2, max_value=4, value=3, step=1)
    top_parlay_pool = st.slider("Parlay candidate pool size", min_value=6, max_value=20, value=12, step=1)

    st.markdown("---")
    st.info(
        "This app estimates value by comparing DraftKings lines with the consensus of other sportsbooks. It does not guarantee profit."
    )

if not api_key:
    st.warning("Add your The Odds API key in the sidebar or .streamlit/secrets.toml.")
    st.stop()

try:
    sports = get_sports(api_key)
except Exception as e:
    st.error(f"Could not load sports: {e}")
    st.stop()

active_sports = [s for s in sports if s.get("active")]
if not active_sports:
    st.error("No active sports were returned by the API.")
    st.stop()

sport_options = {f"{s['title']} ({s['key']})": s["key"] for s in active_sports}

hero_left, hero_right = st.columns([1.9, 1.1])
with hero_left:
    st.markdown(
        """
        <div class="hero-box">
            <div style="font-size:0.9rem; color:#86efac; font-weight:700; margin-bottom:8px;">LIVE VALUE SCANNER</div>
            <div style="font-size:1.55rem; font-weight:800; color:#f8fafc; margin-bottom:8px;">Spot lines that may be priced softer than the market.</div>
            <div style="color:#cbd5e1; line-height:1.5;">This dashboard compares DraftKings against other books, estimates fair win probability, and highlights the strongest straight-bet and parlay candidates in a cleaner sportsbook-style layout.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_right:
    selected_label = st.selectbox("Choose a sport", list(sport_options.keys()))
    sport_key = sport_options[selected_label]
    refresh = st.button("Refresh lines", use_container_width=True)
    st.caption("Use refresh whenever you want the newest odds snapshot.")

markets_param = ",".join(markets_selected)
if not markets_param:
    st.warning("Pick at least one market.")
    st.stop()

try:
    events, requests_remaining, requests_used = get_odds(api_key, sport_key, markets_param)
except Exception as e:
    st.error(f"Could not load odds: {e}")
    st.stop()

value_df = extract_value_rows(events)
if value_df.empty:
    st.warning("No DraftKings comparison rows were found for that sport and market selection.")
    st.stop()

filtered = value_df[
    (value_df["ev_per_dollar"] >= min_ev / 100)
    & (value_df["edge"] >= min_edge / 100)
    & (value_df["comparison_books_used"] >= min_books)
].copy()

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Games pulled</div><div class="metric-value">{len(events)}</div></div>',
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">Value bets found</div><div class="metric-value">{len(filtered)}</div></div>',
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">API requests used</div><div class="metric-value">{requests_used}</div></div>',
        unsafe_allow_html=True,
    )
with m4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">API requests remaining</div><div class="metric-value">{requests_remaining}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="note-box"><strong>How it works:</strong> The app matches DraftKings prices with the same outcomes at other books, removes vig for two-way markets, estimates a fair probability, and ranks bets by edge and expected value per dollar.</div>',
    unsafe_allow_html=True,
)

if filtered.empty:
    st.warning("Nothing passed your thresholds. Lower the EV or edge filters, reduce minimum books, or choose a different sport.")
    st.stop()

st.markdown('<div class="section-label">Best straight bets</div>', unsafe_allow_html=True)
display_df = filtered.copy()
display_df["start"] = display_df["commence_time"].dt.strftime("%Y-%m-%d %I:%M %p UTC")
display_df["DK Odds"] = display_df["draftkings_odds"].apply(fmt_american)
display_df["DK Implied"] = display_df["draftkings_implied_prob"].apply(fmt_pct)
display_df["Consensus Fair"] = display_df["consensus_fair_prob"].apply(fmt_pct)
display_df["Edge"] = display_df["edge"].apply(fmt_pct)
display_df["EV / $1"] = display_df["ev_per_dollar"].apply(fmt_ev)

st.dataframe(
    display_df[
        [
            "start",
            "event",
            "market",
            "selection",
            "DK Odds",
            "DK Implied",
            "Consensus Fair",
            "Edge",
            "EV / $1",
            "comparison_books_used",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.markdown('<div class="section-label">Top picks</div>', unsafe_allow_html=True)
card_cols = st.columns(2)
for idx, row in enumerate(filtered.head(6).to_dict("records")):
    start_str = row["commence_time"].strftime("%b %d, %I:%M %p UTC") if pd.notna(row["commence_time"]) else "Unknown time"
    with card_cols[idx % 2]:
        st.markdown(
            f"""
            <div class="pick-card">
                <div class="pick-topline">VALUE BET</div>
                <div class="pick-title">{row['selection']}</div>
                <div class="pick-event">{row['event']}</div>
                <div class="stat-grid">
                    <div class="stat-pill">
                        <div class="stat-pill-label">Market</div>
                        <div class="stat-pill-value">{row['market']}</div>
                    </div>
                    <div class="stat-pill">
                        <div class="stat-pill-label">DraftKings Odds</div>
                        <div class="stat-pill-value">{fmt_american(row['draftkings_odds'])}</div>
                    </div>
                    <div class="stat-pill">
                        <div class="stat-pill-label">Consensus Fair</div>
                        <div class="stat-pill-value">{fmt_pct(row['consensus_fair_prob'])}</div>
                    </div>
                    <div class="stat-pill">
                        <div class="stat-pill-label">Edge</div>
                        <div class="stat-pill-value">{fmt_pct(row['edge'])}</div>
                    </div>
                    <div class="stat-pill">
                        <div class="stat-pill-label">EV / $1</div>
                        <div class="stat-pill-value">{fmt_ev(row['ev_per_dollar'])}</div>
                    </div>
                    <div class="stat-pill">
                        <div class="stat-pill-label">Books Used</div>
                        <div class="stat-pill-value">{row['comparison_books_used']}</div>
                    </div>
                </div>
                <div style="margin-top:12px; color:#94a3b8; font-size:0.85rem;">Start time: {start_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="section-label">Parlay ideas</div>', unsafe_allow_html=True)
parlays_df = build_parlays(filtered, max_legs=max_parlay_legs, top_n_base=top_parlay_pool)

if parlays_df.empty:
    st.info("No parlay combinations were available from the current filtered set.")
else:
    parlays_display = parlays_df.head(10).copy()
    parlays_display["Parlay Odds"] = parlays_display["parlay_odds_american"].apply(fmt_american)
    parlays_display["Fair Win %"] = parlays_display["combined_fair_prob"].apply(fmt_pct)
    parlays_display["Combined EV"] = parlays_display["combined_ev"].apply(fmt_ev)
    parlays_display["Total Edge"] = parlays_display["total_edge"].apply(fmt_pct)

    st.dataframe(
        parlays_display[
            ["num_legs", "legs", "Parlay Odds", "Fair Win %", "Combined EV", "Total Edge"]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")
st.caption(f"Last updated in app: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
