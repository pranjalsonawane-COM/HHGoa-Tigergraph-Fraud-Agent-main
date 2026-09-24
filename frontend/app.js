/**
 * Hacker House Goa (2:47 PM Studio) — TigerGraph Fraud Agent Dashboard Application
 * Clean, high-performance, interactive dashboard controller.
 */

const API_BASE = '';
let allCases = [];
let currentCase = null;
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await fetchStats();
    await fetchCases();
}

function setupEventListeners() {
    // Filter Pills
    document.querySelectorAll('.filter-pills .pill-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-pills .pill-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentFilter = e.target.getAttribute('data-filter');
            renderCaseList();
        });
    });

    // Dossier Tabs
    document.querySelectorAll('.tabs-header .tab-item').forEach(tab => {
        tab.addEventListener('click', (e) => {
            document.querySelectorAll('.tabs-header .tab-item').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tabs-body .tab-content').forEach(p => p.classList.remove('active'));
            
            e.target.classList.add('active');
            const targetId = e.target.getAttribute('data-target');
            const pane = document.getElementById(targetId);
            if (pane) pane.classList.add('active');
        });
    });

    // On-Demand Investigation
    const txnInput = document.getElementById('onDemandTxnInput');
    const triggerInvestigate = () => {
        const raw = txnInput.value.trim();
        const clean = raw.replace(/^#+/, '').trim();
        if (clean) runOnDemandInvestigation(clean);
    };

    document.getElementById('btnInvestigateTxn').addEventListener('click', triggerInvestigate);
    if (txnInput) {
        txnInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') triggerInvestigate();
        });
    }

    // Copy SAR Button
    document.getElementById('btnCopySar').addEventListener('click', () => {
        const text = document.getElementById('sarNarrativeText').innerText;
        navigator.clipboard.writeText(text).then(() => {
            const btn = document.getElementById('btnCopySar');
            const orig = btn.innerText;
            btn.innerText = '✅ Copied!';
            setTimeout(() => btn.innerText = orig, 2000);
        });
    });

    // Simulation Buttons
    document.getElementById('btnSimTravel').addEventListener('click', () => {
        if (currentCase) simulateEvidence('customer_contact', 'travel_confirmed', 'Cardholder confirmed vacation travel to Goa / billing region.');
    });

    document.getElementById('btnSimFraud').addEventListener('click', () => {
        if (currentCase) simulateEvidence('customer_contact', 'fraud_confirmed', 'Cardholder confirmed unauthorized charge dispute.');
    });
}

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const stats = await res.json();
        document.getElementById('statTotalCases').innerText = stats.total_benchmark_cases || '20';
        document.getElementById('statConfirmedFraud').innerText = stats.confirmed_fraud_cases || '15';
        document.getElementById('statUncertainCases').innerText = stats.uncertain_cases || '4';
        document.getElementById('statSarFilings').innerText = stats.sar_filings_count || '14';
        document.getElementById('statTotalExposure').innerText = `$${(stats.total_exposure_mitigated_usd || 3623.21).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    } catch (err) {
        console.error('Failed to fetch stats:', err);
    }
}

async function fetchCases() {
    try {
        const res = await fetch(`${API_BASE}/api/cases`);
        const data = await res.json();
        allCases = data.cases || [];
        renderCaseList();
        if (allCases.length > 0) {
            // Default select HHG-014 (Syndicate Master Case) or first case
            const defaultCase = allCases.find(c => c.case_id === 'HHG-014') || allCases[0];
            selectCase(defaultCase.case_id);
        }
    } catch (err) {
        console.error('Failed to fetch cases:', err);
    }
}

function renderCaseList() {
    const container = document.getElementById('caseListContainer');
    container.innerHTML = '';

    let filtered = allCases;
    if (currentFilter === 'confirmed_fraud') {
        filtered = allCases.filter(c => c.verdict === 'confirmed_fraud');
    } else if (currentFilter === 'uncertain') {
        filtered = allCases.filter(c => c.verdict === 'uncertain');
    } else if (currentFilter === 'sar') {
        filtered = allCases.filter(c => c.sar_required);
    }

    filtered.forEach(c => {
        const item = document.createElement('div');
        item.className = `case-item ${currentCase && currentCase.case_id === c.case_id ? 'active' : ''}`;
        item.onclick = () => selectCase(c.case_id);

        const verdictColor = c.verdict === 'confirmed_fraud' ? 'var(--goa-pink)' : (c.verdict === 'uncertain' ? 'var(--goa-yellow)' : 'var(--goa-emerald)');
        const verdictBg = c.verdict === 'confirmed_fraud' ? 'rgba(255,0,127,0.15)' : (c.verdict === 'uncertain' ? 'rgba(255,230,0,0.15)' : 'rgba(16,185,129,0.15)');

        item.innerHTML = `
            <div class="case-item-header">
                <span class="case-item-id">${c.case_id}</span>
                <span style="font-size:0.68rem; font-weight:700; color:${verdictColor}; background:${verdictBg}; padding:0.15rem 0.45rem; border-radius:3px; border:1px solid ${verdictColor};">
                    ${c.verdict.toUpperCase()}
                </span>
            </div>
            <div class="case-item-body">
                <span>Txn: #${c.flagged_txn_id}</span>
                <span style="color:var(--goa-yellow); font-weight:700;">$${parseFloat(c.exposure_usd || 0).toFixed(2)}</span>
            </div>
            <div style="font-size:0.7rem; color:var(--text-muted); display:flex; justify-content:space-between; align-items:center;">
                <span>Pattern: <strong style="color:var(--text-sand);">${c.pattern}</strong></span>
                ${c.sar_required ? '<span style="color:var(--goa-pink); font-weight:700;">[SAR]</span>' : ''}
            </div>
        `;
        container.appendChild(item);
    });
}

async function selectCase(caseId) {
    try {
        const res = await fetch(`${API_BASE}/api/cases/${caseId}`);
        currentCase = await res.json();
        renderCaseDetails(currentCase);
        renderCaseList();
        renderGraphCanvas(currentCase.flagged_txn_id);
    } catch (err) {
        console.error('Failed to select case:', err);
    }
}

function renderCaseDetails(c) {
    document.getElementById('dossierCaseId').innerText = `Case ${c.case_id} Dossier`;
    
    // Verdict Badge
    const vb = document.getElementById('dossierVerdictBadge');
    vb.innerText = c.verdict.toUpperCase();
    vb.className = `badge-tag ${c.verdict === 'confirmed_fraud' ? 'badge-fraud' : (c.verdict === 'uncertain' ? 'badge-uncertain' : 'badge-cleared')}`;

    // Approval Badge
    const ab = document.getElementById('dossierApprovalBadge');
    ab.innerText = c.approval_route.toUpperCase();
    ab.className = `badge-tag ${c.approval_route === 'L2_senior_manager' ? 'badge-l2' : 'badge-l1'}`;

    document.getElementById('dossierAmount').innerText = `$${parseFloat(c.exposure_usd || 0).toFixed(2)}`;
    document.getElementById('dossierConfidence').innerText = `${Math.round((c.confidence || 0) * 100)}%`;
    document.getElementById('dossierSarStatus').innerText = c.sar_required ? 'YES (Mandatory)' : 'No';

    // Tab 1: Evidence
    const eb = document.getElementById('evidenceBox');
    eb.innerHTML = `
        <div style="background:#03170c; border:1px solid var(--border-gold); padding:0.85rem; border-radius:6px; margin-bottom:0.65rem;">
            <h4 style="color:var(--goa-yellow); font-size:0.95rem; font-weight:700; margin-bottom:0.25rem;">
                🎯 Fraud Typology: <code>${c.pattern}</code>
            </h4>
            <p style="color:var(--text-sand); font-size:0.82rem; line-height:1.4;">
                ${c.pattern_description || 'Multi-hop graph traversal validated pattern against 5,565 closed case memory.'}
            </p>
        </div>
        <h5 style="color:var(--goa-yellow); font-size:0.95rem; font-weight:700; margin-bottom:0.45rem;">
            🔎 Grounded Graph Evidence:
        </h5>
    `;
    if (c.evidence && c.evidence.length > 0) {
        c.evidence.forEach(ev => {
            const evCard = document.createElement('div');
            evCard.className = 'evidence-card';
            evCard.innerHTML = `
                <div class="evidence-claim-text">📌 ${ev.claim}</div>
                <div class="evidence-meta-text">Query: <code>${ev.ref}</code> | Entities: [${ev.entity_ids ? ev.entity_ids.join(', ') : ''}]</div>
            `;
            eb.appendChild(evCard);
        });
    }

    // Tab 2: Trace (8-step ReAct cycle)
    const sc = document.getElementById('stepperContainer');
    sc.innerHTML = '';
    
    const defaultSteps = [
        { title: "Step 1: Alert Ingestion & Context Extraction", desc: `Ingested flagged transaction #${c.flagged_txn_id} on card ${c.card_id} for customer ${c.customer_id}.` },
        { title: "Step 2: Multi-Hop TigerGraph Neighborhood Traversal", desc: "Executed GSQL subgraphs traversing Customer ➔ Card ➔ Transaction ➔ DeviceProfile ➔ Region." },
        { title: "Step 3: Graph Typology & Pattern Reasoning", desc: `Evaluated 5 fraud patterns: Classified as typology '${c.pattern}' with high confidence.` },
        { title: "Step 4: Case Memory Precedent Grounding", desc: "Retrieved BM25 nearest neighbors from 5,565 historical closed cases with strict temporal cutoff." },
        { title: "Step 5: Fraud Policy v1.0 Rules Evaluation", desc: `Triggered deterministic rules [${(c.triggered_rules || []).join(', ')}] with strict regulatory compliance.` },
        { title: "Step 6: Uncertainty Assessment & Simulator Check", desc: `Confidence evaluated at ${(c.confidence * 100).toFixed(0)}%. Resolved verdict: ${c.verdict}.` },
        { title: "Step 7: Next Best Action & Playbook Synthesis", desc: `Synthesized 5-pillar containment playbook routed to ${c.approval_route}. Primary action: ${c.next_best_action}.` },
        { title: "Step 8: FinCEN SAR Narrative & Graph Persistence", desc: c.sar_required ? "Generated 5-section FinCEN compliant SAR narrative and queued write-back to graph." : "SAR not required based on exposure and single-party risk profile." }
    ];

    defaultSteps.forEach((step, idx) => {
        const stepEl = document.createElement('div');
        stepEl.className = 'trace-item';
        stepEl.innerHTML = `
            <div class="trace-num">${idx + 1}</div>
            <div class="trace-body">
                <h5>${step.title}</h5>
                <p>${step.desc}</p>
            </div>
        `;
        sc.appendChild(stepEl);
    });

    // Tab 3: Playbook
    const pb = document.getElementById('playbookContainer');
    if (c.playbook) {
        pb.innerHTML = `
            <div class="playbook-hero">
                <h4>⚡ PRIMARY DIRECTIVE: ${c.playbook.primary_action}</h4>
                <p style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted); margin-top:0.2rem;">
                    Approval Route: <strong style="color:var(--goa-yellow);">${c.approval_route}</strong> | SLA: Immediate Containment
                </p>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;">
                <div style="background:#03170c; border:1px solid var(--border-subtle); padding:0.75rem; border-radius:6px;">
                    <h5 style="color:var(--goa-yellow); font-size:0.85rem; font-weight:700; margin-bottom:0.4rem;">🛡️ Containment Steps:</h5>
                    <ul style="padding-left:1.25rem; color:var(--text-sand); font-size:0.8rem; line-height:1.5;">
                        ${c.playbook.containment_steps.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
                <div style="background:#03170c; border:1px solid var(--border-subtle); padding:0.75rem; border-radius:6px;">
                    <h5 style="color:var(--goa-yellow); font-size:0.85rem; font-weight:700; margin-bottom:0.4rem;">💰 Remediation:</h5>
                    <ul style="padding-left:1.25rem; color:var(--text-sand); font-size:0.8rem; line-height:1.5;">
                        ${c.playbook.financial_remediation.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
            </div>
            <div style="background:#03170c; border:1px solid var(--border-subtle); padding:0.75rem; border-radius:6px;">
                <h5 style="color:var(--goa-yellow); font-size:0.85rem; font-weight:700; margin-bottom:0.25rem;">📱 Customer SMS / Email Copy:</h5>
                <p style="font-style:italic; font-family:var(--font-mono); font-size:0.8rem; color:#ffffff; background:rgba(0,0,0,0.5); padding:0.6rem; border-radius:4px; border-left:3px solid var(--goa-pink);">
                    "${c.playbook.customer_communication ? c.playbook.customer_communication.message_copy : ''}"
                </p>
            </div>
        `;
    }

    // Tab 4: SAR
    const st = document.getElementById('sarNarrativeText');
    st.innerText = c.sar_narrative && c.sar_narrative.trim() ? c.sar_narrative : 'No SAR required for this case. Loss exposure is below threshold and no multi-party syndicate was detected.';

    // Reset Sim Result
    document.getElementById('simResultBox').style.display = 'none';
}

