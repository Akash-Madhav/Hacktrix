import React, { useState, useEffect } from 'react';
import { 
  X, Clock, Calendar, ShieldAlert, CheckCircle, 
  AlertTriangle, ArrowRight, Sparkles, User, Info
} from 'lucide-react';

export default function SLAExplainerModal({ taskId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!taskId) return;
    setLoading(true);
    fetch(`/api/monitoring/tasks/${taskId}/explain`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load SLA explanation');
        return res.json();
      })
      .then(resData => {
        setData(resData);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [taskId]);

  if (!taskId) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-card modal-lg">
        <div className="modal-header">
          <div className="flex-header">
            <Clock className="text-purple mr-2" size={20} />
            <div>
              <h3 className="modal-title">Explainable SLA &amp; Monitoring Intelligence</h3>
              <p className="modal-sub">Transparent mathematical breakdown &amp; decision logic</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <span>Generating deterministic SLA explanation...</span>
            </div>
          )}

          {error && (
            <div className="alert-error-box">
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {data && (
            <div className="explainer-content">
              {/* Header Status Banner */}
              <div className={`explainer-banner banner-${data.status.toLowerCase()}`}>
                <div className="banner-status-tag">
                  STATUS: <strong>{data.status}</strong> (Escalation Level {data.escalation_level})
                </div>
                <div className="banner-title">{data.title}</div>
                <div className="banner-sub">
                  Task ID: <code>{data.task_number}</code> | Current Stage: <strong>{data.current_stage.replace(/_/g, ' ')}</strong>
                </div>
              </div>

              {/* 10-Point Transparent Breakdown Grid */}
              <div className="explainer-grid-2">
                <div className="explainer-box">
                  <div className="box-label">1. WHAT IS BEING MONITORED?</div>
                  <div className="box-val">{data.process_category.replace(/_/g, ' ')} ({data.entity_type})</div>
                </div>

                <div className="explainer-box">
                  <div className="box-label">2. APPLICABLE STATUTORY RULE</div>
                  <div className="box-val text-purple font-mono">
                    {data.applicable_rule.rule_code} (v{data.applicable_rule.version})
                  </div>
                </div>

                <div className="explainer-box">
                  <div className="box-label">3. ALLOWED STATUTORY SLA</div>
                  <div className="box-val">
                    <strong>{data.applicable_rule.duration_days}</strong> {data.applicable_rule.duration_type.replace(/_/g, ' ')}
                  </div>
                </div>

                <div className="explainer-box">
                  <div className="box-label">4. MONITORING START DATE</div>
                  <div className="box-val">{data.calculation_breakdown.start_date}</div>
                </div>

                <div className="explainer-box">
                  <div className="box-label">5. CALCULATED DEADLINE</div>
                  <div className="box-val text-amber font-semibold">
                    {data.calculation_breakdown.calculated_deadline}
                  </div>
                </div>

                <div className="explainer-box">
                  <div className="box-label">6. TIME ELAPSED VS REMAINING</div>
                  <div className="box-val">
                    Elapsed: <strong>{data.calculation_breakdown.working_days_elapsed}</strong> work days | 
                    Remaining: <strong className={data.calculation_breakdown.is_overdue ? 'text-rose' : 'text-emerald'}>
                      {data.calculation_breakdown.working_days_remaining}
                    </strong> work days
                  </div>
                </div>

                <div className="explainer-box col-span-2">
                  <div className="box-label">7. ASSIGNED RESPONSIBLE OFFICER</div>
                  <div className="box-val">
                    <User size={15} className="inline mr-1" />
                    <strong>{data.assigned_responsible.name}</strong> ({data.assigned_responsible.role})
                  </div>
                </div>

                <div className="explainer-box col-span-2 highlight-box">
                  <div className="box-label">8. TRIGGER REASON</div>
                  <div className="box-val text-amber">
                    {data.trigger_reason}
                  </div>
                </div>

                <div className="explainer-box col-span-2 action-box">
                  <div className="box-label">9. RECOMMENDED NEXT ACTION</div>
                  <div className="box-val text-emerald font-medium">
                    {data.next_action}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close Explainer
          </button>
        </div>
      </div>
    </div>
  );
}
