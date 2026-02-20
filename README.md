# 🧬 RareAgent: Autonomous Swarm for Orphan Drug Repurposing

## Abstract
**RareAgent** is an advanced, multi-agent AI system designed to tackle one of the most challenging problems in modern medicine: orphan diseases. By leveraging an autonomous reasoning "swarm," RareAgent dynamically evaluates existing, FDA-approved drugs to identify novel, viable repurposing candidates for rare genetic disorders. 

Through its unique architecture of antagonistic generative agents (Proponent vs. Skeptic) governed by deterministic biological guardrails (Validator), RareAgent synthesizes literature, infers genetic targets, and significantly reduces hallucinations to propose scientifically grounded hypotheses.

## 🚀 Key Features
- **Multi-Agent Debate Framework**: A generative `Proponent` proposes drug candidates, while an adversarial `Skeptic` aggressively critiques their clinical safety and efficacy.
- **Deterministic Validation Loop**: A robust `Validator` agent ensures hypotheses are anchored in reality by verifying drug-target-disease linkages against deterministic databases.
- **Self-Correcting "Taboo List" Memory**: The swarm learns from its mistakes, dynamically ingesting rejection reasons and employing an "Exclusion Memory" to never repeat invalid guesses, forcing the deep exploration of novel biological pathways.
- **Interactive Visualizations**: Real-time evaluation metrics (Affinity, Safety, Novelty, etc.) are plotted on dynamic Plotly radar charts, overlaying multiple drug candidates for comparative analysis.
- **High-Speed Inference**: Powered by the Groq LPU engine, enabling the rapid, iterative reasoning cycles critical for multi-agent swarm intelligence.

## 🏗️ Architecture & Tech Stack
- **Orchestration**: [LangGraph](https://python.langchain.com/docs/langgraph/) (Stateful Multi-Agent Graph)
- **Agent Framework**: [DSPy](https://dspy-docs.vercel.app/) (Declarative Self-Improving Language Models)
- **LLM Engine**: Groq (Llama 3.3 70B Versatile)
- **Biological Data Sources**: UniProt REST API, PubChem REST API
- **User Interface**: [Gradio](https://gradio.app/) with customized Plotly integrations

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/RareAgent.git
cd RareAgent
```

### 2. Set Up the Environment
Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=gsk_your_api_key_here
```

### 4. Launch the Swarm
Run the Gradio dashboard:
```bash
python app.py
```
*Navigate to the local URL provided in the terminal (usually http://127.0.0.1:7860) to launch the swarm interface.*

## 🔬 Swarm Workflow
1. **Explorer Node**: Receives the target orphan disease and queries biological databases to construct a randomized, prioritized list of associated genetic targets.
2. **Proponent Node**: Generates a drug repurposing hypothesis by linking an existing drug to an identified genetic target mechanism.
3. **Skeptic Node**: Critiques the clinical safety and plausibility of the proposed drug.
4. **Validator Node**: Performs deterministic verification, checking drug identifiers (PubChem) and verifying target-disease linkages (UniProt).
5. **Orchestrator Node**: Routes the graph. If a hypothesis is rejected, the failure reason is injected directly back into the Proponent's prompt to enforce immediate self-correction. Validated hypotheses are outputted to the user.
