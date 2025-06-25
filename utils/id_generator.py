import datetime
import random

# Simulated in-memory store to avoid duplicate IDs per run
generated_ids = set()

def generate_complaint_id():
    date_str = datetime.datetime.now().strftime('%Y%m%d')

    while True:
        random_number = random.randint(0, 9999)
        complaint_id = f'ETH-{date_str}-{random_number:04d}'
        
        # Ensure uniqueness within the current run
        if complaint_id not in generated_ids:
            generated_ids.add(complaint_id)
            return complaint_id