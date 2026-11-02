import React, { useState } from 'react';
import {
  Search,
  X,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Clock,
  Info,
  ListFilter,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';

export default function ApplicationTrackingView({ applications = [] }) {
  const [appNumber, setAppNumber] = useState('1-A8564C456B');
  const [collegeName, setCollegeName] = useState('Meenakshi Sundararajan Engineering College');

  // Active dossier data (defaulting to the reference dossier in Image 1)
  const [dossier, setDossier] = useState({
    institution: 'Meenakshi Sundararajan Engineering College (MSEC)',
    applicationNo: '1-A8564C456B',
    pid: '1-580D42F',
    region: 'Western Region',
    location: 'Chennai, Tamil Nadu',
    applicationType: 'Institutional Approval',
    currentStage: '2. Document Scrutiny',
    submittedOn: '20 October 2026',
    slaDeadline: '04 November 2026, 11:58 AM',
    completedStages: 2,
    totalStages: 5,
    progressPercent: 40,
    statusText: 'ACTION DUE SOON',
    slaRemaining: '3 days remaining',
    slaServiceWindow: '15 working-day service window'
  });

  const handleTrack = (e) => {
    e.preventDefault();
    if (!appNumber.trim() && !collegeName.trim()) return;

    // Search existing applications list if available
    const matched = applications.find(a => 
      (appNumber && a.application_number?.toLowerCase().includes(appNumber.toLowerCase())) ||
      (collegeName && a.institution_name?.toLowerCase().includes(collegeName.toLowerCase()))
    );

    if (matched) {
      setDossier({
        institution: matched.institution_name,
        applicationNo: matched.application_number || '1-A8564C456B',
        pid: matched.institution_permanent_id || '1-580D42F',
        region: `${matched.region || 'Western'} Region`,
        location: `${matched.district || 'Pune'}, ${matched.state || 'Maharashtra'}`,
        applicationType: matched.application_type || 'Institutional Approval',
        currentStage: matched.current_stage_label || '2. Document Scrutiny',
        submittedOn: matched.created_at ? new Date(matched.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' }) : '20 October 2026',
        slaDeadline: matched.deadline_str || '04 November 2026, 11:58 AM',
        completedStages: 2,
        totalStages: 5,
        progressPercent: 40,
        statusText: matched.sla_status === 'OVERDUE' ? 'OVERDUE' : 'ACTION DUE SOON',
        slaRemaining: `${matched.working_days_rem ?? 3} days remaining`,
        slaServiceWindow: `${matched.sla_days_total || 15} working-day service window`
      });
    }
  };

  return (
    <div className="gov-main-container">
      {/* Breadcrumb */}
      <div className="gov-breadcrumb">
        <span className="gov-breadcrumb-link">Home</span>
        <span className="gov-breadcrumb-separator">/</span>
        <span className="gov-breadcrumb-current">Application Tracking</span>
      </div>

      {/* Page Title */}
      <div className="gov-page-header">
        <h2 className="gov-page-title">Track Approval Application</h2>
        <p className="gov-page-subtitle">
          View application progress, pending actions and statutory timelines.
        </p>
      </div>

      {/* Search Panel */}
      <form onSubmit={handleTrack} className="gov-search-panel">
        <div className="gov-field-group">
          <label className="gov-field-label">Application Number *</label>
          <div className="gov-input-wrapper">
            <input
              type="text"
              className="gov-input"
              value={appNumber}
              onChange={(e) => setAppNumber(e.target.value)}
              placeholder="e.g. 1-A8564C456B"
            />
            <Search size={16} color="#64748B" style={{ position: 'absolute', right: '12px' }} />
          </div>
        </div>

        <div className="gov-field-group" style={{ flex: 1.6 }}>
          <label className="gov-field-label">College / Institution Name *</label>
          <div className="gov-input-wrapper">
            <input
              type="text"
              className="gov-input"
              value={collegeName}
              onChange={(e) => setCollegeName(e.target.value)}
              placeholder="Enter institution name"
            />
            {collegeName && (
              <X 
                size={16} 
                color="#64748B" 
                style={{ position: 'absolute', right: '12px', cursor: 'pointer' }}
                onClick={() => setCollegeName('')}
              />
            )}
          </div>
        </div>

        <button type="submit" className="gov-btn-primary">
          <Search size={16} />
          <span>Track Application</span>
        </button>
      </form>

      {/* Main 2-Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.9fr 1fr', gap: '24px', alignItems: 'start' }}>
        
        {/* Left Column */}
        <div>
          {/* Card 1: Application Details */}
          <div className="gov-card">
            <div className="gov-card-header">
              <h3 className="gov-card-title">Application Details</h3>
              <span className="gov-badge gov-badge-amber">
                <AlertTriangle size={13} />
                <span>{dossier.statusText}</span>
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '12px 28px', fontSize: '0.86rem' }}>
              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>Institution</span>
                <span style={{ fontWeight: 600, color: 'var(--gov-text-primary)' }}>: {dossier.institution}</span>
              </div>
              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>Application Type</span>
                <span style={{ fontWeight: 500, color: 'var(--gov-text-primary)' }}>: {dossier.applicationType}</span>
              </div>

              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>Application No.</span>
                <span style={{ fontWeight: 600, color: 'var(--gov-text-primary)' }}>: {dossier.applicationNo}</span>
              </div>
              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>Current Stage</span>
                <span style={{ fontWeight: 700, color: 'var(--gov-blue)' }}>: {dossier.currentStage}</span>
              </div>

              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>PID</span>
                <span style={{ fontWeight: 500, color: 'var(--gov-text-primary)' }}>: {dossier.pid}</span>
              </div>
              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>Submitted On</span>
                <span style={{ fontWeight: 500, color: 'var(--gov-text-primary)' }}>: {dossier.submittedOn}</span>
              </div>

              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>Region</span>
                <span style={{ fontWeight: 500, color: 'var(--gov-text-primary)' }}>: {dossier.region}</span>
              </div>
              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>SLA Deadline</span>
                <span style={{ fontWeight: 600, color: 'var(--gov-text-primary)' }}>: {dossier.slaDeadline}</span>
              </div>

              <div>
                <span style={{ color: 'var(--gov-text-secondary)', display: 'inline-block', width: '130px' }}>Location</span>
                <span style={{ fontWeight: 500, color: 'var(--gov-text-primary)' }}>: {dossier.location}</span>
              </div>
            </div>

            {/* Progress Row */}
            <div style={{ marginTop: '22px', paddingTop: '16px', borderTop: '1px solid #EDF2F7' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.84rem' }}>
                <span style={{ fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                  {dossier.completedStages} of {dossier.totalStages} stages completed
                </span>
                <span style={{ color: 'var(--gov-text-secondary)', fontWeight: 500 }}>
                  {dossier.progressPercent}%
                </span>
              </div>
              <div style={{ width: '100%', height: '8px', backgroundColor: '#E2E8F0', borderRadius: '999px', overflow: 'hidden' }}>
                <div style={{ width: `${dossier.progressPercent}%`, height: '100%', backgroundColor: 'var(--gov-blue)', borderRadius: '999px' }} />
              </div>
            </div>
          </div>

          {/* Card 2: Approval Journey */}
          <div className="gov-card">
            <div className="gov-card-header">
              <h3 className="gov-card-title">Approval Journey</h3>
              <button className="gov-btn-outline">
                <ListFilter size={14} />
                <span>View Detailed Status</span>
              </button>
            </div>

            {/* 5-Stage Horizontal Stepper */}
            <div className="gov-stepper">
              {/* Stage 1 */}
              <div className="gov-step">
                <div className="gov-step-node completed">
                  <CheckCircle2 size={18} color="#FFFFFF" />
                </div>
                <div className="gov-step-title">1. Application Submitted</div>
                <div className="gov-step-subtitle" style={{ color: 'var(--gov-green)', fontWeight: 500 }}>
                  20 Oct 2026
                </div>
              </div>

              {/* Stage 2 */}
              <div className="gov-step">
                <div className="gov-step-node current">
                  2
                </div>
                <div className="gov-step-title">2. Document Scrutiny</div>
                <div className="gov-step-subtitle" style={{ color: 'var(--gov-blue)', fontWeight: 600 }}>
                  Under review
                </div>
                <div style={{ marginTop: '4px' }}>
                  <span className="gov-badge gov-badge-amber" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                    3 days remaining
                  </span>
                </div>
              </div>

              {/* Stage 3 */}
              <div className="gov-step">
                <div className="gov-step-node pending">
                  3
                </div>
                <div className="gov-step-title">3. Expert Visit Committee (EVC)</div>
                <div className="gov-step-subtitle">Pending</div>
              </div>

              {/* Stage 4 */}
              <div className="gov-step">
                <div className="gov-step-node pending">
                  4
                </div>
                <div className="gov-step-title">4. SAC / SHC Review</div>
                <div className="gov-step-subtitle">Pending</div>
              </div>

              {/* Stage 5 */}
              <div className="gov-step">
                <div className="gov-step-node pending">
                  5
                </div>
                <div className="gov-step-title">5. Bureau Decision</div>
                <div className="gov-step-subtitle">Pending</div>
              </div>
            </div>

            {/* Current Action Callout */}
            <div style={{
              backgroundColor: 'var(--gov-blue-light)',
              border: '1px solid #B9D7F2',
              borderRadius: '6px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.84rem',
              color: 'var(--gov-blue-dark)'
            }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: 'var(--gov-blue)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Info size={15} />
              </div>
              <div>
                <strong>Current action:</strong> Documents are being examined by the scrutiny officer. Next update will appear after officer verification.
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div>
          {/* Card 3: SLA & Compliance */}
          <div className="gov-card">
            <div className="gov-card-header">
              <h3 className="gov-card-title">SLA & Compliance</h3>
            </div>

            <div style={{
              backgroundColor: '#FEF9F0',
              border: '1px solid #FBE3B5',
              borderRadius: '8px',
              padding: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '18px'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: '#FDE68A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--gov-amber)',
                flexShrink: 0
              }}>
                <Calendar size={24} />
              </div>

              <div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--gov-amber)' }}>
                  {dossier.slaRemaining}
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--gov-text-primary)', marginTop: '2px', fontWeight: 500 }}>
                  Deadline: {dossier.slaDeadline}
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                  {dossier.slaServiceWindow}
                </div>
              </div>
            </div>
          </div>

          {/* Card 4: Recent Activity */}
          <div className="gov-card">
            <div className="gov-card-header">
              <h3 className="gov-card-title">Recent Activity</h3>
              <a href="#activity" style={{ fontSize: '0.82rem', color: 'var(--gov-blue)', textDecoration: 'none', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '3px' }}>
                <span>View All</span>
                <ArrowRight size={13} />
              </a>
            </div>

            <div style={{ position: 'relative', paddingLeft: '22px' }}>
              {/* Vertical connector line */}
              <div style={{ position: 'absolute', left: '7px', top: '10px', bottom: '18px', width: '2px', backgroundColor: '#E2E8F0' }} />

              {/* Event 1 */}
              <div style={{ position: 'relative', marginBottom: '22px' }}>
                <div style={{ position: 'absolute', left: '-22px', top: '4px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--gov-blue)', border: '2px solid #FFFFFF', boxShadow: '0 0 0 1px var(--gov-blue)' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                    Document scrutiny initiated
                  </div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--gov-text-secondary)' }}>
                    28 Oct 2026<br />10:24 AM
                  </div>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--gov-text-secondary)', marginTop: '4px' }}>
                  Application moved to Document Scrutiny stage by Scrutiny Officer.
                </div>
              </div>

              {/* Event 2 */}
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '-22px', top: '4px', width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--gov-blue)', border: '2px solid #FFFFFF', boxShadow: '0 0 0 1px var(--gov-blue)' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                    Application received
                  </div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--gov-text-secondary)' }}>
                    20 Oct 2026<br />04:12 PM
                  </div>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--gov-text-secondary)', marginTop: '4px' }}>
                  Application submitted successfully.
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
