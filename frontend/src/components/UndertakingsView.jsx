import React, { useState } from 'react';
import { FileCheck2, Clock, CheckCircle2, AlertTriangle, ShieldCheck, X } from 'lucide-react';

export default function UndertakingsView({ undertakings, onVerifyUndertaking }) {
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [verifyModalUndertaking, setVerifyModalUndertaking] = useState(null);
  const [verificationNotes, setVerificationNotes] = useState('');

  const filtered = undertakings.filter(u => {
    if (selectedStatus !== 'ALL' && u.compliance_status !== selectedStatus) return false;
    return true;
  });

  const handleVerify = (status) => {
    if (!verifyModalUndertaking) return;
    onVerifyUndertaking(verifyModalUndertaking.id, status, verificationNotes);
    setVerifyModalUndertaking(null);
  };

  return (
    <div className="undertakings-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Time-Bound Undertakings Register (WATCH)</h2>
          <p className="view-desc">
            Tracks promises attached to approval letters (e.g. "Recommended for EoA with undertaking for recruitment") to prevent institutions operating with lapsed commitments.
          </p>
        </div>
        <div className="filter-chip-group">
          {['ALL', 'PENDING', 'VERIFIED', 'BREACHED'].map(st => (
            <button
              key={st}
              className={`filter-chip ${selectedStatus === st ? 'active' : ''}`}
              onClick={() => setSelectedStatus(st)}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <div className="panel-card">
        <table className="niriksha-table">
          <thead>
            <tr>
              <th>Undertaking No</th>
              <th>Institution</th>
              <th>Category</th>
              <th>Obligation Description</th>
              <th>Due Date</th>
              <th>Days Left</th>
              <th>Compliance Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(u => {
              const isBreached = u.compliance_status === 'BREACHED' || u.is_overdue;
              const isVerified = u.compliance_status === 'VERIFIED';

              return (
                <tr key={u.id}>
                  <td className="font-mono text-purple">{u.undertaking_number}</td>
                  <td className="font-medium">{u.institution_name}</td>
                  <td><span className="badge-highlight">{u.category.replace(/_/g, ' ')}</span></td>
                  <td className="desc-cell" title={u.undertaking_text}>{u.undertaking_text}</td>
                  <td>{u.due_date ? new Date(u.due_date).toLocaleDateString() : 'N/A'}</td>
                  <td>
                    <span className={isBreached ? 'text-rose font-bold' : (u.days_remaining <= 15 ? 'text-amber' : 'text-emerald')}>
                      {u.days_remaining} days
                    </span>
                  </td>
                  <td>
                    <span className={`status-pill ${isVerified ? 'pill-success' : (isBreached ? 'pill-danger' : 'pill-warning')}`}>
                      {u.compliance_status}
                    </span>
                  </td>
                  <td>
                    {!isVerified && (
                      <button 
                        className="btn-sm btn-primary"
                        onClick={() => {
                          setVerifyModalUndertaking(u);
                          setVerificationNotes('');
                        }}
                      >
                        Review &amp; Verify
                      </button>
                    )}
                    {isVerified && <span className="text-muted text-xs">Verified</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Verification Modal */}
      {verifyModalUndertaking && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3 className="modal-title">Verify Undertaking Compliance</h3>
              <button className="modal-close-btn" onClick={() => setVerifyModalUndertaking(null)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Institution:</label>
                <input type="text" className="form-input" value={verifyModalUndertaking.institution_name} disabled />
              </div>
              <div className="form-group">
                <label className="form-label">Obligation:</label>
                <textarea className="form-textarea" rows={3} value={verifyModalUndertaking.undertaking_text} disabled />
              </div>
              <div className="form-group">
                <label className="form-label">Verification Comments:</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Enter scrutiny officer verification remarks..."
                  value={verificationNotes}
                  onChange={(e) => setVerificationNotes(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-danger" onClick={() => handleVerify('BREACHED')}>
                Flag as Breached
              </button>
              <button className="btn-success" onClick={() => handleVerify('VERIFIED')}>
                Approve &amp; Mark Verified
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
