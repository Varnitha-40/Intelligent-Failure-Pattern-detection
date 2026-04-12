import polars as pl
import numpy as np
from sentence_transformers import SentenceTransformer
from pyod.models.iforest import IForest
from sklearn.cluster import KMeans
import streamlit as st

# ✅ Cache model (speed boost)
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

def process_logs(file):
    logs = pl.read_csv(file)

    # ✅ LIMIT DATA (speed)
    logs = logs.head(2000)

    # ✅ Combine all text columns
    text_cols = [c for c in logs.columns if logs[c].dtype == pl.Utf8]

    if len(text_cols) == 0:
        logs = logs.with_columns(pl.all().cast(str))
        text_cols = logs.columns

    logs = logs.with_columns(
        pl.concat_str(text_cols, separator=" ").alias("log")
    )

    log_list = logs["log"].to_list()

    # ✅ Embeddings
    embeddings = model.encode(log_list)

    # ✅ Anomaly detection (better tuning)
    clf = IForest(contamination=0.3)
    clf.fit(embeddings)

    labels = clf.labels_
    scores = clf.decision_scores_

    logs = logs.with_columns([
        pl.Series("anomaly", labels),
        pl.Series("score", scores)
    ])

    # ✅ Severity
    min_s = scores.min()
    max_s = scores.max()
    norm_scores = (scores - min_s) / (max_s - min_s + 1e-8)

    severity = []
    for s in norm_scores:
        if s > 0.7:
            severity.append("High")
        elif s > 0.4:
            severity.append("Medium")
        else:
            severity.append("Low")

    logs = logs.with_columns(pl.Series("severity", severity))

    # ✅ BETTER PATTERN DETECTION (only anomalies)
    anomaly_embeddings = embeddings[np.where(labels == 1)]

    if len(anomaly_embeddings) > 2:
        kmeans = KMeans(n_clusters=2, random_state=42)
        cluster_labels = kmeans.fit_predict(anomaly_embeddings)

        cluster_full = np.full(len(labels), -1)
        idxs = np.where(labels == 1)[0]

        for i, c in zip(idxs, cluster_labels):
            cluster_full[i] = c

        logs = logs.with_columns(pl.Series("pattern", cluster_full))
    else:
        logs = logs.with_columns(pl.Series("pattern", np.full(len(labels), -1)))

    # ✅ HUMAN-READABLE LABELS
    pattern_labels = []
    for p in logs["pattern"]:
        if p == 0:
            pattern_labels.append("System Issues")
        elif p == 1:
            pattern_labels.append("Network/Disk Issues")
        else:
            pattern_labels.append("Normal")

    logs = logs.with_columns(pl.Series("pattern_label", pattern_labels))

    return logs