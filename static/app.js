/* =============================================
   DVR Checklist Analyzer - Frontend Logic
   ============================================= */

// Configurazione backend (puoi sovrascrivere con env var o snippet in index.html)
// Per deploy su Netlify: imposta API_BASE al dominio del backend Flask
const API_BASE = (typeof window !== 'undefined' && window.__API_BASE__) || '';

function apiUrl(path) {
    return API_BASE + path;
}

// --- State ---
let currentRisks       = [];
let detectedKeys       = [];
let allDbRisks         = [];
let checklistStructure = [];
let editingIndex       = null;
let selectedFile       = null;
let progressInterval   = null;
let currentModalImage  = null;

// --- DOM Refs ---
const dropzone               = document.getElementById('dropzone');
const fileInput              = document.getElementById('file-input');
const fileDetails            = document.getElementById('file-details');
const fileNameEl             = document.getElementById('file-name');
const fileSizeEl             = document.getElementById('file-size');
const removeFileBtn          = document.getElementById('remove-file-btn');
const analyzeBtn             = document.getElementById('analyze-btn');

const uploadSection          = document.getElementById('upload-section');
const loadingSection         = document.getElementById('loading-section');
const interactiveSection     = document.getElementById('interactive-checklist-section');
const resultsSection         = document.getElementById('results-section');
const databaseBrowserSection = document.getElementById('database-browser-section');

const progressBar            = document.getElementById('progress-bar');
const progressPercent        = document.getElementById('progress-percent');
const progressStatusMsg      = document.getElementById('progress-status-msg');
const loadingTitle           = document.getElementById('loading-title');
const loadingDesc            = document.getElementById('loading-description');
const stepConvert            = document.getElementById('step-convert');
const stepAI                 = document.getElementById('step-ai');
const stepMatch              = document.getElementById('step-match');

const detectedCount          = document.getElementById('detected-count');
const matchedCount           = document.getElementById('matched-count');
const detectedList           = document.getElementById('detected-list-container');
const risksContainer         = document.getElementById('risks-container');
const checklistGridContainer = document.getElementById('checklist-grid-container');

const btnSelectAllCL         = document.getElementById('btn-select-all-cl');
const btnDeselectAllCL       = document.getElementById('btn-deselect-all-cl');
const btnApplyCL             = document.getElementById('btn-apply-cl');
const btnEditFlags           = document.getElementById('btn-edit-flags');

const btnAddRisk             = document.getElementById('btn-add-risk');
const btnExportWord          = document.getElementById('btn-export-word');
const btnNewAnalysis         = document.getElementById('btn-new-analysis');

const interactiveBadge       = document.getElementById('interactive-badge');
const resultsBadge           = document.getElementById('results-badge');

const dbSearchInput          = document.getElementById('db-search-input');
const dbTotalCount           = document.getElementById('db-total-count');
const dbTableBody            = document.getElementById('db-table-body');

const modal                  = document.getElementById('risk-modal');
const modalTitle             = document.getElementById('modal-title');
const modalLuogo             = document.getElementById('modal-luogo');
const modalRischio           = document.getElementById('modal-rischio');
const modalAzione            = document.getElementById('modal-azione');
const modalEntro             = document.getElementById('modal-entro');
const modalOrdine            = document.getElementById('modal-ordine');
const modalImageFile         = document.getElementById('modal-image-file');
const modalImagePreviewBox   = document.getElementById('modal-image-preview-container');
const modalImagePreview      = document.getElementById('modal-image-preview');
const btnRemoveModalImage    = document.getElementById('btn-remove-modal-image');
const modalCloseBtn          = document.getElementById('modal-close-btn');
const modalCancelBtn         = document.getElementById('modal-cancel-btn');
const modalSaveBtn           = document.getElementById('modal-save-btn');

// ─── Page & Section Mapping for 2-Column PDF Layout ────────────────────────
const PAGE1_LEFT  = ['CARATTERISTICHE EDIFICIO', 'TERRAZZA CONDOMINIALE', 'LOCALE LAVATOIO'];
const PAGE1_RIGHT = ['CONTATORI ELETTRICI', 'CANTINE', 'CHIOSTRINA CONDOMINIALE', 'AUTORIMESSA >300 / 10 posti auto', 'AUTORIMESSA <300 / 10 posti auto'];

