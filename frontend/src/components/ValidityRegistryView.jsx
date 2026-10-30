import React, { useState } from 'react';
import { CalendarClock, AlertTriangle, CheckCircle, FileText, Download, BellRing } from 'lucide-react';

export default function ValidityRegistryView({ records }) {
  const [filterType, setFilterType] = useState('ALL');

  const filtered = records.filter(r => {
    if (filterType !== 'ALL' && r.document_type !== filterType) return false;
    return true;
  });

  return (
    <div className="validity-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Validity &amp; Document Expiry Registry (T-30 / 15 / 7 / 1)</h2>
          <p className="view-desc">
            Four automatic warnings before any lease deed, Fire NOC, or statutory certificate lapses. Prevents institutions operating with quietly expired paperwork.
          </p>
        </div>
        <div className="filter-chip-group">
          {['ALL', 'LEASE_DEED', 'FIRE_SAFETY_NOC'].map(t => (
            <button
              key={t}
              className={`filter-chip ${filterType === t ? 'active' : ''}`}
              onClick={() => setFilterType(t)}
            >
              {t.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="panel-card">
        <table className="niriksha-table">
          <thead>
            <tr>
              <th>Document Type</th>
              <th>Certificate / Lease No</th>
              <th>Institution</th>
              <th>Issuing Authority</th>
              <th>Expiry Date</th>
              <th>Days Until Expiry</th>
              <th>Advance Alert Stage</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(r => {
              const isOverdue = r.is_overdue || r.status === 'OVERDUE_EXPIRED';
              const isExpiring = r.status === 'EXPIRING_SOON';

              return (
                <tr key={r.id}>
                  <td className="font-semibold text-purple">{r.document_type.replace(/_/g, ' ')}</td>
                  <td className="font-mono">{r.certificate_number}</td>
                  <td>{r.institution_name}</td>
                  <td className="text-muted text-xs">{r.issuing_authority}</td>
                  <td>{r.expiry_date ? new Date(r.expiry_date).toLocaleDateString() : 'N/A'}</td>
                  <td>
                    <span className={isOverdue ? 'text-rose font-bold' : (isExpiring ? 'text-amber font-semibold' : 'text-emerald')}>
                      {isOverdue ? `EXPIRED (${Math.abs(r.days_until_expiry)}d ago)` : `${r.days_until_expiry} days`}
                    </span>
                  </td>
                  <td>
                    {r.last_reminder_offset ? (
                      <span className="reminder-pill">
                        <BellRing size={12} className="mr-1" />
                        {r.last_reminder_offset} Dispatched
                      </span>
                    ) : (
                      <span className="text-muted text-xs">Scheduled</span>
                    )}
                  </td>
                  <td>
                    <span className={`status-pill ${isOverdue ? 'pill-danger' : (isExpiring ? 'pill-warning' : 'pill-success')}`}>
                      {r.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
