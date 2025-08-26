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


def _load_pil_images(uploaded_files: List[Any]) -> List[Image.Image]:
    images: List[Image.Image] = []
    for uf in uploaded_files:
        try:
            img = Image.open(uf)
            images.append(img.convert("RGB"))
        except Exception:
            st.warning(f"Could not read image: {getattr(uf, 'name', 'unknown')}")
    return images


def sidebar():
    st.sidebar.markdown(
        f"## {APP_TITLE}\n"
        f"{APP_TAGLINE}\n\n"
        "- Ask questions about plants, lawn, pests, soil and more.\n"
        "- Upload photos to get visual diagnosis.\n"
        "- Your advice is saved and searchable."
    )
    st.sidebar.divider()
    st.sidebar.markdown("**Settings**")
    st.sidebar.caption(
        "Set OPENAI_API_KEY in your environment before running: export OPENAI_API_KEY=..."
    )


def page_ask():
    st.markdown("### Ask for Garden Advice")
    question = st.text_area("What would you like help with?", placeholder="e.g., Is this plant healthy? How to improve my lawn?")
    uploaded = st.file_uploader("Upload garden photos (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        run = st.button("Get Advice", type="primary")
    with col2:
        clear = st.button("Clear")

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


def _new_element_form() -> None:
    st.markdown("### Add New Element")
    with st.form("create_element_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            name = st.text_input("Name", placeholder="e.g., Rose Bush", max_chars=100)
            element_type = st.selectbox(
                "Type",
                options=["flower", "shrub", "tree", "bed", "planter"],
            )
            location = st.text_input("Location (optional)", placeholder="North bed")
            planted_on = st.date_input("Planted on (optional)", value=None)
        with col2:
            variety = st.text_input("Variety (optional)")
            up = st.file_uploader("Image (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=False)
            want_sample = st.checkbox("Generate a sample image if none uploaded")
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
            elif want_sample:
                image_path = save_sample_image(caption=name.strip())

            pid = create_element(
                name=name.strip(),
                type=element_type,
                location=location.strip() or None,
                planted_on=str(planted_on) if planted_on else None,
                variety=variety.strip() or None,
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
    st.markdown("## 📊 Garden Dashboard")
    try:
        stats = compute_progress_stats()
    except Exception as e:
        st.error(str(e))
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Total elements", stats.get("total_elements", 0))
    c2.metric("Currently blooming", stats.get("currently_blooming", 0))
    c3.metric("Notes (7 days)", stats.get("notes_last_7_days", 0))

    st.divider()
    st.markdown("### Elements by type")
    by_type = stats.get("by_type", {})
    if by_type:
        # Build a simple chart-friendly structure
        import pandas as pd
        df = pd.DataFrame({"type": list(by_type.keys()), "count": list(by_type.values())})
        st.bar_chart(df.set_index("type"))
    else:
        st.info("No data yet.")


def _render_advice_card(advice):
    with st.container(border=True):
        st.caption(advice.created_at)
        st.markdown(f"**Q:** {advice.question_text}")
        st.markdown(f"**A:** {advice.answer_text}")
        if advice.image_paths:
            st.image(advice.image_paths, width=160)


def page_history():
    st.markdown("### History & Search")
    tabs = st.tabs(["Recent", "Search", "Semantic Search"])

    with tabs[0]:
        recents = fetch_recent(limit=25)
        if not recents:
            st.info("No advice saved yet.")
        for a in recents:
            _render_advice_card(a)

    with tabs[1]:
        q = st.text_input("Search text", placeholder="tomato, powdery mildew, lawn, compost...")
        if st.button("Search", key="text_search"):
            results = search_text(q, limit=50)
            if not results:
                st.info("No results.")
            for a in results:
                _render_advice_card(a)

    with tabs[2]:
        q2 = st.text_input("Semantic search", placeholder="yellowing leaves cause and fix")
        if st.button("Search", key="semantic_search"):
            try:
                scored = semantic_search(q2, top_k=25)
                ids = [i for i, _ in scored]
                if not ids:
                    st.info("No results.")
                else:
                    results = get_advice_by_ids(ids)
                    # Keep original order by score
                    id_to_obj = {a.id: a for a in results}
                    for i, score in scored:
                        a = id_to_obj.get(i)
                        if a:
                            st.caption(f"Similarity: {score:.3f}")
                            _render_advice_card(a)
            except Exception as e:
                st.error(str(e))


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🌿", layout="wide")
    init_db()
    init_garden_session()
    sidebar()

    # Add garden image at the top of the page
    st.image(
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
        caption="A beautiful garden",
        use_container_width=True,
    )

    st.markdown("## 🌿 Garden Guide")
    st.caption(APP_TAGLINE)
    st.divider()

    page = st.tabs(["Ask", "History", "Design", "Elements", "Dashboard"])
    with page[0]:
        page_ask()
    with page[1]:
        page_history()
    with page[2]:
        garden_designer()
    with page[3]:
        page_elements()
    with page[4]:
        page_dashboard()
    st.set_page_config(page_title=APP_TITLE, page_icon="🌿", layout="wide")


if __name__ == "__main__":
    main()


