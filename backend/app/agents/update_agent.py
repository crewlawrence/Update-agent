"""
Agno agent that drafts brief, professional client update emails from change summaries.
No tools: we pass context and get back subject + body.
"""
import json
from agno.agent import Agent
try:
    from agno.models.openai.responses import OpenAIResponses
except ImportError:
    from agno.models.openai import OpenAIResponses

from app.config import get_settings

settings = get_settings()


def create_update_agent() -> Agent:
    return Agent(
        model=OpenAIResponses(id="gpt-4o-mini"),
        markdown=True,
        instruction=(
            "You are a professional assistant that writes brief, friendly email updates "
            "for business clients. Given a summary of what changed (e.g. new invoices, "
            "milestone completions), draft a short email (2-4 sentences) that informs "
            "the client without overwhelming detail. Tone: clear, professional, warm. "
            "Do not invent data; only reference what is provided. "
            "Respond with valid JSON only, in this exact shape: "
            '{"subject": "Subject line here", "body_plain": "Plain text body.", "body_html": "<p>HTML body.</p>"}'
        ),
    )


def draft_client_update(
    client_display_name: str,
    client_email: str | None,
    change_summary: str,
    company_context: str = "",
) -> dict:
    """
    Returns {"subject": str, "body_plain": str, "body_html": str}.
    """
    agent = create_update_agent()
    prompt = f"""Client name: {client_display_name}
Contact email: {client_email or 'Not set'}
{company_context}
Changes to report:
{change_summary}

Draft one brief email update. Output only the JSON object, no other text."""
    response = agent.run(prompt)
    text = response.content if hasattr(response, "content") else str(response)
    # Parse JSON from response (handle markdown code block)
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    data = json.loads(text)
    return {
        "subject": data.get("subject", "Update for you"),
        "body_plain": data.get("body_plain", data.get("body_html", "")),
        "body_html": data.get("body_html", data.get("body_plain", "")),
    }
