// Multi-Agent Research Assistant - Group 16 Web Application Logic

let currentReportMarkdown = "";
let latestResult = null;

// Tab Switching
window.switchTab = function(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  const activeBtn = document.getElementById(`tab-btn-${tabId}`);
  const activeContent = document.getElementById(`tab-content-${tabId}`);
  if (activeBtn) activeBtn.classList.add('active');
  if (activeContent) activeContent.classList.add('active');

  if (tabId === 'audit') {
    window.fetchAuditLogs();
  }
};

// Set preset queries
window.setPreset = function(query) {
  const input = document.getElementById('research-query-input');
  if (input) {
    input.value = query;
    input.focus();
  }
};

// Run Workflow
window.runWorkflow = async function() {
  const queryInput = document.getElementById('research-query-input');
  const runBtn = document.getElementById('btn-run-workflow');
  const prodToggle = document.getElementById('production-mode-toggle');
  const question = queryInput.value.trim();

  if (!question) return;

  runBtn.disabled = true;
  runBtn.innerHTML = '<span>Executing Multi-Agent Run...</span>';
  document.getElementById('pipeline-status-text')?.remove();
  
  // Reset nodes
  resetAgentNodes();
  animateNode('node-coordinator', 'running', 'Sequencing...');

  try {
    const isProduction = prodToggle ? prodToggle.checked : true;
    
    // Simulate pipeline stage progression
    setTimeout(() => animateNode('node-query', 'running', 'Extracting queries...'), 200);
    setTimeout(() => animateNode('node-retrieval', 'running', 'Searching corpus...'), 400);
    setTimeout(() => animateNode('node-summary', 'running', 'Grouping themes...'), 600);
    setTimeout(() => animateNode('node-critic', 'running', 'Critic review gate...'), 800);
    setTimeout(() => animateNode('node-writer', 'running', 'Formatting brief...'), 1000);

    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, production_mode: isProduction })
    });

    const data = await res.json();
    latestResult = data;
    renderResults(data);
  } catch (err) {
    console.error(err);
    alert('Workflow execution error: ' + err.message);
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Execute Multi-Agent Run</span>
    `;
  }
};

// Simulate Chaos Failure Scenario
window.simulateScenario = async function(scenario) {
  resetAgentNodes();
  animateNode('node-coordinator', 'running', 'Simulating chaos...');

  try {
    const res = await fetch('/api/simulate-failure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario })
    });
    const data = await res.json();
    latestResult = data;
    renderResults(data);
    window.switchTab('trace');
  } catch (err) {
    alert('Simulation error: ' + err.message);
  }
};

// Render results
function renderResults(data) {
  // Update node statuses
  updateNodesFromTrace(data);

  // Meta chips
  document.getElementById('tag-run-id').innerText = `Run ID: ${data.run_id ? data.run_id.slice(0, 8) + '...' : 'N/A'}`;
  const statusTag = document.getElementById('tag-run-status');
  statusTag.innerText = `Status: ${data.status}`;
  if (data.status === 'success') {
    statusTag.className = 'tag-chip chip-success';
  } else {
    statusTag.className = 'tag-chip';
    statusTag.style.borderColor = 'rgba(244, 63, 94, 0.4)';
    statusTag.style.color = '#fda4af';
  }

  const evidenceCount = (data.evidence || []).length;
  document.getElementById('tag-evidence-count').innerText = `${evidenceCount} Sources Grounded`;

  // 1. Report
  currentReportMarkdown = data.report || '';
  const reportView = document.getElementById('report-rendered-view');
  if (data.report) {
    reportView.innerHTML = renderMarkdown(data.report);
  } else {
    reportView.innerHTML = `
      <div class="empty-state" style="padding: 2rem; text-align: center; color: #fca5a5;">
        <h3>Safe Stop Executed (${data.status})</h3>
        <p>No literature summary produced to prevent ungrounded assertions or hallucination.</p>
        <p style="font-size: 0.85rem; color: #94a3b8; margin-top: 0.5rem;">Check the Critic &amp; Fact-Check Audit tab for specific details.</p>
      </div>
    `;
  }

  // 2. Critic Audit Tab
  const verdictEl = document.getElementById('critic-verdict-text');
  const verdict = data.review ? data.review.verdict : 'N/A';
  verdictEl.innerText = verdict.toUpperCase();
  verdictEl.className = verdict === 'pass' ? 'verdict-status' : 'verdict-status fail';

  const claims = (data.analysis && data.analysis.claims) || [];
  const dropped = (data.analysis && data.analysis.dropped_claims) || [];
  document.getElementById('stat-claims-retained').innerText = claims.length;
  document.getElementById('stat-claims-dropped').innerText = dropped.length;

  // Claims Audit Table
  const tbody = document.getElementById('claims-audit-tbody');
  if (claims.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">No claims available.</td></tr>';
  } else {
    tbody.innerHTML = claims.map(c => `
      <tr>
        <td style="font-weight: 500; color: #f1f5f9;">${escapeHtml(c.claim)}</td>
        <td><span class="evidence-id">${escapeHtml(c.source_id)}</span></td>
        <td style="font-size: 0.82rem; color: #cbd5e1; font-style: italic;">
          "${escapeHtml(c.evidence_quote || '')}"
        </td>
        <td><span class="claim-status-badge badge-grounded">✓ Grounded</span></td>
      </tr>
    `).join('');
  }

  // Dropped Claims List
  const droppedContainer = document.getElementById('dropped-claims-list');
  if (dropped.length === 0) {
    droppedContainer.innerHTML = '<p style="color: #6ee7b7; font-size: 0.85rem;">✓ None. All retained claims passed source and quote verification checks.</p>';
  } else {
    droppedContainer.innerHTML = dropped.map(d => `
      <div style="padding: 0.4rem 0; border-bottom: 1px solid rgba(244, 63, 94, 0.2); font-size: 0.85rem; color: #fca5a5;">
        ❌ <strong>Dropped:</strong> ${escapeHtml(d)}
      </div>
    `).join('');
  }

  // 3. Evidence Cards
  const evidenceGrid = document.getElementById('evidence-cards-container');
  if (!data.evidence || data.evidence.length === 0) {
    evidenceGrid.innerHTML = '<p class="text-muted">No evidence passages retrieved.</p>';
  } else {
    evidenceGrid.innerHTML = data.evidence.map(e => `
      <div class="evidence-card">
        <div class="evidence-header">
          <span class="evidence-id">${escapeHtml(e.source_id)}</span>
          <span class="evidence-score">Relevance: ${e.relevance !== undefined ? e.relevance : 'Grounded'}</span>
        </div>
        <h4 class="evidence-title">${escapeHtml(e.title || 'Untitled Document')}</h4>
        <p class="evidence-authors">${escapeHtml(e.authors || '')} (${escapeHtml(e.year || '')}) • <em>${escapeHtml(e.venue || '')}</em></p>
        <div class="evidence-passage">
          "${escapeHtml(e.passage || '')}"
        </div>
        ${e.doi ? `<div style="font-size: 0.75rem;"><a href="https://doi.org/${encodeURIComponent(e.doi)}" target="_blank" rel="noopener" style="color: #818cf8; text-decoration: none;">DOI: ${escapeHtml(e.doi)} ↗</a></div>` : ''}
      </div>
    `).join('');
  }

  // 4. Unit-4 Trace Timeline
  const traceBox = document.getElementById('unit4-timeline-container');
  const traceEvents = data.unit4_trace || data.trace || [];
  if (traceEvents.length === 0) {
    traceBox.innerHTML = '<p class="text-muted">No trace events recorded.</p>';
  } else {
    traceBox.innerHTML = traceEvents.map(t => {
      const sender = t.sender_id || t.sender;
      const receiver = t.receiver_id || t.recipient;
      const perf = t.performative || t.message_type || 'INFORM';
      const status = t.status || 'SUCCESS';
      const attempt = (t.metadata && t.metadata.attempt) ? ` (attempt ${t.metadata.attempt})` : '';

      return `
        <div class="trace-item">
          <div class="trace-route">
            <span style="color: #fff; font-weight: 600;">${escapeHtml(sender)}</span>
            <span class="trace-arrow">➔</span>
            <span style="color: #94a3b8;">${escapeHtml(receiver)}</span>
            <span style="color: #64748b; font-size: 0.75rem;">${attempt}</span>
          </div>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <span class="trace-performative">${escapeHtml(perf)}</span>
            <span style="color: ${status === 'SUCCESS' || status === 'success' ? '#34d399' : '#f87171'}; font-size: 0.8rem; font-weight: 600;">
              ${escapeHtml(status)}
            </span>
          </div>
        </div>
      `;
    }).join('');
  }

  // Reassignments Alert
  if (data.reassignments && data.reassignments.length > 0) {
    const reassignedInfo = data.reassignments.map(r => 
      `• Primary [${r.original_agent}] failed; task successfully reassigned to [${r.reassigned_to}]`
    ).join('\n');
    alert(`Fault Tolerance Triggered:\n${reassignedInfo}`);
  }
}

function resetAgentNodes() {
  const nodes = ['coordinator', 'query', 'retrieval', 'summary', 'critic', 'writer'];
  nodes.forEach(n => {
    const el = document.getElementById(`node-${n}`);
    const pill = document.getElementById(`pill-${n}`);
    if (el) el.className = n === 'critic' ? 'agent-node critic-highlight' : 'agent-node';
    if (pill) {
      pill.className = 'node-status-pill';
      pill.innerText = 'Idle';
    }
  });
}

function animateNode(nodeId, stateClass, text) {
  const el = document.getElementById(nodeId);
  const pillId = nodeId.replace('node-', 'pill-');
  const pill = document.getElementById(pillId);
  if (el) el.classList.add(stateClass);
  if (pill) {
    pill.className = `node-status-pill ${stateClass}`;
    pill.innerText = text;
  }
}

function updateNodesFromTrace(data) {
  resetAgentNodes();
  const allSuccess = data.status === 'success';

  animateNode('node-coordinator', allSuccess ? 'done' : 'done', 'Finished');
  animateNode('node-query', 'done', 'Plan Generated');
  animateNode('node-retrieval', data.evidence && data.evidence.length ? 'done' : 'done', `${data.evidence ? data.evidence.length : 0} Passages`);
  animateNode('node-summary', 'done', 'Themes Structured');
  animateNode('node-critic', data.review && data.review.verdict === 'pass' ? 'done' : 'done', data.review ? data.review.verdict.toUpperCase() : 'PASS');
  animateNode('node-writer', data.report ? 'done' : 'done', data.report ? 'Report Validated' : 'Safe Stopped');
}

// Simple Markdown to HTML Formatter
function renderMarkdown(md) {
  if (!md) return '';
  let html = escapeHtml(md);

  // Headers
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');

  // Blockquotes
  html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

  // Bullet items
  html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

  // Source tag highlighting
  html = html.replace(/\[(paper_\d+)\]/g, '<span class="evidence-id">[$1]</span>');

  // Line breaks
  html = html.replace(/\n\n/g, '<br><br>');

  return html;
}

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Copy Report
window.copyReport = function() {
  if (!currentReportMarkdown) {
    alert('No report to copy.');
    return;
  }
  navigator.clipboard.writeText(currentReportMarkdown).then(() => {
    alert('Markdown report copied to clipboard!');
  });
};

// Download Report
window.downloadReport = function() {
  if (!currentReportMarkdown) {
    alert('No report to download.');
    return;
  }
  const blob = new Blob([currentReportMarkdown], { type: 'text/markdown;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `academic_research_brief_${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
};

// Fetch Audit Logs
window.fetchAuditLogs = async function() {
  const streamEl = document.getElementById('jsonl-log-stream');
  if (!streamEl) return;
  streamEl.innerText = 'Loading latest run logs from logs/run.jsonl...';
  try {
    const res = await fetch('/api/logs');
    const data = await res.json();
    if (data.logs && data.logs.length > 0) {
      streamEl.innerText = data.logs.map(r => JSON.stringify(r, null, 2)).join('\n\n');
    } else {
      streamEl.innerText = 'Log file empty or no runs recorded yet.';
    }
  } catch (err) {
    streamEl.innerText = 'Error loading logs: ' + err.message;
  }
};

// Fetch Corpus on load
async function loadCorpusData() {
  const container = document.getElementById('corpus-papers-container');
  if (!container) return;
  try {
    const res = await fetch('/api/corpus');
    const data = await res.json();
    if (data.papers && data.papers.length > 0) {
      container.innerHTML = data.papers.map(p => `
        <div class="corpus-card">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span class="evidence-id">${escapeHtml(p.source_id)}</span>
            <span style="font-size: 0.75rem; color: #94a3b8;">${escapeHtml(p.year || '')}</span>
          </div>
          <h5>${escapeHtml(p.title)}</h5>
          <p style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 0.5rem;">${escapeHtml(p.authors || '')} • <em>${escapeHtml(p.venue || '')}</em></p>
          <p style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.4;">"${escapeHtml((p.text || '').slice(0, 150))}..."</p>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to load corpus', err);
  }
}

// Initial bootstrap
document.addEventListener('DOMContentLoaded', () => {
  loadCorpusData();
  window.fetchAuditLogs();
});
