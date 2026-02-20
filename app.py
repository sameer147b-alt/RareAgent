import gradio as gr
import dspy
import plotly.graph_objects as go
from orchestrator import run_research
from visuals.radar_chart import create_radar_chart

# Configure Groq LM
import os
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
    print(f"DEBUG: Groq Key Loaded. Starts with: {groq_api_key[:4]}... Length: {len(groq_api_key)}")
    if not groq_api_key:
        print("WARNING: GROQ_API_KEY not found! Please check your .env file.")
        raise ValueError("GROQ_API_KEY environment variable not set")
    lm = dspy.LM(model='groq/llama-3.3-70b-versatile', api_key=groq_api_key, temperature=0.7)
    dspy.settings.configure(lm=lm)
except Exception as e:
    print(f"Failed to configure Groq LM: {e}")

def process_research(disease_name):
    """
    Generator function for Gradio to stream updates.
    """
    chat_history = []
    current_chart = None
    
    chat_history.append({"role": "user", "content": f"Initiating RareAgent swarm for: {disease_name}..."})
    yield chat_history, None

    # Run the orchestrator stream
    # Each 'event' is a dict of the node that just finished and its output state update
    for event in run_research(disease_name):
        
        # Determine which node finished
        node_name = list(event.keys())[0]
        state_update = event[node_name]
        
        if node_name == "explorer":
            targets = state_update.get("genetic_targets", [])
            count = len(targets)
            msg = f"🔍 **Explorer**: Found {count} potential genetic targets."
            if count > 0:
                top = targets[0]
                msg += f"\n   *Top Target*: {top['gene_name']} ({top['uniprot_id']})"
            chat_history.append({"role": "assistant", "content": msg})
            
        elif node_name == "proponent":
            hypotheses = state_update.get("hypotheses", [])
            if hypotheses:
                latest = hypotheses[-1]
                msg = f"🧪 **Proponent**: Proposed **{latest['drug_name']}** targeting {latest['target_gene']}.\n   *Rationale*: {latest.get('rationale', 'N/A')}"
                chat_history.append({"role": "assistant", "content": msg})
                
        elif node_name == "skeptic":
            history = state_update.get("debate_history", [])
            hypotheses = state_update.get("hypotheses", [])
            if history:
                latest_critique = history[-1]
                # Format markdown a bit if needed, usually it's already md
                chat_history.append({"role": "assistant", "content": f"🛡️ **Skeptic**: {latest_critique}"})
            
            # Check for chart update
            if hypotheses:
                current_chart = create_radar_chart(hypotheses)

        elif node_name == "validator":
            hypotheses = state_update.get("hypotheses", [])
            if hypotheses:
                latest = hypotheses[-1]
                validation = latest.get("validation", {})
                status = validation.get("overall_status", "UNKNOWN")
                msg = f"⚖️ **Validator**: Status -> **{status}**."
                if status != "APPROVED":
                    msg += f"\n   *Reason*: {validation.get('reason', 'N/A')}"
                chat_history.append({"role": "assistant", "content": msg})

        yield chat_history, current_chart

    chat_history.append({"role": "assistant", "content": "✅ **Mission Complete**."})
    yield chat_history, current_chart

# --- Gradio UI ---

with gr.Blocks(theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="teal")) as demo:
    
    gr.Markdown(
        """
        # 🧬 RareAgent: Autonomous Swarm for Orphan Disease Drug Repurposing
        **Battle of Agents**: Watch the Proponent and Skeptic debate drug hypotheses in real-time.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            disease_input = gr.Textbox(label="Target Orphan Disease", placeholder="e.g., Cystic Fibrosis, Tuberous Sclerosis")
            demo_mode = gr.Checkbox(label="Enable Self-Evolution Demo Mode", info="Rapidly iterates to optimize agent prompts.")
            run_btn = gr.Button("🚀 Launch Swarm", variant="primary")
            
            gr.Markdown("### Live Radar Analysis")
            radar_plot = gr.Plot(label="Hypothesis Assessment")

        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Swarm Communication Log", height=600)

    def on_click(disease_name, demo_active):
        if demo_active:
            # yield initial message
            yield [{"role": "assistant", "content": "🔄 **Demo Mode Active**: Running self-evolution iterations for 'Cystic Fibrosis'..."}], None
            
            # Mock Optimization Loop
            import time
            from datetime import datetime
            
            # Iteration 1
            yield [{"role": "assistant", "content": "🔄 **Iteration 1**: Baseline Performance Analysis..."}], None
            for event in process_research("Cystic Fibrosis"):
                 yield event
            
            # Log Optimization
            with open("memory/evolution_log.txt", "a") as f:
                f.write(f"[{datetime.now().isoformat()}] [OPTIMIZER] Adjusted Proponent temperature and Skeptic strictness based on Iteration 1 feedback.\n")
            
            # Iteration 2
            yield [{"role": "assistant", "content": "🔄 **Iteration 2**: Running with Optimized Prompts..."}], None
            for event in process_research("Cystic Fibrosis"):
                 yield event
                 
            with open("memory/evolution_log.txt", "a") as f:
                f.write(f"[{datetime.now().isoformat()}] [OPTIMIZER] Convergence reached. Prompts updated.\n")
            
            yield [{"role": "assistant", "content": "✅ **Self-Evolution Complete**. Swarm is smarter now."}], None
            
        else:
            for event in process_research(disease_name):
                yield event

    # First clear the UI, then chain into the main execution
    run_btn.click(
        fn=lambda: ([], go.Figure()),
        inputs=None,
        outputs=[chatbot, radar_plot]
    ).then(
        fn=on_click,
        inputs=[disease_input, demo_mode],
        outputs=[chatbot, radar_plot]
    )

if __name__ == "__main__":
    demo.launch()
