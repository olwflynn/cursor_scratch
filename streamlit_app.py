import os
from typing import List, Any, Optional

import streamlit as st
from PIL import Image

from ai import generate_advice
from db import (
    init_db,
    insert_advice,
    fetch_recent,
    search_text,
    get_advice_by_ids,
    create_element,
    update_element,
    delete_element,
    list_elements,
    add_note,
    list_notes,
    add_bloom,
    list_blooms,
    compute_progress_stats,
)
from embeddings import compute_text_embedding
from semantic import semantic_search
from storage import save_uploaded_images, save_sample_image
from garden_designer import garden_designer, init_garden_session


APP_TITLE = "Garden Guide"
APP_TAGLINE = "Get friendly AI tips to grow a thriving garden"


# Lightweight CSS for a clean, card-based dashboard look
DASHBOARD_CSS = """
<style>
:root {
  --accent: #7C4DFF; /* vibrant purple accent */
  --card-bg: #ffffff;
  --muted: #6b7280;
  --border: #e5e7eb;
}
.section-title {
  font-weight: 700;
  letter-spacing: 0.2px;
  margin: 0.25rem 0 0.5rem 0;
}
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 1px 1px rgba(16,24,40,0.06);
}
.kpi { display: flex; flex-direction: column; gap: 6px; }
.kpi .label { color: var(--muted); font-size: 0.85rem; }
.kpi .value { font-weight: 800; font-size: 1.8rem; line-height: 1.2; }
.divider { height: 1px; background: var(--border); margin: 12px 0 8px 0; }
.accent { color: var(--accent); }
</style>
"""


def _load_pil_images(uploaded_files: List[Any]) -> List[Image.Image]:
    images: List[Image.Image] = []
    for uf in uploaded_files:
        try:
            img = Image.open(uf)
            images.append(img.convert("RGB"))
        except Exception:
            st.warning(f"Could not read image: {getattr(uf, 'name', 'unknown')}")
    return images


