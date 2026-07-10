"""Streamlit UI for OPT Navigator: cited Q&A + a personalized OPT timeline.

Run (with the API running via `uvicorn app.api:app --reload`):
    streamlit run frontend/app.py
"""
import os

import requests
import streamlit as st


def _api_url() -> str:
    # Streamlit Community Cloud injects secrets via st.secrets; locally use env or localhost.
    try:
        if "API_URL" in st.secrets:
            return st.secrets["API_URL"]
    except Exception:
        pass
    return os.getenv("API_URL", "http://localhost:8000")


API_URL = _api_url()

st.set_page_config(page_title="OPT Navigator", page_icon="📘")
st.title("📘 OPT Navigator")
st.caption("Cited answers about F-1 OPT rules, grounded only in official USCIS / SEVP sources.")

st.warning(
    "This tool gives general information from official sources. It is **not legal advice** - "
    "always confirm your situation with your school's DSO or an immigration attorney.",
    icon="⚠️",
)

ask_tab, timeline_tab = st.tabs(["Ask a question", "My OPT timeline"])

# ---------------------------------------------------------------- Ask a question
with ask_tab:
    with st.expander("Example questions"):
        for ex in [
            "How many unemployment days do I get on post-completion OPT?",
            "Can I start working before my EAD start date?",
            "How long is the STEM OPT extension and who qualifies?",
            "Is self-employment allowed on OPT?",
        ]:
            st.markdown(f"- {ex}")

    q = st.text_input("Your question", placeholder="Ask about OPT, STEM OPT, cap-gap, EAD, reporting...")
    if st.button("Ask", type="primary") and q:
        try:
            with st.spinner("Searching official sources... (first request after idle can take ~30-60s while the free server wakes up)"):
                r = requests.post(f"{API_URL}/ask", json={"question": q}, timeout=120)
                r.raise_for_status()
                data = r.json()
        except requests.exceptions.Timeout:
            st.warning("The free-tier server was asleep and is waking up. Give it ~30 seconds, then click Ask again.")
        except requests.exceptions.RequestException as e:
            st.error(f"Couldn't reach the API at {API_URL}. ({e})")
        else:
            st.markdown(data["answer"])
            seen, links = set(), []
            for s in data.get("sources", []):
                url = s.get("source")
                if not url or url in seen:
                    continue
                seen.add(url)
                links.append(f"- [{s.get('title', url)}]({url})")
            if links:
                st.markdown("**Sources**")
                st.markdown("\n".join(links))

# ---------------------------------------------------------------- My OPT timeline
with timeline_tab:
    st.write(
        "Tell me your situation and I'll compute your personal OPT dates, with the official "
        "rule cited for each. I only use the dates you give me - I never guess a date."
    )
    situation = st.text_area(
        "Your situation",
        placeholder=(
            "e.g. My program ends May 15, 2026. I have a CS (STEM) degree. My EAD runs "
            "July 1, 2026 to June 30, 2027, and I've used about 80 unemployment days."
        ),
        height=120,
    )
    if st.button("Build my timeline", type="primary") and situation:
        try:
            with st.spinner("Computing your dates..."):
                r = requests.post(f"{API_URL}/timeline", json={"situation": situation}, timeout=120)
                r.raise_for_status()
                data = r.json()
        except requests.exceptions.Timeout:
            st.warning("The free-tier server was asleep and is waking up. Give it ~30 seconds, then try again.")
        except requests.exceptions.RequestException as e:
            st.error(f"Couldn't reach the API at {API_URL}. ({e})")
        else:
            st.caption("What I understood from your message (correct me if any date is wrong):")
            st.json(data.get("parsed", {}))

            icons = {"info": "🟢", "warning": "🟡", "danger": "🔴"}
            for it in data.get("timeline", []):
                st.markdown(f"{icons.get(it['status'], '•')} **{it['label']}: {it['value']}**")
                extra = f" — {it['detail']}" if it.get("detail") else ""
                st.caption(f"{it['rule']} [[source]]({it['citation']}){extra}")

            st.info(
                "These dates are computed from the information you provided. General information "
                "from official sources, not legal advice - confirm with your DSO."
            )
