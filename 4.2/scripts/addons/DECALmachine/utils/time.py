from datetime import datetime

def get_time_code():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
