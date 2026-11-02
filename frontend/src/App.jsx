import React, { useState, useEffect } from 'react';
import GovernmentHeader from './components/GovernmentHeader';
import GovernmentFooter from './components/GovernmentFooter';
import ApplicationTrackingView from './components/ApplicationTrackingView';
import InstitutionRecordsView from './components/InstitutionRecordsView';
import SLAAlertsView from './components/SLAAlertsView';
import AuditTrailView from './components/AuditTrailView';
import OverviewView from './components/OverviewView';

export default function App() {
  const getInitialTab = () => {
    const hash = window.location.hash.replace('#', '');
    if (['tracking', 'records', 'sla-alerts', 'audit-trail', 'overview', 'reports'].includes(hash)) {
      return hash;
    }
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab');
    if (tabParam && ['tracking', 'records', 'sla-alerts', 'audit-trail', 'overview', 'reports'].includes(tabParam)) {
      return tabParam;
    }
    return 'tracking'; // Default to highest priority Tracking view matching screenshot 1
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());
  const [colleges, setColleges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // Sync hash changes
  const handleSelectTab = (tabId) => {
    setActiveTab(tabId);
    window.location.hash = tabId;
  };

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (['tracking', 'records', 'sla-alerts', 'audit-trail', 'overview', 'reports'].includes(hash)) {
        setActiveTab(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Fetch real colleges from the API if available
  const fetchColleges = () => {
    setLoading(true);
    fetch('/api/colleges')
      .then((res) => {
        if (!res.ok) throw new Error('API unavailable');
        return res.json();
      })
      .then((data) => {
        setColleges(data || []);
        setLoading(false);
      })
      .catch((err) => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchColleges();
  }, []);

  const handleSelectRecord = (rec) => {
    setSelectedRecord(rec);
    handleSelectTab('tracking');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--gov-bg)' }}>
      {/* Government Blue Header & Navigation Bar */}
      <GovernmentHeader activeTab={activeTab} onSelectTab={handleSelectTab} />

      {/* Main Page Content */}
      <div style={{ flex: 1 }}>
        {activeTab === 'tracking' && (
          <ApplicationTrackingView applications={colleges} selectedRecord={selectedRecord} />
        )}

        {activeTab === 'records' && (
          <InstitutionRecordsView onSelectRecord={handleSelectRecord} colleges={colleges} />
        )}

        {activeTab === 'sla-alerts' && (
          <SLAAlertsView />
        )}

        {activeTab === 'audit-trail' && (
          <AuditTrailView />
        )}

        {activeTab === 'overview' && (
          <OverviewView onNavigate={handleSelectTab} />
        )}

        {activeTab === 'reports' && (
          <OverviewView onNavigate={handleSelectTab} />
        )}
      </div>

      {/* Official Footer */}
      <GovernmentFooter activeTab={activeTab} />
    </div>
  );
}
