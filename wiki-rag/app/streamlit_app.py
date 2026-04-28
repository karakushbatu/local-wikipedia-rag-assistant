import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.styles import (
    apply_styles,
    badge,
    card,
    metric_card,
    page_header,
    status_dot,
    thinking_dots,
)
from database.sqlite_tracker import (
    clear_all,
    get_all_entities,
    get_stats,
    init_db,
    is_ingested,
    mark_failed,
    mark_ingested,
)
from embeddings.embedder import embed_text
from generation.llm import check_ollama_available, generate_answer
from ingest.chunker import chunk_text
from ingest.entities import PEOPLE, PLACES
from ingest.wikipedia_fetcher import fetch_wikipedia_page
from retrieval.classifier import classify_query
from retrieval.retriever import retrieve
from vectorstore.chroma_store import (
    count_documents,
    query as chroma_query,
    reset_collection,
    upsert_chunks,
)

st.set_page_config(
    page_title="WikiRAG — Local AI Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()
init_db()


# ── Session state ────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_query_type" not in st.session_state:
    st.session_state.last_query_type = None

if "prefill_query" not in st.session_state:
    st.session_state.prefill_query = ""


# ── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown("""
<div style="display:flex;align-items:center;gap:11px;margin-bottom:4px;padding:2px 0;">
  <div style="
    background:var(--bg-elevated);
    border:1px solid var(--border-mid);
    border-radius:10px;
    width:36px;height:36px;
    display:flex;align-items:center;justify-content:center;
    font-size:18px;flex-shrink:0;
    box-shadow:var(--shadow-sm);
  ">📚</div>
  <div>
    <div style="font-family:'Outfit',sans-serif;font-size:15px;font-weight:700;
                color:var(--text-primary);line-height:1.15;letter-spacing:-0.02em;">WikiRAG</div>
    <div style="font-size:10px;color:var(--text-tertiary);letter-spacing:0.06em;
                font-family:'DM Sans',sans-serif;">Local AI · Wikipedia RAG</div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            ["💬 Chat", "📥 Ingest Data", "🔍 Debug / Explore", "ℹ️ About"],
            label_visibility="collapsed",
        )

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

        # Status panel
        ollama_ok = check_ollama_available()
        stats = get_stats()

        ollama_dot = status_dot(ollama_ok)
        ollama_label = (
            '<span style="color:var(--success);font-size:12px;font-weight:500;">Connected</span>'
            if ollama_ok
            else '<span style="color:var(--danger);font-size:12px;font-weight:500;">Not running</span>'
        )

        st.markdown(f"""
<div style="
  background:var(--bg-tertiary);
  border:1px solid var(--border-subtle);
  border-radius:10px;
  padding:14px;
">
  <div style="font-size:10px;color:var(--text-muted);
              text-transform:uppercase;letter-spacing:0.12em;font-weight:600;
              margin-bottom:12px;font-family:'DM Sans',sans-serif;">
    System
  </div>
  <div style="display:flex;align-items:center;margin-bottom:10px;">
    {ollama_dot}{ollama_label}
  </div>
  <div style="font-size:11px;color:var(--text-tertiary);margin-bottom:10px;
              font-family:'JetBrains Mono',monospace;">
    mistral:7b · nomic-embed-text
  </div>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;">
    <span style="background:var(--bg-secondary);border:1px solid var(--border-subtle);
                 border-radius:6px;padding:3px 8px;font-size:11px;color:var(--text-secondary);">
      👤 {stats['people_success']} people
    </span>
    <span style="background:var(--bg-secondary);border:1px solid var(--border-subtle);
                 border-radius:6px;padding:3px 8px;font-size:11px;color:var(--text-secondary);">
      🏛️ {stats['places_success']} places
    </span>
  </div>
  <div style="font-size:11px;color:var(--text-tertiary);
              font-family:'JetBrains Mono',monospace;">
    {stats['total_chunks']:,} chunks indexed
  </div>
</div>
""", unsafe_allow_html=True)

        if st.button("Refresh", use_container_width=True):
            st.rerun()

        # Quick Questions — only show on Chat page
        if "quick_page_check" not in st.session_state:
            st.session_state.quick_page_check = True

        st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:10px;color:var(--text-muted);text-transform:uppercase;'
            'letter-spacing:0.12em;font-weight:600;margin:0 0 8px 0;'
            'font-family:\'DM Sans\',sans-serif;">Quick Questions</p>',
            unsafe_allow_html=True,
        )

        people_questions = [
            "Who was Albert Einstein?",
            "What did Marie Curie discover?",
            "Why is Nikola Tesla famous?",
            "What is Frida Kahlo known for?",
            "Tell me about Napoleon Bonaparte.",
            "What were Isaac Newton's contributions?",
            "Describe Cleopatra's reign.",
            "What did Charles Darwin propose?",
            "Who was Abraham Lincoln?",
            "Compare Messi and Ronaldo.",
        ]

        place_questions = [
            "Where is the Eiffel Tower?",
            "What was the Colosseum used for?",
            "Where is the Taj Mahal located?",
            "How tall is Mount Everest?",
            "What is Machu Picchu?",
            "Where is the Hagia Sophia?",
            "Tell me about the Pyramids of Giza.",
            "What is Stonehenge?",
            "Where is Angkor Wat?",
            "Describe the Grand Canyon.",
        ]

        with st.expander("👤 People", expanded=False):
            for q in people_questions:
                if st.button(q, key=f"qq_people_{q}", use_container_width=True):
                    st.session_state.prefill_query = q
                    st.rerun()

        with st.expander("🏛️ Places", expanded=False):
            for q in place_questions:
                if st.button(q, key=f"qq_place_{q}", use_container_width=True):
                    st.session_state.prefill_query = q
                    st.rerun()

        return page


