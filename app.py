import streamlit as st
import requests

API = "http://localhost:8000"

st.set_page_config(page_title="AI Job Recommender", page_icon="💼", layout="wide")
st.title("💼 AI Job Recommender")
st.caption("Upload your resume → Get AI-powered job matches + chat with your resume")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 User Setup")

    # register / login by email
    email = st.text_input("Your Email")
    name = st.text_input("Your Name (only needed first time)")

    if st.button("Login / Register"):
        if not email:
            st.warning("Enter your email.")
        else:
            # check if user already exists
            res = requests.get(f"{API}/users/by-email/{email}")
            if res.status_code == 200:
                # existing user — log them in directly
                st.session_state["user"] = res.json()
                st.success(f"Welcome back, {res.json()['name']}!")
            else:
                # new user — register them
                if not name:
                    st.warning("New user? Please enter your name too.")
                else:
                    res2 = requests.post(f"{API}/users", json={"name": name, "email": email})
                    if res2.status_code == 201:
                        st.session_state["user"] = res2.json()
                        st.success(f"Welcome, {res2.json()['name']}!")
                    else:
                        st.error("Registration failed. Try again.")

    if "user" in st.session_state and st.session_state["user"].get("id"):
        st.divider()
        st.header("📄 Upload Resume")
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

        if uploaded_file and st.button("📤 Upload & Process"):
            with st.spinner("Processing resume...."):
                res = requests.post(
                    f"{API}/users/{st.session_state['user']['id']}/resume",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                )
            if res.status_code == 200:
                data = res.json()
                st.success(f"✅ Resume indexed! ({data['chunks_indexed']} chunks)")
                st.session_state["resume_uploaded"] = True
            else:
                st.error(res.json().get("detail", "Upload failed."))

    st.divider()
    st.markdown("**How it works:**")
    st.markdown("1. Register with email")
    st.markdown("2. Upload PDF resume")
    st.markdown("3. Get AI job matches")
    st.markdown("4. Chat with your resume")

# ── Guard: must be logged in ─────────────────────────────────────────────────
if "user" not in st.session_state or not st.session_state["user"].get("id"):
    st.info("👈 Please login or register from the sidebar to get started.")
    st.stop()

user_id = st.session_state["user"]["id"]

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 Job Recommendations", "💬 Chat with Resume", "📋 History"])

# ── Tab 1: Recommendations ────────────────────────────────────────────────────
with tab1:
    st.subheader("Get Personalized Job Recommendations")
    focus = st.text_input("Any specific role or skill focus? (optional)", placeholder="e.g. AI/ML roles, backend")

    if st.button("🔍 Find My Best Jobs", type="primary"):
        with st.spinner("Analyzing your resume and matching jobs..."):
            res = requests.post(f"{API}/recommend", json={"user_id": user_id, "query": focus})
        if res.status_code == 200:
            st.markdown("### 🏆 Your Top Job Matches")
            st.markdown(res.json()["result"])
        else:
            st.error(res.json().get("detail", "Error getting recommendations."))

# ── Tab 2: Chat ───────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Chat with Your Resume")
    st.caption("Ask: 'What are my strongest skills?', 'Am I ready for senior roles?'")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask about your resume...")
    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                res = requests.post(f"{API}/chat", json={"user_id": user_id, "message": user_input})
            if res.status_code == 200:
                reply = res.json()["reply"]
                st.write(reply)
                st.session_state["chat_history"].append({"role": "assistant", "content": reply})
            else:
                st.error(res.json().get("detail", "Error."))

# ── Tab 3: History ────────────────────────────────────────────────────────────
with tab3:
    st.subheader("📋 Your History")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Past Recommendations**")
        if st.button("Load Recommendations"):
            res = requests.get(f"{API}/users/{user_id}/recommendations")
            if res.status_code == 200:
                for item in res.json():
                    with st.expander(f"Query: {item['query'] or 'General'} — {item['created_at']}"):
                        st.markdown(item["result"])
            else:
                st.error("Could not load history.")

    with col2:
        st.markdown("**Past Chats**")
        if st.button("Load Chat History"):
            res = requests.get(f"{API}/users/{user_id}/chats")
            if res.status_code == 200:
                for msg in res.json():
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
            else:
                st.error("Could not load chats.")
