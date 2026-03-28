from itertools import combinations

import pandas as pd

from odds_utils import american_to_decimal


def build_parlays(df: pd.DataFrame, max_legs=3, top_n_base=12):
    if df.empty:
        return pd.DataFrame()

    candidates = (
        df[df["ev_per_dollar"] > 0]
        .sort_values(["ev_per_dollar", "edge"], ascending=False)
        .head(top_n_base)
        .copy()
    )

    parlays = []
    for leg_count in range(2, max_legs + 1):
        for combo in combinations(candidates.to_dict("records"), leg_count):
            event_ids = [x["event_id"] for x in combo]
            if len(set(event_ids)) < len(event_ids):
                continue

            combined_dec = 1.0
            combined_prob = 1.0
            total_edge = 0.0

            for leg in combo:
                combined_dec *= american_to_decimal(leg["draftkings_odds"])
                combined_prob *= leg["consensus_fair_prob"]
                total_edge += leg["edge"]

            if combined_dec >= 2:
                combined_american = (combined_dec - 1) * 100
            else:
                combined_american = -100 / (combined_dec - 1)

            ev = (combined_prob * (combined_dec - 1)) - (1 - combined_prob)

            parlays.append(
                {
                    "legs": " | ".join([f"{x['event']}: {x['selection']}" for x in combo]),
                    "num_legs": leg_count,
                    "events": len(set(event_ids)),
                    "parlay_odds_american": combined_american,
                    "combined_fair_prob": combined_prob,
                    "combined_ev": ev,
                    "total_edge": total_edge,
                }
            )

    out = pd.DataFrame(parlays)
    if not out.empty:
        out = out.sort_values(["combined_ev", "total_edge"], ascending=False).reset_index(drop=True)
    return out
