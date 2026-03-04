import streamlit as st
import pandas as pd

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pitcher Metrics",
    page_icon="⚾",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Barlow+Condensed:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow Condensed', sans-serif;
}
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}
h1, h2, h3 {
    font-family: 'Barlow Condensed', sans-serif;
    letter-spacing: 0.05em;
}
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #8b949e;
    margin-bottom: 0.25rem;
}
.metric-value {
    font-family: 'DM Mono', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: #58a6ff;
}
.metric-value.good { color: #3fb950; }
.metric-value.neutral { color: #d29922; }
.stDataFrame { font-family: 'DM Mono', monospace; font-size: 0.85rem; }
div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b949e;
}
.section-header {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #8b949e;
    border-bottom: 1px solid #30363d;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# TO CONNECT TO GOOGLE SHEETS:
# 1. Share your sheet with a service account email (see README)
# 2. Uncomment the block below and fill in your SHEET_ID
# 3. Add credentials to .streamlit/secrets.toml
# ─────────────────────────────────────────────────────────────────────────────
import gspread
from google.oauth2.service_account import Credentials

# @st.cache_data(ttl=300)
# def load_data():
#     SHEET_ID = "1lqt0Wnl86S8PYsq7a-PwUD7uYx1Y9RrXhojZjjY1Ua8"
#     creds = Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"],
#         scopes=["https://spreadsheets.google.com/feeds",
#                 "https://www.googleapis.com/auth/drive"],
#     )
#     gc = gspread.authorize(creds)
#     ws = gc.open_by_key(SHEET_ID).worksheet("test")
#     df = pd.DataFrame(ws.get_all_records())
#     df["game_date"] = pd.to_datetime(df["game_date"])
#     num_cols = [c for c in df.columns if c not in ("pitcher", "pitch_type", "game_date", "opponent")]
#     df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
#     return df


@st.cache_data(ttl=300)
def load_data():
    SHEET_ID = "1lqt0Wnl86S8PYsq7a-PwUD7uYx1Y9RrXhojZjjY1Ua8"
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"],
    )
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(SHEET_ID).worksheet("test")
    df = pd.DataFrame(ws.get_all_records())
    df["game_date"] = pd.to_datetime(df["game_date"])
    num_cols = [c for c in df.columns if c not in ("pitcher", "pitch_type", "game_date", "opponent")]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    return df

# @st.cache_data
# def load_data():
#     """Local CSV fallback — replace with Google Sheets loader above when ready."""
#     df = pd.read_csv("lev_test.csv")
#     df["game_date"] = pd.to_datetime(df["game_date"])
#     # Coerce numeric columns
#     num_cols = [c for c in df.columns if c not in ("pitcher", "pitch_type", "game_date", "opponent")]
#     df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
#     return df

df = load_data()

# ── Derived columns ───────────────────────────────────────────────────────────
def add_rates(d):
    d = d.copy()
    # Force all columns except identifiers to numeric
    non_numeric = ["pitcher", "pitch_type", "game_date", "opponent"]
    for col in d.columns:
        if col not in non_numeric:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    
    d["oh_oh_win%"]    = (d["oh_oh_winners"]    / d["oh_oh_chances"].where(d["oh_oh_chances"] > 0) * 100).round(1)
    d["one_one_win%"]  = (d["one_one_winners"]   / d["one_one_chances"].where(d["one_one_chances"] > 0) * 100).round(1)
    d["all_lev_win%"]  = (d["all_lev_winners"]   / d["all_lev_chances"].where(d["all_lev_chances"] > 0) * 100).round(1)
    d["2k_cs%"]        = (d["two_strike_cs"]      / d["two_strike_chances"].where(d["two_strike_chances"] > 0) * 100).round(1)
    d["2k_whiff%"]     = (d["two_strike_whiffs"]  / d["two_strike_chances"].where(d["two_strike_chances"] > 0) * 100).round(1)
    d["2k_csw%"]    = ((d["two_strike_cs"] + d["two_strike_whiffs"]) / d["two_strike_chances"].where(d["two_strike_chances"] > 0) * 100).round(1)
    d["k_per_pa"]      = (d["strikeouts"] / d["total_pa"].where(d["total_pa"] > 0) * 100).round(1)
    d["efficient_pa%"] = ((d["early_count_weak_contact"] + d["strikeouts"]) / d["total_pa"] * 100).round(1)
    d["weak_contact%"] = (d["early_count_weak_contact"] / d["total_pa"].where(d["total_pa"] > 0) * 100).round(1)
    return d

df = add_rates(df)

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚾ Filters")

    all_pitchers = sorted(df["pitcher"].unique())
    sel_pitchers = st.selectbox("Pitcher", ["All Pitchers"] + all_pitchers)

    pitch_type_order = ["All", "FF", "CB", "SL", "CH"]
    all_types = [p for p in pitch_type_order if p in df["pitch_type"].values]
    sel_type = st.selectbox("Pitch Type", all_types)

    all_opps = ["All Opponents"] + sorted(df["opponent"].unique())
    sel_opp = st.selectbox("Opponent", all_opps)

    st.markdown("---")
    st.caption("Data refreshes every 5 min when connected to Google Sheets.")

# ── Filter data ───────────────────────────────────────────────────────────────
filtered = df[df["pitch_type"] == sel_type]
if sel_pitchers != "All Pitchers":
    filtered = filtered[filtered["pitcher"] == sel_pitchers]
if sel_opp != "All Opponents":
    filtered = filtered[filtered["opponent"] == sel_opp]

# ── Season totals ─────────────────────────────────────────────────────────────
sum_cols  = ["oh_oh_chances","oh_oh_winners","one_one_chances","one_one_winners",
             "all_lev_chances","all_lev_winners","total_pa","early_count_weak_contact",
             "strikeouts","two_strike_chances","two_strike_cs","two_strike_whiffs"]
season = (
    filtered.groupby("pitcher")[sum_cols]
    .sum()
    .reset_index()
)
season = add_rates(season)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# ⚾ ECHS Pitcher Metrics Dashboard")
st.markdown(f"<div class='section-header'>Season Totals · Pitch Type: {sel_type} · {len(season)} pitchers</div>",
            unsafe_allow_html=True)

# ── Fleet-level summary cards ─────────────────────────────────────────────────
if not season.empty:
    totals = season[sum_cols].sum()
    t_oh   = round(totals["oh_oh_winners"]   / totals["oh_oh_chances"]   * 100, 1) if totals["oh_oh_chances"]   else 0
    t_11   = round(totals["one_one_winners"]  / totals["one_one_chances"] * 100, 1) if totals["one_one_chances"] else 0
    t_lev  = round(totals["all_lev_winners"]  / totals["all_lev_chances"] * 100, 1) if totals["all_lev_chances"] else 0
    t_fin  = round((totals["two_strike_cs"] + totals["two_strike_whiffs"])
                   / totals["two_strike_chances"] * 100, 1) if totals["two_strike_chances"] else 0
    t_k    = round(totals["strikeouts"] / totals["total_pa"] * 100, 1) if totals["total_pa"] else 0
    t_eff = round((totals["early_count_weak_contact"] + totals["strikeouts"]) / totals["total_pa"] * 100, 1) if totals["total_pa"] else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    for col, label, val, cls in [
        (c1, "0-0 Win%",       f"{t_oh}%",  "good" if t_oh  >= 55 else "neutral"),
        (c2, "1-1 Win%",       f"{t_11}%",  "good" if t_11  >= 50 else "neutral"),
        (c3, "All Leverage Win%",   f"{t_lev}%", "good" if t_lev >= 50 else "neutral"),
        (c4, "2-Strike CSW%",f"{t_fin}%","good" if t_fin >= 30 else "neutral"),
        (c5, "K%",             f"{t_k}%",   "good" if t_k   >= 20 else "neutral"),
        (c6, "Efficient PA%", f"{t_eff}%", "good" if t_eff >= 70 else "neutral")
    ]:
        col.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>{label}</div>
            <div class='metric-value {cls}'>{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# ── Per-pitcher season table ──────────────────────────────────────────────────
st.markdown("<div class='section-header'>Per-Pitcher Breakdown</div>", unsafe_allow_html=True)

display_cols = {
    "pitcher":            "Pitcher",
    "oh_oh_chances":      "0-0 Chances",
    "oh_oh_winners":      "0-0 Winners",
    "oh_oh_win%":         "0-0 Win%",
    "one_one_chances":    "1-1 Chances",
    "one_one_winners":    "1-1 Winners",
    "one_one_win%":       "1-1 Win%",
    "all_lev_chances":    "All Leverage Chances",
    "all_lev_winners":    "All Leverage Winners",
    "all_lev_win%":       "All Leverage Win%",
    "strikeouts":         "K",
    "k_per_pa":           "K%",
    "two_strike_chances": "2K Chances",
    "2k_csw%":            "2K CSW%",
    "2k_cs%":             "2K CS%",
    "2k_whiff%":          "2K Whiff%",
    "efficient_pa%":      "Efficient PA%",
    "weak_contact%":      "Weak Contact%",
}

table = season[list(display_cols.keys())].rename(columns=display_cols)

# Color map helpers
def highlight_pct(val):
    if pd.isna(val):
        return ""
    if isinstance(val, float) and val >= 50:
        return "color: #3fb950"
    return ""

styled = (
    table.style
    .format({
        "0-0 Win%":           "{:.1f}",
        "1-1 Win%":           "{:.1f}",
        "All Leverage Win%":  "{:.1f}",
        "K":                  "{:.0f}",
        "K%":                 "{:.1f}",
        "2K CSW%":            "{:.1f}",
        "2K CS%":             "{:.1f}",
        "2K Whiff%":          "{:.1f}",
        "Efficient PA%":      "{:.1f}",
        "Weak Contact%":      "{:.1f}",
    }, na_rep="—")
    .applymap(highlight_pct, subset=["0-0 Win%","1-1 Win%","All Leverage Win%","2K CSW%"])
    .set_properties(**{"background-color": "#161b22", "border-color": "#30363d"})
    .set_table_styles([
        {"selector": "th", "props": [("background-color","#0d1117"),
                                      ("color","#8b949e"),
                                      ("font-size","0.72rem"),
                                      ("text-transform","uppercase"),
                                      ("letter-spacing","0.08em")]},
    ])
)

st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Raw game log ──────────────────────────────────────────────────────────────
with st.expander("📋 Raw Game Log"):
    st.dataframe(
        filtered.sort_values("game_date", ascending=False)
                .reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
