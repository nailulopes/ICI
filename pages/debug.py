"""ICI Debug Page — shows raw API data to diagnose issues"""
import streamlit as st
import pandas as pd
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ici_shared import WOMEN_FACILITIES, COMPANION_FACILITIES, BASE_URL

try:
    KOBO_TOKEN = st.secrets["KOBO_TOKEN"]
except Exception:
    st.error("No KOBO_TOKEN"); st.stop()

st.title("🔍 ICI Debug")

for label, facilities in [("WOMEN", WOMEN_FACILITIES), ("COMPANION", COMPANION_FACILITIES)]:
    st.markdown(f"## {label}")
    for fac_id, fac_info in facilities.items():
        st.markdown(f"### {fac_info['name']} — `{fac_info['asset_uid']}`")
        headers = {"Authorization": f"Token {KOBO_TOKEN}"}
        url = f"{BASE_URL}/api/v2/assets/{fac_info['asset_uid']}/data/?format=json&limit=5"
        r = requests.get(url, headers=headers)
        st.write(f"**HTTP status:** {r.status_code}")
        if r.status_code != 200:
            st.error(f"API error: {r.text[:500]}")
            continue
        data = r.json()
        st.write(f"**Total count:** {data.get('count', '?')}")
        results = data.get("results", [])
        if not results:
            st.warning("No results returned")
            continue
        df = pd.DataFrame(results)
        st.write(f"**Columns ({len(df.columns)}):**")
        st.write(list(df.columns))
        st.write(f"**First row sample (key fields):**")
        key_cols = [c for c in ['method','education','satisfaction','_submission_time',
                                 '_country','_facility','age','emotion','verbal','payment']
                    if c in df.columns]
        st.dataframe(df[key_cols].head(3))
        st.write(f"**`_submission_time` values:**")
        if '_submission_time' in df.columns:
            st.write(df['_submission_time'].head(5).tolist())
        st.write(f"**`method` values:**")
        if 'method' in df.columns:
            st.write(df['method'].unique().tolist())
