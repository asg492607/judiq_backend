import sys
import traceback
from engine_core import JudiQEngine

raw_data = {
    "case_type": "Criminal",
    "description": "This is a criminal case for murder",
    "offense_type": "302"
}

try:
    JudiQEngine.analyze_case(raw_data)
    print("Success")
except Exception as e:
    traceback.print_exc()
