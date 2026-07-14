from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
WORKBOOK = DATA_DIR / "glioblastoma_clinical_trial_intelligence_platform.xlsx"

st.set_page_config(
    page_title="Glioblastoma Clinical Trial Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px;}
    h1, h2, h3 {color: #173b73;}
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e3e8f0;
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 2px 10px rgba(25, 55, 95, 0.05);
    }
    [data-testid="stMetricLabel"] {font-weight: 600;}
    .small-note {color:#627086; font-size:0.88rem;}
    .insight-box {
        background:#eef5ff;
        border-left:4px solid #1f5aa6;
        padding:0.85rem 1rem;
        border-radius:8px;
        margin:0.3rem 0 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_sheet(sheet_name: str) -> pd.DataFrame:
    """Load a workbook sheet, with CSV fallback for easier deployment."""
    csv_map = {
        "All Trials": "all_trials.csv",
        "Executive Summary": "executive_summary.csv",
        "Failure Intelligence": "failure_intelligence.csv",
        "Failure by Intervention": "failure_by_intervention.csv",
        "Drug Intelligence": "drug_intelligence.csv",
        "Biomarker Intelligence": "biomarker_intelligence.csv",
        "Combination Intelligence": "combination_intelligence.csv",
        "Research Opportunity": "research_opportunity.csv",
    }
    csv_path = DATA_DIR / csv_map[sheet_name]
    if csv_path.exists():
        return pd.read_csv(csv_path)
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Missing data workbook: {WORKBOOK}")
    return pd.read_excel(WORKBOOK, sheet_name=sheet_name)


@st.cache_data(show_spinner=False)
def load_all_data() -> dict[str, pd.DataFrame]:
    sheets = [
        "All Trials",
        "Executive Summary",
        "Failure Intelligence",
        "Failure by Intervention",
        "Drug Intelligence",
        "Biomarker Intelligence",
        "Combination Intelligence",
        "Research Opportunity",
    ]
    return {sheet: load_sheet(sheet) for sheet in sheets}


def clean_text_series(series: pd.Series) -> pd.Series:
    return series.fillna("Not reported").astype(str).str.strip().replace("", "Not reported")


def safe_number(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def format_metric(value: Any, digits: int = 0) -> str:
    number = safe_number(value)
    if digits == 0:
        return f"{number:,.0f}"
    return f"{number:,.{digits}f}"


def metric_value(summary: pd.DataFrame, label: str, default: Any = 0) -> Any:
    match = summary.loc[summary["Metric"].astype(str).str.casefold() == label.casefold(), "Value"]
    return match.iloc[0] if not match.empty else default


def horizontal_bar(df: pd.DataFrame, category: str, value: str, title: str, top_n: int = 10) -> go.Figure:
    plot_df = df[[category, value]].copy()
    plot_df[value] = pd.to_numeric(plot_df[value], errors="coerce").fillna(0)
    plot_df = plot_df.nlargest(top_n, value).sort_values(value)
    fig = px.bar(plot_df, x=value, y=category, orientation="h", title=title, text_auto=True)
    fig.update_layout(height=420, margin=dict(l=10, r=20, t=55, b=20), yaxis_title=None, xaxis_title="Trials")
    return fig


def add_download_button(df: pd.DataFrame, filename: str, label: str = "Download CSV") -> None:
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def executive_dashboard(data: dict[str, pd.DataFrame]) -> None:
    trials = data["All Trials"].copy()
    summary = data["Executive Summary"].copy()

    st.title("Glioblastoma Clinical Trial Intelligence Platform")
    st.caption("Transforming ClinicalTrials.gov data into actionable oncology research intelligence")

    

    total = metric_value(summary, "Total Trials", len(trials))
    completed = metric_value(summary, "Completed Trials", 0)
    failed = metric_value(summary, "Stopped / Failed Trials", metric_value(summary, "Stopped/Failed Trials", 0))
    ongoing = metric_value(summary, "Ongoing / Other Trials", metric_value(summary, "Ongoing/Other Trials", 0))
    median_enrollment = metric_value(summary, "Median Enrollment", 0)

    # Calculate countries automatically if summary value is missing
    countries = metric_value(summary, "Countries Represented", None)

    if countries is None or safe_number(countries) == 0:
        if "Countries" in trials.columns:
            country_list = []
            for value in trials["Countries"].dropna().astype(str):
                country_list.extend([c.strip() for c in value.split(";") if c.strip()])
        countries = len(set(country_list))
    else:
        countries = 0

    cols = st.columns(6)
    values = [
        ("Total Trials", total),
        ("Completed", completed),
        ("Stopped / Failed", failed),
        ("Ongoing / Other", ongoing),
        ("Countries", countries),
        ("Median Enrollment", median_enrollment),
    ]
    for col, (label, value) in zip(cols, values):
        col.metric(label, format_metric(value))

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        outcome_col = "Outcome Category" if "Outcome Category" in trials.columns else "Trial Outcome Category"
        outcome = clean_text_series(trials[outcome_col]).value_counts().reset_index()
        outcome.columns = ["Outcome", "Trials"]
        fig = px.pie(outcome, names="Outcome", values="Trials", hole=0.55, title="Trial Outcome Distribution")
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=10), legend_title=None)
        st.plotly_chart(fig, width="stretch")

    with right:
        trend = trials.copy()
        trend["Start Year"] = pd.to_numeric(trend.get("Start Year"), errors="coerce")
        trend = trend.dropna(subset=["Start Year"])
        trend = trend[(trend["Start Year"] >= 1980) & (trend["Start Year"] <= pd.Timestamp.now().year)]
        trend_df = trend.groupby("Start Year").size().reset_index(name="Trials")
        fig = px.line(trend_df, x="Start Year", y="Trials", markers=True, title="Clinical Trial Start Trend")
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=20))
        st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)
    with left:
        phase = clean_text_series(trials.get("Phase Clean", trials.get("Phase", pd.Series(dtype=str))))
        phase_df = phase.value_counts().head(10).reset_index()
        phase_df.columns = ["Phase", "Trials"]
        fig = px.bar(phase_df, x="Phase", y="Trials", title="Phase Distribution", text_auto=True)
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=90), xaxis_tickangle=-35)
        st.plotly_chart(fig, width="stretch")

    with right:
        drugs = data["Drug Intelligence"]
        st.plotly_chart(horizontal_bar(drugs, "Drug", "Total_Trials", "Top Studied Drugs", 10), width="stretch")

    left, right = st.columns(2)
    with left:
        sponsor = clean_text_series(trials.get("Sponsor Class Clean", trials.get("Sponsor Class", pd.Series(dtype=str))))
        sponsor_df = sponsor.value_counts().reset_index()
        sponsor_df.columns = ["Sponsor Class", "Trials"]
        fig = px.bar(sponsor_df, x="Trials", y="Sponsor Class", orientation="h", title="Sponsor Class Distribution", text_auto=True)
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=55, b=20), yaxis_title=None)
        st.plotly_chart(fig, width="stretch")

    with right:
        country_rows: list[str] = []
        if "Countries" in trials.columns:
            for value in trials["Countries"].dropna().astype(str):
                country_rows.extend([part.strip() for part in value.split(";") if part.strip()])
        country_df = pd.Series(country_rows, name="Country").value_counts().head(10).reset_index()
        country_df.columns = ["Country", "Trials"]
        fig = px.bar(country_df.sort_values("Trials"), x="Trials", y="Country", orientation="h", title="Top Countries by Trial Activity", text_auto=True)
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=55, b=20), yaxis_title=None)
        st.plotly_chart(fig, width="stretch")

    st.markdown(
        '<div class="insight-box"><b>Executive insight:</b> The platform combines trial outcomes, development phases, therapeutic interventions, sponsors and geography so users can move from descriptive counts toward research prioritization.</div>',
        unsafe_allow_html=True,
    )


