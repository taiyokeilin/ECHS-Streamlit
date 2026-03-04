import streamlit as st
import pandas as pd
import gspread
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ECHS Pitcher Metrics",
    page_icon="⚾",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Barlow+Condensed:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Barlow Condensed', sans-serif; }
.stApp { background-color: #0d1117; color: #e6edf3; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.05em; }

.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-label {
    font-size: 0.95rem;
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
.metric-value.good    { color: #3fb950; }
.metric-value.neutral { color: #d29922; }
.metric-value.bad     { color: #f85149; }

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
    ws = gc.open_by_key(SHEET_ID).worksheet("By Game")
    df = pd.DataFrame(ws.get_all_records())
    df["game_date"] = pd.to_datetime(df["game_date"])
    num_cols = [c for c in df.columns if c not in ("pitcher", "pitch_type", "game_date", "opponent")]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    return df

df = load_data()

# ── Derived columns ───────────────────────────────────────────────────────────
def add_rates(d):
    d = d.copy()
    non_numeric = ["pitcher", "pitch_type", "game_date", "opponent"]
    for col in d.columns:
        if col not in non_numeric:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    d["oh_oh_win%"]    = (d["oh_oh_winners"]   / d["oh_oh_chances"].where(d["oh_oh_chances"] > 0) * 100).round(1)
    d["one_one_win%"]  = (d["one_one_winners"]  / d["one_one_chances"].where(d["one_one_chances"] > 0) * 100).round(1)
    d["all_lev_win%"]  = (d["all_lev_winners"]  / d["all_lev_chances"].where(d["all_lev_chances"] > 0) * 100).round(1)
    d["2k_cs%"]        = (d["two_strike_cs"]     / d["two_strike_chances"].where(d["two_strike_chances"] > 0) * 100).round(1)
    d["2k_whiff%"]     = (d["two_strike_whiffs"] / d["two_strike_chances"].where(d["two_strike_chances"] > 0) * 100).round(1)
    d["2k_csw%"]       = ((d["two_strike_cs"] + d["two_strike_whiffs"]) / d["two_strike_chances"].where(d["two_strike_chances"] > 0) * 100).round(1)
    d["k_per_pa"]      = (d["strikeouts"] / d["total_pa"].where(d["total_pa"] > 0) * 100).round(1)
    d["efficient_pa%"] = ((d["early_count_weak_contact"] + d["strikeouts"]) / d["total_pa"].where(d["total_pa"] > 0) * 100).round(1)
    d["weak_contact%"] = (d["early_count_weak_contact"] / d["total_pa"].where(d["total_pa"] > 0) * 100).round(1)
    return d

df = add_rates(df)

# ── Shared constants ──────────────────────────────────────────────────────────
sum_cols = ["oh_oh_chances","oh_oh_winners","one_one_chances","one_one_winners",
            "all_lev_chances","all_lev_winners","total_pa","early_count_weak_contact",
            "strikeouts","two_strike_chances","two_strike_cs","two_strike_whiffs"]

display_cols = {
    "pitcher":            "Pitcher",
    "oh_oh_chances":      "0-0 Chances",
    "oh_oh_winners":      "0-0 Winners",
    "oh_oh_win%":         "0-0 Win%",
    "one_one_chances":    "1-1 Chances",
    "one_one_winners":    "1-1 Winners",
    "one_one_win%":       "1-1 Win%",
    "all_lev_chances":    "All Lev. Chances",
    "all_lev_winners":    "All Lev. Winners",
    "all_lev_win%":       "All Lev. Win%",
    "two_strike_chances": "2K Chances",
    "two_strike_cs":      "2K CS",
    "two_strike_whiffs":  "2K Whiffs",
    "2k_csw%":            "2K CSW%",
    "strikeouts":         "K",
    "k_per_pa":           "K%",
    "weak_contact%":      "Weak Contact%",
    "efficient_pa%":      "Efficient PA%",
}

game_display_cols = {
    "game_date":          "Date",
    "opponent":           "Opponent",
    "oh_oh_chances":      "0-0 Chances",
    "oh_oh_winners":      "0-0 Winners",
    "oh_oh_win%":         "0-0 Win%",
    "one_one_chances":    "1-1 Chances",
    "one_one_winners":    "1-1 Winners",
    "one_one_win%":       "1-1 Win%",
    "all_lev_chances":    "All Lev. Chances",
    "all_lev_winners":    "All Lev. Winners",
    "all_lev_win%":       "All Lev. Win%",
    "two_strike_chances": "2K Chances",
    "two_strike_cs":      "2K CS",
    "two_strike_whiffs":  "2K Whiffs",
    "2k_csw%":            "2K CSW%",
    "strikeouts":         "K",
    "k_per_pa":           "K%",
    "weak_contact%":      "Weak Contact%",
    "efficient_pa%":      "Efficient PA%",
}

thresholds = {
    "0-0 Win%":      (65, 50),
    "1-1 Win%":      (65, 50),
    "All Lev. Win%": (65, 50),
    "2K CSW%":       (35, 25),
    "K%":            (25, 20),
    "Efficient PA%": (60, 50),
}

int_cols = ["K", "0-0 Chances", "0-0 Winners", "1-1 Chances", "1-1 Winners",
            "All Lev. Chances", "All Lev. Winners", "2K Chances", "2K CS", "2K Whiffs"]

# ── Shared helpers ────────────────────────────────────────────────────────────
def color_for(val, col_name):
    try:
        val = float(val)
    except (TypeError, ValueError):
        return ""
    if pd.isna(val):
        return ""
    if col_name not in thresholds:
        return ""
    green, yellow = thresholds[col_name]
    if val >= green:    return "#3fb950"
    elif val >= yellow: return "#d29922"
    else:               return "#f85149"

def fmt(val, col_name):
    if pd.isna(val):
        return "—"
    if col_name == "Date":
        try:
            return pd.Timestamp(val).strftime("%m/%d/%y")
        except:
            return str(val)
    if col_name in int_cols:
        try:
            return str(int(val))
        except:
            return str(val)
    if isinstance(val, float):
        return f"{val:.1f}"
    return str(val)

def build_html_table(df, freeze_col=True, total_row=False):
    cols = list(df.columns)
    header_cells = ""
    for i, c in enumerate(cols):
        sticky = 'style="position:sticky;left:0;z-index:2;background:#0d1117;white-space:nowrap;padding:0.4rem 0.75rem;"' if (i == 0 and freeze_col) else 'style="white-space:nowrap;padding:0.4rem 0.75rem;"'
        header_cells += f'<th {sticky}>{c}</th>'

    def make_row(row, is_total=False):
        cells = ""
        bg = "#1f2937" if is_total else "#161b22"
        border = "2px solid #58a6ff" if is_total else "1px solid #30363d"
        for i, c in enumerate(cols):
            val = row[c]
            color = color_for(val, c)
            color_style = f"color:{color};" if color else "color:#e6edf3;"
            if is_total:
                color_style += "font-weight:600;"
            sticky = f"position:sticky;left:0;z-index:1;background:{bg};" if (i == 0 and freeze_col) else f"background:{bg};"
            cells += f'<td style="{sticky}{color_style}padding:0.4rem 0.75rem;">{fmt(val, c)}</td>'
        return f'<tr style="border-top:{border};">{cells}</tr>'

    rows = ""
    for idx, (_, row) in enumerate(df.iterrows()):
        is_last = total_row and idx == len(df) - 1
        rows += make_row(row, is_total=is_last)

    return f"""
    <div style="overflow-x:auto; border-radius:8px; border:1px solid #30363d;">
    <table style="border-collapse:collapse; width:100%; font-family:'DM Mono',monospace; font-size:0.85rem;">
        <thead>
            <tr style="background:#0d1117; color:#8b949e; font-family:'Barlow Condensed',sans-serif;
                       font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em;">
                {header_cells}
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    </div>
    """

def summary_cards(totals_row):
    t_oh  = round(totals_row["oh_oh_winners"]  / totals_row["oh_oh_chances"]   * 100, 1) if totals_row["oh_oh_chances"]   else 0
    t_11  = round(totals_row["one_one_winners"] / totals_row["one_one_chances"] * 100, 1) if totals_row["one_one_chances"] else 0
    t_lev = round(totals_row["all_lev_winners"] / totals_row["all_lev_chances"] * 100, 1) if totals_row["all_lev_chances"] else 0
    t_fin = round((totals_row["two_strike_cs"] + totals_row["two_strike_whiffs"]) / totals_row["two_strike_chances"] * 100, 1) if totals_row["two_strike_chances"] else 0
    t_k   = round(totals_row["strikeouts"] / totals_row["total_pa"] * 100, 1) if totals_row["total_pa"] else 0
    t_eff = round((totals_row["early_count_weak_contact"] + totals_row["strikeouts"]) / totals_row["total_pa"] * 100, 1) if totals_row["total_pa"] else 0

    scols = st.columns(6)
    for col, label, val, thres in [
        (scols[0], "0-0 Win%",      f"{t_oh}%",  (65, 50)),
        (scols[1], "1-1 Win%",      f"{t_11}%",  (65, 50)),
        (scols[2], "All Lev. Win%", f"{t_lev}%", (65, 50)),
        (scols[3], "2K CSW%",       f"{t_fin}%", (35, 25)),
        (scols[4], "K%",            f"{t_k}%",   (25, 20)),
        (scols[5], "Efficient PA%", f"{t_eff}%", (60, 50)),
    ]:
        v = float(val.replace("%", ""))
        cls = "good" if v >= thres[0] else ("neutral" if v >= thres[1] else "bad")
        col.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>{label}</div>
            <div class='metric-value {cls}'>{val}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── Filter to "All" pitch type only ──────────────────────────────────────────
df_all = df[df["pitch_type"] == "All"].copy()
all_pitchers = sorted(df_all["pitcher"].unique().tolist())

# ── Routing via query params ──────────────────────────────────────────────────
params = st.query_params
current_pitcher = params.get("pitcher", None)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME — Season totals
# ══════════════════════════════════════════════════════════════════════════════
if current_pitcher is None:

    season = df_all.groupby("pitcher")[sum_cols].sum().reset_index()
    season = add_rates(season)

    st.markdown("# ⚾ ECHS Pitcher Metrics")
    st.markdown(f"<div class='section-header'>Season Totals · {len(season)} Pitchers · click a name to view game log</div>",
                unsafe_allow_html=True)

    totals = season[sum_cols].sum()
    summary_cards(totals)

    st.markdown("<div class='section-header'>Per-Pitcher Breakdown</div>", unsafe_allow_html=True)

    table = (season[list(display_cols.keys())]
             .rename(columns=display_cols)
             .sort_values("0-0 Chances", ascending=False)
             .reset_index(drop=True))

    # Build table with clickable pitcher names
    def build_html_table_with_links(df):
        cols = list(df.columns)
        header_cells = ""
        for i, c in enumerate(cols):
            sticky = 'style="position:sticky;left:0;z-index:2;background:#0d1117;white-space:nowrap;padding:0.4rem 0.75rem;"' if i == 0 else 'style="white-space:nowrap;padding:0.4rem 0.75rem;"'
            header_cells += f'<th {sticky}>{c}</th>'

        rows = ""
        for _, row in df.iterrows():
            cells = ""
            for i, c in enumerate(cols):
                val = row[c]
                color = color_for(val, c)
                color_style = f"color:{color};" if color else "color:#e6edf3;"
                sticky = "position:sticky;left:0;z-index:1;background:#161b22;" if i == 0 else "background:#161b22;"
                if i == 0:
                    # Make pitcher name a link
                    encoded = str(val).replace(" ", "+")
                    cell_content = f'<a href="?pitcher={encoded}" style="color:#58a6ff;text-decoration:none;font-weight:600;">{val}</a>'
                else:
                    cell_content = fmt(val, c)
                cells += f'<td style="{sticky}{color_style}padding:0.4rem 0.75rem;">{cell_content}</td>'
            rows += f'<tr style="border-top:1px solid #30363d;">{cells}</tr>'

        return f"""
        <div style="overflow-x:auto; border-radius:8px; border:1px solid #30363d;">
        <table style="border-collapse:collapse; width:100%; font-family:'DM Mono',monospace; font-size:0.85rem;">
            <thead>
                <tr style="background:#0d1117; color:#8b949e; font-family:'Barlow Condensed',sans-serif;
                           font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em;">
                    {header_cells}
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        </div>
        """

    st.markdown(build_html_table_with_links(table), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PITCHER — Game-by-game log
# ══════════════════════════════════════════════════════════════════════════════
else:
    pitcher = current_pitcher.replace("+", " ")

    # Sidebar pitcher switcher
    with st.sidebar:
        st.markdown("## ⚾ Pitchers")
        for p in all_pitchers:
            encoded = p.replace(" ", "+")
            is_active = p == pitcher
            color = "#58a6ff" if is_active else "#8b949e"
            weight = "700" if is_active else "400"
            st.markdown(
                f'<a href="?pitcher={encoded}" style="display:block;color:{color};font-weight:{weight};'
                f'font-family:Barlow Condensed,sans-serif;font-size:1rem;text-transform:uppercase;'
                f'letter-spacing:0.05em;text-decoration:none;padding:0.3rem 0;'
                f'border-left:{"3px solid #58a6ff" if is_active else "3px solid transparent"};'
                f'padding-left:0.75rem;margin-bottom:0.25rem;">{p}</a>',
                unsafe_allow_html=True
            )
        st.markdown("---")
        st.markdown(
            '<a href="/" style="color:#8b949e;font-family:Barlow Condensed,sans-serif;'
            'font-size:0.8rem;text-transform:uppercase;letter-spacing:0.08em;text-decoration:none;">'
            '← Season Overview</a>',
            unsafe_allow_html=True
        )

    if pitcher not in all_pitchers:
        st.error(f"Pitcher '{pitcher}' not found.")
        st.stop()

    # ── Data for this pitcher ─────────────────────────────────────────────────
    pitcher_df = df_all[df_all["pitcher"] == pitcher].sort_values("game_date").reset_index(drop=True)
    pitcher_df = add_rates(pitcher_df)
    totals = pitcher_df[sum_cols].sum()

    # ── Header row: title + radar chart ──────────────────────────────────────
    title_col, radar_col = st.columns([3, 2])

    with title_col:
        st.markdown(f"# ⚾ {pitcher}")

        # View toggle
        if "pitcher_view" not in st.session_state:
            st.session_state.pitcher_view = "by_game"

        col_btn1, col_btn2, col_btn3, _ = st.columns([1, 1.4, 1, 5])
        with col_btn1:
            if st.button("By Game", type="primary" if st.session_state.pitcher_view == "by_game" else "secondary"):
                st.session_state.pitcher_view = "by_game"
                st.rerun()
        with col_btn2:
            if st.button("By Pitch Type", type="primary" if st.session_state.pitcher_view == "by_pitch_type" else "secondary"):
                st.session_state.pitcher_view = "by_pitch_type"
                st.rerun()
        with col_btn3:
            if st.button("Graph", type="primary" if st.session_state.pitcher_view == "graph" else "secondary"):
                st.session_state.pitcher_view = "graph"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        summary_cards(totals)

    with radar_col:
        # Radar chart — normalize each metric to 0-100 scale based on reasonable max
        radar_metrics = {
            "0-0 Win%":      ("oh_oh_win%",    100),
            "1-1 Win%":      ("one_one_win%",   100),
            "All Lev. Win%": ("all_lev_win%",   100),
            "Eff. PA%":      ("efficient_pa%",  100),
            "2K CSW%":       ("2k_csw%",         70),
        }

        season_rates = add_rates(pd.DataFrame([totals])).iloc[0]

        labels = list(radar_metrics.keys())
        values = []
        for label, (raw, max_val) in radar_metrics.items():
            v = season_rates.get(raw, 0)
            if pd.isna(v):
                v = 0
            values.append(round(min(float(v) / max_val * 100, 100), 1))

        # Close the polygon
        labels_closed = labels + [labels[0]]
        values_closed = values + [values[0]]

        radar_fig = go.Figure()
        radar_fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=labels_closed,
            fill="toself",
            fillcolor="rgba(88, 166, 255, 0.15)",
            line=dict(color="#58a6ff", width=2),
            marker=dict(color="#58a6ff", size=6),
            hovertemplate="%{theta}<br>%{r:.0f}/100<extra></extra>",
        ))
        radar_fig.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            polar=dict(
                bgcolor="#161b22",
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    showticklabels=False,
                    gridcolor="#30363d",
                    linecolor="#30363d",
                ),
                angularaxis=dict(
                    tickfont=dict(family="Barlow Condensed, sans-serif", size=13, color="#e6edf3"),
                    linecolor="#30363d",
                    gridcolor="#30363d",
                ),
            ),
            margin=dict(l=40, r=40, t=40, b=40),
            height=300,
            showlegend=False,
        )
        st.plotly_chart(radar_fig, use_container_width=True)

    view = st.session_state.pitcher_view

    # ── Columns through 2K CSW% only (for both views) ────────────────────────
    pitch_display_cols = {
        "oh_oh_chances":      "0-0 Chances",
        "oh_oh_winners":      "0-0 Winners",
        "oh_oh_win%":         "0-0 Win%",
        "one_one_chances":    "1-1 Chances",
        "one_one_winners":    "1-1 Winners",
        "one_one_win%":       "1-1 Win%",
        "all_lev_chances":    "All Lev. Chances",
        "all_lev_winners":    "All Lev. Winners",
        "all_lev_win%":       "All Lev. Win%",
        "two_strike_chances": "2K Chances",
        "two_strike_cs":      "2K CS",
        "two_strike_whiffs":  "2K Whiffs",
        "2k_csw%":            "2K CSW%",
    }

    def build_totals_row(source_df, first_col_name, first_col_val, col_map):
        rates = add_rates(pd.DataFrame([source_df[sum_cols].sum()]))[
            ["oh_oh_win%","one_one_win%","all_lev_win%","2k_csw%","k_per_pa","efficient_pa%","weak_contact%"]
        ].iloc[0]
        row = {first_col_name: first_col_val}
        for raw, display in col_map.items():
            if raw in sum_cols:
                row[display] = source_df[sum_cols].sum()[raw]
            elif raw in rates.index:
                row[display] = rates[raw]
            else:
                row[display] = float("nan")
        return pd.DataFrame([row])

    # ── BY GAME ───────────────────────────────────────────────────────────────
    if view == "by_game":
        st.markdown("<div class='section-header'>Game Log — All Pitches</div>", unsafe_allow_html=True)

        game_cols = {"game_date": "Date", "opponent": "Opponent", **{k: v for k, v in game_display_cols.items() if k not in ("game_date", "opponent")}}
        game_table = pitcher_df[list(game_cols.keys())].rename(columns=game_cols).copy()
        totals_row = build_totals_row(pitcher_df, "Date", "SEASON", {"opponent": "Opponent", **{k: v for k, v in game_display_cols.items() if k not in ("game_date", "opponent")}})
        totals_row["Opponent"] = ""
        full_table = pd.concat([game_table, totals_row], ignore_index=True)
        st.markdown(build_html_table(full_table, freeze_col=True, total_row=True), unsafe_allow_html=True)

    # ── BY PITCH TYPE ─────────────────────────────────────────────────────────
    elif view == "by_pitch_type":
        st.markdown("<div class='section-header'>Season Totals by Pitch Type</div>", unsafe_allow_html=True)

        pitch_type_order = ["FF", "CB", "SL", "CH"]
        df_pitcher_all_types = df[df["pitcher"] == pitcher].copy()
        df_pitcher_all_types = add_rates(df_pitcher_all_types)

        pitch_rows = []
        for pt in pitch_type_order:
            pt_df = df_pitcher_all_types[df_pitcher_all_types["pitch_type"] == pt]
            if pt_df.empty:
                continue
            pt_totals = pt_df[sum_cols].sum()
            pt_rates = add_rates(pd.DataFrame([pt_totals])).iloc[0]
            row = {"Pitch": pt}
            for raw, display in pitch_display_cols.items():
                if raw in sum_cols:
                    row[display] = pt_totals[raw]
                elif raw in pt_rates.index:
                    row[display] = pt_rates[raw]
                else:
                    row[display] = float("nan")
            pitch_rows.append(row)

        if pitch_rows:
            pitch_table = pd.DataFrame(pitch_rows)
            all_df = df_pitcher_all_types[df_pitcher_all_types["pitch_type"] == "All"]
            totals_row = build_totals_row(all_df, "Pitch", "SEASON", pitch_display_cols)
            full_pitch_table = pd.concat([pitch_table, totals_row], ignore_index=True)
            st.markdown(build_html_table(full_pitch_table, freeze_col=True, total_row=True), unsafe_allow_html=True)
        else:
            st.info("No pitch type data available for this pitcher.")

    # ── GRAPH ─────────────────────────────────────────────────────────────────
    elif view == "graph":
        st.markdown("<div class='section-header'>Game-by-Game Trends — All Pitches</div>", unsafe_allow_html=True)

        chart_metrics = {
            "0-0 Win%":      "oh_oh_win%",
            "1-1 Win%":      "one_one_win%",
            "All Lev. Win%": "all_lev_win%",
            "2K CSW%":       "2k_csw%",
            "Efficient PA%": "efficient_pa%",
        }

        metric_colors = {
            "0-0 Win%":      "#58a6ff",
            "1-1 Win%":      "#3fb950",
            "All Lev. Win%": "#d29922",
            "2K CSW%":       "#f78166",
            "Efficient PA%": "#bc8cff",
        }

        selected_metrics = st.multiselect(
            "Select metrics to display",
            options=list(chart_metrics.keys()),
            default=list(chart_metrics.keys()),
        )

        if not selected_metrics:
            st.info("Select at least one metric above.")
        else:
            graph_df = pitcher_df.copy()
            graph_df["date_label"] = graph_df["game_date"].dt.strftime("%m/%d")
            x_labels = graph_df["date_label"] + " vs " + graph_df["opponent"]

            fig = go.Figure()
            for metric in selected_metrics:
                raw_col = chart_metrics[metric]
                color = metric_colors[metric]
                fig.add_trace(go.Scatter(
                    x=x_labels,
                    y=graph_df[raw_col],
                    mode="lines+markers",
                    name=metric,
                    line=dict(color=color, width=2),
                    marker=dict(color=color, size=7),
                    hovertemplate=f"<b>{metric}</b><br>%{{x}}<br>%{{y:.1f}}%<extra></extra>",
                ))

            fig.update_layout(
                paper_bgcolor="#0d1117",
                plot_bgcolor="#0d1117",
                font=dict(family="Barlow Condensed, sans-serif", color="#e6edf3"),
                legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1, font=dict(size=13)),
                xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(family="DM Mono, monospace", size=11, color="#8b949e"), linecolor="#30363d"),
                yaxis=dict(showgrid=True, gridcolor="#21262d", ticksuffix="%", tickfont=dict(family="DM Mono, monospace", size=11, color="#8b949e"), linecolor="#30363d", rangemode="tozero"),
                hovermode="x unified",
                margin=dict(l=40, r=20, t=20, b=80),
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True)
