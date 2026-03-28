# DraftKings Value Finder

A Streamlit app that compares DraftKings lines against broader sportsbook consensus to identify potentially undervalued betting lines and simple parlay ideas.

## Features
- Pulls live odds from The Odds API
- Filters to DraftKings lines
- Compares DraftKings against other books
- Estimates fair probability by removing vig on two-way markets
- Ranks straight bets by edge and expected value
- Builds basic parlay ideas from the strongest legs on different events

## Setup
1. Clone this repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