def trial_explorer(data: dict[str, pd.DataFrame]) -> None:
    trials = data["All Trials"].copy()
    st.header("Clinical Trial Explorer")
    st.caption("Search, filter and export individual glioblastoma clinical trials.")

    filter_cols = st.columns([1.2, 1.2, 1.2, 1.2])
    status_options = sorted(clean_text_series(trials["Status Clean"] if "Status Clean" in trials else trials["Status"]).unique())
    phase_options = sorted(clean_text_series(trials["Phase Clean"] if "Phase Clean" in trials else trials["Phase"]).unique())
    sponsor_options = sorted(clean_text_series(trials["Sponsor Class Clean"] if "Sponsor Class Clean" in trials else trials["Sponsor Class"]).unique())

    selected_status = filter_cols[0].multiselect("Status", status_options)
    selected_phase = filter_cols[1].multiselect("Phase", phase_options)
    selected_sponsor = filter_cols[2].multiselect("Sponsor class", sponsor_options)
    keyword = filter_cols[3].text_input("Keyword", placeholder="Drug, sponsor, title, NCT...")

    year_series = pd.to_numeric(trials.get("Start Year"), errors="coerce")
    finite_years = year_series.dropna().astype(int)
    min_year = int(finite_years.min()) if not finite_years.empty else 1980
    max_year = int(finite_years.max()) if not finite_years.empty else pd.Timestamp.now().year
    year_range = st.slider("Start year range", min_year, max_year, (min_year, max_year))

    filtered = trials.copy()
    status_field = "Status Clean" if "Status Clean" in filtered else "Status"
    phase_field = "Phase Clean" if "Phase Clean" in filtered else "Phase"
    sponsor_field = "Sponsor Class Clean" if "Sponsor Class Clean" in filtered else "Sponsor Class"

    if selected_status:
        filtered = filtered[clean_text_series(filtered[status_field]).isin(selected_status)]
    if selected_phase:
        filtered = filtered[clean_text_series(filtered[phase_field]).isin(selected_phase)]
    if selected_sponsor:
        filtered = filtered[clean_text_series(filtered[sponsor_field]).isin(selected_sponsor)]

    start_year = pd.to_numeric(filtered.get("Start Year"), errors="coerce")
    filtered = filtered[start_year.between(year_range[0], year_range[1], inclusive="both") | start_year.isna()]

    if keyword.strip():
        query = keyword.strip().casefold()
        search_columns = [
            "NCT Number", "Brief Title", "Lead Sponsor", "Intervention Names", "Detected Drugs",
            "Detected Biomarkers", "Countries", "Primary Outcomes", "Brief Summary",
        ]
        mask = pd.Series(False, index=filtered.index)
        for col in search_columns:
            if col in filtered.columns:
                mask |= filtered[col].fillna("").astype(str).str.casefold().str.contains(query, regex=False)
        filtered = filtered[mask]

    st.metric("Matching trials", f"{len(filtered):,}")

    display_cols = [
        "NCT Number", "Brief Title", "Status Clean", "Phase Clean", "Enrollment", "Start Year",
        "Lead Sponsor", "Sponsor Class Clean", "Intervention Names", "Detected Biomarkers", "Countries",
        "ClinicalTrials.gov URL",
    ]
    display_cols = [col for col in display_cols if col in filtered.columns]
    display_df = filtered[display_cols].copy()
    st.dataframe(display_df, width="stretch", height=520, hide_index=True)
    add_download_button(display_df, "filtered_glioblastoma_trials.csv", "Download filtered trials")


