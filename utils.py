from datetime import datetime

def parse_date(date_str):
    """Parse date string in various formats"""
    if not date_str:
        return None
    
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %B %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except:
            continue
    return None

def days_between(date1_str, date2_str):
    """Calculate days between two dates (date2 - date1)"""
    d1 = parse_date(date1_str)
    d2 = parse_date(date2_str)
    if d1 and d2:
        return (d2 - d1).days
    return None
