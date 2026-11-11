from html import escape
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import settings
from src.core.exceptions import RateLimitExceededError, RiotAPIError
from src.services.match_workflows import (
    rebuild_analysis_reports,
    synchronize_matches,
    validate_local_data,
)
from src.visualization.theme import (
    ACCENT_COLOR,
    BACKGROUND_COLOR,
    CYBER_PALETTE,
    MUTED_TEXT_COLOR,
    PANEL_COLOR,
    TEXT_COLOR,
    register_plotly_template,
)

REPORT_PATH = settings.DATA_DIR / "processed" / "matches.csv"
REQUIRED_COLUMNS = {
    "played_at_utc",
    "calendar_month",
    "game_version",
    "queue_id",
    "champion",
    "team_position",
    "win",
    "kills",
    "deaths",
    "assists",
    "kda_ratio",
    "cs_per_minute",
    "champion_damage",
    "vision_score",
    "duration_minutes",
}
QUEUE_LABELS = {
    400: "Draft Pick",
    420: "Ranked Solo/Duo",
    440: "Ranked Flex",
    450: "ARAM",
    1700: "Arena",
}

st.set_page_config(
    page_title="Nexus Metrics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
register_plotly_template()


@st.cache_data(show_spinner=False, ttl=300)
def load_match_table(
    report_path: str, modified_time_ns: int, file_size: int
) -> pd.DataFrame:
    del modified_time_ns, file_size
    frame = pd.read_csv(report_path)
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            "The match report is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    frame["played_at_utc"] = pd.to_datetime(
        frame["played_at_utc"], utc=True, errors="coerce"
    )
    frame["win"] = (
        frame["win"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .map({"true": True, "1": True, "yes": True, "false": False, "0": False, "no": False})
    )
    numeric_columns = [
        "queue_id",
        "kills",
        "deaths",
        "assists",
        "kda_ratio",
        "cs_per_minute",
        "champion_damage",
        "vision_score",
        "duration_minutes",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(subset=["played_at_utc", "win", "champion"])
    frame["queue_label"] = frame["queue_id"].map(
        lambda queue_id: QUEUE_LABELS.get(
            int(queue_id), f"Queue {int(queue_id)}")
        if pd.notna(queue_id)
        else "Unknown queue"
    )
    return frame.sort_values("played_at_utc", ascending=False).reset_index(drop=True)


def _inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --nexus-bg: {BACKGROUND_COLOR};
            --nexus-panel: {PANEL_COLOR};
            --nexus-cyan: {ACCENT_COLOR};
            --nexus-text: {TEXT_COLOR};
            --nexus-muted: {MUTED_TEXT_COLOR};
            --nexus-pink: {CYBER_PALETTE[5]};
        }}
        .stApp {{
            background:
                radial-gradient(ellipse at 12% 0%, rgba(0,229,255,.09), transparent 35%),
                radial-gradient(ellipse at 92% 4%, rgba(255,0,127,.08), transparent 29%),
                var(--nexus-bg);
            color: var(--nexus-text);
            font-family: Inter, Segoe UI, sans-serif;
        }}
        [data-testid="stHeader"] {{ background: rgba(13,14,21,.72); }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #11131f 0%, #0d0e15 100%);
            border-right: 1px solid rgba(0,229,255,.16);
        }}
        [data-testid="stMetric"] {{
            background: linear-gradient(145deg, rgba(20,21,33,.96), rgba(15,17,27,.96));
            border: 1px solid rgba(0,229,255,.20);
            border-radius: 14px;
            padding: 17px 19px;
            box-shadow: 0 0 22px rgba(0,229,255,.045);
        }}
        [data-testid="stMetricLabel"] p {{ color: var(--nexus-muted); text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; }}
        [data-testid="stMetricValue"] {{ color: var(--nexus-text); font-family: Bahnschrift Condensed, 'Arial Narrow', sans-serif; }}
        .nexus-eyebrow {{ color: var(--nexus-cyan); font-size: .74rem; font-weight: 700; letter-spacing: .24em; text-transform: uppercase; }}
        .nexus-title {{ font-family: Bahnschrift Condensed, 'Arial Narrow', Impact, sans-serif; font-size: clamp(3.2rem, 8vw, 6.2rem); line-height: .91; font-weight: 800; letter-spacing: .035em; margin: .25rem 0 .7rem; text-shadow: 0 0 26px rgba(0,229,255,.21); }}
        .nexus-title span {{ color: var(--nexus-cyan); }}
        .nexus-subtitle {{ color: var(--nexus-muted); font-size: 1rem; max-width: 720px; }}
        .nexus-section {{ font-family: Bahnschrift Condensed, 'Arial Narrow', sans-serif; letter-spacing: .08em; text-transform: uppercase; border-left: 3px solid var(--nexus-cyan); padding-left: .65rem; margin: .4rem 0 1rem; }}
        .nexus-note {{ border: 1px solid rgba(0,229,255,.2); border-radius: 12px; padding: .9rem 1rem; background: rgba(20,21,33,.72); color: var(--nexus-muted); }}
        div.stButton > button {{
            border: 1px solid rgba(0,229,255,.52);
            background: linear-gradient(100deg, rgba(0,229,255,.15), rgba(138,43,226,.14));
            color: var(--nexus-text);
            border-radius: 9px;
            font-weight: 700;
            transition: all .16s ease-in-out;
        }}
        div.stButton > button:hover {{ border-color: var(--nexus-cyan); box-shadow: 0 0 18px rgba(0,229,255,.18); color: white; }}
        div[data-baseweb="tab-list"] {{ gap: .4rem; }}
        button[data-baseweb="tab"] {{ border-radius: 8px 8px 0 0; }}
        [data-testid="stDataFrame"] {{ border: 1px solid rgba(0,229,255,.16); border-radius: 10px; }}
        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _load_reports() -> Optional[pd.DataFrame]:
    if not REPORT_PATH.is_file():
        return None
    try:
        stat = REPORT_PATH.stat()
        return load_match_table(str(REPORT_PATH), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        st.error(f"Could not load the local match report: {error}")
        return None


def _format_date_range(frame: pd.DataFrame) -> str:
    earliest = frame["played_at_utc"].min().strftime("%d %b %Y")
    latest = frame["played_at_utc"].max().strftime("%d %b %Y")
    return f"{earliest} — {latest} UTC"


def _filter_matches(frame: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown("<div class='nexus-eyebrow'>Match filters</div>",
                    unsafe_allow_html=True)
        min_date = frame["played_at_utc"].min().date()
        max_date = frame["played_at_utc"].max().date()
        date_value = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
        )
        queue_options = sorted(frame["queue_label"].dropna().unique().tolist())
        selected_queues = st.multiselect("Queue", queue_options)
        position_options = sorted(
            frame["team_position"].dropna().unique().tolist())
        selected_positions = st.multiselect("Position", position_options)
        champion_options = sorted(frame["champion"].dropna().unique().tolist())
        selected_champions = st.multiselect("Champion", champion_options)

    if isinstance(date_value, tuple) and len(date_value) == 2:
        date_start, date_end = date_value
    else:
        date_start = date_end = date_value

    played_dates = frame["played_at_utc"].dt.date
    mask = played_dates.between(date_start, date_end)
    if selected_queues:
        mask &= frame["queue_label"].isin(selected_queues)
    if selected_positions:
        mask &= frame["team_position"].isin(selected_positions)
    if selected_champions:
        mask &= frame["champion"].isin(selected_champions)
    return frame.loc[mask].copy()


def _render_kpis(frame: pd.DataFrame) -> None:
    match_count = len(frame)
    wins = int(frame["win"].sum()) if match_count else 0
    win_rate = wins / match_count * 100 if match_count else 0.0
    total_deaths = int(frame["deaths"].sum()) if match_count else 0
    aggregate_kda = (
        (int(frame["kills"].sum()) +
         int(frame["assists"].sum())) / total_deaths
        if total_deaths
        else 0.0
    )
    average_duration = frame["duration_minutes"].mean() if match_count else 0.0

    columns = st.columns(4)
    columns[0].metric("Matches", f"{match_count:,}")
    columns[1].metric("Win rate", f"{win_rate:.1f}%",
                      f"{wins} W / {match_count - wins} L")
    columns[2].metric("Aggregate KDA", f"{aggregate_kda:.2f}")
    columns[3].metric("Avg. duration", f"{average_duration:.1f} min")


def _render_overview(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No matches match the selected filters.")
        return

    monthly = (
        frame.assign(month=frame["played_at_utc"].dt.strftime("%Y-%m"))
        .groupby("month", as_index=False)
        .agg(matches=("win", "size"), win_rate=("win", "mean"), avg_kda=("kda_ratio", "mean"))
    )
    month_index = pd.PeriodIndex(monthly["month"], freq="M")
    all_months = pd.period_range(
        month_index.min(), month_index.max(), freq="M")
    monthly = (
        monthly.drop(columns="month")
        .set_axis(month_index)
        .reindex(all_months)
        .rename_axis("month")
        .reset_index()
    )
    monthly["month"] = monthly["month"].astype(str)
    monthly["matches"] = monthly["matches"].fillna(0).astype(int)
    monthly["win_rate_pct"] = monthly["win_rate"] * 100

    left, right = st.columns([1.55, 1])
    with left:
        figure = px.line(
            monthly,
            x="month",
            y="win_rate_pct",
            markers=True,
            hover_data={"matches": True,
                        "avg_kda": ":.2f", "win_rate_pct": ":.1f"},
            labels={"month": "Month", "win_rate_pct": "Win rate (%)"},
            title="Win rate over time",
        )
        figure.add_hline(y=50, line_dash="dot",
                         line_color="#8A94A8", opacity=0.6)
        figure.update_traces(
            line={"width": 3}, marker={"size": 9}, connectgaps=False
        )
        figure.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(figure, width="stretch")
    with right:
        monthly_counts = px.bar(
            monthly,
            x="month",
            y="matches",
            color="matches",
            color_continuous_scale=["#1E2035", ACCENT_COLOR, CYBER_PALETTE[2]],
            labels={"month": "Month", "matches": "Matches"},
            title="Activity by month",
        )
        monthly_counts.update_layout(coloraxis_showscale=False)
        st.plotly_chart(monthly_counts, width="stretch")

    role_metrics = (
        frame.groupby("team_position", as_index=False)
        .agg(matches=("win", "size"), win_rate=("win", "mean"), avg_vision=("vision_score", "mean"))
        .sort_values("matches", ascending=False)
    )
    role_metrics["win_rate_pct"] = role_metrics["win_rate"] * 100
    role_figure = px.bar(
        role_metrics,
        x="team_position",
        y="win_rate_pct",
        color="team_position",
        text="matches",
        hover_data={"avg_vision": ":.1f", "matches": True},
        labels={"team_position": "Position", "win_rate_pct": "Win rate (%)"},
        title="Win rate by position · match count shown on bars",
    )
    role_figure.update_traces(textposition="outside")
    role_figure.update_yaxes(range=[0, 100], ticksuffix="%")
    st.plotly_chart(role_figure, width="stretch")


def _render_champions_and_roles(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No matches match the selected filters.")
        return

    st.markdown("### Champion performance")
    minimum_games = st.slider(
        "Minimum games per champion",
        min_value=1,
        max_value=max(1, min(30, int(frame["champion"].value_counts().max()))),
        value=min(5, max(1, int(frame["champion"].value_counts().max()))),
    )
    champion_stats = (
        frame.groupby("champion", as_index=False)
        .agg(matches=("win", "size"), wins=("win", "sum"), win_rate=("win", "mean"), avg_kda=("kda_ratio", "mean"), avg_cs=("cs_per_minute", "mean"))
    )
    champion_stats = champion_stats[champion_stats["matches"] >= minimum_games]
    if champion_stats.empty:
        st.info("No champions meet this minimum sample size.")
    else:
        champion_stats["win_rate_pct"] = champion_stats["win_rate"] * 100
        champion_stats = champion_stats.sort_values(
            "matches", ascending=True).tail(20)
        chart = px.bar(
            champion_stats,
            x="win_rate_pct",
            y="champion",
            orientation="h",
            color="win_rate_pct",
            color_continuous_scale=[CYBER_PALETTE[3],
                                    CYBER_PALETTE[1], CYBER_PALETTE[4]],
            text="matches",
            hover_data={"wins": True, "avg_kda": ":.2f", "avg_cs": ":.2f"},
            labels={"win_rate_pct": "Win rate (%)", "champion": "Champion"},
            title="Top 20 champions by games · count shown on bars",
        )
        chart.update_layout(coloraxis_showscale=False)
        st.plotly_chart(chart, width="stretch")

    left, right = st.columns(2)
    with left:
        role_stats = (
            frame.groupby("team_position", as_index=False)
            .agg(matches=("win", "size"), win_rate=("win", "mean"), avg_cs=("cs_per_minute", "mean"))
            .sort_values("matches", ascending=False)
        )
        role_stats["win_rate_pct"] = role_stats["win_rate"] * 100
        role_chart = px.bar(
            role_stats,
            x="team_position",
            y="win_rate_pct",
            color="team_position",
            text="matches",
            hover_data={"avg_cs": ":.2f"},
            labels={"team_position": "Position",
                    "win_rate_pct": "Win rate (%)"},
            title="Position summary · count shown on bars",
        )
        role_chart.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(role_chart, width="stretch")
    with right:
        patch_stats = (
            frame.groupby("game_version", as_index=False)
            .agg(matches=("win", "size"), win_rate=("win", "mean"))
            .sort_values("game_version")
        )
        patch_stats["win_rate_pct"] = patch_stats["win_rate"] * 100
        patch_chart = px.scatter(
            patch_stats,
            x="matches",
            y="win_rate_pct",
            color="win_rate_pct",
            color_continuous_scale=[CYBER_PALETTE[3],
                                    CYBER_PALETTE[2], CYBER_PALETTE[4]],
            hover_name="game_version",
            size="matches",
            labels={"matches": "Matches", "win_rate_pct": "Win rate (%)"},
            title="Patch results · bubble size represents match count",
        )
        patch_chart.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(patch_chart, width="stretch")


def _render_match_history(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No matches match the selected filters.")
        return

    display_columns = [
        "played_at_utc",
        "champion",
        "team_position",
        "queue_label",
        "win",
        "kills",
        "deaths",
        "assists",
        "kda_ratio",
        "cs_per_minute",
        "champion_damage",
        "vision_score",
        "duration_minutes",
        "game_version",
    ]
    table = frame[display_columns].copy()
    table["played_at_utc"] = table["played_at_utc"].dt.strftime(
        "%Y-%m-%d %H:%M UTC")
    table = table.rename(
        columns={
            "played_at_utc": "Played at",
            "champion": "Champion",
            "team_position": "Position",
            "queue_label": "Queue",
            "win": "Win",
            "kills": "K",
            "deaths": "D",
            "assists": "A",
            "kda_ratio": "KDA",
            "cs_per_minute": "CS/min",
            "champion_damage": "Champion damage",
            "vision_score": "Vision",
            "duration_minutes": "Minutes",
            "game_version": "Patch",
        }
    )
    st.dataframe(table, width="stretch", hide_index=True, height=560)
    csv_bytes = frame[display_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered matches as CSV",
        data=csv_bytes,
        file_name="nexus_filtered_matches.csv",
        mime="text/csv",
    )


def _render_data_management(frame: Optional[pd.DataFrame]) -> None:
    st.markdown("### Local data status")
    try:
        data_status = validate_local_data()
        columns = st.columns(5)
        columns[0].metric(
            "Archived IDs", f"{data_status['archived_match_count']:,}")
        columns[1].metric(
            "Match files", f"{data_status['match_file_count']:,}")
        columns[2].metric("Timeline files",
                          f"{data_status['timeline_file_count']:,}")
        columns[3].metric("Missing details",
                          data_status["missing_match_count"])
        columns[4].metric("Missing timelines",
                          data_status["missing_timeline_count"])
    except (OSError, ValueError) as error:
        st.warning(f"Local archive check unavailable: {error}")

    st.markdown("### Synchronize with Riot")
    st.caption(
        "This action makes Riot API requests. It checks for new match IDs and "
        "downloads up to the selected number of incomplete matches."
    )
    limit = st.number_input(
        "Maximum matches to download this run",
        min_value=1,
        max_value=10000,
        value=100,
        step=25,
    )
    full_rescan = st.checkbox(
        "Full rescan for older matches Riot may have surfaced retroactively",
        value=False,
    )
    if st.button("Sync matches", type="primary", width="stretch"):
        reports_updated = False
        with st.status("Synchronizing match history…", expanded=True) as status:
            try:
                result = synchronize_matches(int(limit), full_rescan)
                status.update(
                    label="Riot synchronization finished", state="complete")
                st.success(
                    f"Found {result.discovered_match_count} new IDs. "
                    f"Selected {result.selected_match_count} matches; "
                    f"{result.failed_match_count} failed."
                )
                if result.failed_match_count == 0:
                    try:
                        rebuilt_count = rebuild_analysis_reports()
                        st.info(
                            f"Refreshed reports for {rebuilt_count:,} matches.")
                        load_match_table.clear()
                        reports_updated = True
                    except ValueError as error:
                        st.warning(f"Reports could not be refreshed: {error}")
                else:
                    st.warning(
                        "Some matches failed; rerun sync to retry incomplete pairs.")
            except RateLimitExceededError:
                status.update(label="Riot rate limit reached", state="error")
                st.error(
                    "Riot kept returning 429. Stop and wait before trying again; "
                    "completed match files are retained."
                )
            except (RiotAPIError, RuntimeError, ValueError, OSError) as error:
                status.update(label="Synchronization failed", state="error")
                st.error(f"Synchronization failed: {error}")
        if reports_updated:
            st.rerun()

    st.markdown("### Rebuild analysis reports")
    st.caption("Reprocesses local match JSON only; this does not call Riot.")
    if st.button("Rebuild local reports", width="stretch"):
        with st.spinner("Rebuilding reports from local match details…"):
            try:
                rebuilt_count = rebuild_analysis_reports()
                load_match_table.clear()
                st.success(f"Refreshed reports for {rebuilt_count:,} matches.")
                st.rerun()
            except ValueError as error:
                st.error(f"Could not rebuild reports: {error}")

    st.markdown("### Source data")
    st.markdown(
        "<div class='nexus-note'>Raw JSON remains the source of truth. "
        "CSV reports are disposable, reproducible analytics outputs; timelines "
        "remain archived separately for future event-level analysis.</div>",
        unsafe_allow_html=True,
    )
    if frame is not None:
        st.caption(
            f"Current report covers {len(frame):,} matches · {_format_date_range(frame)}")


def main() -> None:
    _inject_styles()
    st.markdown(
        "<div class='nexus-eyebrow'>PERSONAL MATCH INTELLIGENCE · EUW</div>"
        "<div class='nexus-title'>NEXUS <span>METRICS</span></div>"
        "<div class='nexus-subtitle'>Your match history, distilled into a local-first "
        "performance workspace. Riot sync is always user-triggered; viewing reports "
        "never contacts the API.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    frame = _load_reports()
    if frame is None:
        st.warning("No usable analysis report is available yet.")
        _render_data_management(None)
        return

    st.sidebar.markdown(
        f"### {escape(settings.PLAYER_GAME_NAME)}#{escape(settings.PLAYER_TAG_LINE)}"
    )
    st.sidebar.caption(f"Local dataset · {len(frame):,} matches")
    filtered_frame = _filter_matches(frame)

    st.markdown(
        f"<div class='nexus-eyebrow'>FILTERED WINDOW · {_format_date_range(filtered_frame) if not filtered_frame.empty else 'NO MATCHES'}</div>", unsafe_allow_html=True)
    _render_kpis(filtered_frame)

    overview_tab, champions_tab, history_tab, data_tab = st.tabs(
        ["Overview", "Champions & roles", "Match history", "Data & sync"]
    )
    with overview_tab:
        st.markdown(
            "<div class='nexus-section'>Performance signal</div>", unsafe_allow_html=True)
        _render_overview(filtered_frame)
    with champions_tab:
        st.markdown(
            "<div class='nexus-section'>Where the games are won</div>", unsafe_allow_html=True)
        _render_champions_and_roles(filtered_frame)
    with history_tab:
        st.markdown(
            "<div class='nexus-section'>Filtered match ledger</div>", unsafe_allow_html=True)
        _render_match_history(filtered_frame)
    with data_tab:
        _render_data_management(frame)

    st.caption(
        "Descriptive summaries, not causal or ranked predictions. Small samples are noisy; "
        "season labels require an authoritative season mapping."
    )


if __name__ == "__main__":
    main()