def research_intelligence(data: dict[str, pd.DataFrame]) -> None:
    st.header("Research Intelligence")
    st.caption("Failure, drug, biomarker, combination and opportunity analyses generated from the trial corpus.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Failure", "Drug", "Biomarker", "Combination", "Opportunity"
    ])

    with tab1:
        failure = data["Failure Intelligence"].copy()
        failure_by = data["Failure by Intervention"].copy()
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(horizontal_bar(failure, "Failure Reason Category", "Number of Failed Trials", "Top Failure Reasons", 10), width="stretch")
        with col2:
            rate_df = failure_by.sort_values("Failure Rate %", ascending=False).head(12).sort_values("Failure Rate %")
            fig = px.bar(rate_df, x="Failure Rate %", y="Intervention_Type", orientation="h", title="Failure Rate by Intervention Type", text_auto=".1f")
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=20), yaxis_title=None)
            st.plotly_chart(fig, width="stretch")
        st.dataframe(failure_by.sort_values("Failure Rate %", ascending=False), width="stretch", hide_index=True)
        add_download_button(failure_by, "failure_by_intervention.csv")

    with tab2:
        drugs = data["Drug Intelligence"].copy()
        selected_drug = st.selectbox("Select a drug", drugs["Drug"].tolist())
        row = drugs.loc[drugs["Drug"] == selected_drug].iloc[0]
        metrics = st.columns(6)
        for col, label, field in zip(
            metrics,
            ["Trials", "Completed", "Failed", "Ongoing", "Median enrollment", "Failure rate"],
            ["Total_Trials", "Completed", "Failed", "Ongoing_Other", "Median_Enrollment", "Failure Rate %"],
        ):
            suffix = "%" if "rate" in label.lower() else ""
            col.metric(label, f"{safe_number(row[field]):,.1f}{suffix}" if suffix else f"{safe_number(row[field]):,.0f}")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(horizontal_bar(drugs, "Drug", "Total_Trials", "Top Drugs by Trial Volume", 15), width="stretch")
        with col2:
            top = drugs.nlargest(15, "Total_Trials").sort_values("Failure Rate %")
            fig = px.bar(top, x="Failure Rate %", y="Drug", orientation="h", title="Failure Rate Among High-Volume Drugs", text_auto=".1f")
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=20), yaxis_title=None)
            st.plotly_chart(fig, width="stretch")
        st.dataframe(drugs, width="stretch", hide_index=True)
        add_download_button(drugs, "drug_intelligence.csv")

    with tab3:
        biomarkers = data["Biomarker Intelligence"].copy()
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(horizontal_bar(biomarkers, "Biomarker", "Total_Trials", "Most Studied Biomarkers", 15), width="stretch")
        with col2:
            rate = biomarkers.sort_values("Failure Rate %", ascending=False).head(15).sort_values("Failure Rate %")
            fig = px.bar(rate, x="Failure Rate %", y="Biomarker", orientation="h", title="Biomarker Trial Failure Rate", text_auto=".1f")
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=20), yaxis_title=None)
            st.plotly_chart(fig, width="stretch")
        st.dataframe(biomarkers, width="stretch", hide_index=True)
        add_download_button(biomarkers, "biomarker_intelligence.csv")

    with tab4:
        combos = data["Combination Intelligence"].copy()
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(horizontal_bar(combos, "Combination", "Total_Trials", "Combination Therapy Volume", 10), width="stretch")
        with col2:
            long_df = combos.melt(
                id_vars=["Combination"],
                value_vars=["Completed", "Failed", "Ongoing_Other"],
                var_name="Outcome",
                value_name="Trials",
            )
            fig = px.bar(long_df, x="Trials", y="Combination", color="Outcome", orientation="h", title="Combination Outcomes")
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=20), yaxis_title=None)
            st.plotly_chart(fig, width="stretch")
        st.dataframe(combos, width="stretch", hide_index=True)
        add_download_button(combos, "combination_intelligence.csv")

    with tab5:
        opportunity = data["Research Opportunity"].copy()
        min_trials = int(opportunity["Total_Trials"].min())
        max_trials = int(opportunity["Total_Trials"].max())
        threshold = st.slider("Minimum trial volume", min_trials, max_trials, min(20, max_trials))
        view = opportunity[opportunity["Total_Trials"] >= threshold].copy()
        fig = px.scatter(
            view,
            x="Failure Rate %",
            y="Opportunity Score",
            size="Total_Trials",
            color="Completion Rate %",
            hover_name="Drug",
            hover_data=["Total_Trials", "Completed", "Failed", "Median_Enrollment"],
            title="Drug Research Opportunity Landscape",
        )
        fig.update_layout(height=520, margin=dict(l=10, r=10, t=55, b=20))
        st.plotly_chart(fig, width="stretch")
        st.dataframe(opportunity.sort_values("Opportunity Score", ascending=False), width="stretch", hide_index=True)
        add_download_button(opportunity, "research_opportunity.csv")