page = render_sidebar()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: CHAT
# ═══════════════════════════════════════════════════════════════════════════════

def render_chat():
    # Header row with clear button aligned right
    h_col, btn_col = st.columns([5, 1])
    with h_col:
        page_header(
            "Ask Anything",
            "Powered by mistral:7b · Wikipedia Knowledge Base",
        )
    with btn_col:
        st.markdown("<div style='padding-top:6px;'>", unsafe_allow_html=True)
        if st.button("Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_query_type = None
            st.rerun()
        if st.session_state.last_query_type:
            color = {"person": "blue", "place": "teal", "both": "purple"}.get(
                st.session_state.last_query_type, "gray"
            )
            label_text = {"person": "person", "place": "place", "both": "mixed"}.get(
                st.session_state.last_query_type, ""
            )
            st.markdown(
                f'<div style="text-align:center;margin-top:8px;">'
                f'{badge(label_text, color)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Empty state
    if not st.session_state.messages:
        st.markdown("""
<div style="text-align:center;padding:56px 20px 40px;">
  <div style="font-size:40px;margin-bottom:20px;opacity:0.6;">◎</div>
  <h2 style="font-family:'Outfit',sans-serif;font-size:20px;font-weight:600;
             color:var(--text-primary);margin-bottom:8px;letter-spacing:-0.02em;">
    What would you like to know?
  </h2>
  <p style="color:var(--text-tertiary);font-size:13px;margin-bottom:32px;
            max-width:340px;margin-left:auto;margin-right:auto;line-height:1.6;">
    Ask about any of the 40 famous people and places in the knowledge base.
  </p>
</div>
""", unsafe_allow_html=True)

        chip_col1, chip_col2, chip_col3 = st.columns(3)
        suggestions = [
            "Who was Albert Einstein?",
            "Where is the Hagia Sophia?",
            "Compare Messi and Ronaldo",
        ]
        for col, suggestion in zip([chip_col1, chip_col2, chip_col3], suggestions):
            with col:
                if st.button(suggestion, use_container_width=True, key=f"chip_{suggestion}"):
                    st.session_state.prefill_query = suggestion
                    st.rerun()

    # Message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("chunks"):
                chunks = msg["chunks"]
                with st.expander(f"📎 View Sources ({len(chunks)} chunks used)"):
                    for i, chunk in enumerate(chunks, 1):
                        meta = chunk.get("metadata", {})
                        entity = meta.get("entity_name", "Unknown")
                        chunk_idx = meta.get("chunk_index", 0)
                        entity_type = meta.get("entity_type", "")
                        url = meta.get("source_url", "#")
                        dist = chunk.get("distance", 0)
                        preview = chunk["text"][:200].replace("\n", " ")
                        type_icon = "🧑" if entity_type == "person" else "🏛️"
                        relevance = max(0, 1 - dist)
                        bar_width = int(relevance * 100)

                        st.markdown(f"""
<div style="background:var(--bg-tertiary);border:1px solid var(--border-subtle);
            border-radius:10px;padding:12px 14px;margin-bottom:8px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
    {badge(entity, 'blue')}
    <span style="color:var(--text-tertiary);font-size:11px;
                 font-family:'JetBrains Mono',monospace;">{type_icon} /{chunk_idx}</span>
    <span style="color:var(--text-tertiary);font-size:11px;margin-left:auto;
                 font-family:'JetBrains Mono',monospace;">{relevance:.3f}</span>
  </div>
  <div style="background:var(--bg-secondary);border-radius:9999px;height:3px;margin-bottom:10px;">
    <div style="width:{bar_width}%;height:100%;
                background:var(--accent);border-radius:9999px;opacity:0.7;"></div>
  </div>
  <p style="color:var(--text-secondary);font-family:'DM Sans',sans-serif;
            font-size:13px;margin:0 0 8px 0;line-height:1.6;">{preview}…</p>
  <a href="{url}" target="_blank"
     style="color:var(--text-muted);font-size:11px;text-decoration:none;
            font-family:'JetBrains Mono',monospace;">
    ↗ {url[:65]}{"…" if len(url) > 65 else ""}
  </a>
</div>
""", unsafe_allow_html=True)

    # Chat input
    default_val = st.session_state.pop("prefill_query", "") if st.session_state.get("prefill_query") else ""
    query = st.chat_input(
        "Ask about a famous person or place...",
        key="chat_input",
    )

    if not query and default_val:
        query = default_val

    if query:
        if not query.strip():
            st.warning("Please enter a question.")
            return

        st.session_state.messages.append({"role": "user", "content": query})

        query_type = classify_query(query)
        st.session_state.last_query_type = query_type

        with st.spinner("Searching knowledge base..."):
            chunks = retrieve(query, n_results=8)

        with st.spinner("Generating answer..."):
            answer = generate_answer(query, chunks)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "chunks": chunks,
        })

        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: INGEST DATA
