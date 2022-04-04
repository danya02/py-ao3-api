import datetime

def parse_date(date_str):
    if not date_str:
        return None
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()