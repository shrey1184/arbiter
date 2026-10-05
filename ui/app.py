import os

import httpx
import streamlit as st

API = os.getenv("ARBITER_API_URL", "http://localhost:8000")
KEY = os.getenv("ARBITER_API_KEY", "dev-key-change-me")

st.set_page_config(page_title="Arbiter", layout="wide")
st.title("Arbiter: LLM Output Arbitration")
tab_single, tab_batch, tab_analytics = st.tabs(["Verdict", "Batch", "Analytics"])

with tab_single:
    prompt = st.text_area("Original prompt (optional)")
    output = st.text_area("LLM output to evaluate", height=250)
    if st.button("Arbitrate") and output.strip():
        with st.spinner("Critics are evaluating..."):
            r = httpx.post(f"{API}/v1/arbitrate", json={"output": output, "prompt": prompt or None},
                           headers={"x-api-key": KEY}, timeout=120)
        if r.is_success:
            data = r.json()
            v = data["verdict"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Score", f"{v['overall_score']}/10")
            c2.metric("Confidence", f"{v['confidence']:.0%}")
            c3.metric("Latency", f"{data['latency_ms']} ms")
            st.write(v["summary"])
            st.json(data)   # TODO: inline highlights + critic comparison panel
        else:
            st.error(r.text)

with tab_batch:
    st.info("TODO: upload CSV/JSONL, run batch, sortable results table.")
with tab_analytics:
    st.info("TODO: critic behavior analytics.")

# adding comment