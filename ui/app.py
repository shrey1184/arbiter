import json
import os

import httpx
import pandas as pd
import streamlit as st

from render import (DIM_ICON, EDGE, FILL, build_spans, conflicted_dimensions, parse_batch_text,
                    render_highlighted, score_color)

DEFAULT_API = os.getenv("ARBITER_API_URL", "http://localhost:8000")
DEFAULT_KEY = os.getenv("ARBITER_API_KEY", "dev-key-change-me")

SAMPLES = {
    "Planted factual error": (
        "When did the Berlin Wall fall and who was the US president?",
        "The Berlin Wall fell in 1991 while George H. W. Bush was president. The event marked "
        "the beginning of German reunification, which was completed in 1990.",
    ),
    "Flawed logic": (
        "Should our startup adopt microservices?",
        "Netflix uses microservices and Netflix is successful. Therefore our five-person startup "
        "will be successful if it adopts microservices. Monoliths are always slow.",
    ),
    "Misses the point": (
        "Explain what a hash map is, its average lookup complexity, and one drawback.",
        "A hash map stores key-value pairs and uses a hash function to compute an index into an "
        "array of buckets.",
    ),
    "Clean answer": ("What is the capital of France?", "The capital of France is Paris."),
}

st.set_page_config(page_title="Arbiter", page_icon="⚖️", layout="wide")
st.markdown(
    """<style>
    .block-container {padding-top: 2rem; max-width: 1250px;}
    div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.3); border-radius: 10px; padding: .6rem .9rem;}
    .pill {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.78rem; margin-right:6px; color:#111;}
    </style>""",
    unsafe_allow_html=True,
)

ss = st.session_state
ss.setdefault("prompt_in", "")
ss.setdefault("output_in", "")
ss.setdefault("result", None)
ss.setdefault("history", [])
ss.setdefault("batch_df", None)


# ---------------------------------------------------------------- API helpers
def call_api(output: str, prompt: str | None) -> dict:
    r = httpx.post(f"{api_url}/v1/arbitrate", json={"output": output, "prompt": prompt or None},
                   headers={"x-api-key": api_key}, timeout=180)
    r.raise_for_status()
    return r.json()


def load_sample(name: str) -> None:
    ss.prompt_in, ss.output_in = SAMPLES[name]


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("⚖️ Arbiter")
    st.caption("Three critics. One verdict.")
    api_url = st.text_input("API URL", DEFAULT_API)
    api_key = st.text_input("API key", DEFAULT_KEY, type="password")
    try:
        httpx.get(f"{api_url}/health", timeout=2).raise_for_status()
        st.success("API online", icon="🟢")
    except Exception:
        st.error("API unreachable", icon="🔴")

    st.divider()
    st.markdown("**Highlight legend**")
    for kind, text in [("confirmed", "Confirmed issue"), ("flagged", "Flagged / unreviewed"),
                       ("validated", "Validated claim")]:
        st.markdown(f'<span class="pill" style="background:{FILL[kind]};border-bottom:2px solid {EDGE[kind]}">'
                    f"{text}</span>", unsafe_allow_html=True)
    st.caption("Hover a highlight to see why it was flagged.")

    if ss.history:
        st.divider()
        st.markdown("**Recent runs**")
        for i, h in enumerate(reversed(ss.history[-6:])):
            if st.button(f"{h['verdict']['overall_score']}/10 · {h['_excerpt']}", key=f"hist{i}",
                         use_container_width=True):
                ss.result = h

tab_single, tab_batch, tab_analytics = st.tabs(["🔍 Verdict", "📦 Batch", "📊 Analytics"])

