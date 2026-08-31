/**
 * JudiQ AI — Draft Workflow Frontend UI Module
 * Handles Draft Review Pipelines, In-App Editing, Versioning, Approval Sign-off, and PDF/DOCX Exports.
 */

import { api } from '../api.js?v=15';
import { ui } from '../ui.js?v=14';
import { escapeHtml } from './modules/utils.js?v=14';
import { store } from './modules/store.js?v=14';

export function initDraftWorkflow() {
    // Setup modal or editor listeners if needed
}

export async function loadDraftList(caseId) {
    const container = document.getElementById('cmsDraftListContainer');
    if (!container) return;
    container.innerHTML = `<div class="cms-loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading drafts...</div>`;

    try {
        const drafts = await api.listCmsDrafts(caseId);

        container.innerHTML = `
            <div class="cms-drafts-header">
                <h4>Legal Pleadings, Notices & Court Drafts</h4>
                <div class="cms-dh-actions">
                    <select id="newDraftTypeSelect" class="cms-input-sm">
                        <option value="LEGAL_NOTICE">Statutory Demand Notice (S.138)</option>
                        <option value="COMPLAINT">Section 138 Criminal Complaint</option>
                        <option value="SARFAESI_13_2_NOTICE">SARFAESI Section 13(2) Demand Notice</option>
                        <option value="SARFAESI_SEC_14_APPLICATION">SARFAESI Section 14 DM Application</option>
                        <option value="SARFAESI_SEC_17_SA_PETITION">DRT Securitization Application (S.17)</option>
                        <option value="DELAY_CONDONATION">Section 142 Delay Condonation Petition</option>
                        <option value="AFFIDAVIT">Sworn Evidence Affidavit</option>
                    </select>
                    <button class="btn btn-sm btn-primary" onclick="handleCreateNewDraft('${escapeHtml(caseId)}')"><i class="fas fa-plus"></i> Generate Draft</button>
                </div>
            </div>

            <div class="cms-drafts-pipeline">
                ${drafts.length === 0 ? '<p class="text-muted">No draft pleadings generated for this case yet.</p>' : drafts.map(d => {
                    const statusClass = `wf-status--${(d.status || 'draft').toLowerCase()}`;
                    return `
                        <div class="cms-draft-card">
                            <div class="drc-left">
                                <div class="drc-type">${escapeHtml(d.draft_type.replace(/_/g, ' '))}</div>
                                <div class="drc-meta">Version ${d.current_version || 1} • Created: ${formatDate(d.created_at)}</div>
                            </div>
                            <div class="drc-center">
                                <span class="cms-wf-pill ${statusClass}">${escapeHtml(d.status || 'DRAFT')}</span>
                            </div>
                            <div class="drc-right">
                                <button class="btn btn-sm btn-outline" onclick="openDraftEditorModal('${escapeHtml(d.workflow_id)}')"><i class="fas fa-edit"></i> Edit / Review</button>
                                <button class="btn btn-sm btn-outline" onclick="handleExportDraft('${escapeHtml(d.workflow_id)}', 'pdf')"><i class="fas fa-file-pdf"></i> PDF</button>
                                <button class="btn btn-sm btn-outline" onclick="handleExportDraft('${escapeHtml(d.workflow_id)}', 'docx')"><i class="fas fa-file-word"></i> Word</button>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="cms-error-box">Failed to load drafts: ${escapeHtml(err.message)}</div>`;
    }
}

export async function handleCreateNewDraft(caseId) {
    const draftType = document.getElementById('newDraftTypeSelect')?.value || 'LEGAL_NOTICE';
    try {
        if (ui && typeof ui.toast === 'function') ui.toast(`Generating ${draftType.replace(/_/g, ' ')}...`, 'info');
        const res = await api.createCmsDraft(caseId, draftType);
        if (ui && typeof ui.toast === 'function') ui.toast("Draft created in DRAFT status!", 'success');
        loadDraftList(caseId);
        openDraftEditorModal(res.workflow_id);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Failed to create draft: ${err.message}`, 'error');
    }
}

