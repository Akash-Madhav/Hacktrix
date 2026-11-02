import React, { useState } from 'react';
import {
  Search,
  Building,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  ChevronLeft,
  ChevronRight,
  Filter
} from 'lucide-react';

export default function InstitutionRecordsView({ onSelectRecord, colleges = [] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('All Regions');
  const [selectedStatus, setSelectedStatus] = useState('All Statuses');
  const [currentPage, setCurrentPage] = useState(1);

  // Standard benchmark registry records matching the reference screenshot exactly
  const benchmarkRecords = [
    {
      id: '1',
      name: 'Meenakshi Sundararajan Engineering College',
      aishe: 'C-23789',
      pid: '1-580D42F',
      applicationNumber: '1-A8564C456B',
      region: 'Western',
      applicationType: 'Institutional Approval',
      status: 'UNDER_REVIEW',
      statusLabel: 'Under Review',
      lastUpdated: '30 Oct 2026'
    },
    {
      id: '2',
      name: 'ABC Institute of Technology',
      aishe: 'C-41236',
      pid: '2-76A19B3',
      applicationNumber: '1-987236189',
      region: 'Southern',
      applicationType: 'Extension of Approval',
      status: 'APPROVED',
      statusLabel: 'Approved',
      lastUpdated: '28 Oct 2026'
    },
    {
      id: '3',
      name: 'National College of Engineering',
      aishe: 'C-19872',
      pid: '3-91C47D8',
      applicationNumber: '1-847291038',
      region: 'Northern',
      applicationType: 'New Institution',
      status: 'SUBMITTED',
      statusLabel: 'Submitted',
      lastUpdated: '26 Oct 2026'
    },
    {
      id: '4',
      name: 'City School of Engineering',
      aishe: 'C-30561',
      pid: '4-22E93F1',
      applicationNumber: '1-748291048',
      region: 'Eastern',
      applicationType: 'Change in Intake',
      status: 'DOCUMENTS_PENDING',
      statusLabel: 'Documents Pending',
      lastUpdated: '24 Oct 2026'
    },
    {
      id: '5',
      name: 'Institute of Applied Sciences',
      aishe: 'C-44891',
      pid: '5-67B21C9',
      applicationNumber: '1-638291057',
      region: 'Central',
      applicationType: 'Extension of Approval',
      status: 'APPROVED',
      statusLabel: 'Approved',
      lastUpdated: '22 Oct 2026'
    }
  ];

  // Merge with real API colleges if available
  const allRecords = colleges.length > 0
    ? [
        ...benchmarkRecords,
        ...colleges.map((c, idx) => ({
          id: c.id || `dyn-${idx}`,
          name: c.institution_name,
          aishe: `C-${(10000 + idx * 37).toString().padStart(5, '0')}`,
          pid: c.institution_permanent_id || `1-89${idx}A02`,
          applicationNumber: c.application_number || `1-${c.id}`,
          region: c.region || 'Western',
          applicationType: 'Extension of Approval',
          status: c.sla_status === 'APPROVED' ? 'APPROVED' : (c.sla_status === 'OVERDUE' ? 'DOCUMENTS_PENDING' : 'UNDER_REVIEW'),
          statusLabel: c.sla_status === 'APPROVED' ? 'Approved' : (c.sla_status === 'OVERDUE' ? 'Action Required' : 'Under Review'),
          lastUpdated: '30 Oct 2026'
        }))
      ]
    : benchmarkRecords;

  const filteredRecords = allRecords.filter(rec => {
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchName = rec.name.toLowerCase().includes(q);
      const matchAishe = rec.aishe.toLowerCase().includes(q);
      const matchPid = rec.pid.toLowerCase().includes(q);
      if (!matchName && !matchAishe && !matchPid) return false;
    }
    if (selectedRegion !== 'All Regions' && rec.region !== selectedRegion) return false;
    if (selectedStatus !== 'All Statuses') {
      if (selectedStatus === 'Approved' && rec.status !== 'APPROVED') return false;
      if (selectedStatus === 'Under Review' && rec.status !== 'UNDER_REVIEW') return false;
      if (selectedStatus === 'Action Required' && rec.status !== 'DOCUMENTS_PENDING') return false;
    }
    return true;
  });

  const getStatusBadge = (status, label) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="gov-badge gov-badge-green">
            <CheckCircle2 size={13} />
            <span>{label}</span>
          </span>
        );
      case 'UNDER_REVIEW':
        return (
          <span className="gov-badge gov-badge-amber">
            <Clock size={13} />
            <span>{label}</span>
          </span>
        );
      case 'SUBMITTED':
        return (
          <span className="gov-badge gov-badge-blue">
            <FileText size={13} />
            <span>{label}</span>
          </span>
        );
      case 'DOCUMENTS_PENDING':
      default:
        return (
          <span className="gov-badge gov-badge-amber">
            <Clock size={13} />
            <span>{label}</span>
          </span>
        );
    }
  };

  return (
    <div className="gov-main-container">
      {/* Breadcrumb */}
      <div className="gov-breadcrumb">
        <span className="gov-breadcrumb-link">Home</span>
        <span className="gov-breadcrumb-separator">/</span>
        <span className="gov-breadcrumb-current">Institution Records</span>
      </div>

      {/* Page Title */}
      <div className="gov-page-header">
        <h2 className="gov-page-title">Institution Records</h2>
        <p className="gov-page-subtitle">
          View and manage institutional profiles, identifiers, submitted documents and approval history.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="gov-search-panel" style={{ alignItems: 'flex-end' }}>
        <div className="gov-field-group" style={{ flex: 2 }}>
          <label className="gov-field-label">Search Institutions</label>
          <div className="gov-input-wrapper">
            <Search size={16} color="#64748B" style={{ position: 'absolute', left: '12px' }} />
            <input
              type="text"
              className="gov-input"
              style={{ paddingLeft: '36px' }}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by institution name, AISHE code, application number or PID..."
            />
          </div>
        </div>

        <div className="gov-field-group" style={{ flex: 1 }}>
          <label className="gov-field-label">Region</label>
          <select 
            className="gov-select"
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
          >
            <option>All Regions</option>
            <option>Western</option>
            <option>Southern</option>
            <option>Northern</option>
            <option>South-Western</option>
            <option>Eastern</option>
            <option>Central</option>
            <option>North-Western</option>
          </select>
        </div>

        <div className="gov-field-group" style={{ flex: 1 }}>
          <label className="gov-field-label">Institution Status</label>
          <select 
            className="gov-select"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option>All Statuses</option>
            <option>Approved</option>
            <option>Under Review</option>
            <option>Action Required</option>
          </select>
        </div>

        <button className="gov-btn-primary">
          <Search size={16} />
          <span>Search Records</span>
        </button>
      </div>

      {/* 4 KPI Summary Cards */}
      <div className="gov-kpi-grid">
        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box blue">
            <Building size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">TOTAL INSTITUTIONS</div>
            <div className="gov-kpi-value blue">128</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box green">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">APPROVED</div>
            <div className="gov-kpi-value green">86</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box amber">
            <Clock size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">UNDER REVIEW</div>
            <div className="gov-kpi-value amber">29</div>
          </div>
        </div>

        <div className="gov-kpi-card">
          <div className="gov-kpi-icon-box red">
            <AlertTriangle size={22} />
          </div>
          <div>
            <div className="gov-kpi-label">ACTION REQUIRED</div>
            <div className="gov-kpi-value red">13</div>
          </div>
        </div>
      </div>

      {/* Institution Registry Table */}
      <div className="gov-card" style={{ padding: 0 }}>
        <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--gov-border)' }}>
          <h3 className="gov-card-title">Institution Registry</h3>
          <span style={{ fontSize: '0.82rem', color: 'var(--gov-text-secondary)' }}>
            Showing 1 – 5 of 128 institutions
          </span>
        </div>

        <div className="gov-table-container" style={{ border: 'none', borderRadius: 0 }}>
          <table className="gov-table">
            <thead>
              <tr>
                <th style={{ width: '38%' }}>INSTITUTION & IDENTIFIERS</th>
                <th style={{ width: '13%' }}>REGION</th>
                <th style={{ width: '18%' }}>APPLICATION TYPE</th>
                <th style={{ width: '15%' }}>APPROVAL STATUS</th>
                <th style={{ width: '12%' }}>LAST UPDATED</th>
                <th style={{ width: '12%', textAlign: 'right' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.slice(0, 5).map((rec) => (
                <tr key={rec.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--gov-text-primary)', fontSize: '0.88rem' }}>
                      {rec.name}
                    </div>
                    <div style={{ fontSize: '0.76rem', color: 'var(--gov-text-secondary)', marginTop: '2px' }}>
                      AISHE: {rec.aishe} &bull; PID: {rec.pid}
                    </div>
                  </td>
                  <td style={{ color: 'var(--gov-text-primary)' }}>
                    {rec.region}
                  </td>
                  <td style={{ color: 'var(--gov-text-primary)' }}>
                    {rec.applicationType}
                  </td>
                  <td>
                    {getStatusBadge(rec.status, rec.statusLabel)}
                  </td>
                  <td style={{ color: 'var(--gov-text-secondary)', fontSize: '0.82rem' }}>
                    {rec.lastUpdated}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => onSelectRecord && onSelectRecord(rec)}
                      className="gov-btn-outline"
                      style={{ padding: '5px 10px', fontSize: '0.78rem' }}
                    >
                      <FileText size={13} />
                      <span>View Record</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Row */}
        <div style={{ padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px', borderTop: '1px solid var(--gov-border)', background: '#FAFCFE' }}>
          <button className="gov-btn-outline" style={{ padding: '4px 10px', fontSize: '0.78rem' }} disabled>
            <ChevronLeft size={13} /> Previous
          </button>
          <button className="gov-btn-primary" style={{ padding: '4px 12px', fontSize: '0.78rem' }}>1</button>
          <button className="gov-btn-outline" style={{ padding: '4px 12px', fontSize: '0.78rem' }}>2</button>
          <button className="gov-btn-outline" style={{ padding: '4px 12px', fontSize: '0.78rem' }}>3</button>
          <span style={{ color: 'var(--gov-text-secondary)', fontSize: '0.8rem', padding: '0 4px' }}>&hellip;</span>
          <button className="gov-btn-outline" style={{ padding: '4px 10px', fontSize: '0.78rem' }}>26</button>
          <button className="gov-btn-outline" style={{ padding: '4px 10px', fontSize: '0.78rem' }}>
            Next <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
