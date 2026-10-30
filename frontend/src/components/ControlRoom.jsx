import React from 'react';
import { 
  Building2, Clock, AlertTriangle, ShieldAlert, CheckCircle, 
  TrendingUp, MapPin, ArrowUpRight, ShieldCheck, Flame
} from 'lucide-react';

export default function ControlRoom({ summary, onSelectRegion, onOpenTaskExplain }) {
  const kpis = summary?.kpis || {
    total_monitored: 60,
    active_on_track: 15,
    due_soon: 25,
    overdue_breach: 0,
    escalated_critical: 14,
    compliance_percentage: 76.7
  };

  const regions = summary?.regional_breakdown || [
    { region: 'Northern', total_dossiers: 9, breached_count: 2, compliance_rate: 77.8 },
    { region: 'Western', total_dossiers: 12, breached_count: 1, compliance_rate: 91.7 },
    { region: 'Southern', total_dossiers: 8, breached_count: 1, compliance_rate: 87.5 },
    { region: 'South-Western', total_dossiers: 8, breached_count: 0, compliance_rate: 100.0 },
    { region: 'Eastern', total_dossiers: 8, breached_count: 3, compliance_rate: 62.5 },
    { region: 'Central', total_dossiers: 7, breached_count: 2, compliance_rate: 71.4 },
    { region: 'North-Western', total_dossiers: 8, breached_count: 1, compliance_rate: 87.5 }
  ];

  return (
    <div className="control-room-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Executive Control Room — National AICTE Dashboard</h2>
          <p className="view-desc">
            Real-time stage ageing, SLA velocity, and regional compliance monitoring across India's technical education institutions.
          </p>
        </div>
        <div className="system-health-pill">
          <ShieldCheck size={16} className="text-emerald" />
          <span>Schneier-Kelsey Ledger: 100% Verified</span>
        </div>
      </div>

      {/* 5 Foundational KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card total">
          <div className="kpi-head">
            <span className="kpi-label">TOTAL MONITORED</span>
            <Building2 size={20} className="kpi-icon" />
          </div>
          <div className="kpi-val">{kpis.total_monitored}</div>
          <div className="kpi-meta">60 Institutional Dossiers (8 Regions)</div>
        </div>

        <div className="kpi-card active">
          <div className="kpi-head">
            <span className="kpi-label">ON-TRACK (HEALTHY)</span>
            <CheckCircle size={20} className="kpi-icon text-emerald" />
          </div>
          <div className="kpi-val text-emerald">{kpis.active_on_track}</div>
          <div className="kpi-meta">Progressing within statutory limits</div>
        </div>

        <div className="kpi-card warning">
          <div className="kpi-head">
            <span className="kpi-label">DUE SOON (&le; 3 DAYS)</span>
            <Clock size={20} className="kpi-icon text-amber" />
          </div>
          <div className="kpi-val text-amber">{kpis.due_soon}</div>
          <div className="kpi-meta">Early-warning reminders dispatched</div>
        </div>

        <div className="kpi-card overdue">
          <div className="kpi-head">
            <span className="kpi-label">OVERDUE SLA</span>
            <AlertTriangle size={20} className="kpi-icon text-rose" />
          </div>
          <div className="kpi-val text-rose">{kpis.overdue_breach}</div>
          <div className="kpi-meta">Statutory deadline exceeded</div>
        </div>

        <div className="kpi-card escalated">
          <div className="kpi-head">
            <span className="kpi-label">CRITICAL ESCALATIONS</span>
            <Flame size={20} className="kpi-icon text-purple" />
          </div>
          <div className="kpi-val text-purple">{kpis.escalated_critical}</div>
          <div className="kpi-meta">Level 1 &amp; 2 ladder triggered</div>
        </div>
      </div>

      {/* Regional Compliance & Bottlenecks */}
      <div className="dashboard-grid-2">
        <div className="panel-card">
          <div className="panel-header">
            <div>
              <h3 className="panel-title">Regional Pendency &amp; Compliance Rate</h3>
              <p className="panel-sub">SLA compliance breakdown across AICTE's 8 regional offices</p>
            </div>
            <span className="badge-highlight">{kpis.compliance_percentage}% National Compliance</span>
          </div>

          <div className="regional-table-wrapper">
            <table className="niriksha-table">
              <thead>
                <tr>
                  <th>Regional Office</th>
                  <th>Total Active Dossiers</th>
                  <th>Breached Cases</th>
                  <th>Compliance Rate</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {regions.map(r => {
                  const isHighRisk = r.compliance_rate < 75;
                  return (
                    <tr key={r.region}>
                      <td className="font-medium flex-cell">
                        <MapPin size={15} className="mr-1 text-muted" />
                        {r.region} Office
                      </td>
                      <td>{r.total_dossiers}</td>
                      <td className={r.breached_count > 0 ? 'text-rose font-semibold' : 'text-muted'}>
                        {r.breached_count}
                      </td>
                      <td>
                        <div className="progress-cell">
                          <div className="progress-track">
                            <div 
                              className={`progress-fill ${isHighRisk ? 'bg-amber' : 'bg-emerald'}`} 
                              style={{ width: `${r.compliance_rate}%` }}
                            />
                          </div>
                          <span className="progress-text">{r.compliance_rate}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`status-pill ${isHighRisk ? 'pill-warning' : 'pill-success'}`}>
                          {isHighRisk ? 'Attention Required' : 'Healthy Velocity'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Process Intelligence Panel */}
        <div className="panel-card">
          <div className="panel-header">
            <div>
              <h3 className="panel-title">Multi-Process Architecture</h3>
              <p className="panel-sub">Active regulatory pipelines managed by NIRIKSHA</p>
            </div>
          </div>

          <div className="process-cards-stack">
            <div className="process-info-card">
              <div className="proc-title">1. Application Stage Tracking</div>
              <div className="proc-desc">
                Enforces 15-day Scrutiny and 14-day EVC working-day timelines. Fast-forwards trigger automatic climbing ladders.
              </div>
            </div>

            <div className="process-info-card">
              <div className="proc-title">2. Validity Registry (T-30/15/7/1)</div>
              <div className="proc-desc">
                Monitors registered lease deeds and Fire Safety NOCs with four advance notices and downloadable .ics calendar invites.
              </div>
            </div>

            <div className="process-info-card">
              <div className="proc-title">3. Undertakings Register</div>
              <div className="proc-desc">
                Tracks conditional approvals (e.g. faculty recruitment promises) to prevent institutions operating without compliance.
              </div>
            </div>

            <div className="process-info-card">
              <div className="proc-title">4. EVC CP-SAT Optimizer</div>
              <div className="proc-desc">
                Google OR-Tools constraint-satisfaction engine matching conflict-free inspection panels with zero university overlap.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
