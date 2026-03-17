"""ICI Debug Page v2 — shows data at each processing step"""
import streamlit as st
import pandas as pd
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ici_shared import (
    WOMEN_FACILITIES, COMPANION_FACILITIES, BASE_URL,
    normalize_columns, to_int, METHOD_MAP, QUALITY_MAP, LIKERT5_MAP,
)

try:
    KOBO_TOKEN = st.secrets["KOBO_TOKEN"]
except Exception:
    st.error("No KOBO_TOKEN"); st.stop()

st.title("ICI Debug v2")
lang = st.radio("Language", ["EN", "ES", "FR"], horizontal=True)

st.markdown("## Step 1: Raw vs normalized columns")
for label, facilities in [("WOMEN", WOMEN_FACILITIES), ("COMPANION", COMPANION_FACILITIES)]:
    st.markdown(f"### {label}")
    for fac_id, fac_info in facilities.items():
        st.markdown(f"**{fac_info['name']}**")
        headers = {"Authorization": f"Token {KOBO_TOKEN}"}
        r = requests.get(f"{BASE_URL}/api/v2/assets/{fac_info['asset_uid']}/data/?format=json&limit=5", headers=headers)
        st.write(f"HTTP: {r.status_code}")
        if r.status_code != 200: continue
        raw_df = pd.DataFrame(r.json().get("results", []))
        if raw_df.empty: continue
        norm_df = normalize_columns(raw_df)
        missing = [c for c in ['method','age','satisfaction','emotion','verbal'] if c not in norm_df.columns]
        st.write(f"interview/ cols before: {[c for c in raw_df.columns if c.startswith('interview/')][:5]}")
        st.write(f"method col exists after normalize: {'method' in norm_df.columns}")
        st.write(f"Missing key cols after normalize: {missing}")
        st.write(f"method values: {norm_df['method'].tolist() if 'method' in norm_df.columns else 'N/A'}")
        st.write(f"_submission_time[0]: {repr(norm_df['_submission_time'].iloc[0]) if '_submission_time' in norm_df.columns else 'N/A'}")

st.markdown("## Step 2: Full load + country filter")
all_dfs = []
for fac_id, fac_info in WOMEN_FACILITIES.items():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    r = requests.get(f"{BASE_URL}/api/v2/assets/{fac_info['asset_uid']}/data/?format=json&limit=3000", headers=headers)
    if r.status_code != 200: continue
    results = r.json().get("results", [])
    if not results: continue
    df = pd.DataFrame(results)
    df = normalize_columns(df)
    df["_facility"] = fac_info["name"]
    df["_country"]  = fac_info["country"]
    all_dfs.append(df)

if all_dfs:
    raw = pd.concat(all_dfs, ignore_index=True)
    raw["_submission_time"] = pd.to_datetime(raw["_submission_time"], errors="coerce")
    st.write(f"Combined shape: {raw.shape}")
    st.write(f"_country values: {raw['_country'].value_counts().to_dict()}")
    st.write(f"_country repr: {[repr(v) for v in raw['_country'].unique()]}")
    b = raw[raw["_country"] == "Country B"]
    st.write(f"Rows after filter 'Country B': {len(b)}")
    if len(b) == 0:
        st.error("COUNTRY B FILTER FAILS")
        st.write(f"All _country values repr: {[repr(v) for v in raw['_country'].unique()]}")
    if "method" in raw.columns:
        raw["method_int"] = to_int(raw["method"])
        raw["method_label"] = raw["method_int"].map(METHOD_MAP[lang])
        st.write(f"method_label per country:")
        st.write(raw.groupby("_country")["method_label"].value_counts().to_dict())
    ts = raw.groupby(pd.Grouper(key="_submission_time", freq="MS")).size().reset_index(name="n")
    ts = ts[ts["n"]>0]
    st.write(f"Timeline rows: {len(ts)}, X values: {ts['_submission_time'].tolist()}")

st.markdown("## Step 3: Companion emotions")
for fac_id, fac_info in COMPANION_FACILITIES.items():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    r = requests.get(f"{BASE_URL}/api/v2/assets/{fac_info['asset_uid']}/data/?format=json&limit=10", headers=headers)
    if r.status_code != 200: continue
    df = pd.DataFrame(r.json().get("results", []))
    df = normalize_columns(df)
    st.write(f"emotion col exists: {'emotion' in df.columns}")
    if "emotion" in df.columns:
        st.write(f"emotion raw values: {df['emotion'].tolist()}")
        df["emotion_int"] = to_int(df["emotion"])
        st.write(f"emotion int values: {df['emotion_int'].tolist()}")
    if "verbal" in df.columns:
        st.write(f"verbal raw: {df['verbal'].tolist()}")
        df["verbal_int"] = to_int(df["verbal"])
        mapped = df["verbal_int"].map(LIKERT5_MAP[lang])
        st.write(f"verbal mapped: {mapped.tolist()}")
