import React, { useState } from 'react';
import { 
  Search, Filter, Layers, MapPin, Building, 
  ExternalLink, ChevronRight, CheckCircle, Clock, AlertTriangle, Flame
} from 'lucide-react';

export default function ApplicationsList({ applications, onSelectApplication, onOpenExplain }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('ALL');
  const [selectedStage, setSelectedStage] = useState('ALL');
  const [selectedSla, setSelectedSla] = useState('ALL');

  const filtered = applications.filter(app => {
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchName = (app.institution_name || '').toLowerCase().includes(q);
      const matchNum = (app.application_number || '').toLowerCase().includes(q);
      const matchPerm = (app.institution_permanent_id || '').toLowerCase().includes(q);
      if (!matchName && !matchNum && !matchPerm) return false;
    }
    if (selectedRegion !== 'ALL' && app.region !== selectedRegion) return false;
    if (selectedStage !== 'ALL' && app.current_stage !== selectedStage) return false;
    if (selectedSla !== 'ALL' && app.sla_status !== selectedSla) return false;
    return true;
  });

  return (
    <div className="applications-view">
      <div className="view-header">
        <div>
          <h2 className="view-title">Applications Directory (60 Institutional Dossiers)</h2>
          <p className="view-desc">
            Complete registry of technical education applications under APH 2024-27 pathways with real AICTE identifiers.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-controls-card">
        <div className="search-input-box">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search by Institution Name, Application No (1-XXXXXXX), Permanent ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="select-filters-row">
          <div className="filter-select-group">
            <label>Region:</label>
            <select value={selectedRegion} onChange={(e) => setSelectedRegion(e.target.value)}>
              <option value="ALL">All Regions (8)</option>
              <option value="Western">Western</option>
              <option value="Northern">Northern</option>
              <option value="Southern">Southern</option>
              <option value="South-Western">South-Western</option>
              <option value="Eastern">Eastern</option>
              <option value="Central">Central</option>
              <option value="North-Western">North-Western</option>
            </select>
          </div>

          <div className="filter-select-group">
            <label>Workflow Stage:</label>
            <select value={selectedStage} onChange={(e) => setSelectedStage(e.target.value)}>
              <option value="ALL">All Stages</option>
              <option value="INITIAL_SCRUTINY">Initial Scrutiny</option>
              <option value="RE_SCRUTINY">Re-Scrutiny</option>
              <option value="EVC_INSPECTION">EVC Inspection</option>
              <option value="REGIONAL_COMMITTEE">Regional Committee</option>
              <option value="SAC_SHC">SAC / SHC Appeal</option>
              <option value="RETURNED_FOR_CORRECTION">Returned for Correction</option>
              <option value="APPROVED">Approved (EoA Granted)</option>
            </select>
          </div>

          <div className="filter-select-group">
            <label>SLA Status:</label>
            <select value={selectedSla} onChange={(e) => setSelectedSla(e.target.value)}>
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active (On-Track)</option>
              <option value="DUE_SOON">Due Soon (&le; 3d)</option>
              <option value="OVERDUE">Overdue Breach</option>
              <option value="ESCALATED">Escalated (L1/L2)</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>

          <div className="filter-count ml-auto">
            Showing <strong>{filtered.length}</strong> of {applications.length} dossiers
          </div>
        </div>
      </div>

      {/* Grid of Institutional Dossier Cards */}
      <div className="apps-grid">
        {filtered.map(app => {
          const isEscalated = app.sla_status === 'ESCALATED';
          const isOverdue = app.sla_status === 'OVERDUE';
          const isDueSoon = app.sla_status === 'DUE_SOON';
          const isApproved = app.current_stage === 'APPROVED';

          return (
            <div key={app.id} className="app-card">
              <div className="app-card-header">
                <div>
                  <span className="app-card-id">{app.application_number}</span>
                  <span className="app-card-perm">Perm ID: {app.institution_permanent_id || '1-XXXXXX'}</span>
                </div>
                <span className={`status-pill ${
                  isEscalated ? 'pill-purple' : 
                  (isOverdue ? 'pill-danger' : 
                  (isDueSoon ? 'pill-warning' : 
                  (isApproved ? 'pill-success' : 'pill-neutral')))
                }`}>
                  {app.sla_status}
                </span>
              </div>

              <h4 className="app-card-title">{app.institution_name}</h4>

              <div className="app-card-meta">
                <div className="meta-item">
                  <MapPin size={13} />
                  <span>{app.district}, {app.state} ({app.region})</span>
                </div>
                <div className="meta-item">
                  <Building size={13} />
                  <span>{app.institution_type.replace(/_/g, ' ')}</span>
                </div>
              </div>

              <div className="app-card-stage-strip">
                <span className="stage-label">Current Stage:</span>
                <span className="stage-val">{app.current_stage.replace(/_/g, ' ')}</span>
              </div>

              <div className="app-card-actions">
                <button 
                  className="btn-card-primary"
                  onClick={() => onSelectApplication(app.id)}
                >
                  View Dossier <ChevronRight size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
