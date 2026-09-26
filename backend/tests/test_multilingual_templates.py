import pytest
from multilingual_drafts import (
    format_multilingual_draft,
    num_to_marathi_words,
    num_to_hindi_words
)

def test_num_to_devanagari_words():
    # Marathi numbers
    assert "पाच लाख" in num_to_marathi_words(500000)
    assert "दोन कोटी" in num_to_marathi_words(20000000)
    assert "पंचवीस हजार" in num_to_marathi_words(25000)

    # Hindi numbers
    assert "पांच लाख" in num_to_hindi_words(500000)
    assert "दो करोड़" in num_to_hindi_words(20000000)
    assert "पच्चीस हजार" in num_to_hindi_words(25000)


def test_marathi_draft_templates():
    case_data = {
        "complainant_name": "सचिन रमेश तेंडुलकर",
        "complainant_address": "वांद्रे पश्चिम, मुंबई, महाराष्ट्र",
        "accused_name": "विजय विठ्ठल माल्या",
        "accused_address": "जुहू, मुंबई, महाराष्ट्र",
        "cheque_number": "549201",
        "cheque_date": "15/01/2026",
        "cheque_amount": 750000,
        "bank_name": "स्टेट बँक ऑफ इंडिया",
        "branch_name": "वांद्रे शाखा",
        "dishonour_date": "20/01/2026",
        "return_reason": "खात्यात अपुरी रक्कम (Funds Insufficient)",
        "notice_date": "25/01/2026",
        "notice_delivery_date": "28/01/2026"
    }

    # 1. Legal Demand Notice
    notice_mr = format_multilingual_draft("LEGAL_NOTICE", "mr", case_data)
    assert "कायदेशीर मागणी नोटीस" in notice_mr
    assert "कलम १३८ परक्राम्य संलेख अधिनियम" in notice_mr
    assert "सचिन रमेश तेंडुलकर" in notice_mr
    assert "विजय विठ्ठल माल्या" in notice_mr
    assert "549201" in notice_mr
    assert "₹750,000" in notice_mr
    assert "१५ (पंधरा) दिवसांच्या आत" in notice_mr

    # 2. Criminal Complaint (JMFC)
    complaint_mr = format_multilingual_draft("COMPLAINT", "mr", case_data)
    assert "मा. प्रथम वर्ग न्यायदंडाधिकारी" in complaint_mr
    assert "समरी फौजदारी केस क्र." in complaint_mr
    assert "तक्रारदार" in complaint_mr
    assert "आरोपी" in complaint_mr
    assert "दाद / प्रार्थना" in complaint_mr
    assert "सत्यता पडताळणी" in complaint_mr

    # 3. Application 143A (20% Interim Compensation)
    app143a_mr = format_multilingual_draft("APPLICATION_143A", "mr", case_data)
    assert "कलम १४३-अ" in app143a_mr
    assert "२०% अंतरिम भरपाई" in app143a_mr
    assert "₹150,000" in app143a_mr  # 20% of 7,50,000

    # 4. Affidavit in lieu of Exam-in-Chief (145(1))
    affidavit_mr = format_multilingual_draft("AFFIDAVIT_EXAM_CHIEF", "mr", case_data)
    assert "मुख्य तपासणी प्रतिज्ञापत्र" in affidavit_mr
    assert "कलम १४५(१)" in affidavit_mr

    # 5. Delay Condonation Application
    delay_mr = format_multilingual_draft("DELAY_CONDONATION", "mr", case_data)
    assert "विलंब क्षमा करण्याबाबत अर्ज" in delay_mr
    assert "कलम १४२(१)(ब)" in delay_mr

    # 6. Defence Notice Reply
    reply_mr = format_multilingual_draft("DEFENCE_REPLY", "mr", case_data)
    assert "कायदेशीर नोटीसला लेखी उत्तर" in reply_mr
    assert "सुरक्षिततेसाठी (Security Cheque)" in reply_mr

    # 7. Bail Application
    bail_mr = format_multilingual_draft("REGULAR_BAIL", "mr", case_data)
    assert "नियमित जामीन मिळण्याबाबत अर्ज" in bail_mr

    # 8. SARFAESI Notice & Reply
    sarfaesi_notice_mr = format_multilingual_draft("SARFAESI_13_2_NOTICE", "mr", case_data)
    assert "कलम १३(२) अन्वये वैधानिक मागणी नोटीस" in sarfaesi_notice_mr

    sarfaesi_reply_mr = format_multilingual_draft("SARFAESI_13_3A_REPLY", "mr", case_data)
    assert "कलम १३(३-अ) अन्वये कायदेशीर आक्षेप" in sarfaesi_reply_mr