export async function openDraftEditorModal(workflowId) {
    const modal = document.getElementById('cmsDraftEditorModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.dataset.workflowId = workflowId;

    try {
        const wf = await api.getCmsDraftDetail(workflowId);
        const titleEl = document.getElementById('draftModalTitle');
        const editorEl = document.getElementById('draftModalEditor');
        const statusEl = document.getElementById('draftModalStatus');
        const commentsContainer = document.getElementById('draftModalComments');

        if (titleEl) titleEl.textContent = `${wf.draft_type.replace(/_/g, ' ')} (v${wf.current_version || 1})`;
        if (editorEl) editorEl.value = wf.draft_content || '';
        if (statusEl) statusEl.textContent = `Status: ${wf.status || 'DRAFT'}`;

        if (commentsContainer) {
            const comments = wf.reviewer_comments || [];
            commentsContainer.innerHTML = comments.length === 0
                ? '<p class="text-muted">No reviewer remarks yet.</p>'
                : comments.map(c => `
                    <div class="cms-comment-chip">
                        <strong>${escapeHtml(c.user_id || 'Reviewer')}:</strong> ${escapeHtml(c.comment)}
                        <span class="text-muted">(${c.status})</span>
                    </div>
                `).join('');
        }
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Failed to load draft: ${err.message}`, 'error');
    }
}

export async function handleExportDraft(workflowId, format = 'pdf') {
    try {
        if (ui && typeof ui.toast === 'function') ui.toast(`Generating ${format.toUpperCase()} export...`, 'info');
        const blob = await api.exportCmsDraft(workflowId, format);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `JUDIQ_Draft_${workflowId}.${format === 'docx' ? 'docx' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Export failed: ${err.message}`, 'error');
    }
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

// ── Global Window Exports ──────────────────────────────────────
window.loadDraftList = loadDraftList;
window.handleCreateNewDraft = handleCreateNewDraft;
window.openDraftEditorModal = openDraftEditorModal;
window.handleExportDraft = handleExportDraft;

window.submitSaveDraftContent = async () => {
    const modal = document.getElementById('cmsDraftEditorModal');
    if (!modal) return;
    const wfId = modal.dataset.workflowId;
    const content = document.getElementById('draftModalEditor')?.value;

    try {
        await api.updateCmsDraft(wfId, content);
        if (ui && typeof ui.toast === 'function') ui.toast("Draft updated!", 'success');
        const caseId = store.get('activeCaseId');
        if (caseId) loadDraftList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Save failed: ${err.message}`, 'error');
    }
};

window.submitDraftForReviewAction = async () => {
    const modal = document.getElementById('cmsDraftEditorModal');
    if (!modal) return;
    const wfId = modal.dataset.workflowId;

    try {
        await api.submitCmsDraft(wfId);
        if (ui && typeof ui.toast === 'function') ui.toast("Submitted for review!", 'success');
        modal.classList.add('hidden');
        const caseId = store.get('activeCaseId');
        if (caseId) loadDraftList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Submit failed: ${err.message}`, 'error');
    }
};

window.approveDraftAction = async () => {
    const modal = document.getElementById('cmsDraftEditorModal');
    if (!modal) return;
    const wfId = modal.dataset.workflowId;

    try {
        await api.approveCmsDraft(wfId);
        if (ui && typeof ui.toast === 'function') ui.toast("Draft Approved!", 'success');
        modal.classList.add('hidden');
        const caseId = store.get('activeCaseId');
        if (caseId) loadDraftList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Approval failed: ${err.message}`, 'error');
    }
};

window.markDraftFiledAction = async () => {
    const modal = document.getElementById('cmsDraftEditorModal');
    if (!modal) return;
    const wfId = modal.dataset.workflowId;
    const filingRef = prompt("Enter Court Filing / CNR / Diary Reference Number:");
    if (!filingRef) return;

    try {
        await api.markCmsDraftFiled(wfId, filingRef);
        if (ui && typeof ui.toast === 'function') ui.toast(`Marked as FILED with Ref: ${filingRef}`, 'success');
        modal.classList.add('hidden');
        const caseId = store.get('activeCaseId');
        if (caseId) loadDraftList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Filing update failed: ${err.message}`, 'error');
    }
};
