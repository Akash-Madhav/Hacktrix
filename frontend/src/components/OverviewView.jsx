import React from 'react';
import {
  Building2,
  Users,
  CheckCircle2,
  Clock,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  FileText
} from 'lucide-react';

export default function OverviewView({ onNavigate }) {
  return (
    <div className="gov-main-container">
      {/* Breadcrumb */}
      <div className="gov-breadcrumb">
        <span className="gov-breadcrumb-current">Home / Executive Overview</span>
      </div>

      {/* Page Title */}
      <div className="gov-page-header">
        <h2 className="gov-page-title">National Institutional Approval Overview</h2>
        <p className="gov-page-subtitle">
          Real-time oversight of AICTE approval workflows, statutory compliance, and predictive monitoring across 8 regions.
        </p>
      </div>

      {/* National Metric Tiles */}
      <div className="gov-kpi-grid">
        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box blue">
            <Building2 size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">APPROVED COLLEGES</div>
            <div className="gov-kpi-value blue">14,000+</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box green">
            <Users size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">STUDENTS COVERED</div>
            <div className="gov-kpi-value green">40M</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box amber">
            <Clock size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">APPLICATIONS IN REVIEW</div>
            <div className="gov-kpi-value amber">42</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box green">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">STATUTORY COMPLIANCE</div>
            <div className="gov-kpi-value green">94.2%</div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1fr', gap: '24px' }}>
        {/* Left Column: Regional Overview */}
        <div className="gov-card">
          <div className="gov-card-header">
            <h3 className="gov-card-title">Regional Processing Status (APH 2026-27)</h3>
            <button onClick={() => onNavigate('records')} className="gov-btn-outline">
              <span>View Full Registry</span>
              <ArrowRight size={13} />
            </button>
          </div>

          <div className="gov-table-container" style={{ border: 'none' }}>
            <table className="gov-table">
              <thead>
                <tr>
                  <th>REGION</th>
                  <th>DOSSIERS</th>
                  <th>ON TRACK</th>
                  <th>DUE SOON</th>
                  <th>COMPLIANCE RATE</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>Western Region</td>
                  <td>32</td>
                  <td>26</td>
                  <td>5</td>
                  <td style={{ color: 'var(--gov-green)', fontWeight: 600 }}>91.7%</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Southern Region</td>
                  <td>28</td>
                  <td>24</td>
                  <td>3</td>
                  <td style={{ color: 'var(--gov-green)', fontWeight: 600 }}>88.2%</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Northern Region</td>
                  <td>24</td>
                  <td>18</td>
                  <td>4</td>
                  <td style={{ color: 'var(--gov-amber)', fontWeight: 600 }}>79.5%</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>South-Western Region</td>
                  <td>22</td>
                  <td>20</td>
                  <td>2</td>
                  <td style={{ color: 'var(--gov-green)', fontWeight: 600 }}>95.0%</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Eastern Region</td>
                  <td>22</td>
                  <td>15</td>
                  <td>5</td>
                  <td style={{ color: 'var(--gov-amber)', fontWeight: 600 }}>72.4%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Quick Action Cards */}
        <div>
          <div className="gov-card">
            <div className="gov-card-header">
              <h3 className="gov-card-title">Quick Portals</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button
                onClick={() => onNavigate('tracking')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 16px',
                  backgroundColor: 'var(--gov-blue-light)',
                  border: '1px solid #B9D7F2',
                  borderRadius: '6px',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--gov-blue)', fontSize: '0.9rem' }}>
                    Track Application Status
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                    View real-time scrutiny stages & timelines
                  </div>
                </div>
                <ArrowRight size={16} color="var(--gov-blue)" />
              </button>

              <button
                onClick={() => onNavigate('sla-alerts')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 16px',
                  backgroundColor: '#FEF9F0',
                  border: '1px solid #FBE3B5',
                  borderRadius: '6px',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--gov-amber)', fontSize: '0.9rem' }}>
                    SLA & Early-Warning Control
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                    Predictive breach prevention & officer docket
                  </div>
                </div>
                <ArrowRight size={16} color="var(--gov-amber)" />
              </button>

              <button
                onClick={() => onNavigate('audit-trail')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 16px',
                  backgroundColor: '#F8FAFC',
                  border: '1px solid var(--gov-border)',
                  borderRadius: '6px',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--gov-text-primary)', fontSize: '0.9rem' }}>
                    Tamper-Evident Audit Ledger
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                    Schneier-Kelsey cryptographic chain verification
                  </div>
                </div>
                <ShieldCheck size={16} color="var(--gov-green)" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
