/**
 * JudiQ AI — Case Management Frontend UI Module
 * Handles Case List, Case Detail (8 tabs), Case Creation, and Status Transitions.
 */

import { api } from '../api.js?v=15';
import { ui, switchScreen } from '../ui.js?v=14';
import { escapeHtml } from './modules/utils.js?v=14';
import { store } from './modules/store.js?v=14';

export function initCaseManager() {
    // Setup listener for search input on caseListScreen
    const searchInput = document.getElementById('caseSearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const filters = store.get('cmsListFilters', {});
                filters.search = e.target.value;
                filters.page = 1;
                store.set('cmsListFilters', filters);
                loadCaseList();
            }, 300);
        });
    }

    // Setup case creation form submit
    const createForm = document.getElementById('caseCreateForm');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitCaseCreate();
        });
    }
}

export async function loadCaseList() {
    const filters = store.get('cmsListFilters', { status: 'all', case_type: 'all', priority: 'all', search: '', page: 1 });
    const tbody = document.getElementById('caseListTableBody');
    const statsContainer = document.getElementById('caseListStats');
    if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="cms-table-loading"><i class="fas fa-spinner fa-spin"></i> Loading cases...</td></tr>`;

    try {
        const res = await api.listCases(filters);
        const cases = res.cases || [];
        const total = res.total || 0;

        if (tbody) {
            if (cases.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="cms-empty-state">
                            <i class="fas fa-folder-open"></i>
                            <p>No cases found matching the criteria.</p>
                            <button class="btn btn-primary btn-sm" onclick="showCaseCreate()">Create New Case</button>
                        </td>
                    </tr>
                `;
            } else {
                tbody.innerHTML = cases.map(c => {
                    const statusClass = `status-pill--${c.case_status || 'draft'}`;
                    const priorityColor = c.priority === 'high' ? '#ef4444' : c.priority === 'medium' ? '#f59e0b' : '#6b7280';
                    const scoreDisplay = c.compliance_score !== null && c.compliance_score !== undefined
                        ? `<span class="cms-score-badge ${c.compliance_score >= 70 ? 'score--green' : c.compliance_score >= 50 ? 'score--yellow' : 'score--red'}">${c.compliance_score}</span>`
                        : `<span class="cms-score-badge score--gray">—</span>`;
                    
                    return `
                        <tr onclick="showCaseDetail('${escapeHtml(c.case_id)}')" class="cms-table-row">
                            <td class="cms-cell-id"><strong>${escapeHtml(c.case_id)}</strong></td>
                            <td class="cms-cell-name">
                                <div class="case-name-text">${escapeHtml(c.case_name)}</div>
                                <div class="case-tags">${(c.tags || []).map(t => `<span class="cms-tag">${escapeHtml(t)}</span>`).join('')}</div>
                            </td>
                            <td><span class="cms-type-tag">${escapeHtml(formatCaseType(c.case_type))}</span></td>
                            <td><span class="cms-status-pill ${statusClass}">${escapeHtml((c.case_status || 'draft').toUpperCase())}</span></td>
                            <td><span class="cms-priority-dot" style="background:${priorityColor};"></span> ${escapeHtml(c.priority || 'medium')}</td>
                            <td>${scoreDisplay}</td>
                            <td class="cms-cell-date">${formatDate(c.updated_at)}</td>
                        </tr>
                    `;
                }).join('');
            }
        }

        // Render Pagination
        renderPagination(total, filters.page, 20);

        // Update stats
        if (statsContainer) {
            const ongoing = cases.filter(c => c.case_status === 'ongoing').length;
            const draft = cases.filter(c => c.case_status === 'draft').length;
            const resolved = cases.filter(c => c.case_status === 'resolved').length;
            statsContainer.innerHTML = `
                <div class="cms-stat-chip"><strong>${total}</strong> Total</div>
                <div class="cms-stat-chip status--ongoing"><strong>${ongoing}</strong> Ongoing</div>
                <div class="cms-stat-chip status--draft"><strong>${draft}</strong> Drafts</div>
                <div class="cms-stat-chip status--resolved"><strong>${resolved}</strong> Resolved</div>
            `;
        }
    } catch (err) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" class="cms-error-cell">Error loading cases: ${escapeHtml(err.message)}</td></tr>`;
    }
}

