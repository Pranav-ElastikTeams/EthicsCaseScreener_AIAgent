import google.generativeai as genai

def evaluate_complaint_status(description: str, evidence: str) -> dict:
    # Rules-based logic can be re-enabled if needed. Currently, only Gemini-based logic is used.
    prompt = (
        "You are an AI Ethics Case Screener. Your job is to assign a status to each ethics complaint based on the incident description and available evidence. Use professional judgment and the following guidelines:\n\n"
        "Statuses:\n"
        "- New: No actionable information yet.\n"
        "- Under Review: Sufficient information to be reviewed by the ethics officer.\n"
        "- Escalated: High-risk complaint with clear violation and valid evidence.\n"
        "- Needs More Info: Vague or insufficient description or evidence.\n"
        "- Closed: Case has been resolved or withdrawn (not applicable initially).\n\n"
        "Assign one of the statuses strictly based on severity and information quality.\n\n"
        f"Input:\nIncident Description: {description}\nEvidence Provided: {evidence}\n\n"
        "Answer Format:\nStatus: <One of New, Under Review, Escalated, Needs More Info>\nReason: <Brief justification>"
    )
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    resp = model.generate_content(prompt)
    text = resp.text.strip()
    # Parse Gemini response
    status = None
    reason = None
    for line in text.split('\n'):
        if line.lower().startswith('status:'):
            status = line.split(':', 1)[1].strip()
        elif line.lower().startswith('reason:'):
            reason = line.split(':', 1)[1].strip()
    return {"status": status or "Needs More Info", "reason": reason or "AI fallback used."}