def answer_research_question(question: str, data: dict[str, pd.DataFrame]) -> str:
    q = question.casefold().strip()
    drugs = data["Drug Intelligence"].copy()
    biomarkers = data["Biomarker Intelligence"].copy()
    failure = data["Failure Intelligence"].copy()
    failure_by = data["Failure by Intervention"].copy()
    combos = data["Combination Intelligence"].copy()
    opportunity = data["Research Opportunity"].copy()
    summary = data["Executive Summary"].copy()

    if not q:
        return "Enter a question about trial volume, drugs, biomarkers, failure, combinations or research opportunity."

    if "total" in q and "trial" in q:
        return f"The dataset contains {format_metric(metric_value(summary, 'Total Trials', 0))} glioblastoma clinical trials."
    if "most studied" in q and ("drug" in q or "intervention" in q):
        row = drugs.sort_values("Total_Trials", ascending=False).iloc[0]
        return f"{row['Drug']} is the most studied detected drug, appearing in {int(row['Total_Trials']):,} trials."
    if "highest failure" in q and "drug" in q:
        eligible = drugs[drugs["Total_Trials"] >= 10]
        row = eligible.sort_values("Failure Rate %", ascending=False).iloc[0]
        return f"Among drugs with at least 10 trials, {row['Drug']} has the highest failure rate at {row['Failure Rate %']:.1f}% ({int(row['Failed'])} failed of {int(row['Total_Trials'])} trials)."
    if "biomarker" in q and ("most" in q or "top" in q or "frequent" in q):
        row = biomarkers.sort_values("Total_Trials", ascending=False).iloc[0]
        return f"{row['Biomarker']} is the most frequently detected biomarker, appearing in {int(row['Total_Trials']):,} trials."
    if "failure reason" in q or "why" in q and "stop" in q:
        row = failure.sort_values("Number of Failed Trials", ascending=False).iloc[0]
        return f"The most common failure-reason category is '{row['Failure Reason Category']}', covering {int(row['Number of Failed Trials']):,} stopped or failed trials."
    if "intervention type" in q and "failure" in q:
        row = failure_by.sort_values("Failure Rate %", ascending=False).iloc[0]
        return f"{row['Intervention_Type']} has the highest observed failure rate at {row['Failure Rate %']:.1f}% ({int(row['Failed_Trials'])} of {int(row['Total_Trials'])} trials)."
    if "combination" in q and ("common" in q or "most" in q or "top" in q):
        row = combos.sort_values("Total_Trials", ascending=False).iloc[0]
        return f"The most common combination category is '{row['Combination']}' with {int(row['Total_Trials']):,} trials."
    if "opportunity" in q or "candidate" in q or "prioritize" in q:
        row = opportunity.sort_values("Opportunity Score", ascending=False).iloc[0]
        return f"{row['Drug']} has the highest calculated opportunity score ({row['Opportunity Score']:.1f}), based on trial volume, ongoing activity and outcome patterns. This is a prioritization signal, not evidence of clinical efficacy."
    if "completed" in q:
        return f"There are {format_metric(metric_value(summary, 'Completed Trials', 0))} completed trials in the dataset."
    if "stopped" in q or "failed" in q:
        value = metric_value(summary, "Stopped / Failed Trials", metric_value(summary, "Stopped/Failed Trials", 0))
        return f"There are {format_metric(value)} trials categorized as stopped or failed."

    # Drug-name lookup
    for _, row in drugs.iterrows():
        drug = str(row["Drug"])
        if drug.casefold() in q:
            return (
                f"{drug}: {int(row['Total_Trials'])} total trials, {int(row['Completed'])} completed, "
                f"{int(row['Failed'])} failed and {int(row['Ongoing_Other'])} ongoing/other. "
                f"Failure rate: {row['Failure Rate %']:.1f}%; median enrollment: {row['Median_Enrollment']:.1f}."
            )

    return (
        "I could not map that question to a prepared intelligence rule. Try asking about the most studied drug, "
        "top biomarker, common failure reason, intervention failure rate, combinations or opportunity score."
    )