def page_ask_search():
    st.markdown("### Ask for Garden Advice")
    question = st.text_area("What would you like help with?", placeholder="e.g., Is this plant healthy? How to improve my lawn?")
    uploaded = st.file_uploader("Upload garden photos (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        run = st.button("Get Advice", key="ask_get_advice", type="primary", use_container_width=True)
    with col2:
        clear = st.button("Clear", key="ask_clear", use_container_width=True)

    if clear:
        st.session_state.pop("last_answer", None)

    if run:
        if not question.strip() and not uploaded:
            st.warning("Please enter a question or upload at least one image.")
            return

        try:
            with st.spinner("Analyzing and preparing advice..."):
                images = _load_pil_images(uploaded or [])
                answer = generate_advice(question, images)
                if not answer.strip():
                    st.error("No answer returned. Please try again.")
                    return
                embedding = compute_text_embedding("\n".join([question, answer]))
                saved_paths = save_uploaded_images(images) if images else []
                advice_id = insert_advice(question, saved_paths, answer, embedding)
                st.session_state["last_answer"] = (advice_id, answer, saved_paths)
        except Exception as e:
            st.error(str(e))
            return

    if "last_answer" in st.session_state:
        advice_id, answer, saved_paths = st.session_state["last_answer"]
        st.success("Advice saved!")
        st.markdown("#### Advice")
        st.write(answer)
        if saved_paths:
            st.markdown("#### Uploaded Photos")
            st.image(saved_paths, width=220)

    st.divider()
    st.markdown("### Search")
    st.markdown("#### Find previous advice for your garden")
    # semantic-only search
    q2 = st.text_input("Search", placeholder="yellowing leaves cause and fix")
    if st.button("Search", key="semantic_search_btn"):
        try:
            scored = semantic_search(q2, top_k=25)
            ids = [i for i, _ in scored]
            if not ids:
                st.info("No results.")
            else:
                results = get_advice_by_ids(ids)
                id_to_obj = {a.id: a for a in results}
                for i, score in scored:
                    a = id_to_obj.get(i)
                    if a:
                        st.caption(f"Similarity: {score:.3f}")
                        _render_advice_card(a)
        except Exception as e:
            st.error(str(e))



def _new_element_form() -> None:
    st.markdown("### Add New Element")
    with st.form("create_element_form", clear_on_submit=True):
        name = st.text_input("Name", placeholder="e.g., Rose Bush", max_chars=100)
        element_type = st.selectbox(
            "Type",
            options=["flower", "shrub", "tree", "bed", "planter"],
        )
        with st.expander("More details (optional)"):
            col1, col2 = st.columns([1, 1])
            with col1:
                location = st.text_input("Location", placeholder="North bed")
                planted_on = st.date_input("Planted on", value=None)
            with col2:
                variety = st.text_input("Variety")
                up = st.file_uploader("Image (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=False)
        submitted = st.form_submit_button("Create Element", type="primary")

    if submitted:
        if not name.strip():
            st.warning("Name is required.")
            return
        image_path: Optional[str] = None
        try:
            if up is not None:
                imgs = _load_pil_images([up])
                paths = save_uploaded_images(imgs)
                image_path = paths[0] if paths else None
            else:
                # Always generate a sample image when none uploaded
                image_path = save_sample_image(caption=name.strip())

            pid = create_element(
                name=name.strip(),
                type=element_type,
                location=(location.strip() if 'location' in locals() and location else None),
                planted_on=(str(planted_on) if 'planted_on' in locals() and planted_on else None),
                variety=(variety.strip() if 'variety' in locals() and variety else None),
                image_path=image_path,
            )
            st.success(f"Element created (id={pid}).")
        except Exception as e:
            st.error(str(e))


def _render_element_card(el: dict) -> None:
    with st.container(border=True):
        header = f"{el['name']} ({el['type']})"
        st.markdown(f"**{header}**")
        meta = []
        if el.get("location"): meta.append(f"📍 {el['location']}")
        if el.get("planted_on"): meta.append(f"🌱 {el['planted_on']}")
        if el.get("variety"): meta.append(f"🧬 {el['variety']}")
        if meta:
            st.caption(" · ".join(meta))
        if el.get("image_path") and os.path.exists(el["image_path"]):
            st.image(el["image_path"], width=220)

        # Notes
        with st.expander("Notes", expanded=False):
            note_key = f"note_input_{el['id']}"
            new_note = st.text_input("Add note", key=note_key)
            cols = st.columns([1, 5])
            if cols[0].button("Add", key=f"add_note_{el['id']}"):
                if new_note.strip():
                    try:
                        add_note(el["id"], new_note.strip())
                        st.success("Note added.")
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Enter a note.")
            notes = list_notes(el["id"]) or []
            for n in notes:
                st.caption(n["created_at"])
                st.write(n["note_text"])

        # Bloom tracker
        with st.expander("Bloom tracker", expanded=False):
            bcol1, bcol2, bcol3 = st.columns([1, 1, 2])
            start = bcol1.date_input("Start date", value=None, key=f"bstart_{el['id']}")
            end = bcol2.date_input("End date (optional)", value=None, key=f"bend_{el['id']}")
            if bcol3.button("Add bloom", key=f"add_bloom_{el['id']}"):
                if start:
                    try:
                        add_bloom(el["id"], str(start), str(end) if end else None)
                        st.success("Bloom added.")
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Start date required.")
            blooms = list_blooms(el["id"]) or []
            for b in blooms:
                label = f"{b['start_date']} → {b['end_date'] or 'present'}"
                st.write(label)


def page_elements():
    st.markdown("## 🌱 Elements")
    tabs = st.tabs(["Create", "Manage"])
    with tabs[0]:
        _new_element_form()
    with tabs[1]:
        items = list_elements()
        if not items:
            st.info("No elements yet. Add your first element.")
        else:
            for el in items:
                _render_element_card(el)


def page_dashboard():
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Garden Dashboard</div>', unsafe_allow_html=True)
    try:
        stats = compute_progress_stats()
    except Exception as e:
        st.error(str(e))
        return
    k1, k2, k3 = st.columns(3)
    with k1:
        with st.container():
            st.markdown('<div class="card kpi"><div class="label">Total elements</div>'
                        f'<div class="value">{stats.get("total_elements", 0)}</div></div>', unsafe_allow_html=True)
    with k2:
        with st.container():
            st.markdown('<div class="card kpi"><div class="label">Currently blooming</div>'
                        f'<div class="value accent">{stats.get("currently_blooming", 0)}</div></div>', unsafe_allow_html=True)
    with k3:
        with st.container():
            st.markdown('<div class="card kpi"><div class="label">Notes (7 days)</div>'
                        f'<div class="value">{stats.get("notes_last_7_days", 0)}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Elements by type</div>', unsafe_allow_html=True)

    by_type = stats.get("by_type", {})
    if by_type:
        import pandas as pd, altair as alt
        df = pd.DataFrame({"type": list(by_type.keys()), "count": list(by_type.values())})
        chart = (
            alt.Chart(df)
            .mark_bar(size=36, cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
            .encode(
                x=alt.X("type:N", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("count:Q", title=None),
                color=alt.value("#7C4DFF"),
                tooltip=[alt.Tooltip("type:N", title="Type"), alt.Tooltip("count:Q", title="Count")],
            )
            .properties(height=220)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data yet.")


def _render_advice_card(advice):
    with st.container(border=True):
        st.caption(advice.created_at)
        st.markdown(f"**Q:** {advice.question_text}")
        st.markdown(f"**A:** {advice.answer_text}")
        if advice.image_paths:
            st.image(advice.image_paths, width=160)


def _nav_buttons():
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Get Advice"
    st.markdown("## 🌿 Garden Guide")
    st.caption(APP_TAGLINE)
    st.divider()

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Get Advice", use_container_width=True, type=("primary" if st.session_state["current_page"] == "Get Advice" else "secondary")):
            st.session_state["current_page"] = "Get Advice"
            st.rerun()
    with b2:
        if st.button("Design", use_container_width=True, type=("primary" if st.session_state["current_page"] == "Design" else "secondary")):
            st.session_state["current_page"] = "Design"
            st.rerun()
    with b3:
        if st.button("Elements", use_container_width=True, type=("primary" if st.session_state["current_page"] == "Elements" else "secondary")):
            st.session_state["current_page"] = "Elements"
            st.rerun()
    with b4:
        if st.button("Dashboard", use_container_width=True, type=("primary" if st.session_state["current_page"] == "Dashboard" else "secondary")):
            st.session_state["current_page"] = "Dashboard"
            st.rerun()
    st.divider()


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🌿", layout="wide")
    init_db()
    init_garden_session()

    _nav_buttons()

    page = st.session_state.get("current_page", "Get Advice")
    if page == "Get Advice":
        page_ask_search()
    elif page == "Design":
        garden_designer()
    elif page == "Elements":
        page_elements()
    elif page == "Dashboard":
        page_dashboard()


if __name__ == "__main__":
    main()


