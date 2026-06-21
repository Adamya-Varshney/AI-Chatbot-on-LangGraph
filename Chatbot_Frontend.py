import streamlit as st
from Chatbot_Backend import (
    chatbot,
    generate_title,
    ingest_pdf,
    thread_document_metadata,
)
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones


st.markdown("""
<style>
/* Main canvas — dirty white */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: #F3F1EA;
}

/* ---------- Sidebar — deep navy ---------- */
[data-testid="stSidebar"] {
    background-color: #16243F;
    border-right: 1px solid #0E1A30;
}
/* Light text on the navy sidebar (headings + input labels) */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label {
    color: #E8EEF8 !important;
}

/* ---------- Buttons — light blue, pop against navy ---------- */
.stButton > button {
    background-color: #DCEBF5;
    color: #143B4F;
    border: 1px solid #AFCFE3;
    border-radius: 8px;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background-color: #C7DEF0;
    border-color: #7FB2D4;
    color: #0E2D3E;
}

/* ---------- Input boxes — deep navy, a shade lighter than the sidebar ---------- */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] > div,
[data-testid="stChatInput"] {
    background-color: #22365C !important;
    border: 1px solid #3E5A8A !important;
    border-radius: 8px;
}
/* Typed text, selected value, chat input — light */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] span,
[data-testid="stChatInput"] textarea {
    color: #EAF1F8 !important;
}
/* Placeholders — muted light blue */
.stTextInput input::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: #9DB0CC !important;
}
/* Send icon — light so it's visible on navy */
[data-testid="stChatInput"] button svg {
    fill: #EAF1F8 !important;
}
/* Dropdown list popup — keep readable */
ul[role="listbox"] {
    background-color: #22365C !important;
}
ul[role="listbox"] li {
    color: #EAF1F8 !important;
}

/* ---------- Chat bubbles — soft white cards (dark text stays readable) ---------- */
[data-testid="stChatMessage"] {
    background-color: #FBFBF6;
    border: 1px solid #E7E4D9;
    border-radius: 12px;
    padding: 0.5rem 0.75rem;
}

/* ---------- Conversation area — framed blue rectangle, responsive ---------- */
[data-testid="stMainBlockContainer"] {
    background-color: #E9F2FB;                 /* subtle blue fill */
    border: 2px solid #5B9BD5;                 /* the blue rectangle */
    border-radius: 16px;
    box-shadow: 0 4px 18px rgba(27, 42, 74, 0.12);
    padding: 1.5rem 1.75rem 2rem !important;
    max-width: 900px !important;               /* tidy on wide screens */
    width: 92% !important;                      /* shrinks on smaller screens */
    margin: 1.5rem auto !important;            /* centered */
}

/* Align the pinned chat input under the rectangle */
[data-testid="stBottom"] .block-container {
    max-width: 900px !important;
    margin: 0 auto !important;
}

/* ---------- Responsiveness ---------- */
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        width: 96% !important;
        padding: 1rem 1rem 1.5rem !important;
        border-radius: 12px;
        margin: 0.75rem auto !important;
    }
    [data-testid="stBottom"] .block-container {
        max-width: 96% !important;
    }
}


/* ---------- Location / Time info card ---------- */
.info-card {
    width: fit-content;
    margin-left: auto;                        /* sits top-right */
    background: #FFFFFF;
    border: 1.5px solid #5B9BD5;              /* the bordered section */
    border-radius: 12px;
    padding: 0.5rem 0.85rem;
    box-shadow: 0 2px 8px rgba(27, 42, 74, 0.10);
    font-size: 0.82rem;
    line-height: 1.6;
}
.info-card .info-row {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.4rem;
    color: #4F6B7A;
}
.info-card .info-row.info-time {
    font-weight: 600;
    color: #1F4E66;
}
.info-card svg {
    width: 14px;
    height: 14px;
    color: #4F8FB0;                           /* icon color (via currentColor) */
    flex-shrink: 0;
}

/* "Your time zone" selectbox — force white text in the field & search */
.stSelectbox div[data-baseweb="select"],
.stSelectbox div[data-baseweb="select"] *,
.stSelectbox div[data-baseweb="select"] input {
    color: #EAF1F8 !important;
    -webkit-text-fill-color: #EAF1F8 !important;
}
</style>
""", unsafe_allow_html=True)

# **************************************** utility functions *************************

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

@st.fragment(run_every="1s")
def render_live_time():
    tz_name = st.session_state.get('user_timezone', 'Asia/Kolkata')
    now = datetime.now(ZoneInfo(tz_name))
    st.markdown(f"**Time zone**  \n{tz_name}")
    st.markdown(f"**Date**  \n{now.strftime('%a, %d %b %Y')}")
    st.markdown(f"**Time**  \n{now.strftime('%I:%M:%S %p')}")

# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

if 'chat_titles' not in st.session_state:
    st.session_state['chat_titles'] = {}

if 'user_location' not in st.session_state:
    st.session_state['user_location'] = ''
if 'user_timezone' not in st.session_state:
    st.session_state['user_timezone'] = 'Asia/Kolkata'
if 'settings_expanded' not in st.session_state:
    st.session_state['settings_expanded'] = True