const PAGE2_LEFT  = ['SOFFITTE', 'FINESTRE POSIZIONE', 'VANO SCALA CONDOMINIALE', 'IMPIANTO ASCENSORE'];
const PAGE2_RIGHT = ['PERCORSI VEICOLARI INT/EST.', 'FABBRICATO ESTERNO', 'GIARDINO CONDOMINIALE', 'CALDAIA CONDOMINIALE', 'IMPIANTO ANTINCENDIO', 'CONTATORI GAS', 'CONTATORI IDRICI', 'AMIANTO MCA PRESENTE'];

const PAGE3_FULL  = ['DIPENDENTE CONDOMINIALE'];

// ─── Initialization ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    await loadChecklistStructure();
    await loadDatabaseRisks();
    showSection('home-section');
    const tabHome = document.getElementById('tab-home');
    if (tabHome) {
        tabHome.addEventListener('click', () => goHome());
    }
});

// ─── Tab Navigation ─────────────────────────────────────────────────────────

function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.target;
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                switchTab(tab, targetSection);
            }
        });
    });
}

function switchTab(activeTabEl, activeSectionEl) {
    console.log("switchTab:", activeSectionEl ? activeSectionEl.id : null);
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(s => {
        s.classList.add('hidden');
        s.style.display = '';
        s.style.visibility = '';
    });

    if (activeTabEl) activeTabEl.classList.add('active');
    if (activeSectionEl) {
        activeSectionEl.classList.remove('hidden');
        activeSectionEl.style.display = '';
        activeSectionEl.style.visibility = 'visible';
        console.log("switchTab visible:", activeSectionEl.id);
    }

    const navTabs = document.querySelector('.nav-tabs');
    if (navTabs) navTabs.style.visibility = 'visible';
}

function showSection(sectionId) {
    console.log("showSection:", sectionId);
    const section = document.getElementById(sectionId);
    const isHome = sectionId === 'home-section';
    document.querySelectorAll('.tab-content').forEach(s => {
        s.classList.add('hidden');
        s.style.display = '';
        s.style.visibility = '';
    });
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

    if (isHome) {
        if (section) {
            section.classList.remove('hidden');
            section.style.display = '';
            section.style.visibility = 'visible';
            console.log("Home section visible");
        }
        const navTabs = document.querySelector('.nav-tabs');
        if (navTabs) navTabs.style.visibility = 'hidden';
    } else {
        if (section) {
            section.classList.remove('hidden');
            section.style.display = '';
            section.style.visibility = 'visible';
            console.log("Section visible:", sectionId);
        }
        const navTabs = document.querySelector('.nav-tabs');
        if (navTabs) navTabs.style.visibility = 'visible';
        const tab = document.querySelector(`.nav-tab[data-target="${sectionId}"]`);
        if (tab) tab.classList.add('active');
    }
}

function goHome() {
    console.log("goHome");
    currentRisks = [];
    detectedKeys = [];
    updateInteractiveChecklistState([]);
    renderRisks();
    clearFile();
    showSection('home-section');
}

// ─── Home Options ──────────────────────────────────────────────────────────────

document.querySelectorAll('.home-card').forEach(card => {
    card.addEventListener('click', async () => {
        const action = card.dataset.action;
        if (action === 'import-pdf') {
            switchTab(document.querySelector('[data-target="upload-section"]'), uploadSection);
        } else if (action === 'compile-direct') {
            switchTab(document.getElementById('tab-interactive'), interactiveSection);
        } else if (action === 'view-database') {
            await loadDatabaseRisks();
            switchTab(document.getElementById('tab-database'), databaseBrowserSection);
        }
    });
});

