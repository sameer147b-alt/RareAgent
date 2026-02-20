import streamlit as st
import dspy
import os
from dotenv import load_dotenv
from orchestrator import run_research
from visuals.radar_chart import create_radar_chart

# --- Configure Groq LM (cached to survive Streamlit reruns) ---
load_dotenv(override=True)

@st.cache_resource
def setup_llm():
    api_key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found! Please check your .env file.")
    lm = dspy.LM(model='groq/llama-3.3-70b-versatile', api_key=api_key, temperature=0.7)
    dspy.settings.configure(lm=lm)
    return True

try:
    setup_llm()
except Exception as e:
    st.error(f"⚠️ Failed to configure Groq LM: {e}")
    st.stop()

# --- Page Config ---
st.set_page_config(
    page_title="RareAgent – Orphan Drug Repurposing Swarm",
    page_icon="🧬",
    layout="wide"
)

# --- Session State Initialization ---
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "radar_chart" not in st.session_state:
    st.session_state.radar_chart = None
if "swarm_running" not in st.session_state:
    st.session_state.swarm_running = False
if "last_disease" not in st.session_state:
    st.session_state.last_disease = ""

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/dna-helix.png", width=64)
    st.title("🧬 RareAgent")
    st.caption("Autonomous Swarm for Orphan Drug Repurposing")
    st.divider()

    disease_name = st.text_input(
        "Target Orphan Disease",
        placeholder="e.g., Cystic Fibrosis, Tuberous Sclerosis"
    )

    launch_btn = st.button("🚀 Launch Swarm", type="primary", use_container_width=True)

    st.divider()
    st.markdown("### 📡 Live Radar Analysis")
    radar_placeholder = st.empty()

    # Render radar chart if one exists
    if st.session_state.radar_chart is not None:
        radar_placeholder.plotly_chart(st.session_state.radar_chart, use_container_width=True)

# --- Main Content ---
st.markdown(
    """
    # 🧬 RareAgent: Autonomous Swarm for Orphan Disease Drug Repurposing
    **Battle of Agents**: Watch the Proponent and Skeptic debate drug hypotheses in real-time.
    """
)

# --- Render Existing Chat Log ---
for msg in st.session_state.chat_log:
    role = msg["role"]
    avatar = "🧑‍🔬" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# --- Swarm Execution ---
if launch_btn and disease_name:
    # Reset state if the disease changed
    if disease_name != st.session_state.last_disease:
        st.session_state.chat_log = []
        st.session_state.radar_chart = None
        st.session_state.last_disease = disease_name

    # Clear previous run for a fresh start
    st.session_state.chat_log = []
    st.session_state.radar_chart = None

    # Add user message
    user_msg = {"role": "user", "content": f"Initiating RareAgent swarm for: **{disease_name}**..."}
    st.session_state.chat_log.append(user_msg)
    with st.chat_message("user", avatar="🧑‍🔬"):
        st.markdown(user_msg["content"])

    # Create a placeholder for the status spinner
    status_placeholder = st.empty()

    with status_placeholder.status("🔬 Swarm is running...", expanded=True) as status:
        for event in run_research(disease_name):
            node_name = list(event.keys())[0]
            state_update = event[node_name]

            if node_name == "explorer":
                targets = state_update.get("genetic_targets", [])
                count = len(targets)
                msg_text = f"🔍 **Explorer**: Found {count} potential genetic targets."
                if count > 0:
                    top = targets[0]
                    msg_text += f"\n\n*Top Target*: `{top['gene_name']}` (`{top['uniprot_id']}`)"
                st.write(f"Explorer found {count} targets...")
                assistant_msg = {"role": "assistant", "content": msg_text}
                st.session_state.chat_log.append(assistant_msg)
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg_text)

            elif node_name == "proponent":
                hypotheses = state_update.get("hypotheses", [])
                if hypotheses:
                    latest = hypotheses[-1]
                    msg_text = f"🧪 **Proponent**: Proposed **{latest['drug_name']}** targeting `{latest['target_gene']}`.\n\n*Rationale*: {latest.get('rationale', 'N/A')}"
                    st.write(f"Proponent proposed: {latest['drug_name']}")
                    assistant_msg = {"role": "assistant", "content": msg_text}
                    st.session_state.chat_log.append(assistant_msg)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg_text)

            elif node_name == "skeptic":
                history = state_update.get("debate_history", [])
                hypotheses = state_update.get("hypotheses", [])
                if history:
                    latest_critique = history[-1]
                    msg_text = f"🛡️ **Skeptic**: {latest_critique}"
                    st.write("Skeptic delivered critique...")
                    assistant_msg = {"role": "assistant", "content": msg_text}
                    st.session_state.chat_log.append(assistant_msg)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg_text)

                # Update radar chart
                if hypotheses:
                    st.session_state.radar_chart = create_radar_chart(hypotheses)
                    radar_placeholder.plotly_chart(st.session_state.radar_chart, use_container_width=True)

            elif node_name == "validator":
                hypotheses = state_update.get("hypotheses", [])
                if hypotheses:
                    latest = hypotheses[-1]
                    validation = latest.get("validation", {})
                    overall_status = validation.get("overall_status", "UNKNOWN")
                    msg_text = f"⚖️ **Validator**: Status -> **{overall_status}**."
                    if overall_status != "APPROVED":
                        msg_text += f"\n\n*Reason*: {validation.get('reason', 'N/A')}"
                    st.write(f"Validator: {overall_status}")
                    assistant_msg = {"role": "assistant", "content": msg_text}
                    st.session_state.chat_log.append(assistant_msg)
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg_text)

        status.update(label="✅ Swarm Mission Complete!", state="complete", expanded=False)

    # Final message
    complete_msg = {"role": "assistant", "content": "✅ **Mission Complete**."}
    st.session_state.chat_log.append(complete_msg)
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(complete_msg["content"])

elif launch_btn and not disease_name:
    st.sidebar.warning("Please enter a disease name before launching the swarm.")
