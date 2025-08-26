import os
from typing import List, Any

import streamlit as st
from PIL import Image

from ai import generate_advice
from db import init_db, insert_advice, fetch_recent, search_text, get_advice_by_ids
from embeddings import compute_text_embedding
from semantic import semantic_search
from storage import save_uploaded_images
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

    page = st.tabs(["Ask", "History", "Design"])
    with page[0]:
        page_ask()
    with page[1]:
        page_history()
    with page[2]:
        garden_designer()
    st.set_page_config(page_title=APP_TITLE, page_icon="🌿", layout="wide")


if __name__ == "__main__":
    main()


