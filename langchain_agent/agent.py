import os
import json
from dotenv import load_dotenv
from .tools.complaint_logger import log_complaint
from utils.id_generator import generate_complaint_id
import google.generativeai as genai
from datetime import datetime
import random
from langchain_agent.tools.status_checker import evaluate_complaint_status
from utils.email_service import send_ethics_complaint_email

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Load officers list only (other data is not used in this file)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
with open(os.path.join(DATA_DIR, 'officers_name.json')) as f:
    OFFICERS = json.load(f)

def extract_field_value(question, answer, field):
    prompt = (
        f"For each input case below, extract the required data from the answer based on the question context:\n"
        f"For date-related questions, extract a valid date in YYYY-MM-DD format.\n"
        f"For email-related questions, extract a valid email address.\n"
        f"For evidence-related questions, if the user says they have no evidence, return 'No evidence'. Otherwise, extract the type of evidence (e.g., 'CCTV Footage', 'Witness Testimony', 'Audio Recording', 'Email Records', 'Photograph', etc.)\n"
        f"For name-related questions, extract the name of the person or organization.\n"
        f"For staff_role-related questions, extract the role/designation of the reported person (e.g., 'Manager', 'Subordinate').\n"
        f"If the required value cannot be confidently determined, return null.\n"
        f"Output only the extracted value for each case.\n\n"
        f"Input Case\nQuestion: {question}\nAnswer: {answer}"
    )
    resp = model.generate_content(prompt)
    print(f"\n[Gemini Extraction] Field: {field}, Prompt: {prompt}\nResponse: {resp.text.strip()}\n\n")
    value = resp.text.strip()
    if value.lower() == 'null':
        return None
    return value

# Main agent function with improved flow
def get_agent_response(user_message, conversation_state):
    # If no state, expect the first user message to be the complaint type
    if not conversation_state:
        conversation_state = {
            'collected': {},
            'questions': [],
            'current_q': 0,
            'confirmed': False
        }
        # Save the complaint type from the first user message
        complaint_type = user_message.strip()
        conversation_state['collected']['complaint_type'] = complaint_type
        # Ask Gemini for a list of questions for this complaint type
        prompt = (
            f"Given the selected incident type is {complaint_type}, generate a list of questions to gather data for the following fields:\n"
            f"complainant (String)\ncomplainant_email (String)\nName of the person being complained against (String)\nRole of the person being complained against (String)\ndate when the incident occurred (Date)\ndetailed summary of the incident (Text)\nevidence provided (String)\n"
            f"Output only the list of questions. No explanations. Questions should be relevant to a {complaint_type} incident."
        )
        resp = model.generate_content(prompt)
        print(f"\n[Gemini Extraction] Prompt: {prompt}\nResponse: {resp.text.strip()}\n")
        questions = [q.lstrip('*- ').strip() for q in resp.text.strip().split('\n') if q.strip()]
        conversation_state['questions'] = questions
        conversation_state['current_q'] = 0
        # Ask the first question
        return (questions[0], conversation_state)

    # If in the middle of asking questions
    questions = conversation_state.get('questions', [])
    current_q = conversation_state.get('current_q', 0)
    collected = conversation_state['collected']

    # Map the order of fields to collect
    field_order = [
        'complainant',
        'complainant_email',
        'subject',
        'staff_role',
        'date',
        'details_summary',
        'evidence_provided'
    ]
    if 0 <= current_q < len(field_order):
        field = field_order[current_q]
        question = questions[current_q]
        # Use Gemini to extract the value for each field
        if field == 'details_summary':
            collected[field] = user_message.strip()
        else:
            extracted = extract_field_value(question, user_message, field)
            if not extracted:
                return (question, conversation_state)
            # For date, validate format
            if field == 'date':
                try:
                    datetime.strptime(extracted, '%Y-%m-%d')
                except Exception:
                    return (question, conversation_state)
            collected[field] = extracted
        conversation_state['collected'] = collected
        conversation_state['current_q'] += 1
        current_q += 1
        if current_q < len(questions):
            return (questions[current_q], conversation_state)

    # After all questions, log the complaint
    if not conversation_state.get('confirmed'):
        data = collected.copy()
        # Evaluate status using status_checker
        status_result = evaluate_complaint_status(data.get('details_summary', ''), data.get('evidence_provided', ''))
        print(f"[Status Checker] Status: {status_result['status']}, Reason: {status_result['reason']}")
        data['status'] = status_result['status']
        data['complaint_id'] = generate_complaint_id()
        data['assigned_officer'] = random.choice(OFFICERS)
        data['created_at'] = datetime.utcnow()

        # Convert date string to datetime.date object
        if 'date' in data and isinstance(data['date'], str):
            try:
                data['date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except Exception:
                data['date'] = None
        try:
            log_complaint(data)
            summary = "\n".join([f"{k}: {v}" for k, v in data.items() if k not in ['created_at', 'assigned_officer']])
            confirmation = f"Thank you. Your complaint has been logged.\n\nComplaint ID: {data['complaint_id']}\nAssigned Officer: {data['assigned_officer']}\n\nYou will receive a confirmation email shortly. Our team will follow up within 5 business days."
            conversation_state['confirmed'] = True
            # Prepare email data
            email_data = {
                'Complaint ID': data['complaint_id'],
                'Complaint Type': data.get('complaint_type', ''),
                'Subject': data.get('subject', ''),
                'Date': data.get('date', ''),
                'Description': data.get('details_summary', ''),
                'Evidence': data.get('evidence_provided', ''),
                'Assigned To': data.get('assigned_officer', ''),
                'Status': data.get('status', '')
            }
            send_ethics_complaint_email(data.get('complainant_email', ''), data.get('complainant', ''), email_data)
            return (confirmation, conversation_state)
        except Exception as e:
            return (f"Error logging complaint: {str(e)}", conversation_state)
    else:
        return ("Your complaint has already been submitted. For a new complaint, please refresh the page.", conversation_state)