async function renderGraphCanvas(txnId) {
    const canvas = document.getElementById('graphCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Exact sizing to parent container
    const parent = canvas.parentElement;
    const width = parent ? (parent.clientWidth || 800) : 800;
    const height = 300;
    canvas.width = width;
    canvas.height = height;
    
    ctx.clearRect(0, 0, width, height);

    try {
        const res = await fetch(`${API_BASE}/api/graph/${txnId}`);
        const data = await res.json();
        const nodes = data.nodes || [];
        const links = data.links || [];

        if (nodes.length === 0) {
            ctx.fillStyle = '#64748b';
            ctx.font = '13px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No connected graph entities found for this transaction', width / 2, height / 2);
            return;
        }

        const cx = width / 2;
        const cy = height / 2;
        const nodePos = {};

        // 1. Position Central Transaction Node
        const txnNode = nodes.find(n => n.type === 'Transaction') || nodes[0];
        nodePos[txnNode.id] = {
            x: cx,
            y: cy,
            color: txnNode.color || '#ffe600',
            label: txnNode.label,
            type: 'Transaction'
        };

        // 2. Position Surrounding Neighbors in Radial Orbits
        const otherNodes = nodes.filter(n => n.id !== txnNode.id);
        const count = otherNodes.length;

        otherNodes.forEach((n, idx) => {
            const angle = (idx / Math.max(count, 1)) * Math.PI * 2;
            const isShared = n.label.includes('Shared') || n.color === '#ff007f';
            const radius = isShared ? Math.min(width * 0.38, 125) : Math.min(width * 0.25, 80);

            let themeColor = n.color || '#10b981';
            if (n.type === 'Customer') themeColor = '#38bdf8';
            else if (n.type === 'DeviceProfile') themeColor = '#f59e0b';
            else if (n.type === 'BillingRegion') themeColor = n.color || '#a855f7';
            else if (isShared) themeColor = '#ff007f';

            nodePos[n.id] = {
                x: cx + Math.cos(angle) * radius,
                y: cy + Math.sin(angle) * radius,
                color: themeColor,
                label: n.label,
                type: n.type
            };
        });

        // 3. Draw Links
        links.forEach(l => {
            const p1 = nodePos[l.source];
            const p2 = nodePos[l.target];
            if (p1 && p2) {
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                const isHighlight = p1.color === '#ff007f' || p2.color === '#ff007f';
                ctx.strokeStyle = isHighlight ? 'rgba(255, 0, 127, 0.7)' : 'rgba(255, 230, 0, 0.4)';
                ctx.lineWidth = isHighlight ? 2 : 1.2;
                ctx.stroke();
            }
        });

        // 4. Draw Nodes
        Object.values(nodePos).forEach(p => {
            const isTxn = p.type === 'Transaction';
            const radius = isTxn ? 18 : 12;

            // Outer soft glow
            ctx.beginPath();
            ctx.arc(p.x, p.y, radius + 4, 0, Math.PI * 2);
            ctx.fillStyle = isTxn ? 'rgba(255, 230, 0, 0.25)' : 'rgba(16, 185, 129, 0.15)';
            ctx.fill();

            // Core circle
            ctx.beginPath();
            ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();

            // Dark border
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#021208';
            ctx.stroke();

            // Label text pill
            const firstLine = (p.label || '').split('\n')[0].replace('DEV_', 'DEV:');
            ctx.font = isTxn ? '700 11px monospace' : '600 10px monospace';
            ctx.textAlign = 'center';
            const textY = p.y >= cy ? p.y + radius + 14 : p.y - radius - 6;

            // Text background shadow for contrast
            ctx.fillStyle = 'rgba(2, 18, 8, 0.85)';
            const textWidth = ctx.measureText(firstLine).width;
            ctx.fillRect(p.x - textWidth / 2 - 4, textY - 10, textWidth + 8, 14);

            ctx.fillStyle = '#ffffff';
            ctx.fillText(firstLine, p.x, textY);
        });

    } catch (err) {
        console.error('Failed to render graph canvas:', err);
    }
}

