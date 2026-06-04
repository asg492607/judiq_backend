from datetime import datetime

import dateutil.parser

def parse_date(date_str):
    """Parse date string robustly using dateutil"""
    if not date_str:
        return None
    
    try:
        # fuzzy=True allows it to ignore unknown tokens around the date
        return dateutil.parser.parse(str(date_str), fuzzy=True)
    except (ValueError, OverflowError):
        # Fallback to strict format list if dateutil fails for some reason
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
