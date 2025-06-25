from db.models import Complaint
from db.db_utils import get_db_session

def log_complaint(data):
    session = get_db_session()
    complaint = Complaint(**data)
    session.add(complaint)
    session.commit()
    session.close() 