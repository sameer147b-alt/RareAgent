import plotly.graph_objects as go
import random

# Color palette for multiple drug traces
TRACE_COLORS = [
    '#00cc96', '#636efa', '#ef553b', '#ab63fa', '#ffa15a',
    '#19d3f3', '#ff6692', '#b6e880', '#ff97ff', '#fecb52'
]

def create_radar_chart(hypotheses_list: list):
    """
    Generates a Plotly Radar Chart overlaying ALL evaluated drug hypotheses.
    Each drug gets its own semi-transparent trace for easy comparison.
    """
    if not hypotheses_list:
        return None

    categories = ['Target Affinity', 'Safety Profile', 'Pathway Overlap', 'Novelty', 'Skeptic Approval']

    fig = go.Figure()

    for i, hypothesis in enumerate(hypotheses_list):
        drug_name = hypothesis.get("drug_name", f"Drug {i+1}")

        # Extract real scores or generate mock scores for the demo
        is_valid = hypothesis.get("validation", {}).get("overall_status") == "APPROVED"
        skeptic_verdict = hypothesis.get("skeptic_verdict", "UNKNOWN")

        score_affinity = 85 if is_valid else 40
        score_safety = 90 if skeptic_verdict == "SAFE" else (60 if skeptic_verdict == "RISKY" else 20)
        score_overlap = random.randint(60, 95)
        score_novelty = random.randint(50, 90)
        score_approval = 95 if skeptic_verdict == "SAFE" else (50 if skeptic_verdict == "RISKY" else 10)

        values = [score_affinity, score_safety, score_overlap, score_novelty, score_approval]

        color = TRACE_COLORS[i % len(TRACE_COLORS)]

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=drug_name,
            line_color=color,
            opacity=0.6
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="Multi-Drug Comparative Assessment",
        showlegend=True,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        )
    )

    return fig
