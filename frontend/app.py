"""Block 5 - Streamlit UI for OPT Navigator.

Run (with the API already running via `uvicorn app.api:app --reload`):
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

EXAMPLES = [
    "How many unemployment days do I get on post-completion OPT?",
    "Can I start working before my EAD start date?",
    "How long is the STEM OPT extension and who qualifies?",
    "What is cap-gap?",
]
with st.expander("Example questions"):
    for ex in EXAMPLES:
        st.markdown(f"- {ex}")

q = st.text_input("Your question", placeholder="Ask about OPT, STEM OPT, cap-gap, EAD, reporting...")

if st.button("Ask", type="primary") and q:
    try:
        with st.spinner("Searching official sources..."):
            r = requests.post(f"{API_URL}/ask", json={"question": q}, timeout=60)
            r.raise_for_status()
            data = r.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't reach the API at {API_URL}. Is `uvicorn app.api:app` running? ({e})")
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

        # Lightweight feedback - real logging (-> eval set) comes in a later block.
        st.divider()
        c1, c2, _ = st.columns([1, 1, 6])
        if c1.button("👍 Helpful"):
            st.toast("Thanks for the feedback!")
        if c2.button("👎 Off"):
            st.toast("Noted - this helps improve the eval set.")
