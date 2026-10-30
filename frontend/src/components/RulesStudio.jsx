import React, { useState, useEffect } from 'react';
import { Sliders, Sparkles, CheckCircle2, ShieldCheck, FileText, ArrowRight, Check } from 'lucide-react';

export default function RulesStudio({ rules, onApproveRule }) {
  const [clauses, setClauses] = useState([]);
  const [selectedClauseId, setSelectedClauseId] = useState('APH-2026-CORR-02DEC');
  const [compiling, setCompiling] = useState(false);
  const [compiledDraft, setCompiledDraft] = useState(null);
  const [bilingualMemo, setBilingualMemo] = useState(null);

  useEffect(() => {
    fetch('/api/rules/clauses')
      .then(r => r.json())
      .then(data => setClauses(data))
      .catch(err => console.error(err));
  }, []);

  const handleCompileClause = () => {
    setCompiling(true);
    fetch('/api/rules/compile-clause', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clause_id: selectedClauseId })
    })
      .then(r => r.json())
      .then(data => {
        setCompiledDraft(data);
        setCompiling(false);
      })
      .catch(err => {
        console.error(err);
        setCompiling(false);
      });
  };

  const handleDraftLetterDemo = () => {
    fetch('/api/rules/draft-letter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        application_number: '1-46273286079',
        institution_name: 'Aryabhata Institute of Technology',
        stage: 'INITIAL_SCRUTINY',
        deficiency_reason: 'Building plan carpet area deficit of 450 sqm below APH Table 2.1 standard'
      })
    })
      .then(r => r.json())
      .then(data => setBilingualMemo(data));
  };

  return (
    <div className="rules-studio-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Rules Studio (Rules as Code &amp; SLM Policy Compiler)</h2>
          <p className="view-desc">
            Turns the Approval Process Handbook into executable, versioned, human-approved rules. SLM proposes drafts from corrigendums; deterministic engine enforcers require human gate.
          </p>
        </div>
      </div>

      <div className="dashboard-grid-2">
        {/* Left: SLM Policy Compiler Demonstration */}
        <div className="panel-card">
          <div className="panel-header">
            <h3 className="panel-title">Small Language Model (SLM) Policy Compiler</h3>
            <span className="badge-highlight">On-Prem Quantized 4-Bit</span>
          </div>

          <div className="form-group">
            <label className="form-label">Select Handbook Corrigendum Provision:</label>
            <select 
              className="form-select"
              value={selectedClauseId} 
              onChange={(e) => setSelectedClauseId(e.target.value)}
            >
              {clauses.map(c => (
                <option key={c.clause_id} value={c.clause_id}>
                  {c.title}
                </option>
              ))}
            </select>
          </div>

          <div className="clause-source-text">
            {clauses.find(c => c.clause_id === selectedClauseId)?.source_text}
          </div>

          <button 
            className="btn-primary mt-3 w-full"
            onClick={handleCompileClause}
            disabled={compiling}
          >
            <Sparkles size={16} className="mr-2" />
            {compiling ? 'SLM Parsing into JSON Schema...' : 'Compile Clause into Draft Rule'}
          </button>

          {compiledDraft && (
            <div className="compiled-draft-box mt-3">
              <div className="draft-header">
                <span className="draft-title">Draft Versioned Rule Record:</span>
                <span className="status-pill pill-warning">PENDING HUMAN APPROVAL</span>
              </div>
              <pre className="json-code-block">
                {JSON.stringify(compiledDraft.diff_preview, null, 2)}
              </pre>

              <div className="alert-info-box mt-2">
                <strong>Human Oversight Safety Gate:</strong> This rule is quarantined. Existing in-flight applications remain on v1.0. Click below to approve.
              </div>

              <button 
                className="btn-success mt-2 w-full"
                onClick={() => onApproveRule(compiledDraft.rule_id)}
              >
                <Check size={16} className="mr-1" />
                Human Administrator: Approve &amp; Deploy Rule v{compiledDraft.version}
              </button>
            </div>
          )}
        </div>

        {/* Right: Bilingual Letter Drafter & Active Rules Table */}
        <div className="panel-card">
          <div className="panel-header">
            <h3 className="panel-title">Bilingual Officer Copilot &amp; Active Rule Registry</h3>
          </div>

          <button 
            className="btn-secondary w-full mb-3"
            onClick={handleDraftLetterDemo}
          >
            <FileText size={15} className="mr-2" />
            Generate Sample Bilingual Deficiency Letter (English &amp; Hindi)
          </button>

          {bilingualMemo && (
            <div className="bilingual-memo-container">
              <div className="memo-tab-content">
                <div className="font-semibold text-emerald text-sm mb-1">Hindi Draft (हिंदी):</div>
                <pre className="memo-text">{bilingualMemo.hindi}</pre>
                <div className="font-semibold text-purple text-sm mb-1 mt-2">English Draft:</div>
                <pre className="memo-text">{bilingualMemo.english}</pre>
              </div>
            </div>
          )}

          <h4 className="section-subhead mt-3">Active Versioned Rules Registry:</h4>
          <table className="niriksha-table mt-2">
            <thead>
              <tr>
                <th>Rule Code</th>
                <th>Version</th>
                <th>SLA Duration</th>
                <th>Category</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rules.map(r => (
                <tr key={r.id}>
                  <td className="font-mono text-purple">{r.rule_code}</td>
                  <td>v{r.version}</td>
                  <td>{r.duration_days} {r.duration_type.replace(/_/g, ' ')}</td>
                  <td>{r.process_category}</td>
                  <td>
                    <span className={`status-pill ${r.approval_status === 'APPROVED' ? 'pill-success' : 'pill-warning'}`}>
                      {r.approval_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