# ═══════════════════════════════════════════════════════════════════════════════

def _ingest_single(name: str, entity_type: str, log_container) -> bool:
    """Ingest a single entity. Returns True on success."""
    try:
        log_container.markdown(
            f'<span style="color:var(--accent);">⟳ Fetching Wikipedia: {name}</span>',
            unsafe_allow_html=True,
        )
        page_data = fetch_wikipedia_page(name, entity_type)
        if page_data is None:
            mark_failed(name, entity_type, "Wikipedia page not found or disambiguation failed")
            log_container.markdown(
                f'<span style="color:var(--danger);">✗ Failed to fetch: {name}</span>',
                unsafe_allow_html=True,
            )
            return False

        log_container.markdown(
            f'<span style="color:var(--text-secondary);">  ✓ Fetched · Chunking…</span>',
            unsafe_allow_html=True,
        )
        chunks = chunk_text(
            page_data["content"],
            name,
            entity_type,
            page_data["url"],
        )

        log_container.markdown(
            f'<span style="color:var(--text-secondary);">  ✓ {len(chunks)} chunks · Embedding…</span>',
            unsafe_allow_html=True,
        )
        from embeddings.embedder import embed_batch
        texts = [c["text"] for c in chunks]
        embeddings = embed_batch(texts)

        log_container.markdown(
            f'<span style="color:var(--text-secondary);">  ✓ Embedded · Storing in ChromaDB…</span>',
            unsafe_allow_html=True,
        )
        upsert_chunks(chunks, embeddings)
        mark_ingested(name, entity_type, page_data["url"], len(chunks))

        log_container.markdown(
            f'<span style="color:var(--info);">✓ Done: {name} ({len(chunks)} chunks)</span>',
            unsafe_allow_html=True,
        )
        return True

    except Exception as e:
        mark_failed(name, entity_type, str(e))
        log_container.markdown(
            f'<span style="color:var(--danger);">✗ Error ingesting {name}: {e}</span>',
            unsafe_allow_html=True,
        )
        return False


