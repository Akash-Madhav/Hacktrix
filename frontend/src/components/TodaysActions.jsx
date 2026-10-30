import React, { useState } from 'react';
import { 
  AlertTriangle, Flame, Clock, CheckCircle2, User, 
  ArrowRight, ShieldAlert, Sparkles, Filter, ChevronRight
} from 'lucide-react';

export default function TodaysActions({ 
  actions, 
  onSelectApplication, 
  onOpenExplain, 
  onOpenRevert 
}) {
  const [filterRegion, setFilterRegion] = useState('ALL');

  const filtered = actions.filter(a => {
    if (filterRegion !== 'ALL' && a.region !== filterRegion) return false;
    return true;
  });

  return (
    <div className="todays-actions-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Officer Console — Today's Ranked Actions</h2>
          <p className="view-desc">
            Urgency-ranked docket combining SLA delay, Early-Warning ML risk scores ($P(\text{breach})$), officer workload, and auto-delegation triggers.
          </p>
        </div>
        <div className="filter-chip-group">
          <span className="filter-label"><Filter size={14} /> Region:</span>
          {['ALL', 'Western', 'Northern', 'Southern', 'South-Western'].map(r => (
            <button
              key={r}
              className={`filter-chip ${filterRegion === r ? 'active' : ''}`}
              onClick={() => setFilterRegion(r)}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="actions-card-list">
        {filtered.map((item, index) => {
          const isEscalated = item.status === 'ESCALATED';
          const isOverdue = item.status === 'OVERDUE';
          const isDueSoon = item.status === 'DUE_SOON';
          const riskPct = Math.round((item.risk_score || 0) * 100);

          return (
            <div 
              key={item.task_id} 
              className={`action-card ${isEscalated ? 'border-escalated' : (isOverdue ? 'border-overdue' : 'border-due')}`}
            >
              <div className="action-rank-col">
                <span className="rank-num">#{index + 1}</span>
                <span className="urgency-score-badge" title="Combined Urgency Metric">
                  {item.urgency_score} pts
                </span>
              </div>

              <div className="action-main-content">
                <div className="action-meta-row">
                  <span className="inst-badge">{item.region} Region</span>
                  <span className="app-id-tag">{item.application_number || item.task_number}</span>
                  <span className={`status-pill ${isEscalated ? 'pill-purple' : (isOverdue ? 'pill-danger' : 'pill-warning')}`}>
                    {item.status} (L{item.escalation_level})
                  </span>
                  <span className="stage-tag">{item.current_stage.replace('_', ' ')}</span>
                </div>

                <h3 className="action-inst-title">{item.institution_name}</h3>
                
                {/* Specific Human Reason (from NIRIKSHA Spec) */}
                <div className="urgency-reason-box">
                  <div className="reason-text">
                    <strong>Trigger Reason:</strong> {item.urgency_reason}
                  </div>
                </div>

                <div className="action-footer-row">
                  <div className="action-stat">
                    <Clock size={14} className="text-muted" />
                    <span>Working Days Left: <strong>{item.working_days_remaining}</strong></span>
                  </div>

                  <div className="action-stat" title="Estimated probability of SLA breach within 7 days">
                    <Sparkles size={14} className="text-purple" />
                    <span>ML Risk: <strong className={riskPct > 65 ? 'text-rose' : 'text-amber'}>{riskPct}%</strong></span>
                  </div>

                  <div className="action-stat">
                    <User size={14} className="text-muted" />
                    <span>Officer: <strong>{item.assigned_officer}</strong></span>
                  </div>

                  <div className="action-stat ml-auto text-emerald font-medium">
                    <span>{item.recommended_action}</span>
                  </div>
                </div>
              </div>

              <div className="action-btns-col">
                <button 
                  className="btn-action-primary"
                  onClick={() => onSelectApplication(item.application_id)}
                >
                  Open Dossier <ChevronRight size={14} />
                </button>
                <button 
                  className="btn-action-secondary"
                  onClick={() => onOpenExplain(item.task_id)}
                >
                  Explain SLA
                </button>
                <button 
                  className="btn-action-danger"
                  onClick={() => onOpenRevert(item.application_id, item.institution_name)}
                >
                  Return / Revert
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