export async function loadCaseDetail(caseId) {
    store.set('activeCaseId', caseId);
    const container = document.getElementById('caseDetailContainer');
    if (container) container.innerHTML = `<div class="cms-loading-spinner"><i class="fas fa-spinner fa-spin fa-2x"></i><p>Loading case details...</p></div>`;

    try {
        const caseData = await api.getCaseDetail(caseId);
        if (!caseData) throw new Error("Case not found");

        renderCaseDetailView(caseData);
    } catch (err) {
        if (container) container.innerHTML = `<div class="cms-error-box"><i class="fas fa-exclamation-triangle"></i> Failed to load case: ${escapeHtml(err.message)}</div>`;
    }
}

function renderCaseDetailView(caseData) {
    const container = document.getElementById('caseDetailContainer');
    if (!container) return;

    const statusOptions = ['draft', 'ongoing', 'resolved', 'archived'];
    const activeTab = store.get('cmsActiveTab', 'overview');

    container.innerHTML = `
        <div class="cms-detail-header">
            <div class="cms-dh-left">
                <button class="btn btn-sm btn-outline cms-back-btn" onclick="showCaseList()"><i class="fas fa-arrow-left"></i> Cases</button>
                <div class="cms-dh-title-group">
                    <h2>${escapeHtml(caseData.case_name)}</h2>
                    <span class="cms-dh-id">${escapeHtml(caseData.case_id)}</span>
                    <span class="cms-type-tag">${escapeHtml(formatCaseType(caseData.case_type))}</span>
                </div>
            </div>
            <div class="cms-dh-right">
                <select class="cms-status-select" onchange="handleCaseStatusChange('${escapeHtml(caseData.case_id)}', this.value)">
                    ${statusOptions.map(st => `<option value="${st}" ${caseData.case_status === st ? 'selected' : ''}>${st.toUpperCase()}</option>`).join('')}
                </select>
                <button class="btn btn-primary btn-sm" onclick="handleRunCmsAnalysis('${escapeHtml(caseData.case_id)}')"><i class="fas fa-bolt"></i> Run Audit</button>
                <button class="btn btn-outline btn-sm" onclick="openShareCaseModal('${escapeHtml(caseData.case_id)}')"><i class="fas fa-share-alt"></i> Share</button>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="cms-detail-tabs">
            <button class="cms-tab-btn ${activeTab === 'overview' ? 'active' : ''}" onclick="switchCmsTab('overview')"><i class="fas fa-info-circle"></i> Overview</button>
            <button class="cms-tab-btn ${activeTab === 'parties' ? 'active' : ''}" onclick="switchCmsTab('parties')"><i class="fas fa-users"></i> Parties (${(caseData.linked_clients || []).length})</button>
            <button class="cms-tab-btn ${activeTab === 'documents' ? 'active' : ''}" onclick="switchCmsTab('documents')"><i class="fas fa-file-alt"></i> Documents (${caseData.document_count || 0})</button>
            <button class="cms-tab-btn ${activeTab === 'analysis' ? 'active' : ''}" onclick="switchCmsTab('analysis')"><i class="fas fa-shield-alt"></i> Audit & Score</button>
            <button class="cms-tab-btn ${activeTab === 'drafts' ? 'active' : ''}" onclick="switchCmsTab('drafts')"><i class="fas fa-file-signature"></i> Drafts</button>
            <button class="cms-tab-btn ${activeTab === 'deadlines' ? 'active' : ''}" onclick="switchCmsTab('deadlines')"><i class="fas fa-calendar-alt"></i> Deadlines (${caseData.pending_deadlines || 0})</button>
            <button class="cms-tab-btn ${activeTab === 'timeline' ? 'active' : ''}" onclick="switchCmsTab('timeline')"><i class="fas fa-stream"></i> Timeline</button>
        </div>

        <!-- Tab Content Panels -->
        <div class="cms-tab-content" id="cmsTabContentPanel">
            ${renderActiveTabContent(caseData, activeTab)}
        </div>
    `;

    // If active tab is sub-module (documents, drafts, deadlines), lazy load
    if (activeTab === 'documents' && window.loadDocumentList) {
        window.loadDocumentList(caseData.case_id);
    } else if (activeTab === 'drafts' && window.loadDraftList) {
        window.loadDraftList(caseData.case_id);
    } else if (activeTab === 'deadlines') {
        loadCaseDeadlinesList(caseData.case_id);
    } else if (activeTab === 'timeline') {
        loadCaseTimelineView(caseData.case_id);
    }
}