def render_ingest():
    stats = get_stats()
    total_available = len(PEOPLE) + len(PLACES)
    total_ingested = stats["success"]

    page_header(
        "📥 Knowledge Base",
        f"{total_ingested} / {total_available} entities ingested · "
        f"{stats['total_chunks']:,} total chunks",
    )

    all_entities = {e["entity_name"]: e for e in get_all_entities()}

    # Entity columns
    col_people, col_places = st.columns(2)

    selected_people = []
    selected_places = []

    with col_people:
        st.markdown(
            '<h3 style="font-family:\'Syne\',sans-serif;font-size:18px;margin-bottom:12px;">'
            '👥 People</h3>',
            unsafe_allow_html=True,
        )
        for person in PEOPLE:
            record = all_entities.get(person)
            if record and record["status"] == "success":
                chunks_badge = badge(f"{record['chunk_count']} chunks", "teal")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
                    f'border-bottom:1px solid var(--border-subtle);">'
                    f'<span>✅</span>'
                    f'<span style="color:var(--text-secondary);font-size:14px;flex:1;">{person}</span>'
                    f'{chunks_badge}</div>',
                    unsafe_allow_html=True,
                )
            elif record and record["status"] == "failed":
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
                    f'border-bottom:1px solid var(--border-subtle);">'
                    f'<span>❌</span>'
                    f'<span style="color:var(--text-secondary);font-size:14px;flex:1;">{person}</span>'
                    f'{badge("failed", "red")}</div>',
                    unsafe_allow_html=True,
                )
            else:
                checked = st.checkbox(person, key=f"chk_person_{person}")
                if checked:
                    selected_people.append(person)

    with col_places:
        st.markdown(
            '<h3 style="font-family:\'Syne\',sans-serif;font-size:18px;margin-bottom:12px;">'
            '🏛️ Places</h3>',
            unsafe_allow_html=True,
        )
        for place in PLACES:
            record = all_entities.get(place)
            if record and record["status"] == "success":
                chunks_badge = badge(f"{record['chunk_count']} chunks", "teal")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
                    f'border-bottom:1px solid var(--border-subtle);">'
                    f'<span>✅</span>'
                    f'<span style="color:var(--text-secondary);font-size:14px;flex:1;">{place}</span>'
                    f'{chunks_badge}</div>',
                    unsafe_allow_html=True,
                )
            elif record and record["status"] == "failed":
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;'
                    f'border-bottom:1px solid var(--border-subtle);">'
                    f'<span>❌</span>'
                    f'<span style="color:var(--text-secondary);font-size:14px;flex:1;">{place}</span>'
                    f'{badge("failed", "red")}</div>',
                    unsafe_allow_html=True,
                )
            else:
                checked = st.checkbox(place, key=f"chk_place_{place}")
                if checked:
                    selected_places.append(place)

    st.markdown("<br>", unsafe_allow_html=True)

    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        ingest_selected = st.button(
            "⬇️ Ingest Selected",
            use_container_width=True,
            disabled=not (selected_people or selected_places),
        )
    with btn_col2:
        ingest_all = st.button("⬇️ Ingest All", use_container_width=True, type="primary")
    with btn_col3:
        reingest_all = st.button("🔄 Re-ingest All", use_container_width=True)

    # Determine what to ingest
    entities_to_ingest: list[tuple[str, str]] = []

    if ingest_selected:
        entities_to_ingest = (
            [(p, "person") for p in selected_people]
            + [(pl, "place") for pl in selected_places]
        )
    elif ingest_all:
        not_yet = {e for e in all_entities if all_entities[e]["status"] == "success"}
        entities_to_ingest = (
            [(p, "person") for p in PEOPLE if p not in not_yet]
            + [(pl, "place") for pl in PLACES if pl not in not_yet]
        )
    elif reingest_all:
        clear_all()
        reset_collection()
        entities_to_ingest = (
            [(p, "person") for p in PEOPLE]
            + [(pl, "place") for pl in PLACES]
        )

    if entities_to_ingest:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            f'<p style="color:var(--text-secondary);font-size:14px;">Ingesting '
            f'{len(entities_to_ingest)} entities…</p>',
            unsafe_allow_html=True,
        )
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_box = st.empty()

        success_count = 0
        fail_count = 0
        log_lines: list[str] = []

        for i, (name, etype) in enumerate(entities_to_ingest):
            status_text.markdown(
                f'<p style="color:var(--text-secondary);font-size:14px;">'
                f'Processing <strong style="color:var(--text-primary);">{name}</strong> '
                f'({i+1}/{len(entities_to_ingest)})</p>',
                unsafe_allow_html=True,
            )

            class _LogContainer:
                def markdown(self_inner, text, **_):
                    log_lines.append(text)
                    log_box.markdown(
                        '<div style="background:#050508;border:1px solid var(--border-subtle);'
                        'border-radius:8px;padding:12px;max-height:240px;overflow-y:auto;'
                        'font-family:\'JetBrains Mono\',monospace;font-size:12px;">'
                        + "<br>".join(log_lines[-20:])
                        + "</div>",
                        unsafe_allow_html=True,
                    )

            ok = _ingest_single(name, etype, _LogContainer())
            if ok:
                success_count += 1
            else:
                fail_count += 1

            progress_bar.progress((i + 1) / len(entities_to_ingest))

        status_text.empty()
        st.success(f"Done! ✅ {success_count} succeeded · ❌ {fail_count} failed")
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: DEBUG / EXPLORE
# ═══════════════════════════════════════════════════════════════════════════════

