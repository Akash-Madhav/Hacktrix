import React, { useState } from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert, CheckCircle2, RotateCw, Play, Lock } from 'lucide-react';

export default function AuditLedgerView({ ledger, onVerifyChain, verifyResult, onSimulateTamper }) {
  const [verifying, setVerifying] = useState(false);

  const handleVerify = () => {
    setVerifying(true);
    onVerifyChain();
    setTimeout(() => setVerifying(false), 300);
  };

  return (
    <div className="audit-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Proof-Grade Audit Ledger (PROVE)</h2>
          <p className="view-desc">
            Schneier-Kelsey (1999) style tamper-evident hash-chained secure ledger: $h_i = \text{SHA-256}(h_{i-1} \parallel \text{event}_i)$.
            Guarantees accountability without expensive blockchain overhead.
          </p>
        </div>

        <div className="audit-actions-bar">
          <button 
            className="btn-primary" 
            onClick={handleVerify}
            disabled={verifying}
          >
            <ShieldCheck size={16} className="mr-1" />
            {verifying ? 'Recomputing SHA-256 Chain...' : 'Verify Audit Chain'}
          </button>

          <button 
            className="btn-danger-outline" 
            onClick={onSimulateTamper}
            title="Controlled Evaluator Test: Alter a past record to prove detection"
          >
            <AlertTriangle size={15} className="mr-1" />
            Simulate Controlled Record Tamper
          </button>
        </div>
      </div>

      {/* Verification Status Banner */}
      {verifyResult && (
        <div className={`verification-banner ${verifyResult.is_valid ? 'valid' : 'invalid'}`}>
          <div className="banner-icon">
            {verifyResult.is_valid ? (
              <CheckCircle2 size={24} className="text-emerald" />
            ) : (
              <ShieldAlert size={24} className="text-rose" />
            )}
          </div>
          <div className="banner-details">
            <h4 className="banner-title">
              {verifyResult.is_valid ? 'Audit Chain Cryptographically Verified (100% Integrity)' : 'TAMPER DETECTED: Chain Verification Failed!'}
            </h4>
            <p className="banner-desc">{verifyResult.message}</p>
            {verifyResult.first_broken_sequence && (
              <div className="broken-seq-tag">
                First Corrupted Record: Sequence #{verifyResult.first_broken_sequence}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="panel-card">
        <div className="panel-header">
          <h3 className="panel-title">Immutable Event Stream</h3>
          <span className="text-muted text-xs font-mono">Genesis Hash: 000000000000...</span>
        </div>

        <table className="niriksha-table">
          <thead>
            <tr>
              <th>Seq #</th>
              <th>Timestamp</th>
              <th>Event Type</th>
              <th>Entity</th>
              <th>Actor Role</th>
              <th>Action Summary</th>
              <th>Previous SHA-256</th>
              <th>Current Hash ($h_i$)</th>
              <th>Integrity</th>
            </tr>
          </thead>
          <tbody>
            {ledger.map(row => (
              <tr key={row.sequence_number} className={row.is_tampered ? 'tampered-row' : ''}>
                <td className="font-mono font-bold">#{row.sequence_number}</td>
                <td className="text-muted text-xs">
                  {row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : 'N/A'}
                </td>
                <td>
                  <span className="badge-highlight">{row.event_type}</span>
                </td>
                <td className="font-mono text-xs">{row.entity_id.slice(0, 12)}...</td>
                <td>{row.actor_role}</td>
                <td className="desc-cell" title={row.action_summary}>{row.action_summary}</td>
                <td className="font-mono text-xs text-muted" title={row.previous_hash}>{row.previous_hash}</td>
                <td className="font-mono text-xs text-purple" title={row.full_current_hash}>{row.current_hash}</td>
                <td>
                  {row.is_tampered ? (
                    <span className="status-pill pill-danger">ALTERED</span>
                  ) : (
                    <span className="status-pill pill-success"><Lock size={11} className="mr-1" /> VALID</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