def test_hindi_draft_templates():
    case_data = {
        "complainant_name": "राजेश कुमार शर्मा",
        "complainant_address": "कनॉट प्लेस, नई दिल्ली",
        "accused_name": "अनिल कुमार गुप्ता",
        "accused_address": "सेक्टर 18, नोएडा, उत्तर प्रदेश",
        "cheque_number": "883012",
        "cheque_date": "10/02/2026",
        "cheque_amount": 1200000,
        "bank_name": "पंजाब नेशनल बैंक",
        "branch_name": "संसद मार्ग शाखा",
        "dishonour_date": "14/02/2026",
        "return_reason": "खाते में अपर्याप्त निधि (Funds Insufficient)",
        "notice_date": "20/02/2026",
        "notice_delivery_date": "23/02/2026"
    }

    # 1. Legal Demand Notice
    notice_hi = format_multilingual_draft("LEGAL_NOTICE", "hi", case_data)
    assert "विधिक मांग नोटिस" in notice_hi
    assert "धारा 138 पराक्रम्य लिखत अधिनियम" in notice_hi
    assert "राजेश कुमार शर्मा" in notice_hi
    assert "अनिल कुमार गुप्ता" in notice_hi
    assert "883012" in notice_hi
    assert "₹1,200,000" in notice_hi
    assert "15 (पंद्रह) दिवस के भीतर" in notice_hi

    # 2. Criminal Complaint (JMFC)
    complaint_hi = format_multilingual_draft("COMPLAINT", "hi", case_data)
    assert "न्यायालय माननीय न्यायिक मजिस्ट्रेट प्रथम श्रेणी" in complaint_hi
    assert "आपराधिक परिवाद संख्या" in complaint_hi
    assert "परिवादी / शिकायतकर्ता" in complaint_hi
    assert "अभियुक्त / विपक्षी" in complaint_hi
    assert "प्रार्थना / अनुतोष" in complaint_hi
    assert "सत्यापन एवं शपथपत्र" in complaint_hi

    # 3. Application 143A (20% Interim Compensation)
    app143a_hi = format_multilingual_draft("APPLICATION_143A", "hi", case_data)
    assert "धारा 143A" in app143a_hi
    assert "20% अंतरिम मुआवजा" in app143a_hi
    assert "₹240,000" in app143a_hi  # 20% of 12,00,000

    # 4. Affidavit in lieu of Exam-in-Chief (145(1))
    affidavit_hi = format_multilingual_draft("AFFIDAVIT_EXAM_CHIEF", "hi", case_data)
    assert "मुख्य परीक्षा शपथपत्र" in affidavit_hi
    assert "धारा 145(1)" in affidavit_hi

    # 5. Delay Condonation Application
    delay_hi = format_multilingual_draft("DELAY_CONDONATION", "hi", case_data)
    assert "विलंब को क्षमा किए जाने हेतु प्रार्थना पत्र" in delay_hi
    assert "धारा 142(1)(b)" in delay_hi

    # 6. Defence Notice Reply
    reply_hi = format_multilingual_draft("DEFENCE_REPLY", "hi", case_data)
    assert "विधिक मांग नोटिस का प्रतिउत्तर" in reply_hi
    assert "सुरक्षा (Security Cheque)" in reply_hi

    # 7. Bail Application
    bail_hi = format_multilingual_draft("REGULAR_BAIL", "hi", case_data)
    assert "जमानत प्रार्थना पत्र" in bail_hi

    # 8. SARFAESI Notice & Reply
    sarfaesi_notice_hi = format_multilingual_draft("SARFAESI_13_2_NOTICE", "hi", case_data)
    assert "धारा 13(2) के अंतर्गत विधिक मांग नोटिस" in sarfaesi_notice_hi

    sarfaesi_reply_hi = format_multilingual_draft("SARFAESI_13_3A_REPLY", "hi", case_data)
    assert "धारा 13(3A) सरफेसी अधिनियम के अंतर्गत विधिक आपत्ति" in sarfaesi_reply_hi