def render_debug():
    page_header(
        "🔍 Vector Store Explorer",
        "Directly query ChromaDB without the RAG pipeline",
    )

    search_col, ctrl_col = st.columns([3, 1])

    with search_col:
        search_query = st.text_input(
            "Search query",
            placeholder="Enter a search query to find matching chunks…",
            label_visibility="collapsed",
        )

    with ctrl_col:
        n_results = st.slider("Results", 1, 20, 5, label_visibility="collapsed")

    filter_option = st.radio(
        "Filter by type",
        ["All", "👤 People", "🏛️ Places"],
        horizontal=True,
    )
    entity_type_filter = {
        "All": None,
        "👤 People": "person",
        "🏛️ Places": "place",
    }[filter_option]

    if st.button("🔍 Search", type="primary") and search_query.strip():
        with st.spinner("Embedding query and searching…"):
            try:
                query_embedding = embed_text(search_query)
                results = chroma_query(
                    query_embedding,
                    entity_type=entity_type_filter,
                    n_results=n_results,
                )
            except Exception as e:
                st.error(f"Search failed: {e}")
                return

        if not results:
            st.info("No results found. Try a different query or ingest more data.")
            return

        st.markdown(
            f'<p style="color:var(--text-secondary);font-size:14px;margin-bottom:16px;">'
            f'Found {len(results)} results</p>',
            unsafe_allow_html=True,
        )

        for i, result in enumerate(results):
            meta = result.get("metadata", {})
            entity = meta.get("entity_name", "Unknown")
            chunk_idx = meta.get("chunk_index", 0)
            entity_type = meta.get("entity_type", "")
            url = meta.get("source_url", "#")
            dist = result.get("distance", 0)
            relevance = max(0, 1 - dist)
            bar_width = int(relevance * 100)

            dist_color = (
                "#22c55e" if relevance > 0.7
                else ("var(--warning)" if relevance > 0.4 else "var(--danger)")
            )
            type_icon = "🧑" if entity_type == "person" else "🏛️"

            with st.expander(f"{type_icon} {entity} — chunk {chunk_idx} · score {relevance:.3f}"):
                st.markdown(f"""
<div style="margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
    {badge(entity, 'blue')}
    {badge(entity_type, 'purple')}
    <span style="color:{dist_color};font-size:12px;margin-left:auto;">
      distance: {dist:.4f}
    </span>
  </div>
  <div style="background:var(--bg-secondary);border-radius:4px;height:6px;margin-bottom:12px;">
    <div style="width:{bar_width}%;height:100%;background:{dist_color};
                border-radius:4px;transition:width 0.3s;"></div>
  </div>
</div>
""", unsafe_allow_html=True)

                st.markdown(
                    f'<div style="color:var(--text-secondary);font-family:\'DM Sans\',sans-serif;'
                    f'font-size:14px;line-height:1.6;white-space:pre-wrap;">'
                    f'{result["text"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<a href="{url}" target="_blank" '
                    f'style="color:var(--text-tertiary);font-size:11px;text-decoration:none;">'
                    f'🔗 {url}</a>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: ABOUT
# ═══════════════════════════════════════════════════════════════════════════════

def render_about():
    page_header("ℹ️ About WikiRAG", "Local AI · Wikipedia RAG System")

    # Architecture diagram
    st.markdown("""
<div style="background:var(--bg-secondary);border:1px solid var(--border-subtle);
            border-radius:16px;padding:24px;margin-bottom:28px;">
  <h3 style="font-family:'Outfit',sans-serif;font-size:16px;color:var(--text-primary);
             margin-bottom:20px;text-transform:uppercase;letter-spacing:1px;font-size:12px;
             color:var(--text-tertiary);">System Architecture</h3>

  <div style="display:flex;align-items:center;justify-content:center;
              flex-wrap:wrap;gap:6px;margin-bottom:16px;">
    <div style="background:linear-gradient(135deg,#5B8DEF22,#5B8DEF11);
                border:1px solid #5B8DEF44;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">🌐</div>
      <div style="font-size:12px;color:var(--accent);font-weight:600;">Wikipedia</div>
      <div style="font-size:10px;color:var(--text-tertiary);">wikipedia-api</div>
    </div>
    <div style="color:var(--accent);font-size:18px;animation:flow 2s infinite;">→</div>
    <div style="background:linear-gradient(135deg,#8B5CF622,#8B5CF611);
                border:1px solid #8B5CF644;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">📥</div>
      <div style="font-size:12px;color:#A78BFA;font-weight:600;">Fetcher</div>
      <div style="font-size:10px;color:var(--text-tertiary);">wikipedia_fetcher</div>
    </div>
    <div style="color:var(--accent);font-size:18px;animation:flow 2s infinite 0.3s;">→</div>
    <div style="background:linear-gradient(135deg,#2DD4BF22,#2DD4BF11);
                border:1px solid #2DD4BF44;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">✂️</div>
      <div style="font-size:12px;color:var(--info);font-weight:600;">Chunker</div>
      <div style="font-size:10px;color:var(--text-tertiary);">sliding window</div>
    </div>
    <div style="color:var(--accent);font-size:18px;animation:flow 2s infinite 0.6s;">→</div>
    <div style="background:linear-gradient(135deg,#F59E0B22,#F59E0B11);
                border:1px solid #F59E0B44;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">🔢</div>
      <div style="font-size:12px;color:var(--warning);font-weight:600;">Embedder</div>
      <div style="font-size:10px;color:var(--text-tertiary);">nomic-embed-text</div>
    </div>
    <div style="color:var(--accent);font-size:18px;animation:flow 2s infinite 0.9s;">→</div>
    <div style="background:linear-gradient(135deg,#5B8DEF22,#5B8DEF11);
                border:1px solid #5B8DEF44;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">🗄️</div>
      <div style="font-size:12px;color:var(--accent);font-weight:600;">ChromaDB</div>
      <div style="font-size:10px;color:var(--text-tertiary);">vector store</div>
    </div>
  </div>

  <div style="display:flex;justify-content:center;margin-bottom:16px;">
    <div style="text-align:center;color:var(--accent);font-size:18px;">↓ query time ↓</div>
  </div>

  <div style="display:flex;align-items:center;justify-content:center;
              flex-wrap:wrap;gap:6px;">
    <div style="background:linear-gradient(135deg,#5B8DEF22,#5B8DEF11);
                border:1px solid #5B8DEF44;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">💬</div>
      <div style="font-size:12px;color:var(--accent);font-weight:600;">Streamlit UI</div>
      <div style="font-size:10px;color:var(--text-tertiary);">user interface</div>
    </div>
    <div style="color:var(--accent);font-size:18px;">←</div>
    <div style="background:linear-gradient(135deg,#EF444422,#EF444411);
                border:1px solid #EF444444;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">🤖</div>
      <div style="font-size:12px;color:var(--danger);font-weight:600;">LLM</div>
      <div style="font-size:10px;color:var(--text-tertiary);">mistral:7b</div>
    </div>
    <div style="color:var(--accent);font-size:18px;">←</div>
    <div style="background:linear-gradient(135deg,#8B5CF622,#8B5CF611);
                border:1px solid #8B5CF644;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">🔍</div>
      <div style="font-size:12px;color:#A78BFA;font-weight:600;">Retriever</div>
      <div style="font-size:10px;color:var(--text-tertiary);">classifier + query</div>
    </div>
    <div style="color:var(--accent);font-size:18px;">←</div>
    <div style="background:linear-gradient(135deg,#2DD4BF22,#2DD4BF11);
                border:1px solid #2DD4BF44;border-radius:10px;
                padding:10px 14px;text-align:center;min-width:90px;">
      <div style="font-size:20px;">🗄️</div>
      <div style="font-size:12px;color:var(--info);font-weight:600;">ChromaDB</div>
      <div style="font-size:10px;color:var(--text-tertiary);">similarity search</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Stats grid
    stats = get_stats()
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(metric_card(str(stats["success"]), "Entities Indexed", "📚"), unsafe_allow_html=True)
    with s2:
        st.markdown(metric_card(str(stats["people_success"]), "People Indexed", "👤"), unsafe_allow_html=True)
    with s3:
        st.markdown(metric_card(str(stats["places_success"]), "Places Indexed", "🏛️"), unsafe_allow_html=True)
    with s4:
        st.markdown(metric_card(f"{stats['total_chunks']:,}", "Total Chunks", "📄"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tech stack
    st.markdown("""
<h3 style="font-family:'Outfit',sans-serif;font-size:16px;color:var(--text-primary);
           margin-bottom:12px;">Tech Stack</h3>
<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;">
""", unsafe_allow_html=True)

    tech_items = [
        ("🤖", "mistral:7b", "LLM"),
        ("📐", "nomic-embed-text", "Embeddings"),
        ("🗄️", "ChromaDB", "Vector Store"),
        ("🐍", "Python 3.10+", "Language"),
        ("🖥️", "Streamlit", "UI Framework"),
        ("📦", "SQLite", "Metadata DB"),
        ("🌐", "wikipedia-api", "Data Source"),
        ("⚙️", "Ollama", "Local AI Runtime"),
    ]

    cols = st.columns(4)
    for i, (icon, name, role) in enumerate(tech_items):
        with cols[i % 4]:
            st.markdown(f"""
<div style="background:var(--bg-tertiary);border:1px solid var(--border-subtle);
            border-radius:10px;padding:12px;text-align:center;margin-bottom:8px;">
  <div style="font-size:22px;margin-bottom:4px;">{icon}</div>
  <div style="font-size:13px;font-weight:600;color:var(--text-primary);">{name}</div>
  <div style="font-size:11px;color:var(--text-tertiary);">{role}</div>
</div>
""", unsafe_allow_html=True)

    # Entity lists
    st.markdown("<br>", unsafe_allow_html=True)
    col_p, col_pl = st.columns(2)

    with col_p:
        st.markdown(
            '<h3 style="font-family:\'Syne\',sans-serif;font-size:16px;margin-bottom:10px;">👥 People</h3>',
            unsafe_allow_html=True,
        )
        all_entities_db = {e["entity_name"]: e for e in get_all_entities()}
        for person in PEOPLE:
            record = all_entities_db.get(person)
            status = "✅" if (record and record["status"] == "success") else (
                "❌" if (record and record["status"] == "failed") else "⏳"
            )
            st.markdown(
                f'<div style="padding:4px 0;border-bottom:1px solid var(--border-subtle);'
                f'font-size:13px;color:var(--text-secondary);">{status} {person}</div>',
                unsafe_allow_html=True,
            )

    with col_pl:
        st.markdown(
            '<h3 style="font-family:\'Syne\',sans-serif;font-size:16px;margin-bottom:10px;">🏛️ Places</h3>',
            unsafe_allow_html=True,
        )
        for place in PLACES:
            record = all_entities_db.get(place)
            status = "✅" if (record and record["status"] == "success") else (
                "❌" if (record and record["status"] == "failed") else "⏳"
            )
            st.markdown(
                f'<div style="padding:4px 0;border-bottom:1px solid var(--border-subtle);'
                f'font-size:13px;color:var(--text-secondary);">{status} {place}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p style="color:var(--text-tertiary);font-size:12px;">Chunk size: 500 chars · '
        'Overlap: 100 chars · Min chunk: 100 chars · '
        'Collection: wiki_rag (single, metadata-filtered)</p>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════════════════════════

if page == "💬 Chat":
    render_chat()
elif page == "📥 Ingest Data":
    render_ingest()
elif page == "🔍 Debug / Explore":
    render_debug()
elif page == "ℹ️ About":
    render_about()