def research_assistant(data: dict[str, pd.DataFrame]) -> None:
    st.header("Research Assistant")
    st.caption("A transparent rule-based assistant grounded in the prepared intelligence tables. No paid API is required.")

    examples = [
        "Which drug is most studied?",
        "Which biomarker appears most often?",
        "What is the most common failure reason?",
        "Which intervention type has the highest failure rate?",
        "Which drug has the highest opportunity score?",
    ]
    selected = st.selectbox("Quick question", ["Choose an example..."] + examples)
    question = st.text_input("Ask a research question", value="" if selected == "Choose an example..." else selected)

    if st.button("Analyze", type="primary"):
        st.markdown(
            f'<div class="insight-box"><b>Answer:</b> {answer_research_question(question, data)}</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Available analytical scope")
    st.write(
        "The assistant can answer questions using the executive summary, drug, biomarker, failure, "
        "combination and opportunity tables. Its answers are deterministic and auditable."
    )
    st.warning(
        "Research-use only. Opportunity scores and pattern summaries do not establish treatment efficacy, safety or clinical recommendations."
    )


def about_page(data: dict[str, pd.DataFrame]) -> None:
    st.header("About the Project")
    st.markdown(
        """
        This portfolio project converts publicly available ClinicalTrials.gov glioblastoma records into a clinical trial intelligence platform.

        **Workflow**
        1. Data extraction and cleaning in Python/Pandas  
        2. Descriptive and intelligence-table generation  
        3. One-page Power BI executive dashboard  
        4. Interactive Streamlit application  

        **Core analytical modules**
        - Trial landscape and trends
        - Drug and intervention intelligence
        - Biomarker intelligence
        - Failure analysis
        - Combination therapy analysis
        - Research opportunity prioritization
        """
    )
    counts = {name: len(df) for name, df in data.items()}
    st.dataframe(pd.DataFrame({"Table": counts.keys(), "Rows": counts.values()}), hide_index=True, width="stretch")


def main() -> None:
    try:
        data = load_all_data()
    except Exception as exc:
        st.error(f"Unable to load project data: {exc}")
        st.stop()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Executive Dashboard", "Trial Explorer", "Research Intelligence", "Research Assistant", "About"],
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Data source: ClinicalTrials.gov")
    st.sidebar.caption("Portfolio analytics project — not clinical advice")

    if page == "Executive Dashboard":
        executive_dashboard(data)
    elif page == "Trial Explorer":
        trial_explorer(data)
    elif page == "Research Intelligence":
        research_intelligence(data)
    elif page == "Research Assistant":
        research_assistant(data)
    else:
        about_page(data)


if __name__ == "__main__":
    main()