function renderActiveTabContent(caseData, tab) {
    if (tab === 'overview') {
        const fin = caseData.financial_data || {};
        const court = caseData.court_data || {};
        return `
            <div class="cms-overview-grid">
                <div class="cms-card">
                    <h4><i class="fas fa-balance-scale"></i> Claim & Financial Particulars</h4>
                    <div class="cms-prop-row"><span class="label">Claim / Cheque Amount:</span> <strong>₹ ${fin.cheque_amount || fin.amount || fin.outstanding_amount || '—'}</strong></div>
                    <div class="cms-prop-row"><span class="label">Transaction Date:</span> <span>${fin.transaction_date || '—'}</span></div>
                    <div class="cms-prop-row"><span class="label">Dishonour Date:</span> <span>${fin.dishonour_date || fin.memo_date || '—'}</span></div>
                    <div class="cms-prop-row"><span class="label">Notice Sent Date:</span> <span>${fin.notice_date || '—'}</span></div>
                    <div class="cms-prop-row"><span class="label">Notice Received Date:</span> <span>${fin.notice_received_date || '—'}</span></div>
                </div>
                <div class="cms-card">
                    <h4><i class="fas fa-gavel"></i> Forum & Jurisdiction</h4>
                    <div class="cms-prop-row"><span class="label">Designated Court:</span> <span>${court.court_name || 'Not specified'}</span></div>
                    <div class="cms-prop-row"><span class="label">Jurisdiction City/State:</span> <span>${court.jurisdiction || '—'}</span></div>
                    <div class="cms-prop-row"><span class="label">Filing Date:</span> <span>${court.filing_date || '—'}</span></div>
                    <div class="cms-prop-row"><span class="label">Access Level:</span> <span class="badge">${escapeHtml(caseData.access_level || 'private')}</span></div>
                </div>
                <div class="cms-card" style="grid-column: 1/-1;">
                    <h4><i class="fas fa-align-left"></i> Matter Summary & Description</h4>
                    <p class="cms-description-text">${escapeHtml(caseData.description || 'No detailed description provided.')}</p>
                </div>
            </div>
        `;
    } else if (tab === 'parties') {
        const clients = caseData.linked_clients || [];
        return `
            <div class="cms-parties-view">
                <div class="cms-pv-header">
                    <h4>Linked Clients & Representatives</h4>
                    <button class="btn btn-sm btn-primary" onclick="openLinkClientModal('${escapeHtml(caseData.case_id)}')"><i class="fas fa-plus"></i> Link Client</button>
                </div>
                <div class="cms-clients-grid">
                    ${clients.length === 0 ? '<p class="text-muted">No clients linked to this case yet.</p>' : clients.map(cl => `
                        <div class="cms-client-chip" onclick="showClientDetail('${escapeHtml(cl.client_id)}')">
                            <div class="cc-icon"><i class="fas fa-user-tie"></i></div>
                            <div class="cc-info">
                                <div class="cc-name">${escapeHtml(cl.name)}</div>
                                <div class="cc-role">${escapeHtml((cl.role || 'creditor').toUpperCase())} • ${escapeHtml(cl.client_type || 'Entity')}</div>
                                <div class="cc-email">${escapeHtml(cl.email || 'No email')}</div>
                            </div>
                            <button class="btn btn-icon btn-sm" onclick="event.stopPropagation(); handleUnlinkClient('${escapeHtml(caseData.case_id)}', '${escapeHtml(cl.client_id)}')"><i class="fas fa-times"></i></button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } else if (tab === 'documents') {
        return `<div id="cmsDocumentListContainer" class="cms-doc-container"></div>`;
    } else if (tab === 'analysis') {
        const res = caseData.analysis_result || {};
        const score = caseData.compliance_score;
        return `
            <div class="cms-analysis-tab">
                <div class="cms-score-hero">
                    <div class="score-dial">
                        <span class="score-number">${score !== null && score !== undefined ? score : '—'}</span>
                        <span class="score-label">COMPLIANCE SCORE</span>
                    </div>
                    <div class="score-summary">
                        <h3>Verdict: <span class="verdict-highlight">${escapeHtml(caseData.verdict || 'PENDING EVALUATION')}</span></h3>
                        <p>12-Pillar Statutory & Precedent Examination under applicable Supreme Court doctrine.</p>
                        <button class="btn btn-primary btn-sm" onclick="handleRunCmsAnalysis('${escapeHtml(caseData.case_id)}')"><i class="fas fa-sync"></i> Re-Analyze Case</button>
                    </div>
                </div>
                <div class="cms-analysis-details">
                    <pre class="cms-json-preview">${escapeHtml(JSON.stringify(res, null, 2))}</pre>
                </div>
            </div>
        `;
    } else if (tab === 'drafts') {
        return `<div id="cmsDraftListContainer" class="cms-drafts-container"></div>`;
    } else if (tab === 'deadlines') {
        return `<div id="cmsDeadlinesContainer" class="cms-deadlines-container"></div>`;
    } else if (tab === 'timeline') {
        return `<div id="cmsTimelineContainer" class="cms-timeline-container"></div>`;
    }
    return '';
}

