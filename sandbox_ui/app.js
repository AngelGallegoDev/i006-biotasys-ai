
let sbClient = null;

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');

    document.querySelectorAll('.side-nav button').forEach(b => b.classList.remove('active'));
    if (pageId === 'page1') document.getElementById('nav-btn-1').classList.add('active');
    if (pageId === 'page2') document.getElementById('nav-btn-2').classList.add('active');
}

function addLog(msg, type = 'info') {
    const term = document.getElementById('terminal');
    const span = document.createElement('span');
    span.className = `log-${type}`;
    span.innerText = `> [${new Date().toLocaleTimeString()}] ${msg}`;
    term.appendChild(span);
    term.scrollTop = term.scrollHeight;
}

function handleFileSelect() {
    const file = document.getElementById('report_file').files[0];
    if (file) {
        document.getElementById('file-label').innerText = file.name;
        document.getElementById('file-label').style.color = '#3b82f6';
        addLog(`Archivo listo: ${file.name}`, 'accent');
    }
}

async function executePipeline() {
    const btn = document.getElementById('main-action-btn');
    const file = document.getElementById('report_file').files[0];

    if (!file) return addLog('ERROR: Selecciona un archivo PDF o Imagen.', 'error');

    btn.disabled = true;
    btn.innerText = 'PROCESANDO...';

    try {
        // 1. Storage Upload (Automated)
        addLog('Subiendo archivo automáticamente a Supabase...', 'info');
        if (!sbClient) sbClient = supabase.createClient(CONFIG.SB_URL, CONFIG.SB_KEY);

        const fileExt = file.name.split('.').pop();
        const path = `sandbox_${Date.now()}.${fileExt}`;

        const { error: upErr } = await sbClient.storage.from(CONFIG.SB_BUCKET).upload(path, file);
        if (upErr) throw new Error(`Storage error: ${upErr.message}`);

        const { data: { publicUrl } } = sbClient.storage.from(CONFIG.SB_BUCKET).getPublicUrl(path);
        addLog('Archivo en Storage OK.', 'success');

        // 2. Engine POST (Automated)
        addLog('Enviando datos de Backend A al motor...', 'accent');
        const payload = {
            file_url: publicUrl,
            documento_id: document.getElementById('documento_id').value,
            empresa_id: document.getElementById('empresa_id').value,
            doctor_id: document.getElementById('doctor_id').value,
            fecha_envio: new Date().toISOString()
        };

        const response = await fetch(`${CONFIG.API_BASE}/process-report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': CONFIG.ENGINE_API_KEY
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(`Engine error (${response.status}): ${JSON.stringify(errorPayload)}`);
        }

        const result = await response.json();
        addLog('¡Análisis Brillantemente completado!', 'success');
        addLog(`ID de Reporte: ${result.report_id}`, 'info');

        renderReport(result.data);
        setTimeout(() => showPage('page2'), 1000);

    } catch (e) {
        addLog(`FALLO: ${e.message}`, 'error');
        console.error("Pipeline failure:", e);
    } finally {
        btn.disabled = false;
        btn.innerText = 'Subir y Procesar Informe';
    }
}

async function fetchHistory() {
    const reportId = document.getElementById('search-report-id').value.trim();
    if (!reportId) return addLog('Ingresa un Report ID para buscar.', 'error');

    addLog(`Buscando reporte: ${reportId}...`, 'info');

    try {
        const response = await fetch(`${CONFIG.API_BASE}/report/${reportId}`, {
            method: 'GET',
            headers: {
                'X-API-KEY': CONFIG.ENGINE_API_KEY
            }
        });

        if (!response.ok) {
            throw new Error(`Reporte no encontrado (${response.status})`);
        }

        const result = await response.json();
        addLog('Reporte recuperado con éxito.', 'success');

        // The API returns the raw record, we need result.report_data which has the MicrobiotaReport
        renderReport(result.report_data);
        showPage('page2');

    } catch (e) {
        addLog(`ERROR: ${e.message}`, 'error');
    }
}

function renderReport(report) {
    document.getElementById('no-data').classList.add('hidden');
    document.getElementById('report-content').classList.remove('hidden');

    // 1. Header Interpretation & Metadata
    const diag = report.interpretation?.diversity_diagnosis;
    const metadata = report.metadata || {};

    document.getElementById('res-summary').innerHTML = `
        <span class="badge ${diag?.interpretation === 'High' || diag?.interpretation === 'Optimal' ? 'ok' : 'warn'}">${diag?.interpretation}</span>
        ${report.interpretation?.summary || 'Sin resumen'}
    `;

    // Render Source Metadata if available (from the processing result or record)
    const metaContainer = document.getElementById('report-metadata');
    if (metaContainer) {
        metaContainer.innerHTML = `
            <div class="meta-item"><i data-lucide="building"></i> <span>Empresa: ${document.getElementById('empresa_id').value}</span></div>
            <div class="meta-item"><i data-lucide="user-check"></i> <span>Doctor: ${document.getElementById('doctor_id').value}</span></div>
            <div class="meta-item"><i data-lucide="file-text"></i> <span>Doc ID: ${document.getElementById('documento_id').value}</span></div>
        `;
    }

    // 2. Diversity Metrics
    document.getElementById('res-shannon').innerText = report.diversity.shannon_index.toFixed(2);
    document.getElementById('res-simpson').innerText = report.diversity.simpson_index.toFixed(2);

    // 3. Enterotype Badge
    const ent = report.interpretation?.enterotype_analysis;
    const fbContainer = document.querySelector('.fb-ring');
    // Clear previous FB content specifically if needed, or append? Let's replace the Logic:
    // We reuse the FB Card slot for Enterotype + F/B
    fbContainer.innerHTML = `
        <div class="fb-number">${report.taxonomy.firmicutes_bacteroidetes_ratio.toFixed(2)}</div>
        <span class="v-label">Ratio Firmicutes/Bacteroidetes</span>
        <div class="enterotype-box">
             <i data-lucide="layers"></i> Enterotipo: <strong>${ent?.enterotype || 'N/A'}</strong>
             <small>${ent?.description || ''}</small>
        </div>
    `;

    // 4. Alerts (Clinical Observations)
    const alertsBox = document.getElementById('res-alerts');
    alertsBox.innerHTML = '';
    const allFindings = [
        ...(report.interpretation?.taxonomic_balance || []),
        ...(report.interpretation?.opportunistic_risk || [])
    ];

    if (allFindings.length === 0) {
        alertsBox.innerHTML = '<div class="alert-row ok">✅ No se detectaron riesgos clínicos evidentes.</div>';
    } else {
        allFindings.forEach(f => {
            const lowSev = f.severity?.toLowerCase() || 'info';
            const div = document.createElement('div');
            div.className = `alert-row ${lowSev}`;
            div.innerHTML = `<strong>${f.title}</strong><p>${f.description}</p>`;
            alertsBox.appendChild(div);
        });
    }

    // 5. Metabolic Grid (Structured)
    const metBox = document.getElementById('res-metabolic');
    metBox.innerHTML = '';
    const functions = report.interpretation?.metabolic_potential || [];

    functions.forEach(m => {
        const statusColor = m.status === 'High' || m.status === 'Enhanced' || m.status === 'Normal' ? 'ok' : 'warn';
        const div = document.createElement('div');
        div.className = 'met-box';
        div.innerHTML = `
            <div class="met-header">
                <span class="status-pill ${statusColor}">${m.status}</span>
                <h4>${m.pathway}</h4>
            </div>
            <p class="met-imp">${m.implication}</p>
            <div class="met-bac"><small>Bacteria: ${m.associated_bacteria?.join(', ') || 'N/A'}</small></div>
        `;
        metBox.appendChild(div);
    });

    // 6. NEW: Gut Health Score
    const scoreBox = document.getElementById('res-score');
    if (scoreBox && report.interpretation?.gut_health_score) {
        const s = report.interpretation.gut_health_score;
        scoreBox.innerHTML = `
            <div class="score-circle">
                <span class="score-val">${s.value}</span>
                <span class="score-max">/100</span>
            </div>
            <div class="score-details">
                <h4>${s.label}</h4>
                <p>${s.breakdown}</p>
            </div>
        `;
    }

    // 7. NEW: Dietary Recommendations
    const dietBox = document.getElementById('res-diet');
    if (dietBox) {
        dietBox.innerHTML = '';
        const recs = report.interpretation?.dietary_recommendations || [];
        if (recs.length === 0) dietBox.innerHTML = '<p class="text-muted">No hay recomendaciones específicas.</p>';

        recs.forEach(r => {
            const actionClass = r.action === 'Evitar' ? 'avoid' : (r.action === 'Aumentar' ? 'increase' : 'reduce');
            const icon = r.action === 'Evitar' ? 'x-circle' : (r.action === 'Aumentar' ? 'arrow-up-circle' : 'arrow-down-circle');

            const div = document.createElement('div');
            div.className = `diet-card ${actionClass}`;
            div.innerHTML = `
                <div class="diet-icon"><i data-lucide="${icon}"></i></div>
                <div class="diet-content">
                    <span class="diet-action">${r.action}</span>
                    <strong>${r.item}</strong>
                    <small>${r.reason}</small>
                </div>
            `;
            dietBox.appendChild(div);
        });
    }

    // 8. NEW: Supplements
    const suppBox = document.getElementById('res-supplements');
    if (suppBox) {
        suppBox.innerHTML = '';
        const supps = report.interpretation?.supplement_suggestions || [];
        if (supps.length === 0) suppBox.innerHTML = '<p class="text-muted">No se requieren suplementos.</p>';

        supps.forEach(s => {
            const div = document.createElement('div');
            div.className = 'supp-card';
            div.innerHTML = `
                <div class="supp-header">
                    <span class="badge ok">${s.type}</span>
                    <strong>${s.name}</strong>
                </div>
                <p>${s.reason}</p>
            `;
            suppBox.appendChild(div);
        });
    }

    lucide.createIcons();
}
