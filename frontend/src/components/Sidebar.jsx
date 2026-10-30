import React from 'react';
import { 
  LayoutDashboard, CheckSquare, Layers, GitBranch, 
  FileCheck2, CalendarClock, Users, Sliders, 
  ShieldCheck, FileSearch, MessageSquare, AlertCircle
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, counts, activeRole }) {
  const navItems = [
    { 
      id: 'overview', 
      label: 'Control Room Overview', 
      icon: LayoutDashboard,
      badge: counts?.kpis?.compliance_percentage ? `${counts.kpis.compliance_percentage}%` : null,
      badgeType: 'neutral'
    },
    { 
      id: 'actions', 
      label: "Today's Actions", 
      icon: CheckSquare,
      badge: counts?.actionsCount || 15,
      badgeType: 'urgent',
      roles: ['ADMIN', 'BUREAU_OFFICER', 'REGIONAL_OFFICER', 'SCRUTINY_OFFICER']
    },
    { 
      id: 'applications', 
      label: 'Applications Directory', 
      icon: Layers,
      badge: counts?.kpis?.total_monitored || 60,
      badgeType: 'default'
    },
    { 
      id: 'workflow', 
      label: 'Statechart Pathways', 
      icon: GitBranch,
      badge: '4 Pathways'
    },
    { 
      id: 'undertakings', 
      label: 'Undertakings Register', 
      icon: FileCheck2,
      badge: counts?.undertakingsCount || 11,
      badgeType: 'warning'
    },
    { 
      id: 'validity', 
      label: 'Validity & Expiry (T-30)', 
      icon: CalendarClock,
      badge: counts?.validityCount || 13,
      badgeType: 'warning'
    },
    { 
      id: 'evc', 
      label: 'EVC CP-SAT Optimizer', 
      icon: Users,
      badge: 'CP-SAT'
    },
    { 
      id: 'rules', 
      label: 'Rules Studio (SLM)', 
      icon: Sliders,
      badge: 'Rules as Code',
      roles: ['ADMIN', 'BUREAU_OFFICER']
    },
    { 
      id: 'audit', 
      label: 'Proof-Grade Audit Trail', 
      icon: ShieldCheck,
      badge: 'Tamper-Evident',
      badgeType: 'success'
    },
    { 
      id: 'forensics', 
      label: 'Document Forensics', 
      icon: FileSearch,
      badge: 'ISO 32000'
    },
    { 
      id: 'chat', 
      label: 'Ask BluePill Copilot', 
      icon: MessageSquare,
      badge: 'SLM'
    }
  ];

  return (
    <aside className="niriksha-sidebar">
      <div className="sidebar-group-title">OPERATIONAL CONTROL</div>
      <nav className="sidebar-nav">
        {navItems.map(item => {
          if (item.roles && !item.roles.includes(activeRole)) return null;
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              className={`nav-tab-btn ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <div className="tab-lead">
                <Icon size={18} className="tab-icon" />
                <span className="tab-label">{item.label}</span>
              </div>
              {item.badge && (
                <span className={`tab-badge ${item.badgeType || 'default'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="footer-card">
          <div className="footer-title">Human Oversight</div>
          <p className="footer-desc">Officials decide; NIRIKSHA ensures nothing is forgotten.</p>
        </div>
      </div>
    </aside>
  );
}
