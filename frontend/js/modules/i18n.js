/**
 * JudiQ AI — Internationalization (i18n) Engine for English & Marathi (मराठी)
 * Enables seamless instant switching across landing page, input forms, dashboard, results, and draft generation.
 */

window.i18n = {
    currentLang: localStorage.getItem('judiq_lang') || 'en',

    dictionary: {
        en: {
            brand_name: "JUDIQ AI",
            brand_subtitle: "AI Litigation Strategist",
            nav_about: "About",
            nav_pricing: "Pricing",
            nav_testimonials: "Testimonials",
            nav_faq: "FAQ",
            nav_contact: "Contact",
            nav_docs: "Docs",
            nav_settings: "Settings",
            nav_logout: "Logout",
            load_demo_case: "Load Demo Case",
            hero_title: "Find Fatal Legal Defects Before The Courtroom Does",
            hero_sub: "Adversarial litigation intelligence, Section 138 cheque bounce audit, SARFAESI NPA enforcement, and automated legal draft generator.",
            start_analysis: "Start Case Analysis",
            select_domain: "Select Legal Domain",
            domain_ni: "Cheque Bounce (Section 138 NI Act)",
            domain_sarfaesi: "SARFAESI & DRT Litigation",
            domain_criminal: "Criminal Law (IPC / BNS)",
            domain_civil: "Civil Suit (CPC)",
            account_overview: "Account Overview",
            quick_actions: "Quick Actions",
            cases_analysed: "Cases Analysed",
            fatal_defects: "Fatal Defects Found",
            strong_cases: "Strong Cases",
            analyse_s138: "Analyse S.138 Case",
            s138_sub: "Run adversarial weakness scan — Limitation, Notice, Instrument, Debt",
            generate_draft: "Generate Legal Draft",
            generate_draft_sub: "Auto-generate demand notice, S.138 complaint, or defence reply",
            cheque_amount: "Cheque Amount (₹)",
            dishonour_date: "Date of Dishonour Memo",
            notice_date: "Date of Statutory Demand Notice",
            complainant_type: "Complainant Entity Type",
            analyze_now: "Analyze Case Now",
            viability_score: "Litigation Viability Score",
            procedural_timeline: "Procedural Milestone Graph",
            next_best_actions: "Recommended Next Actions",
            adversarial_vectors: "Adversarial Attack Vectors & Weaknesses",
            export_pdf: "Export Analysis PDF",
            lang_btn: "मराठी"
        },
        mr: {
            brand_name: "ज्युरिक आय (JudiQ AI)",
            brand_subtitle: "न्यायालयीन AI रणनीतिकार",
            nav_about: "माहिती",
            nav_pricing: "दरपत्रक",
            nav_testimonials: "प्रतिक्रिया",
            nav_faq: "प्रश्न",
            nav_contact: "संपर्क",
            nav_docs: "दस्तऐवज",
            nav_settings: "सेटिंग्ज",
            nav_logout: "लॉगआउट",
            load_demo_case: "डेमो प्रकरण लोड करा",
            hero_title: "न्यायालयात जाण्यापूर्वी कायदेशीर त्रुटी आणि कमकुवत बाबी शोधा",
            hero_sub: "कलम १३८ चेक बाऊन्स विश्लेषण, सरफेसी बँक कारवाई, विरोधी युक्तिवाद चाचणी आणि स्वयंचलित कायदेशीर मसुदा.",
            start_analysis: "प्रकरणाचे विश्लेषण सुरू करा",
            select_domain: "कायदेशीर क्षेत्र निवडा",
            domain_ni: "चेक बाऊन्स (कलम १३८ एन.आय. ॲक्ट)",
            domain_sarfaesi: "सरफेसी आणि डी.आर.टी. कायदा",
            domain_criminal: "फौजदारी कायदा (आयपीसी / बीएनएस)",
            domain_civil: "दीवाणी दावा (सीपीसी)",
            account_overview: "खाते विहंगावलोकन",
            quick_actions: "जलद कृती पर्याय",
            cases_analysed: "विश्लेषण केलेली प्रकरणे",
            fatal_defects: "गंभीर कायदेशीर त्रुटी",
            strong_cases: "भक्कम प्रकरणे",
            analyse_s138: "कलम १३८ प्रकरणाचे विश्लेषण",
            s138_sub: "कायदेशीर नोटीस, मुदत, रक्कम व नोटीस त्रुटींची पडताळणी करा",
            generate_draft: "कायदेशीर मसुदा तयार करा",
            generate_draft_sub: "मागणी नोटीस, तक्रार अर्ज किंवा बचाव उत्तर स्वयंचलित तयार करा",
            cheque_amount: "चेकची रक्कम (₹)",
            dishonour_date: "चेक अनादर (बाऊन्स) तारीख",
            notice_date: "कायदेशीर नोटीस पाठवल्याची तारीख",
            complainant_type: "तक्रारदाराचा प्रकार",
            analyze_now: "आत्ता विश्लेषण करा",
            viability_score: "खटल्याची संभाव्य यश टक्केवारी",
            procedural_timeline: "प्रक्रियात्मक कालमर्यादा आलेख",
            next_best_actions: "महत्त्वाच्या पुढील कृती",
            adversarial_vectors: "विरोधी पक्षाचे संभाव्य युक्तिवाद आणि त्रुटी",
            export_pdf: "विश्लेषण पीडीएफ डाऊनलोड करा",
            lang_btn: "English"
        }
    },

    t: function(key) {
        const lang = this.currentLang;
        const dict = this.dictionary[lang] || this.dictionary['en'];
        return dict[key] || this.dictionary['en'][key] || key;
    },

    updatePageText: function() {
        const lang = this.currentLang;
        document.documentElement.lang = lang;

        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const txt = this.t(key);
            if (txt) {
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    el.placeholder = txt;
                } else {
                    el.textContent = txt;
                }
            }
        });

        // Update language toggle buttons
        document.querySelectorAll('.lang-toggle-btn').forEach(btn => {
            btn.innerHTML = `<i class="fas fa-globe"></i> <span>${lang === 'en' ? 'मराठी' : 'English'}</span>`;
        });
    }
};

window.toggleLanguage = function() {
    window.i18n.currentLang = window.i18n.currentLang === 'en' ? 'mr' : 'en';
    localStorage.setItem('judiq_lang', window.i18n.currentLang);
    window.i18n.updatePageText();
    
    // Re-render active screens if available
    if (window.renderDashboard && document.getElementById('dashboardScreen') && !document.getElementById('dashboardScreen').classList.contains('hidden')) {
        window.renderDashboard();
    }
    
    if (window.showToast) {
        window.showToast(
            window.i18n.currentLang === 'mr' ? 'भाषा मराठीत बदलली आहे.' : 'Language switched to English.',
            'info'
        );
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.i18n.updatePageText();
});
