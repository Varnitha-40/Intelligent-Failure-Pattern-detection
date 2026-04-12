from auth import check_auth, logout
import streamlit as st
import polars as pl
from model_utils import process_logs
import plotly.express as px

st.markdown("""
<style>
.stApp {
    background-color: #E6E6FA;
    color: black;
}

h1, h2, h3, h4, h5, h6 {
    color: black;
}

.stButton>button {
    background-color: #6495ED;
    color: white;
    border-radius: 8px;
}

.stSidebar {
    background-color: #7B68EE;
}

.stDataFrame {
    background-color: white;
    color: black;
}

</style>
""", unsafe_allow_html=True)

# Auth
check_auth()
logout()

st.set_page_config(page_title="Log Analyzer", layout="wide")

st.title("Intelligent Failure Pattern Detection From System Logs")

# Sidebar
st.sidebar.header("Controls")
show_only_anomaly = st.sidebar.checkbox("Show Only Anomalies")
show_high = st.sidebar.checkbox("Show Only High Severity")

# Upload
file = st.file_uploader("Upload Log File", type=["csv"])

if file is not None:

    # ✅ RUN ONLY ONCE
    logs = process_logs(file)

    # Metrics
    total = len(logs)
    anomalies = len(logs.filter(pl.col("anomaly") == 1))
    percent = (anomalies / total) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Logs", total)
    col2.metric("Anomalies", anomalies)
    col3.metric("Anomaly %", f"{percent:.2f}%")

    # Filters
    if show_only_anomaly:
        logs = logs.filter(pl.col("anomaly") == 1)

    if show_high:
        logs = logs.filter(pl.col("severity") == "High")

    # Table
    st.subheader("📄 Logs Table")
    st.dataframe(logs.to_pandas(), use_container_width=True)

    # ✅ Better Chart (replace pie)
    st.subheader("📊 Pattern vs Severity")

    fig = px.bar(
        logs.to_pandas(),
        x="pattern_label",
        color="severity",
        title="Failure Patterns Analysis"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ✅ Pattern Count
    st.subheader("📌 Pattern Summary")

    pattern_counts = logs.group_by("pattern_label").count()
    st.dataframe(pattern_counts.to_pandas())

        # ✅ 🔥 Anomaly Insights
    st.subheader("🔍 Why Anomalies Occur")

    anomalies_df = logs.filter(pl.col("anomaly") == 1)

    if len(anomalies_df) > 0:
        words = " ".join(anomalies_df["log"].to_list()).split()

        freq = {}
        for w in words:
            if len(w) > 4:
                freq[w] = freq.get(w, 0) + 1

        top_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]

        st.write("Top keywords causing anomalies:")
        st.write(top_words)
    else:
        st.write("No anomalies found")

    # ✅ 🧠 Failure Cause Analysis
    st.subheader("🧠 Failure Cause Analysis")

    def detect_cause(text):
        text = text.lower()
        if "disk" in text:
            return "Disk Failure"
        elif "cpu" in text:
            return "High CPU Usage"
        elif "memory" in text:
            return "Memory Issue"
        elif "network" in text or "timeout" in text:
            return "Network Issue"
        elif "error" in text:
            return "Application Error"
        else:
            return "Unknown Issue"

    if len(anomalies_df) > 0:
        causes = [detect_cause(t) for t in anomalies_df["log"].to_list()]
        anomalies_df = anomalies_df.with_columns(pl.Series("cause", causes))

        st.dataframe(
            anomalies_df.select(["log", "severity", "pattern_label", "cause"]).to_pandas()
        )
    else:
        st.write("No anomalies to analyze")

    # ✅ Download
    csv = logs.write_csv()
    st.download_button("⬇️ Download Results", csv, "results.csv")