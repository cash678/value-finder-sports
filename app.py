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
st.caption(f"Last updated in app: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
