import React, { useState } from 'react';
import {
  Bell,
  AlertTriangle,
  Clock,
  ShieldAlert,
  ArrowUpRight,
  TrendingUp,
  UserX,
  Send,
  FileCheck,
  CheckCircle,
  ChevronRight
} from 'lucide-react';

export default function SLAAlertsView() {
  const [selectedCase, setSelectedCase] = useState(null);

  const urgencyDocket = [
    {
      id: '1',
      institution: 'Aryabhata Institute of Tech & Mgmt',
      appNo: '1-46273286079',
      stage: 'Re-Scrutiny Pending',
      slaDaysElapsed: 18,
      slaTotal: 15,
      remaining: '1 day left',
      riskScore: 88,
      riskLevel: 'CRITICAL',
      drivers: ['Officer open workload: 18 cases', 'Stage duration: 18 working days', 'Assigned officer on medical leave'],
      status: 'DUE_SOON'
    },
    {
      id: '2',
      institution: 'Shree Ram Engineering College',
      appNo: '1-39201948201',
      stage: 'EVC Inspection',
      slaDaysElapsed: 12,
      slaTotal: 14,
      remaining: '2 days left',
      riskScore: 74,
      riskLevel: 'HIGH',
      drivers: ['Expert availability mismatch', 'Gazetted state holiday overlap', 'Panel conflict check required'],
      status: 'DUE_SOON'
    },
    {
      id: '3',
      institution: 'Vikas Technical Academy',
      appNo: '1-58291048201',
      stage: 'Initial Scrutiny',
      slaDaysElapsed: 11,
      slaTotal: 15,
      remaining: '4 days left',
      riskScore: 62,
      riskLevel: 'MEDIUM',
      drivers: ['Missing Fire NOC clarification', '2 automated reminders dispatched', 'High regional pendency queue'],
      status: 'ON_TRACK'
    },
    {
      id: '4',
      institution: 'Coimbatore Institute of Engineering',
      appNo: '1-29401827401',
      stage: 'Regional Committee',
      slaDaysElapsed: 16,
      slaTotal: 14,
      remaining: 'Overdue (+2d)',
      riskScore: 94,
      riskLevel: 'BREACHED',
      drivers: ['Stage limit exceeded by 2 days', 'Escalation Tier 2 active (Regional Head)', 'Undertaking compliance unverified'],
      status: 'OVERDUE'
    }
  ];

  return (
    <div className="gov-main-container">
      {/* Breadcrumb */}
      <div className="gov-breadcrumb">
        <span className="gov-breadcrumb-link">Home</span>
        <span className="gov-breadcrumb-separator">/</span>
        <span className="gov-breadcrumb-current">SLA & Alerts</span>
      </div>

      {/* Page Title */}
      <div className="gov-page-header">
        <h2 className="gov-page-title">SLA & Alerts Control Room</h2>
        <p className="gov-page-subtitle">
          Predictive SLA breach early-warning engine, officer urgency dockets, and automated escalation ladders.
        </p>
      </div>

      {/* 4 KPI Summary Cards */}
      <div className="gov-kpi-grid">
        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box blue">
            <Clock size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">ACTIVE MONITORED TASKS</div>
            <div className="gov-kpi-value blue">60</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box amber">
            <TrendingUp size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">7-DAY BREACH RISK FLAGGED</div>
            <div className="gov-kpi-value amber">14</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box amber">
            <Bell size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">EXPIRING CERTIFICATES (T-30/15/7/1)</div>
            <div className="gov-kpi-value amber">18</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box red">
            <ShieldAlert size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">ESCALATED TO BUREAU HEAD</div>
            <div className="gov-kpi-value red">4</div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.9fr 1fr', gap: '24px', alignItems: 'start' }}>
        
        {/* Left Column: Today's Actions Urgency Docket */}
        <div className="gov-card" style={{ padding: 0 }}>
          <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--gov-border)' }}>
            <div>
              <h3 className="gov-card-title">Today's Actions — Urgency-Ranked Officer Docket</h3>
              <p style={{ fontSize: '0.78rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                Sorted by predictive 7-day breach probability P(breach &le; 7d) with SHAP explainability.
              </p>
            </div>
            <span className="gov-badge gov-badge-amber">4 Actions Pending</span>
          </div>

          <div className="gov-table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="gov-table">
              <thead>
                <tr>
                  <th style={{ width: '32%' }}>APPLICATION & INSTITUTION</th>
                  <th style={{ width: '20%' }}>STAGE & SLA STATUS</th>
                  <th style={{ width: '18%' }}>BREACH RISK P(7d)</th>
                  <th style={{ width: '30%' }}>TOP SHAP RISK FACTORS</th>
                </tr>
              </thead>
              <tbody>
                {urgencyDocket.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--gov-text-primary)', fontSize: '0.86rem' }}>
                        {item.institution}
                      </div>
                      <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                        App No: {item.appNo}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--gov-blue)', fontSize: '0.82rem' }}>
                        {item.stage}
                      </div>
                      <div style={{ fontSize: '0.76rem', color: item.status === 'OVERDUE' ? 'var(--gov-red)' : 'var(--gov-amber)', marginTop: '2px', fontWeight: 500 }}>
                        {item.remaining}
                      </div>
                    </td>
                    <td>
                      <span className={`gov-badge ${item.riskScore >= 80 ? 'gov-badge-red' : 'gov-badge-amber'}`}>
                        {item.riskScore}% Risk ({item.riskLevel})
                      </span>
                    </td>
                    <td>
                      <ul style={{ listStyle: 'disc', paddingLeft: '14px', fontSize: '0.76rem', color: 'var(--gov-text-secondary)' }}>
                        {item.drivers.map((d, i) => (
                          <li key={i}>{d}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Multi-Tier Escalation Ladder & Expiry Watch */}
        <div>
          {/* Card: Escalation Ladder */}
          <div className="gov-card">
            <div className="gov-card-header">
              <h3 className="gov-card-title">Multi-Tier Escalation Ladder</h3>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '10px 12px', backgroundColor: '#F8FAFC', borderRadius: '6px', border: '1px solid var(--gov-border)' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: 'var(--gov-blue)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.78rem', fontWeight: 700, flexShrink: 0 }}>
                  T1
                </div>
                <div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                    Scrutiny Officer (Day 0)
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                    Normal review window per Approval Process Handbook.
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '10px 12px', backgroundColor: 'var(--gov-amber-light)', borderRadius: '6px', border: '1px solid var(--gov-amber-border)' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: 'var(--gov-amber)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.78rem', fontWeight: 700, flexShrink: 0 }}>
                  T2
                </div>
                <div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--gov-amber)' }}>
                    Regional Head (Day +3 Overdue)
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-primary)', marginTop: '2px' }}>
                    Automated SMS & email dispatch to Regional Director.
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '10px 12px', backgroundColor: 'var(--gov-red-light)', borderRadius: '6px', border: '1px solid var(--gov-red-border)' }}>
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: 'var(--gov-red)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.78rem', fontWeight: 700, flexShrink: 0 }}>
                  T3
                </div>
                <div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--gov-red)' }}>
                    Bureau Head (Day +7 Overdue)
                  </div>
                  <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-primary)', marginTop: '2px' }}>
                    National council intervention and pendency alert.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card: Document Validity Registry Watch */}
          <div className="gov-card">
            <div className="gov-card-header">
              <h3 className="gov-card-title">T-30 / 15 / 7 / 1 Expiry Watch</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ padding: '10px 14px', borderLeft: '4px solid var(--gov-amber)', backgroundColor: '#FEF9F0', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                  Registered Lease Deed Validity
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                  Expires in 30 days &bull; Automated bilingual reminder sent
                </div>
              </div>

              <div style={{ padding: '10px 14px', borderLeft: '4px solid var(--gov-red)', backgroundColor: '#FCE8E6', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                  Fire Safety Certificate (NOC)
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                  Expires in 7 days &bull; Urgent renewal upload requested
                </div>
              </div>

              <div style={{ padding: '10px 14px', borderLeft: '4px solid var(--gov-green)', backgroundColor: '#E6F4EA', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                  Conditional Faculty Undertaking
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                  Due in 14 days &bull; Verifier portal upload link active
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
