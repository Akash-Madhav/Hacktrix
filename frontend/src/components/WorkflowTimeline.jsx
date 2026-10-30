import React, { useState } from 'react';
import { 
  GitBranch, CheckCircle2, Clock, AlertCircle, ArrowRight, 
  RotateCcw, ShieldCheck, FileText, ChevronRight, X 
} from 'lucide-react';

export default function WorkflowTimeline({ 
  currentApplication, 
  pathways, 
  onTransitionStage, 
  history 
}) {
  const [selectedPathway, setSelectedPathway] = useState('PATHWAY_SCRUTINY_EVC');
  const [isTransitionModalOpen, setIsTransitionModalOpen] = useState(false);
  const [targetStage, setTargetStage] = useState('');
  const [actionType, setActionType] = useState('ADVANCE');
  const [mandatoryReason, setMandatoryReason] = useState('');
  const [transitionNotes, setTransitionNotes] = useState('');
  const [validationError, setValidationError] = useState('');

  const activePathwayObj = pathways.find(p => p.pathway_code === selectedPathway) || pathways[1] || pathways[0];
  const stages = activePathwayObj?.stages || [];

  const handleOpenTransition = (stageName, type = 'ADVANCE') => {
    setTargetStage(stageName);
    setActionType(type);
    setMandatoryReason('');
    setTransitionNotes('');
    setValidationError('');
    setIsTransitionModalOpen(true);
  };

  const handleExecuteTransition = () => {
    if ((actionType === 'REVERT' || targetStage === 'RETURNED_FOR_CORRECTION') && !mandatoryReason.trim()) {
      setValidationError('A mandatory legal reason is required when returning or reverting an application.');
      return;
    }

    if (!currentApplication) {
      setValidationError('No active application selected.');
      return;
    }

    onTransitionStage({
      application_id: currentApplication.id,
      to_stage: targetStage,
      action_type: actionType,
      mandatory_reason: mandatoryReason,
      notes: transitionNotes
    });

    setIsTransitionModalOpen(false);
  };

  return (
    <div className="workflow-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Statechart Approval Pathways (ROUTE)</h2>
          <p className="view-desc">
            Pathways stored as data in the statechart engine. Guarded transitions, immutable audit events, and mandatory-reason reverts.
          </p>
        </div>
      </div>

      {/* Pathway Switcher Tabs */}
      <div className="pathway-tabs-bar">
        {pathways.map(pw => (
          <button
            key={pw.pathway_code}
            className={`pathway-tab-btn ${selectedPathway === pw.pathway_code ? 'active' : ''}`}
            onClick={() => setSelectedPathway(pw.pathway_code)}
          >
            <GitBranch size={15} />
            <span>{pw.name}</span>
          </button>
        ))}
      </div>

      {/* Active Application Context Bar */}
      {currentApplication && (
        <div className="active-app-context-box">
          <div className="context-lead">
            <span className="context-label">ACTIVE APPLICATION:</span>
            <span className="context-name">{currentApplication.institution_name}</span>
            <span className="context-id">({currentApplication.application_number})</span>
          </div>
          <div className="context-stage-tag">
            Current Stage: <strong>{currentApplication.current_stage.replace(/_/g, ' ')}</strong>
          </div>
        </div>
      )}

      {/* Horizontal Visual Statechart Pipeline */}
      <div className="panel-card mt-3">
        <div className="panel-header">
          <div>
            <h3 className="panel-title">{activePathwayObj?.name}</h3>
            <p className="panel-sub">{activePathwayObj?.description} (Version: {activePathwayObj?.version})</p>
          </div>
        </div>

        <div className="horizontal-pipeline-wrapper">
          {stages.map((st, idx) => {
            const isCurrent = currentApplication?.current_stage === st.stage_name;
            const isPast = false; // Could be computed from order

            return (
              <div key={st.stage_name} className={`pipeline-step-node ${isCurrent ? 'current' : ''}`}>
                <div className="step-number">{st.order}</div>
                <div className="step-card">
                  <div className="step-title">{st.stage_name.replace(/_/g, ' ')}</div>
                  <div className="step-sla-badge">
                    <Clock size={12} />
                    <span>{st.sla_days} {st.sla_type === 'WORKING_DAYS' ? 'Work Days' : 'Days'}</span>
                  </div>
                  
                  {isCurrent && (
                    <div className="current-indicator-tag">ACTIVE STAGE</div>
                  )}

                  {/* Actions allowed from this stage */}
                  {isCurrent && st.allowed_next && st.allowed_next.length > 0 && (
                    <div className="step-next-actions">
                      <div className="action-prompt">Next Permitted Moves:</div>
                      {st.allowed_next.map(nxt => (
                        <button
                          key={nxt}
                          className={`btn-stage-move ${nxt === 'RETURNED_FOR_CORRECTION' ? 'revert' : ''}`}
                          onClick={() => handleOpenTransition(nxt, nxt === 'RETURNED_FOR_CORRECTION' ? 'REVERT' : 'ADVANCE')}
                        >
                          {nxt === 'RETURNED_FOR_CORRECTION' ? 'Return with Reason' : `Advance to ${nxt.replace(/_/g, ' ')}`}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {idx < stages.length - 1 && (
                  <div className="pipeline-connector">
                    <ChevronRight size={18} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Transition History Table */}
      {history && history.length > 0 && (
        <div className="panel-card mt-4">
          <div className="panel-header">
            <h3 className="panel-title">Immutable Stage Transition Audit History</h3>
          </div>
          <table className="niriksha-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>From Stage</th>
                <th>Target Stage</th>
                <th>Action</th>
                <th>Officer / Role</th>
                <th>Mandatory Reason</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h, i) => (
                <tr key={i}>
                  <td className="text-muted">{h.timestamp ? new Date(h.timestamp).toLocaleString() : 'N/A'}</td>
                  <td>{h.from_stage.replace(/_/g, ' ')}</td>
                  <td className="font-semibold text-emerald">{h.to_stage.replace(/_/g, ' ')}</td>
                  <td><span className="badge-highlight">{h.action_type}</span></td>
                  <td>{h.actor_role}</td>
                  <td className="text-amber">{h.mandatory_reason || h.notes || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Revert / Transition Modal */}
      {isTransitionModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3 className="modal-title">
                {actionType === 'REVERT' ? 'Return Application with Mandatory Reason' : `Advance to ${targetStage.replace(/_/g, ' ')}`}
              </h3>
              <button className="modal-close-btn" onClick={() => setIsTransitionModalOpen(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="modal-body">
              {validationError && (
                <div className="alert-error-box">
                  <AlertCircle size={16} />
                  <span>{validationError}</span>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">
                  Target Stage:
                </label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={targetStage.replace(/_/g, ' ')} 
                  disabled 
                />
              </div>

              {(actionType === 'REVERT' || targetStage === 'RETURNED_FOR_CORRECTION') && (
                <div className="form-group">
                  <label className="form-label required">
                    Mandatory Statutory Reason (Required by APH):
                  </label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    placeholder="Enter explicit deficiency observed (e.g. Inadequate instructional area in building plan; deficit 450 sqm below APH norm)..."
                    value={mandatoryReason}
                    onChange={(e) => setMandatoryReason(e.target.value)}
                  />
                  <span className="form-hint">
                    This reason is permanently recorded in the Schneier-Kelsey audit ledger and sent to the institution.
                  </span>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Officer Notes (Optional):</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Internal administrative comments..."
                  value={transitionNotes}
                  onChange={(e) => setTransitionNotes(e.target.value)}
                />
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setIsTransitionModalOpen(false)}>
                Cancel
              </button>
              <button 
                className={actionType === 'REVERT' ? 'btn-danger' : 'btn-primary'}
                onClick={handleExecuteTransition}
              >
                Confirm &amp; Record Transition
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