# ---------------------------------------------------------------- single verdict
with tab_single:
    st.markdown("##### Try a sample")
    cols = st.columns(len(SAMPLES))
    for col, name in zip(cols, SAMPLES):
        col.button(name, on_click=load_sample, args=(name,), use_container_width=True)

    left, right = st.columns(2)
    left.text_area("Original prompt (optional)", key="prompt_in", height=170)
    right.text_area("LLM output to evaluate", key="output_in", height=170)

    if st.button("⚖️ Arbitrate", type="primary", disabled=not ss.output_in.strip()):
        try:
            with st.spinner("Critics are evaluating in parallel…"):
                res = call_api(ss.output_in, ss.prompt_in)
            res["_text"] = ss.output_in
            res["_prompt"] = ss.prompt_in
            res["_excerpt"] = ss.output_in[:28].replace("\n", " ") + "…"
            ss.result = res
            ss.history.append(res)
        except httpx.HTTPStatusError as e:
            st.error(f"API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            st.error(f"Could not reach the API: {e}")

    res = ss.result
    if res:
        v, crits, dis = res["verdict"], res["critiques"], res["disagreements"]
        text = res.get("_text", "")
        st.divider()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall score", f"{v['overall_score']}/10")
        m2.metric("Confidence", f"{v['confidence']:.0%}")
        m3.metric("Issues confirmed", len(v["confirmed_issues"]),
                  help="Stays 0 until the adjudicator is implemented")
        m4.metric("Latency", f"{res['latency_ms'] / 1000:.1f}s")
        st.progress(v["overall_score"] / 10, text="Quality")

        if v["degraded"]:
            st.warning("Degraded verdict: missing critic(s) "
                       f"{', '.join(v['missing_dimensions']) or 'unknown'}. Confidence is reduced.", icon="⚠️")
        st.info(v["summary"], icon="📝")

        st.markdown("#### Annotated output")
        spans = build_spans(text, v, crits)
        st.markdown(render_highlighted(text, spans), unsafe_allow_html=True)

        if spans:
            issue_spans = [s for s in spans if s["kind"] != "validated"]
            if issue_spans:
                st.markdown("##### Inspect an issue")
                labels = [f"{s['kind'].upper()} · “{s['quote'][:50]}”" for s in issue_spans]
                pick = st.selectbox("Select", range(len(labels)), format_func=lambda i: labels[i],
                                    label_visibility="collapsed")
                s = issue_spans[pick]
                st.markdown(f"**Quote:** “{s['quote']}”  \n**Why:** {s['label']}")
                for crit in crits:
                    for iss in crit["issues"]:
                        if iss["quote"] == s["quote"]:
                            st.caption(f"{DIM_ICON[crit['dimension']]} {crit['dimension']} critic · "
                                       f"category `{iss['category']}` · severity {iss['severity']}")
                for r in v["disagreement_resolutions"]:
                    st.caption(f"Adjudicator: {r['outcome']}")

        st.markdown("#### Critic comparison")
        conflicted = conflicted_dimensions(dis)
        ccols = st.columns(3)
        for col, crit in zip(ccols, sorted(crits, key=lambda c: ["accuracy", "logic", "completeness"].index(c["dimension"]))):
            edge = "#d97706" if crit["dimension"] in conflicted else "#16a34a"
            with col:
                st.markdown(f'<div style="border-left:5px solid {edge};padding-left:10px">'
                            f'<b>{DIM_ICON[crit["dimension"]]} {crit["dimension"].title()}</b></div>',
                            unsafe_allow_html=True)
                st.markdown(f'<span style="font-size:2rem;font-weight:700;color:{score_color(crit["score"], 5)}">'
                            f'{crit["score"]}/5</span> &nbsp; confidence {crit["confidence"]:.0%}',
                            unsafe_allow_html=True)
                st.caption(crit["reasoning_summary"])
                if crit["issues"]:
                    for iss in crit["issues"]:
                        with st.expander(f"sev {iss['severity']} · {iss['category']}"):
                            st.write(f"“{iss['quote']}”")
                            st.write(iss["problem"])
                else:
                    st.success("No issues found")
        st.caption("🟧 orange border = involved in a detected disagreement · 🟩 green = agrees with the others")

        if dis:
            st.markdown("#### Disagreements")
            for d in dis:
                st.warning(f"**{d['type'].replace('_', ' ').title()}** "
                           f"({', '.join(d['critics'])}): {d['summary']}")
        if v["dismissed_flags"]:
            st.markdown("#### Dismissed flags")
            for f in v["dismissed_flags"]:
                st.write(f"~~{f['original_problem']}~~ ({f['raised_by']}) → {f['dismissal_reasoning']}")

        with st.expander("Raw JSON"):
            st.json({k: x for k, x in res.items() if not k.startswith("_")})
    else:
        st.caption("Pick a sample or paste your own output, then press Arbitrate.")

# ---------------------------------------------------------------- batch
with tab_batch:
    st.markdown("Paste multiple outputs separated by a line containing only `---`, or upload a CSV/JSONL "
                "with an `output` column (optional `prompt` column).")
    raw = st.text_area("Outputs", height=180, key="batch_raw")
    up = st.file_uploader("…or upload a file", type=["csv", "jsonl"])

    if st.button("Run batch", type="primary"):
        items: list[dict] = []
        if up is not None:
            df_in = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_json(up, lines=True)
            if "output" not in df_in.columns:
                st.error("File needs an `output` column.")
            else:
                items = [{"output": str(r["output"]), "prompt": r.get("prompt") if "prompt" in df_in.columns else None}
                         for _, r in df_in.iterrows()]
        else:
            items = [{"output": o, "prompt": None} for o in parse_batch_text(raw)]

        if items:
            rows, bar = [], st.progress(0.0, text="Starting…")
            for i, it in enumerate(items, 1):
                try:
                    r = call_api(it["output"], it["prompt"] if isinstance(it["prompt"], str) else None)
                    v = r["verdict"]
                    n = len(v["confirmed_issues"]) or sum(len(c["issues"]) for c in r["critiques"])
                    rows.append({"excerpt": it["output"][:70], "score": v["overall_score"], "issues": n,
                                 "confidence": round(v["confidence"], 2), "degraded": v["degraded"],
                                 "status": "ok", "id": r["arbitration_id"]})
                except Exception as e:
                    rows.append({"excerpt": it["output"][:70], "score": None, "issues": None,
                                 "confidence": None, "degraded": None, "status": f"failed: {e}"[:60], "id": ""})
                bar.progress(i / len(items), text=f"{i}/{len(items)} processed")
            ss.batch_df = pd.DataFrame(rows)
        elif up is None:
            st.warning("Nothing to process.")

    if ss.batch_df is not None:
        df = ss.batch_df
        c1, c2, c3 = st.columns(3)
        c1.metric("Processed", len(df))
        c2.metric("Avg score", f"{df['score'].mean():.1f}" if df["score"].notna().any() else "–")
        c3.metric("Failures", int((df["status"] != "ok").sum()))
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"score": st.column_config.ProgressColumn("score", min_value=0, max_value=10, format="%d"),
                                    "confidence": st.column_config.NumberColumn(format="%.2f")})
        st.download_button("Download CSV", df.to_csv(index=False), "batch_results.csv", "text/csv")

# ---------------------------------------------------------------- analytics
with tab_analytics:
    st.info("Analytics arrive in Phase 5: issues per critic, overrule rate, top failure categories, "
            "agreement rate, and latency per provider.", icon="📊")