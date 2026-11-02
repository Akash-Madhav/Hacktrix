import React from 'react';
import {
  Landmark,
  Home,
  FileSearch,
  Building,
  Bell,
  ShieldCheck,
  BarChart3,
  Globe,
  HelpCircle,
  Eye,
  User,
  ChevronDown
} from 'lucide-react';

export default function GovernmentHeader({ activeTab, onSelectTab }) {
  const navItems = [
    { id: 'overview', label: 'Home', icon: Home },
    { id: 'tracking', label: 'Application Tracking', icon: FileSearch },
    { id: 'records', label: 'Institution Records', icon: Building },
    { id: 'sla-alerts', label: 'SLA & Alerts', icon: Bell },
    { id: 'audit-trail', label: 'Audit Trail', icon: ShieldCheck },
    { id: 'reports', label: 'Reports', icon: BarChart3 },
  ];

  return (
    <>
      {/* Top Government Blue Header */}
      <header className="gov-top-header">
        <div className="gov-branding">
          <div className="gov-emblem-icon">
            <Landmark size={32} />
          </div>
          <div className="gov-title-group">
            <h1>NIRIKSHA</h1>
            <p>AICTE Institutional Approval Monitoring Portal</p>
          </div>
        </div>

        <div className="gov-badge-center">
          OFFICIAL WORKFLOW PORTAL &bull; PROTOTYPE
        </div>

        <div className="gov-utilities-right">
          <button className="gov-util-link" title="Accessibility Options">
            <Eye size={15} />
            <span>Accessibility</span>
          </button>

          <div className="gov-util-link">
            <Globe size={15} />
            <span>English</span>
            <ChevronDown size={13} />
          </div>

          <button className="gov-util-link" title="Help & Documentation">
            <HelpCircle size={15} />
            <span>Help</span>
          </button>

          <button className="gov-officer-login-btn">
            <User size={15} />
            <span>Officer Login</span>
          </button>
        </div>
      </header>

      {/* Primary White Navigation Bar */}
      <nav className="gov-nav-bar">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`gov-nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}
