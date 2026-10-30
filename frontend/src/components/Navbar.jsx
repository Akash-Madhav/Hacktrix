import React, { useState } from 'react';
import { 
  Shield, Clock, FastForward, RotateCcw, UserCheck, 
  Activity, CheckCircle2, AlertTriangle, ChevronDown 
} from 'lucide-react';

export default function Navbar({ 
  currentTime, 
  onAdvanceClock, 
  onResetClock, 
  activeRole, 
  onSwitchRole, 
  clockLoading 
}) {
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);

  const roles = [
    { id: 'ADMIN', label: 'System Administrator', region: 'All-India' },
    { id: 'BUREAU_OFFICER', label: 'Bureau Head (AICTE HQ)', region: 'All-India' },
    { id: 'REGIONAL_OFFICER', label: 'Regional Officer (Western)', region: 'Western' },
    { id: 'SCRUTINY_OFFICER', label: 'Scrutiny Officer (Pune)', region: 'Western' },
    { id: 'INSTITUTION', label: 'College Registrar (Aryabhata)', region: 'Western' },
  ];

  const currentRoleObj = roles.find(r => r.id === activeRole) || roles[0];

  return (
    <header className="niriksha-navbar">
      <div className="nav-brand">
        <div className="brand-logo">
          <Shield className="logo-icon" />
          <span className="logo-badge">PS 26262</span>
        </div>
        <div className="brand-text">
          <h1 className="brand-title">NIRIKSHA</h1>
          <span className="brand-subtitle">AICTE Approval Control Room</span>
        </div>
      </div>

      {/* Injectable Clock & Fast-Forward Bar */}
      <div className="clock-control-bar">
        <div className="clock-display" title="Simulated Application Time Authority">
          <Clock className="clock-icon" />
          <span className="clock-label">Simulated Time:</span>
          <span className="clock-val">{currentTime || '01 October 2026, 09:00 AM'}</span>
        </div>

        <div className="fast-forward-actions">
          <button 
            className="ff-btn" 
            onClick={() => onAdvanceClock(1)} 
            disabled={clockLoading}
            title="Advance clock by 1 Day"
          >
            +1d
          </button>
          <button 
            className="ff-btn" 
            onClick={() => onAdvanceClock(7)} 
            disabled={clockLoading}
            title="Advance clock by 7 Days"
          >
            +7d
          </button>
          <button 
            className="ff-btn" 
            onClick={() => onAdvanceClock(15)} 
            disabled={clockLoading}
            title="Advance clock by 15 Days (Trigger SLA Overdue)"
          >
            +15d
          </button>
          <button 
            className="ff-btn highlight" 
            onClick={() => onAdvanceClock(30)} 
            disabled={clockLoading}
            title="Advance clock by 30 Days (Trigger Multi-Tier Escalations)"
          >
            <FastForward size={14} /> +30d
          </button>
          <button 
            className="ff-btn reset" 
            onClick={onResetClock} 
            disabled={clockLoading}
            title="Reset to Real-Time"
          >
            <RotateCcw size={13} />
          </button>
        </div>
      </div>

      {/* Role Switcher for Evaluator Demo */}
      <div className="nav-user-controls">
        <div className="role-dropdown-container">
          <button 
            className="role-selector-btn"
            onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
          >
            <UserCheck size={16} className="role-icon" />
            <div className="role-meta">
              <span className="role-name">{currentRoleObj.label}</span>
              <span className="role-region">{currentRoleObj.region}</span>
            </div>
            <ChevronDown size={14} />
          </button>

          {roleDropdownOpen && (
            <div className="role-dropdown-menu">
              <div className="dropdown-header">Switch Persona (Evaluator Demo)</div>
              {roles.map(r => (
                <div 
                  key={r.id} 
                  className={`dropdown-item ${activeRole === r.id ? 'active' : ''}`}
                  onClick={() => {
                    onSwitchRole(r.id);
                    setRoleDropdownOpen(false);
                  }}
                >
                  <span className="item-title">{r.label}</span>
                  <span className="item-sub">{r.region}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
