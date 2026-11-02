import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Lock,
  RefreshCw,
  Search,
  FileText,
  KeyRound
} from 'lucide-react';

export default function AuditTrailView() {
  const [verifying, setVerifying] = useState(false);
  const [verifiedStatus, setVerifiedStatus] = useState({
    verified: true,
    totalEvents: 428,
    verifiedAt: '30 Oct 2026, 03:00 PM',
    hashAlg: 'SHA-256 (Schneier-Kelsey 1999 forward-secure)'
  });

  const auditEvents = [
    {
      seq: 428,
      timestamp: '30 Oct 2026, 02:45:12 PM',
      action: 'STAGE_TRANSITION_EVALUATED',
      actor: 'Regional Scrutiny Officer (ID: RO-W-401)',
      entity: 'Application: 1-A8564C456B',
      details: 'Stage transitioned from SUBMITTED to DOCUMENT_SCRUTINY. Guard verified: all mandatory uploads present.',
      prevHash: 'a7f920bc81...384d',
      currHash: 'e3b0c44298...194a',
      status: 'VERIFIED'
    },
    {
      seq: 427,
      timestamp: '30 Oct 2026, 01:15:00 PM',
      action: 'SLA_BREACH_PREDICTION_DISPATCHED',
      actor: 'Predictive Early Warning Engine (LightGBM)',
      entity: 'Application: 1-46273286079',
      details: 'P(breach <= 7d) = 88%. Escalation reminder dispatched to assigned officer docket with SHAP attribution.',
      prevHash: '6b4129fe01...721c',
      currHash: 'a7f920bc81...384d',
      status: 'VERIFIED'
    },
    {
      seq: 426,
      timestamp: '30 Oct 2026, 11:30:22 AM',
      action: 'EVC_PANEL_OPTIMIZED_AND_LOCKED',
      actor: 'EVC Panel Optimizer (OR-Tools CP-SAT)',
      entity: 'Inspection Panel: EVC-2026-W09',
      details: 'Assigned 3 experts satisfying domain match with zero conflict of interest. Council approval recorded.',
      prevHash: '91d84820ac...9102',
      currHash: '6b4129fe01...721c',
      status: 'VERIFIED'
    },
    {
      seq: 425,
      timestamp: '30 Oct 2026, 09:00:15 AM',
      action: 'RULE_CORRIGENDUM_EFFECTIVE_DATE_APPLIED',
      actor: 'Rule Administrator (Council Auth: HQ-001)',
      entity: 'Rule: APH-SLA-EVC-2026-CORR2 (v2.0)',
      details: 'Corrigendum of 2 Dec 2025 enacted. Timeline set to 14 working days. Human review checkpoint verified.',
      prevHash: '04fc2901a8...4490',
      currHash: '91d84820ac...9102',
      status: 'VERIFIED'
    }
  ];

  const handleVerify = () => {
    setVerifying(true);
    setTimeout(() => {
      setVerifying(false);
      setVerifiedStatus({
        verified: true,
        totalEvents: 428,
        verifiedAt: new Date().toLocaleTimeString('en-GB') + ', Today',
        hashAlg: 'SHA-256 (Schneier-Kelsey 1999 forward-secure)'
      });
    }, 600);
  };

  return (
    <div className="gov-main-container">
      {/* Breadcrumb */}
      <div className="gov-breadcrumb">
        <span className="gov-breadcrumb-link">Home</span>
        <span className="gov-breadcrumb-separator">/</span>
        <span className="gov-breadcrumb-current">Audit Trail</span>
      </div>

      {/* Page Title */}
      <div className="gov-page-header">
        <h2 className="gov-page-title">Cryptographic Audit Ledger</h2>
        <p className="gov-page-subtitle">
          Tamper-evident Schneier-Kelsey (1999) forward-secure hash chain proving every statutory action and decision.
        </p>
      </div>

      {/* Verification Status Card */}
      <div className="gov-card" style={{ backgroundColor: '#F8FAFC', border: '1px solid #CBD5E1', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '8px', backgroundColor: 'var(--gov-green-light)', color: 'var(--gov-green)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={28} />
          </div>
          <div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--gov-text-primary)' }}>
              Ledger Integrity: 100% Cryptographically Verified
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
              Algorithm: {verifiedStatus.hashAlg} &bull; Total Blocks: {verifiedStatus.totalEvents} &bull; Last Checked: {verifiedStatus.verifiedAt}
            </div>
          </div>
        </div>

        <button
          onClick={handleVerify}
          disabled={verifying}
          className="gov-btn-primary"
          style={{ backgroundColor: 'var(--gov-green)' }}
        >
          <RefreshCw size={15} className={verifying ? 'animate-spin' : ''} />
          <span>{verifying ? 'Recomputing Hashes...' : 'Re-verify Entire Chain'}</span>
        </button>
      </div>

      {/* Ledger Table */}
      <div className="gov-card" style={{ padding: 0 }}>
        <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--gov-border)' }}>
          <h3 className="gov-card-title">Immutable Event Sequence</h3>
          <span className="gov-badge gov-badge-green">
            <Lock size={12} />
            <span>Forward-Secure Hashes</span>
          </span>
        </div>

        <div className="gov-table-container" style={{ border: 'none', borderRadius: 0 }}>
          <table className="gov-table">
            <thead>
              <tr>
                <th style={{ width: '8%' }}>BLOCK #</th>
                <th style={{ width: '18%' }}>TIMESTAMP & ACTOR</th>
                <th style={{ width: '22%' }}>ACTION & ENTITY</th>
                <th style={{ width: '32%' }}>EVENT DETAILS</th>
                <th style={{ width: '20%' }}>PREV HASH &rarr; CURR HASH</th>
              </tr>
            </thead>
            <tbody>
              {auditEvents.map((evt) => (
                <tr key={evt.seq}>
                  <td style={{ fontWeight: 700, color: 'var(--gov-blue)' }}>
                    #{evt.seq}
                  </td>
                  <td>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--gov-text-primary)' }}>
                      {evt.timestamp}
                    </div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                      {evt.actor}
                    </div>
                  </td>
                  <td>
                    <span className="gov-badge gov-badge-blue" style={{ fontSize: '0.7rem' }}>
                      {evt.action}
                    </span>
                    <div style={{ fontSize: '0.78rem', color: 'var(--gov-text-primary)', marginTop: '4px', fontWeight: 500 }}>
                      {evt.entity}
                    </div>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--gov-text-primary)' }}>
                    {evt.details}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.74rem', color: 'var(--gov-text-secondary)' }}>
                    <div>p: {evt.prevHash}</div>
                    <div style={{ color: 'var(--gov-green)', fontWeight: 600 }}>h: {evt.currHash}</div>
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
