import re

with open('c:/Users/Atharva/OneDrive/Desktop/Level_0judiq/frontend/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix Chart.js Re-rendering
chart_fix_surv = """    try {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded. Skipping chart render.');
        } else {
            const survCtx = document.getElementById('survivabilityChart');
            if (survCtx) {
                if (window.survChartInst) {
                    window.survChartInst.destroy();
                }
                window.survChartInst = new Chart(survCtx, {"""

content = content.replace("    const survCtx = document.getElementById('survivabilityChart');\n    if (survCtx && !window.survChartInst) {\n        window.survChartInst = new Chart(survCtx, {", chart_fix_surv)

chart_fix_att = """    
        const attCtx = document.getElementById('attackChart');
        if (attCtx) {
            if (window.attChartInst) {
                window.attChartInst.destroy();
            }
            window.attChartInst = new Chart(attCtx, {"""

content = content.replace("    const attCtx = document.getElementById('attackChart');\n    if (attCtx && !window.attChartInst) {\n        window.attChartInst = new Chart(attCtx, {", chart_fix_att)

# Fix ends
content = content.replace("            }\n        });\n    }\n\n    const attCtx", "            }\n        });\n        }\n\n    const attCtx")
content = content.replace("            }\n        });\n    }\n}\n", "            }\n        });\n        }\n    } catch(e) { console.error('Chart Error:', e); }\n}\n")


# 2. Fix Emojis & Encodings
content = content.replace('â€', '...')
content = content.replace('â€”', '—')
content = content.replace('A', '—') # Be careful with this! Wait, A with circumflex was â€” but I only used A. Wait, I won't replace single A.

# Let's fix the specific instances
content = content.replace('âš–ï¸', '\\u2696\\uFE0F')
content = content.replace('Building court-ready analysisâ€¦', 'Building court-ready analysis...')
content = content.replace('â€¦', '...')
content = content.replace('â‚¹', '\\u20B9')

with open('c:/Users/Atharva/OneDrive/Desktop/Level_0judiq/frontend/script.js', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed charts and encoding')