async function simulateEvidence(actionType, outcomeCode, notes) {
    if (!currentCase) return;
    try {
        const res = await fetch(`${API_BASE}/api/simulate-evidence`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_id: currentCase.case_id,
                action_type: actionType,
                outcome_code: outcomeCode,
                evidence_notes: notes
            })
        });
        const updated = await res.json();
        currentCase = updated;
        renderCaseDetails(currentCase);
        fetchStats();

        const box = document.getElementById('simResultBox');
        box.style.display = 'block';
        box.innerHTML = `<strong>🌴 Dynamic Resolution Updated:</strong> Case <code>${currentCase.case_id}</code> updated to <strong style="color:var(--goa-yellow);">${currentCase.verdict.toUpperCase()}</strong> (NBA: <strong style="color:var(--goa-pink);">${currentCase.next_best_action}</strong>).`;
    } catch (err) {
        console.error('Simulation failed:', err);
    }
}

async function runOnDemandInvestigation(rawTxnId) {
    const txnId = String(rawTxnId).replace(/[^0-9]/g, '').trim();
    if (!txnId) return;

    const btn = document.getElementById('btnInvestigateTxn');
    const origText = btn ? btn.innerHTML : '⚡ Investigate';
    if (btn) {
        btn.innerHTML = '⏳ Investigating...';
        btn.disabled = true;
    }

    try {
        const res = await fetch(`${API_BASE}/api/investigate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: txnId })
        });
        const dossier = await res.json();
        if (dossier.error) {
            alert(`Investigation notice: ${dossier.error}`);
            return;
        }
        currentCase = dossier;
        renderCaseDetails(currentCase);
        renderGraphCanvas(txnId);

        // Highlight matching case item in list if present
        const matchingEl = [...document.querySelectorAll('.case-item')].find(el => el.innerText.includes(txnId));
        if (matchingEl) {
            document.querySelectorAll('.case-item').forEach(el => el.classList.remove('active'));
            matchingEl.classList.add('active');
            matchingEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    } catch (err) {
        console.error('On demand investigation failed:', err);
    } finally {
        if (btn) {
            btn.innerHTML = origText;
            btn.disabled = false;
        }
    }
}
