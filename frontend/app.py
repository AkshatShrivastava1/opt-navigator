"""Streamlit UI for OPT Navigator: cited Q&A + a personalized OPT timeline.

Run (with the API running via `uvicorn app.api:app --reload`):
    streamlit run frontend/app.py

UI notes (Week 13 polish):
- Clickable example chips that auto-run a question.
- Answers and timeline results are kept in st.session_state so they survive Streamlit's
  top-to-bottom rerun on every widget interaction (e.g. clicking "email me").
- Timeline items render as color-coded risk cards (green/amber/red) with a legend.
All network/logic still lives in the API; this stays a thin client.
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

st.set_page_config(page_title="OPT Navigator", page_icon="📘", layout="centered")

# ---------------------------------------------------------------- styling
st.markdown(
    """
    <style>
      /* tighten the default top padding */
      .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 820px; }

      /* All buttons: translucent so they read on BOTH light and dark themes.
         We never set a text color here -> it inherits the theme's text color. */
      div[data-testid="stButton"] > button {
        border-radius: 999px;
        border: 1px solid rgba(140,150,170,0.45);
        background: rgba(140,150,170,0.12);
        font-size: 0.85rem; padding: 0.3rem 0.85rem; line-height: 1.25;
      }
      div[data-testid="stButton"] > button:hover { border-color: #6f8cff; color: #6f8cff; }

      /* Primary CTAs (Ask / Build): solid accent + white text so they stand out.
         Target both the old and new Streamlit test-ids; !important beats the rule above. */
      button[data-testid="baseButton-primary"],
      button[data-testid="stBaseButton-primary"] {
        border-radius: 8px !important; background: #4f7cff !important; color: #fff !important;
        border: 1px solid #4f7cff !important; padding: 0.45rem 1.2rem !important;
        font-size: 0.95rem !important;
      }
      button[data-testid="baseButton-primary"]:hover,
      button[data-testid="stBaseButton-primary"]:hover {
        background: #3a63d6 !important; border-color: #3a63d6 !important; color: #fff !important;
      }

      /* Timeline risk cards: translucent tints + inherited text (theme-safe). */
      .tl-card {
        border-radius: 8px; padding: 0.6rem 0.85rem; margin: 0.4rem 0;
        border-left: 5px solid #9aa4b2; background: rgba(150,160,175,0.10);
      }
      .tl-info    { border-left-color: #2e9e4f; background: rgba(46,158,79,0.15); }
      .tl-warning { border-left-color: #eda100; background: rgba(237,161,0,0.16); }
      .tl-danger  { border-left-color: #e5484d; background: rgba(229,72,77,0.16); }
      .tl-head { font-size: 0.98rem; }
      .tl-rule { opacity: 0.78; font-size: 0.82rem; margin-top: 0.2rem; }
      .src-link { font-size: 0.9rem; margin: 0.12rem 0; }
      /* verbatim official quote: fixed size, immune to markdown chars in the text */
      .verbatim { border-left: 3px solid rgba(140,150,170,0.55); padding: 0.35rem 0.9rem;
                  font-size: 0.92rem; opacity: 0.92; line-height: 1.5; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("📘 OPT Navigator")
    st.write(
        "Answers about F-1 OPT rules, grounded **only** in official USCIS / SEVP sources. "
        "Every answer cites its source and refuses when the sources don't cover it."
    )
    st.divider()
    st.caption(
        "⚠️ General information from official sources — **not legal advice**. Always confirm "
        "your situation with your school's DSO or an immigration attorney."
    )
    st.caption(f"API: {API_URL}")

# ---------------------------------------------------------------- header
st.title("📘 OPT Navigator")
st.caption("Cited answers about F-1 OPT rules, grounded only in official USCIS / SEVP sources.")

# session defaults
st.session_state.setdefault("ask_box", "")
st.session_state.setdefault("ask_result", None)
st.session_state.setdefault("tl_result", None)
st.session_state.setdefault("situation_box", "")

EXAMPLES = [
    "How many unemployment days do I get on post-completion OPT?",
    "Can I start working before my EAD start date?",
    "How long is the STEM OPT extension and who qualifies?",
    "Do I need a job offer to apply for OPT?",
    "Is self-employment allowed on OPT?",
    "Can I travel internationally while on OPT?",
]


def _run_ask(question: str) -> None:
    """Call /ask and stash the result in session_state so it survives reruns."""
    try:
        with st.spinner(
            "Searching official sources… (first request after idle can take ~30–60s "
            "while the free server wakes up)"
        ):
            r = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=120)
            r.raise_for_status()
            st.session_state.ask_result = {"q": question, "data": r.json()}
    except requests.exceptions.Timeout:
        st.session_state.ask_result = {"q": question, "error": "waking"}
    except requests.exceptions.RequestException as e:
        st.session_state.ask_result = {"q": question, "error": f"Couldn't reach the API. ({e})"}


def _use_example(text: str) -> None:
    """on_click callback: fill the box and flag an auto-run (runs before the next rerun)."""
    st.session_state.ask_box = text
    st.session_state._trigger_ask = True


ask_tab, timeline_tab = st.tabs(["💬 Ask a question", "🗓️ My OPT timeline"])

# ================================================================ Ask a question
with ask_tab:
    st.markdown("**Try an example**")
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        cols[i % 2].button(ex, key=f"ex_{i}", on_click=_use_example, args=(ex,),
                           use_container_width=True)

    st.text_input(
        "Your question",
        key="ask_box",
        placeholder="Ask about OPT, STEM OPT, cap-gap, EAD, reporting…",
    )
    ask_clicked = st.button("Ask", type="primary", key="ask_btn")

    # Run on an Ask click or when an example chip was just pressed.
    if (ask_clicked or st.session_state.pop("_trigger_ask", False)) and st.session_state.ask_box.strip():
        _run_ask(st.session_state.ask_box.strip())

    res = st.session_state.ask_result
    if res:
        if res.get("error") == "waking":
            st.warning("The free-tier server was asleep and is waking up. Give it ~30 seconds, then click Ask again.")
        elif res.get("error"):
            st.error(res["error"])
        else:
            data = res["data"]
            st.markdown("#### Answer")
            st.markdown(data["answer"])
            seen, links = set(), []
            for s in data.get("sources", []):
                url = s.get("source")
                if not url or url in seen:
                    continue
                seen.add(url)
                links.append(f"<div class='src-link'>• <a href='{url}'>{s.get('title', url)}</a></div>")
            if links:
                st.markdown("**Sources**")
                st.markdown("".join(links), unsafe_allow_html=True)

# ================================================================ My OPT timeline
with timeline_tab:
    st.write(
        "Tell me your situation and I'll compute your personal OPT dates, with the official "
        "rule cited for each. I only use the dates you give me — I never guess a date."
    )
    st.text_area(
        "Your situation",
        key="situation_box",
        placeholder=(
            "e.g. My program ends May 15, 2026. I have a CS (STEM) degree. My EAD runs "
            "July 1, 2026 to June 30, 2027, and I've used about 80 unemployment days."
        ),
        height=120,
    )

    if st.button("Build my timeline", type="primary", key="tl_btn") and st.session_state.situation_box.strip():
        try:
            with st.spinner("Computing your dates…"):
                r = requests.post(
                    f"{API_URL}/timeline",
                    json={"situation": st.session_state.situation_box.strip()},
                    timeout=120,
                )
                r.raise_for_status()
                st.session_state.tl_result = {"data": r.json()}
        except requests.exceptions.Timeout:
            st.session_state.tl_result = {"error": "waking"}
        except requests.exceptions.RequestException as e:
            st.session_state.tl_result = {"error": f"Couldn't reach the API. ({e})"}

    tl = st.session_state.tl_result
    if tl:
        if tl.get("error") == "waking":
            st.warning("The free-tier server was asleep and is waking up. Give it ~30 seconds, then try again.")
        elif tl.get("error"):
            st.error(tl["error"])
        else:
            data = tl["data"]
            with st.expander("What I understood from your message (correct me if any date is wrong)"):
                st.json(data.get("parsed", {}))

            st.caption("🟢 on track   🟡 approaching / attention   🔴 urgent or passed")
            icons = {"info": "🟢", "warning": "🟡", "danger": "🔴"}
            for it in data.get("timeline", []):
                status = it.get("status", "info")
                detail = f" — {it['detail']}" if it.get("detail") else ""
                st.markdown(
                    f"<div class='tl-card tl-{status}'>"
                    f"<div class='tl-head'>{icons.get(status, '•')} <b>{it['label']}: {it['value']}</b></div>"
                    f"<div class='tl-rule'>{it['rule']} "
                    f"<a href='{it['citation']}'>source</a>{detail}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if it.get("snippet"):
                    with st.expander("📄 the official rule, verbatim"):
                        safe = (it["snippet"].replace("&", "&amp;")
                                .replace("<", "&lt;").replace(">", "&gt;"))
                        st.markdown(f"<div class='verbatim'>{safe}</div>", unsafe_allow_html=True)
                        st.caption(f"[Read the full source]({it['citation']})")

            st.info(
                "These dates are computed from the information you provided. General information "
                "from official sources, not legal advice — confirm with your DSO."
            )

            st.divider()
            st.caption("Don't want to track these yourself? Get the upcoming ones emailed to you.")
            remind_email = st.text_input("Your email", key="remind_email", placeholder="you@school.edu")
            if st.button("📧 Email me my deadlines", key="remind_btn") and remind_email:
                try:
                    with st.spinner("Sending…"):
                        rr = requests.post(
                            f"{API_URL}/remind",
                            json={"situation": st.session_state.situation_box.strip(), "email": remind_email},
                            timeout=120,
                        )
                        rr.raise_for_status()
                        rres = rr.json()
                except requests.exceptions.RequestException as e:
                    st.error(f"Couldn't reach the API. ({e})")
                else:
                    if rres.get("sent"):
                        st.success(f"Sent {rres['count']} upcoming deadline(s) to {remind_email}.")
                    else:
                        st.warning(rres.get("reason", "Nothing was sent."))