// ─── File Selection ──────────────────────────────────────────────────────────

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function setFile(file) {
    if (!file || file.type !== 'application/pdf') {
        showToast('Seleziona un file PDF valido.', 'error');
        return;
    }
    selectedFile = file;
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatSize(file.size);
    fileDetails.classList.remove('hidden');
    dropzone.classList.add('has-file');
    analyzeBtn.classList.remove('disabled');
    analyzeBtn.disabled = false;
}

function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    fileDetails.classList.add('hidden');
    dropzone.classList.remove('has-file');
    analyzeBtn.classList.add('disabled');
    analyzeBtn.disabled = true;
}

dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => { if (e.target.files[0]) setFile(e.target.files[0]); });
removeFileBtn.addEventListener('click', e => { e.stopPropagation(); clearFile(); });

dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
});

// ─── Progress Bar Polling & Analysis Flow ───────────────────────────────────

function updateProgressUI(pct, msg) {
    progressBar.style.width = pct + '%';
    progressPercent.textContent = pct + '%';
    if (msg) progressStatusMsg.textContent = msg;

    if (pct < 30) {
        activateStep(stepConvert);
    } else if (pct < 90) {
        activateStep(stepAI);
    } else {
        activateStep(stepMatch);
    }
}

function activateStep(step) {
    [stepConvert, stepAI, stepMatch].forEach(s => s.classList.remove('active', 'done'));
    const steps = [stepConvert, stepAI, stepMatch];
    const idx   = steps.indexOf(step);
    for (let i = 0; i < idx; i++) steps[i].classList.add('done');
    step.classList.add('active');
}

function startProgressPolling(sessionId) {
    stopProgressPolling();
    progressInterval = setInterval(async () => {
        try {
            const res = await fetch(apiUrl(`/api/progress/${sessionId}`));
            if (res.ok) {
                const data = await res.json();
                updateProgressUI(data.pct || 0, data.msg || '');
            }
        } catch (e) {
            console.error('Progress poll error:', e);
        }
    }, 350);
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    await runAnalysis();
});

