import React, { useState } from 'react';
import { Users, Sparkles, CheckCircle2, XCircle, ShieldCheck, ChevronRight, Play } from 'lucide-react';

export default function EVCOptimizerView({ panels, onOptimizeApplication }) {
  const [selectedPanel, setSelectedPanel] = useState(panels[0] || null);
  const [optimizingAppId, setOptimizingAppId] = useState('');
  const [optimizerOutput, setOptimizerOutput] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRunOptimizer = (appId) => {
    setLoading(true);
    fetch(`/api/evc/optimize/${appId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheduled_date: '2026-11-18' })
    })
      .then(r => r.json())
      .then(data => {
        setOptimizerOutput(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  return (
    <div className="evc-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">EVC Inspection Panels &amp; CP-SAT Optimizer</h2>
          <p className="view-desc">
            Constraint-programming scheduler matching domain expertise and availability while strictly enforcing conflict-of-interest exclusion rules (e.g. same affiliating university).
          </p>
        </div>
      </div>

      <div className="dashboard-grid-2">
        {/* Left: Empanelled Inspection Panels */}
        <div className="panel-card">
          <div className="panel-header">
            <h3 className="panel-title">Inspection Panels in Queue</h3>
            <span className="badge-highlight">{panels.length} Active Panels</span>
          </div>

          <div className="panel-list">
            {panels.map(p => (
              <div 
                key={p.id} 
                className={`panel-item-card ${selectedPanel?.id === p.id ? 'active' : ''}`}
                onClick={() => {
                  setSelectedPanel(p);
                  setOptimizerOutput(null);
                }}
              >
                <div className="item-head">
                  <span className="font-mono text-purple">{p.panel_number}</span>
                  <span className="status-pill pill-neutral">{p.status}</span>
                </div>
                <div className="item-inst">{p.institution_name}</div>
                <div className="item-meta">
                  <span>Region: {p.region}</span>
                  <span>Experts: {p.assigned_experts.length} Empanelled</span>
                </div>
                <button 
                  className="btn-sm btn-primary mt-2"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRunOptimizer(p.application_id);
                  }}
                >
                  <Sparkles size={13} className="mr-1" /> Re-run CP-SAT Matcher
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Optimizer Output & Conflict Breakdown */}
        <div className="panel-card">
          <div className="panel-header">
            <h3 className="panel-title">Explainable Expert Selection &amp; Exclusion Log</h3>
            <span className="text-muted text-xs">Google OR-Tools CP-SAT</span>
          </div>

          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <span>Evaluating hard constraints and conflict graphs...</span>
            </div>
          )}

          {optimizerOutput && (
            <div className="optimizer-results">
              <div className="optimizer-stats-banner">
                <ShieldCheck size={16} className="text-emerald mr-1" />
                <span>
                  Evaluated {optimizerOutput.optimizer_stats.total_pool_evaluated} candidates in {optimizerOutput.optimizer_stats.solve_time_ms}ms. 
                  Zero conflict violations (Rule 4.4).
                </span>
              </div>

              <h4 className="section-subhead mt-3">Selected Inspection Panel (3 Experts):</h4>
              <div className="chosen-experts-stack">
                {optimizerOutput.chosen_experts.map((exp, i) => (
                  <div key={i} className="expert-card selected">
                    <div className="expert-header">
                      <span className="expert-name">{exp.name} ({exp.assigned_role})</span>
                      <span className="expert-dept">{exp.department} — {exp.affiliation_university}</span>
                    </div>
                    <div className="expert-reason text-emerald">
                      <CheckCircle2 size={13} className="inline mr-1" />
                      {exp.selection_reason}
                    </div>
                  </div>
                ))}
              </div>

              <h4 className="section-subhead mt-4">Excluded Candidates &amp; Violated Conflict Rules:</h4>
              <div className="excluded-experts-stack">
                {optimizerOutput.excluded_candidates.map((exc, i) => (
                  <div key={i} className="expert-card excluded">
                    <span className="expert-name text-rose">{exc.expert_name}</span>
                    <span className="expert-exclusion-rule">
                      <XCircle size={13} className="inline mr-1" />
                      {exc.exclusion_rule}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!optimizerOutput && selectedPanel && (
            <div className="panel-existing-experts">
              <div className="panel-subhead">
                Existing Panel for <strong>{selectedPanel.institution_name}</strong>:
              </div>
              {selectedPanel.assigned_experts.map((exp, i) => (
                <div key={i} className="expert-card selected">
                  <div className="expert-header">
                    <span className="expert-name">{exp.name} ({exp.assigned_role || 'Member'})</span>
                    <span className="expert-dept">{exp.department} — {exp.affiliation_university}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