if 'ingested_docs' not in st.session_state:
    st.session_state['ingested_docs'] = {}

add_thread(st.session_state['thread_id'])

if 'editing_thread' not in st.session_state:
    st.session_state['editing_thread'] = None

thread_key = str(st.session_state['thread_id'])
thread_docs = st.session_state['ingested_docs'].setdefault(thread_key, {})

# **************************************** Sidebar UI *********************************
st.sidebar.title('SAM : Ai Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()
    st.rerun()

# ---- PDF Upload ----
st.sidebar.header('Document Upload')

if thread_docs:
    latest_doc = list(thread_docs.values())[-1]
    st.sidebar.success(
        f"PDF indexed: **{latest_doc.get('filename')}** "
        f"({latest_doc.get('chunks')} chunks, {latest_doc.get('documents')} pages)"
    )
else:
    st.sidebar.info("No PDF indexed for this chat.")

uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for RAG", type=["pdf"])
if uploaded_pdf:
    if uploaded_pdf.name in thread_docs:
        st.sidebar.info(f"`{uploaded_pdf.name}` already processed for this chat.")
    else:
        with st.sidebar.status("Indexing PDF...", expanded=True) as status_box:
            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                thread_id=thread_key,
                filename=uploaded_pdf.name,
            )
            thread_docs[uploaded_pdf.name] = summary
            status_box.update(label="PDF indexed successfully", state="complete", expanded=False)

# ---- Conversations list ----
st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    title = st.session_state['chat_titles'].get(thread_id, 'New Chat')

    if st.session_state['editing_thread'] == thread_id:
        new_title = st.sidebar.text_input(
            'Rename chat',
            value=title,
            key=f'edit_input_{thread_id}',
            label_visibility='collapsed',
        )
        save_col, cancel_col = st.sidebar.columns(2)
        if save_col.button('Save', key=f'save_{thread_id}'):
            st.session_state['chat_titles'][thread_id] = new_title.strip() or title
            st.session_state['editing_thread'] = None
            st.rerun()
        if cancel_col.button('Cancel', key=f'cancel_{thread_id}'):
            st.session_state['editing_thread'] = None
            st.rerun()

    else:
        open_col, edit_col = st.sidebar.columns([4, 1.5])
        if open_col.button(title, key=str(thread_id)):
            st.session_state['thread_id'] = thread_id
            messages = load_conversation(thread_id)
            temp_messages = []
            for msg in messages:
                role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                temp_messages.append({'role': role, 'content': msg.content})
            st.session_state['message_history'] = temp_messages
            st.session_state['ingested_docs'].setdefault(str(thread_id), {})
            st.rerun()
        if edit_col.button('Edit', key=f'edit_{thread_id}'):
            st.session_state['editing_thread'] = thread_id
            st.rerun()


# ---- Location & Time Zone (collapsible) ----
tz_options = sorted(available_timezones())

if st.session_state['settings_expanded']:
    st.sidebar.header('Location & Time Zone')

    loc = st.sidebar.text_input(
        'Your location (city, country)',
        value=st.session_state['user_location'],
        placeholder='e.g., Noida, India',
        key='loc_input',
    )
    tz = st.sidebar.selectbox(
        'Your time zone',
        options=tz_options,
        index=tz_options.index(st.session_state['user_timezone']),
        key='tz_input',
    )

    if st.sidebar.button('Save', key='save_settings'):
        st.session_state['user_location'] = loc.strip()
        st.session_state['user_timezone'] = tz
        st.session_state['settings_expanded'] = False
        st.rerun()
else:
    if st.sidebar.button('', icon=':material/edit_location:',
                         key='expand_settings', help='Set location & time zone'):
        st.session_state['settings_expanded'] = True
        st.rerun()


# **************************************** Main UI ************************************
_, loc_col, time_col = st.columns([8, 1, 1])

with loc_col:
    with st.popover("", icon=":material/location_on:"):
        loc = st.session_state.get('user_location', '').strip() or '—'
        st.markdown(f"**Location**  \n{loc}")

with time_col:
    with st.popover("", icon=":material/schedule:"):
        render_live_time()


for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_input = st.chat_input('Ask about your document, search the web, or run code')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    tz_name = st.session_state.get('user_timezone', 'Asia/Kolkata')
    CONFIG = {
        'configurable': {
            'thread_id': thread_key,
            'user_location': st.session_state.get('user_location', ''),
            'user_timezone': tz_name,
            'local_time': datetime.now(ZoneInfo(tz_name)).strftime('%A, %d %B %Y, %I:%M %p'),
        }
    }

    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"Using {tool_name}...", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"Using {tool_name}...",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="Tool finished", state="complete", expanded=False
            )

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    doc_meta = thread_document_metadata(thread_key)
    if doc_meta:
        st.caption(
            f"Document indexed: {doc_meta.get('filename')} "
            f"(chunks: {doc_meta.get('chunks')}, pages: {doc_meta.get('documents')})"
        )

    current_thread = st.session_state['thread_id']
    if current_thread not in st.session_state['chat_titles']:
        st.session_state['chat_titles'][current_thread] = generate_title(user_input, ai_message)
        st.rerun()