async function runAnalysis() {
    const sessionId = 'session_' + Date.now();
    switchTab(document.querySelector('[data-target="upload-section"]'), loadingSection);
    updateProgressUI(5, 'Inizializzazione sessione di analisi...');
    startProgressPolling(sessionId);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('session_id', sessionId);

    try {
        const response = await fetch(apiUrl('/api/analyze'), { method: 'POST', body: formData });
        const data     = await response.json();

        stopProgressPolling();
        updateProgressUI(100, 'Elaborazione completata con successo!');

        if (!response.ok || data.error) {
            throw new Error(data.error || `Errore HTTP ${response.status}`);
        }

        await delay(300);
        
        detectedKeys = data.detected_keys || [];
        updateInteractiveChecklistState(detectedKeys);
        
        currentRisks = data.risks || [];
        renderRisks();
        
        showToast(`Rilevati ${detectedKeys.length} flag dall'OCR. Verifica la checklist a 2 colonne!`, 'info');
        switchTab(document.getElementById('tab-interactive'), interactiveSection);

    } catch (err) {
        stopProgressPolling();
        switchTab(document.querySelector('[data-target="upload-section"]'), uploadSection);
        showToast('Errore durante l\'analisi: ' + err.message, 'error');
        console.error(err);
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ─── Render 2-Column PDF Paper Checklist Layout ─────────────────────────────

async function loadChecklistStructure() {
    try {
        const res = await fetch(apiUrl('/api/checklist_structure'));
        const data = await res.json();
        if (data.success) {
            checklistStructure = data.categories || [];
            renderPaperChecklist();
        }
    } catch (e) {
        console.error('Errore caricamento struttura checklist:', e);
    }
}

function renderPaperChecklist() {
    checklistGridContainer.innerHTML = '';
    if (!checklistStructure || checklistStructure.length === 0) {
        checklistGridContainer.innerHTML = '<p class="empty-msg">Impossibile caricare la checklist.</p>';
        return;
    }

    const catMap = {};
    checklistStructure.forEach(c => { catMap[c.category] = c; });

    // Page 1
    const p1 = createPaperPage('PAGINA 1 - Sopralluogo Fabbricato & Impianti', catMap, PAGE1_LEFT, PAGE1_RIGHT);
    checklistGridContainer.appendChild(p1);

    // Page 2
    const p2 = createPaperPage('PAGINA 2 - Vano Scala, Caldaia & Prevenzione Incendi', catMap, PAGE2_LEFT, PAGE2_RIGHT);
    checklistGridContainer.appendChild(p2);

    // Page 3 (Dipendente Condominiale & Altre Categorie)
    const otherCats = checklistStructure
        .map(c => c.category)
        .filter(cName => ![...PAGE1_LEFT, ...PAGE1_RIGHT, ...PAGE2_LEFT, ...PAGE2_RIGHT].includes(cName));
    
    if (otherCats.length > 0) {
        const half = Math.ceil(otherCats.length / 2);
        const p3Left = otherCats.slice(0, half);
        const p3Right = otherCats.slice(half);
        const p3 = createPaperPage('PAGINA 3 - Dipendente Condominiale & Ulteriori Voci', catMap, p3Left, p3Right);
        checklistGridContainer.appendChild(p3);
    }
}

function createPaperPage(pageTitle, catMap, leftCatNames, rightCatNames) {
    const pageCard = document.createElement('div');
    pageCard.className = 'pdf-paper-page';

    const header = document.createElement('div');
    header.className = 'pdf-page-header';
    header.innerHTML = `<span><i class="fa-solid fa-file-invoice"></i> ${pageTitle}</span>`;
    pageCard.appendChild(header);

    const colsGrid = document.createElement('div');
    colsGrid.className = 'pdf-paper-columns';

    // Left Column
    const leftCol = document.createElement('div');
    leftCol.className = 'pdf-column';
    leftCatNames.forEach(cName => {
        if (catMap[cName]) leftCol.appendChild(createCategoryCard(catMap[cName]));
    });
    colsGrid.appendChild(leftCol);

    // Right Column
    const rightCol = document.createElement('div');
    rightCol.className = 'pdf-column';
    rightCatNames.forEach(cName => {
        if (catMap[cName]) rightCol.appendChild(createCategoryCard(catMap[cName]));
    });
    colsGrid.appendChild(rightCol);

    pageCard.appendChild(colsGrid);
    return pageCard;
}

function createCategoryCard(cat) {
    const card = document.createElement('div');
    card.className = 'cl-category-card';
    
    const title = document.createElement('div');
    title.className = 'cl-category-title';
    title.innerHTML = `<span><i class="fa-solid fa-folder"></i> ${escHtml(cat.category)}</span>`;
    card.appendChild(title);

    const list = document.createElement('div');
    list.className = 'cl-items-list';

    cat.items.forEach(item => {
        const row = document.createElement('label');
        row.className = 'cl-item-row';
        row.dataset.key = item.key;

        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.dataset.key = item.key;
        chk.addEventListener('change', () => {
            row.classList.toggle('checked', chk.checked);
            updateSelectedKeysFromChecklist();
        });

        const labelSpan = document.createElement('span');
        labelSpan.className = 'cl-item-label';
        labelSpan.textContent = item.item;

        row.appendChild(chk);
        row.appendChild(labelSpan);
        list.appendChild(row);
    });

    card.appendChild(list);
    return card;
}

function updateInteractiveChecklistState(keysToSelect) {
    const keySet = new Set(keysToSelect || []);
    const checkboxes = checklistGridContainer.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(chk => {
        const key = chk.dataset.key;
        const isChecked = keySet.has(key);
        chk.checked = isChecked;
        const parentRow = chk.closest('.cl-item-row');
        if (parentRow) {
            parentRow.classList.toggle('checked', isChecked);
        }
    });

    updateSelectedKeysFromChecklist();
}

function updateSelectedKeysFromChecklist() {
    const selectedCheckboxes = checklistGridContainer.querySelectorAll('input[type="checkbox"]:checked');
    detectedKeys = Array.from(selectedCheckboxes).map(chk => chk.dataset.key);
    interactiveBadge.textContent = detectedKeys.length;
}

btnSelectAllCL.addEventListener('click', () => {
    checklistGridContainer.querySelectorAll('input[type="checkbox"]').forEach(chk => {
        chk.checked = true;
        const p = chk.closest('.cl-item-row');
        if (p) p.classList.add('checked');
    });
    updateSelectedKeysFromChecklist();
});

btnDeselectAllCL.addEventListener('click', () => {
    checklistGridContainer.querySelectorAll('input[type="checkbox"]').forEach(chk => {
        chk.checked = false;
        const p = chk.closest('.cl-item-row');
        if (p) p.classList.remove('checked');
    });
    updateSelectedKeysFromChecklist();
});

btnApplyCL.addEventListener('click', async () => {
    updateSelectedKeysFromChecklist();
    await reMatchKeys(detectedKeys);
    switchTab(document.getElementById('tab-results'), resultsSection);
});

btnEditFlags.addEventListener('click', () => {
    switchTab(document.getElementById('tab-interactive'), interactiveSection);
});

async function reMatchKeys(keys) {
    try {
        const res = await fetch(apiUrl('/api/match_keys'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keys: keys })
        });
        const data = await res.json();
        if (data.success) {
            currentRisks = data.risks || [];
            renderRisks();
            showToast('Criticità rigenerate con foto ed ordinate per colonna H!', 'success');
        } else {
            showToast('Errore rigenerazione: ' + (data.error || ''), 'error');
        }
    } catch (e) {
        showToast('Errore durante la rigenerazione delle criticità', 'error');
    }
}

