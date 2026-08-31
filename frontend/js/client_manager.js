/**
 * JudiQ AI — Client Management Frontend UI Module
 * Handles Client Directory, Profile Details, Client Creation, and Linking Modals.
 */

import { api } from '../api.js?v=15';
import { ui, switchScreen } from '../ui.js?v=14';
import { escapeHtml } from './modules/utils.js?v=14';
import { store } from './modules/store.js?v=14';

export function initClientManager() {
    // Setup listener for search input on clientListScreen
    const searchInput = document.getElementById('clientSearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadClientList({ search: e.target.value });
            }, 300);
        });
    }

    // Setup client creation form submit
    const createForm = document.getElementById('clientCreateForm');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await submitClientCreate();
        });
    }
}

export async function loadClientList(filters = {}) {
    const container = document.getElementById('clientListGrid');
    if (container) container.innerHTML = `<div class="cms-loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading clients...</div>`;

    try {
        const res = await api.listClients(filters);
        const clients = res.clients || [];

        if (container) {
            if (clients.length === 0) {
                container.innerHTML = `
                    <div class="cms-empty-state" style="grid-column: 1/-1;">
                        <i class="fas fa-users-slash"></i>
                        <p>No client profiles found.</p>
                        <button class="btn btn-primary btn-sm" onclick="showClientCreate()">Add New Client</button>
                    </div>
                `;
            } else {
                container.innerHTML = clients.map(cl => {
                    const typeIcon = cl.client_type === 'bank' ? 'fa-university' : cl.client_type === 'company' ? 'fa-building' : 'fa-user';
                    return `
                        <div class="cms-client-card" onclick="showClientDetail('${escapeHtml(cl.client_id)}')">
                            <div class="cl-card-header">
                                <div class="cl-avatar"><i class="fas ${typeIcon}"></i></div>
                                <div class="cl-header-text">
                                    <h4>${escapeHtml(cl.name)}</h4>
                                    <span class="cl-id">${escapeHtml(cl.client_id)}</span>
                                </div>
                            </div>
                            <div class="cl-card-body">
                                <div class="cl-badge-row">
                                    <span class="cl-type-badge">${escapeHtml((cl.client_type || 'Individual').toUpperCase())}</span>
                                    <span class="cl-role-badge">${escapeHtml((cl.role_type || 'Creditor').toUpperCase())}</span>
                                </div>
                                <div class="cl-prop"><i class="fas fa-envelope"></i> ${escapeHtml(cl.email || '—')}</div>
                                <div class="cl-prop"><i class="fas fa-phone"></i> ${escapeHtml(cl.phone || '—')}</div>
                            </div>
                            <div class="cl-card-footer">
                                <span><i class="fas fa-folder"></i> <strong>${cl.total_cases || 0}</strong> Cases</span>
                                <span class="cl-view-link">View Dossier <i class="fas fa-chevron-right"></i></span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
    } catch (err) {
        if (container) container.innerHTML = `<div class="cms-error-box">Failed to load clients: ${escapeHtml(err.message)}</div>`;
    }
}

export async function loadClientDetail(clientId) {
    store.set('activeClientId', clientId);
    const container = document.getElementById('clientDetailContainer');
    if (container) container.innerHTML = `<div class="cms-loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading client profile...</div>`;

    try {
        const client = await api.getClientDetail(clientId);
        if (!client) throw new Error("Client not found");

        const comp = client.company_info || {};
        const addr = client.address_data || {};
        const tax = client.tax_info || {};
        const cases = client.linked_cases || [];

        container.innerHTML = `
            <div class="cms-detail-header">
                <div class="cms-dh-left">
                    <button class="btn btn-sm btn-outline cms-back-btn" onclick="showClientList()"><i class="fas fa-arrow-left"></i> Clients</button>
                    <div class="cms-dh-title-group">
                        <h2>${escapeHtml(client.name)}</h2>
                        <span class="cms-dh-id">${escapeHtml(client.client_id)}</span>
                        <span class="cms-type-tag">${escapeHtml((client.client_type || 'Entity').toUpperCase())}</span>
                    </div>
                </div>
            </div>

            <div class="cms-overview-grid">
                <div class="cms-card">
                    <h4><i class="fas fa-address-card"></i> Contact & Registered Information</h4>
                    <div class="cms-prop-row"><span class="label">Legal / Trade Name:</span> <strong>${escapeHtml(client.legal_name || client.name)}</strong></div>
                    <div class="cms-prop-row"><span class="label">Official Email:</span> <span>${escapeHtml(client.email || '—')}</span></div>
                    <div class="cms-prop-row"><span class="label">Phone / Landline:</span> <span>${escapeHtml(client.phone || '—')}</span></div>
                    <div class="cms-prop-row"><span class="label">Mobile Number:</span> <span>${escapeHtml(client.mobile || '—')}</span></div>
                    <div class="cms-prop-row"><span class="label">City / State:</span> <span>${escapeHtml(addr.city || '—')} / ${escapeHtml(addr.state || '—')}</span></div>
                </div>

                <div class="cms-card">
                    <h4><i class="fas fa-file-invoice-dollar"></i> Corporate & Tax Identity</h4>
                    <div class="cms-prop-row"><span class="label">PAN Number:</span> <span>${escapeHtml(tax.pan || '—')}</span></div>
                    <div class="cms-prop-row"><span class="label">GSTIN / Tax ID:</span> <span>${escapeHtml(tax.gstin || '—')}</span></div>
                    <div class="cms-prop-row"><span class="label">CIN / Registration:</span> <span>${escapeHtml(comp.cin || '—')}</span></div>
                    <div class="cms-prop-row"><span class="label">Authorized Signatory:</span> <span>${escapeHtml(comp.signatory_name || '—')}</span></div>
                </div>

                <div class="cms-card" style="grid-column: 1/-1;">
                    <h4><i class="fas fa-briefcase"></i> Associated Litigation Matters (${cases.length})</h4>
                    ${cases.length === 0 ? '<p class="text-muted">No cases linked to this client yet.</p>' : `
                        <div class="cms-linked-cases-list">
                            ${cases.map(c => `
                                <div class="cms-linked-case-item" onclick="showCaseDetail('${escapeHtml(c.case_id)}')">
                                    <div>
                                        <strong>${escapeHtml(c.case_name)}</strong>
                                        <span class="text-muted">(${escapeHtml(c.case_id)})</span>
                                    </div>
                                    <div>
                                        <span class="cms-type-tag">${escapeHtml(c.case_type || 'General')}</span>
                                        <span class="cms-status-pill status-pill--${c.case_status || 'draft'}">${escapeHtml((c.case_status || 'draft').toUpperCase())}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `}
                </div>
            </div>
        `;
    } catch (err) {
        if (container) container.innerHTML = `<div class="cms-error-box">Failed to load client: ${escapeHtml(err.message)}</div>`;
    }
}

async function submitClientCreate() {
    const form = document.getElementById('clientCreateForm');
    if (!form) return;
    const btn = form.querySelector('button[type="submit"]');
    if (btn) btn.classList.add('loading');

    const name = document.getElementById('clName')?.value.trim();
    const type = document.getElementById('clType')?.value;
    const role = document.getElementById('clRole')?.value;
    const email = document.getElementById('clEmail')?.value.trim();
    const phone = document.getElementById('clPhone')?.value.trim();
    const pan = document.getElementById('clPan')?.value.trim();
    const gstin = document.getElementById('clGstin')?.value.trim();

    const payload = {
        name: name,
        client_type: type,
        role_type: role,
        email: email,
        phone: phone,
        tax_info: { pan: pan, gstin: gstin }
    };

    try {
        const res = await api.createClient(payload);
        if (ui && typeof ui.toast === 'function') {
            ui.toast(`Client ${res.name} added!`, 'success');
        }
        form.reset();
        window.showClientDetail(res.client_id);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') {
            ui.toast(`Error creating client: ${err.message}`, 'error');
        }
    } finally {
        if (btn) btn.classList.remove('loading');
    }
}

export function openLinkClientModal(caseId) {
    const modal = document.getElementById('cmsLinkClientModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.dataset.caseId = caseId;

    // Load available clients in select
    api.listClients().then(res => {
        const select = document.getElementById('linkClientSelect');
        if (select) {
            select.innerHTML = (res.clients || []).map(cl => `
                <option value="${escapeHtml(cl.client_id)}">${escapeHtml(cl.name)} (${escapeHtml(cl.client_type)})</option>
            `).join('');
        }
    });
}

// ── Global Window Exports ──────────────────────────────────────
window.showClientList = () => {
    switchScreen('clientListScreen');
    loadClientList();
};
window.showClientCreate = () => switchScreen('clientCreateScreen');
window.showClientDetail = (clientId) => {
    switchScreen('clientDetailScreen');
    loadClientDetail(clientId);
};
window.openLinkClientModal = openLinkClientModal;
window.submitLinkClientModal = async () => {
    const modal = document.getElementById('cmsLinkClientModal');
    if (!modal) return;
    const caseId = modal.dataset.caseId;
    const clientId = document.getElementById('linkClientSelect')?.value;
    const role = document.getElementById('linkClientRoleSelect')?.value || 'creditor';

    if (!clientId) return;
    try {
        await api.linkClientToCase(caseId, clientId, role);
        if (ui && typeof ui.toast === 'function') ui.toast("Client linked to case!", 'success');
        modal.classList.add('hidden');
        if (window.loadCaseDetail) window.loadCaseDetail(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Failed to link: ${err.message}`, 'error');
    }
};
