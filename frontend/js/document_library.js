/**
 * JudiQ AI — Document Library Frontend UI Module
 * Handles Case Document Library, Drag-and-Drop Encrypted Uploads, and S.65B Evidence Certification.
 */

import { api } from '../api.js?v=15';
import { ui } from '../ui.js?v=14';
import { escapeHtml } from './modules/utils.js?v=14';
import { store } from './modules/store.js?v=14';

export function initDocumentLibrary() {
    // Setup Drag-and-Drop on upload zones
    setupUploadZone();
}

function setupUploadZone() {
    document.addEventListener('dragover', (e) => {
        const zone = e.target.closest('.cms-doc-dropzone');
        if (zone) {
            e.preventDefault();
            zone.classList.add('drag-active');
        }
    });

    document.addEventListener('dragleave', (e) => {
        const zone = e.target.closest('.cms-doc-dropzone');
        if (zone) {
            e.preventDefault();
            zone.classList.remove('drag-active');
        }
    });

    document.addEventListener('drop', (e) => {
        const zone = e.target.closest('.cms-doc-dropzone');
        if (zone) {
            e.preventDefault();
            zone.classList.remove('drag-active');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const caseId = store.get('activeCaseId');
                if (caseId) handleFileUpload(caseId, files[0]);
            }
        }
    });
}

export async function loadDocumentList(caseId) {
    const container = document.getElementById('cmsDocumentListContainer');
    if (!container) return;
    container.innerHTML = `<div class="cms-loading-spinner"><i class="fas fa-spinner fa-spin"></i> Loading documents...</div>`;

    try {
        const docs = await api.listCmsDocuments(caseId);

        container.innerHTML = `
            <div class="cms-docs-header">
                <h4>Evidentiary Dossier & Electronic Records</h4>
                <button class="btn btn-sm btn-primary" onclick="document.getElementById('cmsFileInput').click()"><i class="fas fa-upload"></i> Upload Document</button>
                <input type="file" id="cmsFileInput" style="display:none;" onchange="if(this.files.length) handleFileUpload('${escapeHtml(caseId)}', this.files[0])">
            </div>

            <!-- Drag and Drop Zone -->
            <div class="cms-doc-dropzone">
                <i class="fas fa-cloud-upload-alt fa-2x"></i>
                <p>Drag and drop legal instruments, return memos, notices, or court orders here</p>
                <span class="text-muted">Files are AES-256 / Fernet encrypted at rest with SHA-256 integrity hashing</span>
            </div>

            <div class="cms-docs-grid">
                ${docs.length === 0 ? '<p class="text-muted" style="grid-column:1/-1;">No documents uploaded to this case dossier yet.</p>' : docs.map(d => {
                    const isCert = d.s65b_status === 'certified';
                    const certBadge = isCert
                        ? `<span class="cms-cert-badge cert--certified"><i class="fas fa-check-circle"></i> S.65B Certified</span>`
                        : `<span class="cms-cert-badge cert--pending" onclick="openS65BModal('${escapeHtml(d.document_id)}')"><i class="fas fa-certificate"></i> Certify S.65B</span>`;

                    return `
                        <div class="cms-doc-card">
                            <div class="dc-top">
                                <div class="dc-file-icon"><i class="fas fa-file-pdf"></i></div>
                                <div class="dc-meta">
                                    <div class="dc-filename">${escapeHtml(d.file_name)}</div>
                                    <div class="dc-sub">${escapeHtml(d.doc_type || 'Document')} • ${(d.file_size / 1024).toFixed(1)} KB</div>
                                </div>
                            </div>
                            <div class="dc-middle">
                                ${certBadge}
                            </div>
                            <div class="dc-actions">
                                <button class="btn btn-sm btn-outline" onclick="handleDownloadDoc('${escapeHtml(d.document_id)}', '${escapeHtml(d.file_name)}')"><i class="fas fa-download"></i> Download</button>
                                <button class="btn btn-sm btn-icon" onclick="handleDeleteDoc('${escapeHtml(d.document_id)}')"><i class="fas fa-trash"></i></button>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="cms-error-box">Failed to load documents: ${escapeHtml(err.message)}</div>`;
    }
}

export async function handleFileUpload(caseId, file) {
    if (!file) return;
    if (ui && typeof ui.toast === 'function') ui.toast(`Encrypting & uploading ${file.name}...`, 'info');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', guessDocType(file.name));

    try {
        const res = await api.uploadCmsDocument(caseId, formData);
        if (ui && typeof ui.toast === 'function') ui.toast(`Document ${res.file_name} uploaded and encrypted!`, 'success');
        loadDocumentList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Upload failed: ${err.message}`, 'error');
    }
}

export async function handleDownloadDoc(docId, fileName) {
    try {
        if (ui && typeof ui.toast === 'function') ui.toast("Decrypting document...", "info");
        const blob = await api.downloadCmsDocument(docId);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Download failed: ${err.message}`, 'error');
    }
}

export async function handleDeleteDoc(docId) {
    if (!confirm("Are you sure you want to delete this document from the dossier?")) return;
    try {
        await api.deleteCmsDocument(docId);
        if (ui && typeof ui.toast === 'function') ui.toast("Document deleted", 'info');
        const caseId = store.get('activeCaseId');
        if (caseId) loadDocumentList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Delete failed: ${err.message}`, 'error');
    }
}

export async function openS65BModal(docId) {
    const modal = document.getElementById('cmsS65BModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.dataset.docId = docId;

    try {
        const res = await api.generateS65BCert(docId);
        const preview = document.getElementById('s65bTemplatePreview');
        if (preview) preview.value = res.certificate_template;
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Error generating certificate: ${err.message}`, 'error');
    }
}

function guessDocType(filename) {
    const fn = filename.toLowerCase();
    if (fn.includes('cheque')) return 'cheque';
    if (fn.includes('memo') || fn.includes('return')) return 'bank_return_memo';
    if (fn.includes('notice')) return 'demand_notice';
    if (fn.includes('order') || fn.includes('injunction')) return 'court_order';
    if (fn.includes('loan') || fn.includes('agreement')) return 'loan_agreement';
    return 'other';
}

// ── Global Window Exports ──────────────────────────────────────
window.loadDocumentList = loadDocumentList;
window.handleFileUpload = handleFileUpload;
window.handleDownloadDoc = handleDownloadDoc;
window.handleDeleteDoc = handleDeleteDoc;
window.openS65BModal = openS65BModal;
window.submitS65BCertification = async () => {
    const modal = document.getElementById('cmsS65BModal');
    if (!modal) return;
    const docId = modal.dataset.docId;
    const certifierName = document.getElementById('s65bCertifierName')?.value.trim();
    const certifierDesig = document.getElementById('s65bCertifierDesig')?.value.trim();

    if (!certifierName) {
        alert("Please enter the certifier's name.");
        return;
    }

    try {
        await api.certifyDocument(docId, {
            certifier_name: certifierName,
            certifier_designation: certifierDesig || 'Authorized Officer'
        });
        if (ui && typeof ui.toast === 'function') ui.toast("Document certified under Section 65B!", 'success');
        modal.classList.add('hidden');
        const caseId = store.get('activeCaseId');
        if (caseId) loadDocumentList(caseId);
    } catch (err) {
        if (ui && typeof ui.toast === 'function') ui.toast(`Certification failed: ${err.message}`, 'error');
    }
};