// ─── Results & Risks Rendering ──────────────────────────────────────────────

function renderRisks() {
    sortRisksByOrder(currentRisks);

    detectedCount.textContent = detectedKeys.length;
    matchedCount.textContent  = currentRisks.length;
    resultsBadge.textContent  = currentRisks.length;

    // Sidebar: list of checked keys
    detectedList.innerHTML = '';
    if (detectedKeys.length === 0) {
        detectedList.innerHTML = '<p class="empty-msg">Nessun flag selezionato.</p>';
    } else {
        detectedKeys.forEach(k => {
            const item = document.createElement('div');
            item.className = 'detected-item';
            item.innerHTML = `<i class="fa-solid fa-check-square"></i><span>${escHtml(k)}</span>`;
            detectedList.appendChild(item);
        });
    }

    // Main column
    risksContainer.innerHTML = '';
    if (currentRisks.length === 0) {
        risksContainer.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-magnifying-glass"></i>
                <p>Nessuna criticità associata ai flag selezionati.<br>
                Usa la <strong>Checklist Interattiva</strong> o la <strong>Consultazione Database</strong> per inserire voci.</p>
            </div>`;
        return;
    }

    currentRisks.forEach((risk, idx) => {
        const card = document.createElement('div');
        card.className = 'risk-card';
        const ordVal = (risk.ordine !== undefined && risk.ordine !== 999999) ? risk.ordine : '—';
        const imgHtml = risk.image ? `<img src="${risk.image}" alt="Foto Rischio" class="risk-thumb" title="Clicca per ingrandire">` : `<div style="opacity:0.4; font-size:0.8rem;"><i class="fa-solid fa-image-slash"></i> Nessuna foto</div>`;

        card.innerHTML = `
            <div class="risk-card-header">
                <div class="risk-index" title="Posizione nella tabella finale">${idx + 1}</div>
                <div class="risk-location">
                    <i class="fa-solid fa-location-dot"></i>
                    <strong>${escHtml(risk.luogo || '—')}</strong>
                </div>
                <div class="order-badge" title="Valore Colonna H (ORDINE)">Ord: ${ordVal}</div>
                <div class="risk-actions">
                    <button class="action-btn edit-btn" title="Modifica" data-idx="${idx}">
                        <i class="fa-solid fa-pen"></i>
                    </button>
                    <button class="action-btn delete-btn" title="Elimina" data-idx="${idx}">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="risk-card-body" style="display: flex; gap: 1.25rem;">
                <div style="flex: 1;">
                    <div class="risk-field">
                        <label><i class="fa-solid fa-triangle-exclamation"></i> Fattore di rischio</label>
                        <p>${escHtml(risk.rischio || '—')}</p>
                    </div>
                    <div class="risk-field">
                        <label><i class="fa-solid fa-wrench"></i> Azione migliorativa</label>
                        <p>${escHtml(risk.azione || '—')}</p>
                    </div>
                    <div class="risk-field risk-field-inline">
                        <label><i class="fa-solid fa-calendar"></i> Da attuarsi entro</label>
                        <span class="entro-badge">${escHtml(risk.entro || '—')}</span>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-width: 100px;">
                    ${imgHtml}
                </div>
            </div>`;
        risksContainer.appendChild(card);
    });

    risksContainer.querySelectorAll('.edit-btn').forEach(btn =>
        btn.addEventListener('click', () => openModal(parseInt(btn.dataset.idx))));
    risksContainer.querySelectorAll('.delete-btn').forEach(btn =>
        btn.addEventListener('click', () => deleteRisk(parseInt(btn.dataset.idx))));
}

function sortRisksByOrder(arr) {
    arr.sort((a, b) => {
        const ordA = (a.ordine !== undefined && a.ordine !== null) ? Number(a.ordine) : 999999;
        const ordB = (b.ordine !== undefined && b.ordine !== null) ? Number(b.ordine) : 999999;
        return ordA - ordB;
    });
}

function deleteRisk(idx) {
    currentRisks.splice(idx, 1);
    renderRisks();
    showToast('Criticità eliminata.', 'success');
}

// ─── Modal for Editing/Adding Custom Risks ───────────────────────────────────

let isPermanentDbAdd = false;
const btnAddDbPermanent = document.getElementById('btn-add-db-permanent');

if (btnAddDbPermanent) {
    btnAddDbPermanent.addEventListener('click', () => {
        isPermanentDbAdd = true;
        openModal(null);
        modalTitle.textContent = 'Aggiungi Nuova Criticità al Database Excel';
    });
}

function openModal(idx) {
    editingIndex = idx;
    currentModalImage = null;
    const risk = idx === null ? {} : currentRisks[idx];
    if (!isPermanentDbAdd) {
        modalTitle.textContent = idx === null ? 'Aggiungi Criticità Manuale' : 'Modifica Criticità';
    }
    modalLuogo.value   = risk.luogo   || '';
    modalRischio.value = risk.rischio || '';
    modalAzione.value  = risk.azione  || '';
    modalEntro.value   = risk.entro   || '';
    modalOrdine.value  = (risk.ordine !== undefined && risk.ordine !== 999999) ? risk.ordine : 999;
    modalImageFile.value = '';

    if (risk.image) {
        currentModalImage = risk.image;
        modalImagePreview.src = risk.image;
        modalImagePreviewBox.classList.remove('hidden');
    } else {
        modalImagePreviewBox.classList.add('hidden');
    }

    modal.classList.remove('hidden');
}

function closeModal() {
    modal.classList.add('hidden');
    editingIndex = null;
    currentModalImage = null;
    isPermanentDbAdd = false;
}

modalImageFile.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = ev => {
            currentModalImage = ev.target.result;
            modalImagePreview.src = currentModalImage;
            modalImagePreviewBox.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
});

btnRemoveModalImage.addEventListener('click', () => {
    currentModalImage = null;
    modalImageFile.value = '';
    modalImagePreviewBox.classList.add('hidden');
});

btnAddRisk.addEventListener('click', () => {
    isPermanentDbAdd = false;
    openModal(null);
});
modalCloseBtn.addEventListener('click', closeModal);
modalCancelBtn.addEventListener('click', closeModal);
modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

modalSaveBtn.addEventListener('click', async () => {
    const ordInput = parseInt(modalOrdine.value, 10);
    const risk = {
        luogo:   modalLuogo.value.trim(),
        rischio: modalRischio.value.trim(),
        azione:  modalAzione.value.trim(),
        entro:   modalEntro.value.trim(),
        key:     modalRischio.value.trim(),
        ordine:  isNaN(ordInput) ? 999999 : ordInput,
        image:   currentModalImage
    };

    if (isPermanentDbAdd) {
        // Salvataggio permanente nel file DATABASE.xlsx
        try {
                const res = await fetch(apiUrl('/api/add_database_risk'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(risk)
            });
            const data = await res.json();
            if (data.success) {
                showToast(data.message || 'Criticità salvata nel database Excel!', 'success');
                await loadDatabaseRisks();
                closeModal();
            } else {
                showToast('Errore salvataggio Excel: ' + (data.error || ''), 'error');
            }
        } catch (err) {
            showToast('Errore durante il salvataggio nel database Excel', 'error');
        }
    } else {
        if (editingIndex === null) {
            currentRisks.push(risk);
        } else {
            currentRisks[editingIndex] = risk;
        }
        renderRisks();
        closeModal();
        showToast(editingIndex === null ? 'Criticità personalizzata aggiunta ed ordinata.' : 'Criticità aggiornata.', 'success');
    }
});

// ─── Full Database Browser Logic ─────────────────────────────────────────────

async function loadDatabaseRisks() {
    try {
        const res = await fetch(apiUrl('/api/database_risks'));
        const data = await res.json();
        if (data.success) {
            allDbRisks = data.risks || [];
            dbTotalCount.textContent = allDbRisks.length;
            renderDatabaseTable(allDbRisks);
        }
    } catch (e) {
        console.error('Errore caricamento database rischi:', e);
    }
}

function renderDatabaseTable(risksList) {
    dbTableBody.innerHTML = '';
    if (!risksList || risksList.length === 0) {
        dbTableBody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 2rem; color: #000000;">Nessuna voce trovata nel database.</td></tr>';
        return;
    }

    risksList.forEach(r => {
        const tr = document.createElement('tr');
        const ordVal = (r.ordine !== undefined && r.ordine !== 999999) ? r.ordine : '—';
        const imgCell = r.image 
            ? `<img src="${r.image}" width="110" height="80" style="width:110px; height:80px; max-width:110px; max-height:80px; object-fit:cover; display:block; margin:0 auto; border:1px solid #ccc;" class="db-thumb" alt="Foto">` 
            : `<span style="color:#777777; font-size:0.75rem;">N/D</span>`;

        tr.innerHTML = `
            <td><span class="order-badge" style="background:#004B9B; color:#ffffff !important;">${ordVal}</span></td>
            <td><strong style="color:#000000 !important;">${escHtml(r.luogo)}</strong></td>
            <td style="color:#000000 !important;">${escHtml(r.rischio)}</td>
            <td style="font-size: 0.85rem; color:#000000 !important;">${escHtml(r.azione)}</td>
            <td style="text-align: center;">${imgCell}</td>
            <td><span class="entro-badge">${escHtml(r.entro)}</span></td>
            <td style="text-align: center; white-space: nowrap;">
                <button class="btn primary-btn btn-sm add-db-btn" title="Aggiungi alla tabella lavoro DVR">
                    <i class="fa-solid fa-plus"></i>
                </button>
                <button class="btn secondary-btn btn-sm copy-word-btn" title="Copia riga per Word" style="margin-left: 4px;">
                    <i class="fa-solid fa-copy"></i> Copia
                </button>
            </td>`;
        
        tr.querySelector('.add-db-btn').addEventListener('click', () => addRiskFromDb(r));
        tr.querySelector('.copy-word-btn').addEventListener('click', () => copyRiskToWord(r));
        dbTableBody.appendChild(tr);
    });
}

function copyRiskToWord(r) {
    const imgHtml = r.image 
        ? `<img src="${r.image}" width="120" style="max-width:120px; max-height:95px; width:auto; height:auto; display:block; margin:0 auto;" />` 
        : '';
        
    const htmlTable = `
        <table border="1" style="border-collapse:collapse; width:100%; font-family:Arial, sans-serif; font-size:9.5pt; color:#000000; background-color:#ffffff; border:1.5pt solid #000000;">
            <tr style="background-color:#ffffff; color:#000000; vertical-align:top;" valign="top">
                <td valign="top" style="padding:6px; border:1pt solid #000000; color:#000000; background-color:#ffffff; vertical-align:top; width:20%;"><b>${escHtml(r.luogo)}</b></td>
                <td valign="top" style="padding:6px; border:1pt solid #000000; color:#000000; background-color:#ffffff; vertical-align:top; width:25%;">${escHtml(r.rischio)}</td>
                <td valign="top" style="padding:6px; border:1pt solid #000000; color:#000000; background-color:#ffffff; vertical-align:top; width:35%;">${escHtml(r.azione)}</td>
                <td valign="top" style="padding:6px; border:1pt solid #000000; color:#000000; background-color:#ffffff; vertical-align:top; width:120px; text-align:center;">${imgHtml}</td>
                <td valign="top" style="padding:6px; border:1pt solid #000000; color:#000000; background-color:#ffffff; vertical-align:top; width:10%;">${escHtml(r.entro)}</td>
            </tr>
        </table>`;

    const plainText = `${r.luogo}\t${r.rischio}\t${r.azione}\t${r.entro}`;

    try {
        const blobHtml = new Blob([htmlTable], { type: 'text/html' });
        const blobText = new Blob([plainText], { type: 'text/plain' });
        const data = [new ClipboardItem({ 'text/html': blobHtml, 'text/plain': blobText })];
        
        navigator.clipboard.write(data).then(() => {
            showToast('Riga copiata negli appunti! Incollala direttamente in Word (Ctrl+V).', 'success');
        }).catch(() => {
            fallbackCopyText(plainText);
        });
    } catch (e) {
        fallbackCopyText(plainText);
    }
}

function fallbackCopyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Testo copiato negli appunti!', 'success');
    });
}

function addRiskFromDb(dbRisk) {
    const newRisk = {
        luogo:   dbRisk.luogo,
        rischio: dbRisk.rischio,
        azione:  dbRisk.azione,
        entro:   dbRisk.entro,
        key:     dbRisk.key,
        ordine:  dbRisk.ordine,
        image:   dbRisk.image
    };
    currentRisks.push(newRisk);
    renderRisks();
    showToast(`Voce "${dbRisk.rischio.substring(0, 30)}..." aggiunta con foto!`, 'success');
}

dbSearchInput.addEventListener('input', () => {
    const q = dbSearchInput.value.toLowerCase().trim();
    if (!q) {
        renderDatabaseTable(allDbRisks);
        return;
    }
    const filtered = allDbRisks.filter(r => 
        (r.luogo && r.luogo.toLowerCase().includes(q)) ||
        (r.rischio && r.rischio.toLowerCase().includes(q)) ||
        (r.azione && r.azione.toLowerCase().includes(q)) ||
        (r.key && r.key.toLowerCase().includes(q))
    );
    renderDatabaseTable(filtered);
});

// ─── New Analysis ─────────────────────────────────────────────────────────────

if (btnNewAnalysis) {
    btnNewAnalysis.addEventListener('click', () => {
        goHome();
    });
}

// ─── Word Export ─────────────────────────────────────────────────────────────

btnExportWord.addEventListener('click', async () => {
    if (currentRisks.length === 0) {
        showToast('Nessuna criticità da esportare.', 'error');
        return;
    }
    try {
        sortRisksByOrder(currentRisks);

        const response = await fetch(apiUrl('/api/generate_docx'), {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ risks: currentRisks })
        });
        if (!response.ok) throw new Error('Errore nella generazione del documento.');
        const blob = await response.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = 'criticita_dvr_rilevate.docx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('File Word scaricato con successo! Immagini inserite nella colonna foto.', 'success');
    } catch (err) {
        showToast('Errore esportazione: ' + err.message, 'error');
    }
});

// ─── Toast Notifications ─────────────────────────────────────────────────────

function showToast(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="fa-solid fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'circle-exclamation' : 'circle-info'}"></i> ${msg}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('visible'), 50);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => document.body.removeChild(toast), 400);
    }, 3500);
}

function escHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