async function loadCaseDeadlinesList(caseId) {
    const container = document.getElementById('cmsDeadlinesContainer');
    if (!container) return;
    container.innerHTML = `<div class="cms-loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading deadlines...</div>`;
    try {
        const deadlines = await api.listCaseDeadlines(caseId);
        if (deadlines.length === 0) {
            container.innerHTML = `
                <div class="cms-empty-state">
                    <i class="fas fa-calendar-check"></i>
                    <p>No statutory deadlines calculated yet for this matter.</p>
                    <button class="btn btn-primary btn-sm" onclick="handleCalculateDeadlines('${escapeHtml(caseId)}')"><i class="fas fa-calculator"></i> Calculate Statutory Deadlines</button>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="cms-deadlines-header">
                <h4>Statutory Deadlines & Alert Schedule</h4>
                <div class="cms-dh-actions">
                    <button class="btn btn-sm btn-outline" onclick="handleCalculateDeadlines('${escapeHtml(caseId)}')"><i class="fas fa-sync"></i> Recalculate</button>
                    <a href="${api.API_BASE_URL || ''}/api/v1/deadlines/${encodeURIComponent(caseId)}/calendar.ics" class="btn btn-sm btn-primary" download><i class="fas fa-calendar-plus"></i> Export .ICS</a>
                </div>
            </div>
            <div class="cms-deadlines-list">
                ${deadlines.map(d => {
                    const isCompleted = d.status === 'completed';
                    const urgencyClass = `urgency--${(d.urgency_level || 'safe').toLowerCase()}`;
                    return `
                        <div class="cms-deadline-card ${urgencyClass} ${isCompleted ? 'completed' : ''}">
                            <div class="dc-left">
                                <input type="checkbox" ${isCompleted ? 'checked disabled' : ''} onchange="handleCompleteDeadline('${escapeHtml(d.deadline_id)}')">
                                <div class="dc-info">
                                    <div class="dc-title">${escapeHtml(d.title)}</div>
                                    <div class="dc-basis">${escapeHtml(d.statutory_basis || '')}</div>
                                </div>
                            </div>
                            <div class="dc-right">
                                <div class="dc-date"><i class="fas fa-clock"></i> Due: <strong>${d.due_date}</strong></div>
                                <span class="cms-urgency-badge ${urgencyClass}">${escapeHtml(d.urgency_level || 'SAFE')}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="cms-error-box">Failed to load deadlines: ${escapeHtml(err.message)}</div>`;
    }
}

async function loadCaseTimelineView(caseId) {
    const container = document.getElementById('cmsTimelineContainer');
    if (!container) return;
    container.innerHTML = `<div class="cms-loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading timeline...</div>`;
    try {
        const res = await api.getCaseTimeline(caseId);
        const items = res.timeline || [];
        if (items.length === 0) {
            container.innerHTML = `<p class="text-muted">No activity recorded for this matter yet.</p>`;
            return;
        }
        container.innerHTML = `
            <div class="cms-vertical-timeline">
                ${items.map(it => `
                    <div class="timeline-item">
                        <div class="timeline-dot"></div>
                        <div class="timeline-card">
                            <div class="tc-header">
                                <strong>${escapeHtml(it.action || 'ACTIVITY')}</strong>
                                <span class="tc-time">${formatDate(it.timestamp)}</span>
                            </div>
                            <div class="tc-note">${escapeHtml(it.note || '')}</div>
                            <div class="tc-user">Actor: ${escapeHtml(it.user_id || 'System')}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="cms-error-box">Failed to load timeline: ${escapeHtml(err.message)}</div>`;
    }
}

async function submitCaseCreate() {
    const form = document.getElementById('caseCreateForm');
    if (!form) return;
    const btn = form.querySelector('button[type="submit"]');
    if (btn) btn.classList.add('loading');

    const name = document.getElementById('ccCaseName')?.value.trim();
    const type = document.getElementById('ccCaseType')?.value;
    const priority = document.getElementById('ccPriority')?.value;
    const desc = document.getElementById('ccDescription')?.value.trim();

    // Financial
    const amount = parseFloat(document.getElementById('ccAmount')?.value || 0);
    const transDate = document.getElementById('ccTransactionDate')?.value;
    const disDate = document.getElementById('ccDishonourDate')?.value;
    const noticeDate = document.getElementById('ccNoticeDate')?.value;

    // Parties
    const creditorName = document.getElementById('ccCreditorName')?.value.trim();
    const debtorName = document.getElementById('ccDebtorName')?.value.trim();
    const courtName = document.getElementById('ccCourtName')?.value.trim();

    const payload = {
        case_name: name,
        case_type: type,
        priority: priority,
        description: desc,
        creditor_data: { name: creditorName },
        debtor_data: { name: debtorName },
        financial_data: {
            cheque_amount: amount,
            amount: amount,
            transaction_date: transDate,
            dishonour_date: disDate,
            notice_date: noticeDate
        },
        court_data: { court_name: courtName }
    };

    try {
        const res = await api.createCase(payload);
        if (ui && typeof ui.toast === 'function') {
            ui.toast(`Case ${res.case_id} created successfully!`, 'success');
        }
        form.reset();
        window.showCaseDetail(res.case_id);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') {
            ui.toast(`Error creating case: ${err.message}`, 'error');
        }
    } finally {
        if (btn) btn.classList.remove('loading');
    }
}

function renderPagination(total, currentPage, limit) {
    const pagContainer = document.getElementById('caseListPagination');
    if (!pagContainer) return;
    const totalPages = Math.ceil(total / limit) || 1;
    if (totalPages <= 1) {
        pagContainer.innerHTML = '';
        return;
    }

    pagContainer.innerHTML = `
        <button class="btn btn-sm btn-outline" ${currentPage <= 1 ? 'disabled' : ''} onclick="changeCasePage(${currentPage - 1})"><i class="fas fa-chevron-left"></i> Prev</button>
        <span class="cms-page-indicator">Page ${currentPage} of ${totalPages} (${total} items)</span>
        <button class="btn btn-sm btn-outline" ${currentPage >= totalPages ? 'disabled' : ''} onclick="changeCasePage(${currentPage + 1})">Next <i class="fas fa-chevron-right"></i></button>
    `;
}

function formatCaseType(type) {
    const map = {
        'section_138': 'Section 138 NI Act',
        'sarfaesi': 'SARFAESI / DRT',
        'drt': 'DRT Recovery',
        'ibc': 'IBC / NCLT',
        'criminal': 'Criminal (BNS/IPC)',
        'civil': 'Civil / Commercial Suit'
    };
    return map[type] || type || 'General';
}

function formatDate(isoStr) {
    if (!isoStr) return '—';
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch {
        return isoStr;
    }
}

// ── Global Window Exports for HTML Onclick ─────────────────────
window.showCaseList = () => {
    switchScreen('caseListScreen');
    loadCaseList();
};
window.showCaseCreate = () => switchScreen('caseCreateScreen');
window.showCaseDetail = (caseId) => {
    switchScreen('caseDetailScreen');
    loadCaseDetail(caseId);
};
window.switchCmsTab = (tab) => {
    store.set('cmsActiveTab', tab);
    const caseId = store.get('activeCaseId');
    if (caseId) loadCaseDetail(caseId);
};
window.changeCasePage = (page) => {
    const filters = store.get('cmsListFilters', {});
    filters.page = page;
    store.set('cmsListFilters', filters);
    loadCaseList();
};
window.filterCasesByStatus = (status) => {
    const filters = store.get('cmsListFilters', {});
    filters.status = status;
    filters.page = 1;
    store.set('cmsListFilters', filters);
    document.querySelectorAll('.cms-filter-pill').forEach(p => p.classList.remove('active'));
    event.target.classList.add('active');
    loadCaseList();
};
window.handleCaseStatusChange = async (caseId, newStatus) => {
    try {
        await api.updateCaseStatus(caseId, newStatus);
        if (ui && typeof ui.toast === 'function') ui.toast(`Status updated to ${newStatus.toUpperCase()}`, 'success');
        loadCaseDetail(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Failed to update status: ${err.message}`, 'error');
    }
};
window.handleRunCmsAnalysis = async (caseId) => {
    try {
        if (ui && typeof ui.toast === 'function') ui.toast("Executing 12-Pillar Statutory Compliance Audit...", "info");
        const res = await api.analyzeCmsCase(caseId);
        if (ui && typeof ui.toast === 'function') ui.toast(`Audit Complete! Score: ${res.compliance_score}`, 'success');
        loadCaseDetail(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Analysis error: ${err.message}`, 'error');
    }
};
window.handleCalculateDeadlines = async (caseId) => {
    try {
        await api.calculateCaseDeadlines(caseId);
        if (ui && typeof ui.toast === 'function') ui.toast("Deadlines computed & persisted!", 'success');
        loadCaseDeadlinesList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Error: ${err.message}`, 'error');
    }
};
window.handleCompleteDeadline = async (deadlineId) => {
    try {
        await api.completeDeadline(deadlineId);
        if (ui && typeof ui.toast === 'function') ui.toast("Deadline marked completed!", 'success');
        const caseId = store.get('activeCaseId');
        if (caseId) loadCaseDeadlinesList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Error: ${err.message}`, 'error');
    }
};
window.handleUnlinkClient = async (caseId, clientId) => {
    try {
        await api.unlinkClientFromCase(caseId, clientId);
        if (ui && typeof ui.toast === 'function') ui.toast("Client unlinked", 'info');
        loadCaseDetail(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Error: ${err.message}`, 'error');
    }
};
