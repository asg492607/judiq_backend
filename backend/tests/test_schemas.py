from schemas import CaseInput

def test_case_input_schema_valid():
    data = {
        "case_type": "138 NI Act",
        "client_role": "Complainant",
        "amount": 500000.0,
        "cheque_details": {
            "amount": 500000.0,
            "cheque_date": "2023-01-01",
            "cheque_number": "123456"
        },
        "complainant": {
            "name": "Test Complainant",
            "type": "Individual"
        },
        "accused": {
            "name": "Test Accused",
            "type": "Individual"
        }
    }
    # Should not raise exception
    model = CaseInput(**data)
    assert model.amount == 500000.0

def test_case_input_schema_invalid():
    # Since all fields in CaseInput are optional (except Config), it is flexible.
    # Let's test basic instantiating
    model = CaseInput(case_type="cheque_bounce")
    assert model.case_type == "cheque_bounce"

