"""Block 5 — Streamlit UI. Run: streamlit run frontend/app.py"""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="OPT Navigator", page_icon="📘")
st.title("OPT Navigator")
st.caption(
    "Cited answers about F-1 OPT rules from official USCIS/SEVP sources. "
    "Not legal advice — confirm with your DSO."
)

q = st.text_input("Your question")
if st.button("Ask") and q:
    with st.spinner("Searching official sources..."):
        r = requests.post(f"{API_URL}/ask", json={"question": q}, timeout=60).json()
    st.write(r["answer"])
    st.caption("Sources:")
    st.json(r["sources"])
