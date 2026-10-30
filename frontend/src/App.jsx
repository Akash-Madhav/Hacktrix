import React, { useState, useEffect } from 'react';
import {
  Building2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  XCircle,
  Plus,
  Search,
  Filter,
  ArrowRight,
  RotateCcw,
  Trash2,
  Eye,
  RefreshCw,
  Calendar,
  ShieldCheck,
  ChevronRight,
  X,
  Sparkles,
  Bot
} from 'lucide-react';

export default function App() {
  const [colleges, setColleges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRegion, setFilterRegion] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  
  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showTimelineModal, setShowTimelineModal] = useState(false);
  const [showAiModal, setShowAiModal] = useState(false);
  const [selectedCollege, setSelectedCollege] = useState(null);
  
  // Transitions state
  const [transitionStage, setTransitionStage] = useState('');
  const [transitionReason, setTransitionReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // AI Update state
  const [aiCollegeQuery, setAiCollegeQuery] = useState('');
  const [aiUpdateText, setAiUpdateText] = useState('');
  const [aiResult, setAiResult] = useState(null);
  const [aiSubmitting, setAiSubmitting] = useState(false);

  // New college form state
  const [newCollege, setNewCollege] = useState({
    institution_name: '',
    region: 'Western',
    state: 'Maharashtra',
    district: 'Pune',
    institution_type: 'ENGINEERING_TECH',
    current_stage: 'INITIAL_SCRUTINY',
    sla_working_days: 15
  });

  // Fetch all colleges
  const fetchColleges = () => {
    setLoading(true);
    fetch('/api/colleges')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch colleges');
        return res.json();
      })
      .then(data => {
        setColleges(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching colleges:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchColleges();
  }, []);

  // Fetch single college details for timeline
  const openCollegeDetails = (collegeId) => {
    fetch(`/api/colleges/${collegeId}`)
      .then(async res => {
        if (!res.ok) {
          const errText = await res.text();
          throw new Error(errText || `Server returned ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        setSelectedCollege(data);
        setShowTimelineModal(true);
      })
      .catch(err => alert('Failed to load college details: ' + (err.message || err)));
  };

  // Handle register college submit
  const handleRegisterCollege = (e) => {
    e.preventDefault();
    if (!newCollege.institution_name.trim()) {
      alert('Please enter college name');
      return;
    }
    setSubmitting(true);
    fetch('/api/colleges', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newCollege)
    })
      .then(res => res.json())
      .then(data => {
        setSubmitting(false);
        setShowAddModal(false);
        setNewCollege({
          institution_name: '',
          region: 'Western',
          state: 'Maharashtra',
          district: 'Pune',
          institution_type: 'ENGINEERING_TECH',
          current_stage: 'INITIAL_SCRUTINY',
          sla_working_days: 15
        });
        fetchColleges();
      })
      .catch(err => {
        alert('Failed to register college: ' + err);
        setSubmitting(false);
      });
  };

  // Handle manual stage transition
  const handleTransition = (e) => {
    e.preventDefault();
    if (!transitionStage) {
      alert('Please select target stage');
      return;
    }
    setSubmitting(true);
    fetch(`/api/colleges/${selectedCollege.id}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        to_stage: transitionStage,
        reason: transitionReason || 'Stage advanced by Admin',
        actor: 'Admin / Scrutiny Officer'
      })
    })
      .then(res => res.json())
      .then(data => {
        setSubmitting(false);
        setTransitionStage('');
        setTransitionReason('');
        // Refresh details
        openCollegeDetails(selectedCollege.id);
        fetchColleges();
      })
      .catch(err => {
        alert('Failed to update stage: ' + err);
        setSubmitting(false);
      });
  };

  // Handle AI-powered natural language update
  const handleAiUpdate = (e) => {
    e.preventDefault();
    if (!aiCollegeQuery.trim() || !aiUpdateText.trim()) {
      alert('Please provide the college name and update note.');
      return;
    }
    setAiSubmitting(true);
    setAiResult(null);

    fetch('/api/colleges/ai-update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        college_name: aiCollegeQuery,
        update_text: aiUpdateText
      })
    })
      .then(async res => {
        if (!res.ok) {
          const errData = await res.json().catch(() => null);
          throw new Error(errData?.detail || `Error ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        setAiResult(data);
        setAiSubmitting(false);
        fetchColleges(); // Refresh main list
      })
      .catch(err => {
        alert('AI Update Error: ' + err.message);
        setAiSubmitting(false);
      });
  };

  // Handle delete college
  const handleDeleteCollege = (collegeId, name) => {
    if (!window.confirm(`Are you sure you want to remove '${name}' from monitoring?`)) return;
    fetch(`/api/colleges/${collegeId}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(() => {
        if (selectedCollege && selectedCollege.id === collegeId) {
          setShowTimelineModal(false);
        }
        fetchColleges();
      })
      .catch(err => alert('Failed to delete: ' + err));
  };

  // Handle purge database
  const handlePurgeAll = () => {
    if (!window.confirm('WARNING: This will completely empty all college records in the database. Proceed?')) return;
    fetch('/api/colleges/purge-all', { method: 'POST' })
      .then(res => res.json())
      .then(() => {
        fetchColleges();
        setShowTimelineModal(false);
      })
      .catch(err => alert('Purge failed: ' + err));
  };

  // Derived KPI calculations
  const totalCount = colleges.length;
  const onTrackCount = colleges.filter(c => c.sla_status === 'ON_TRACK').length;
  const dueSoonCount = colleges.filter(c => c.sla_status === 'DUE_SOON').length;
  const overdueCount = colleges.filter(c => c.sla_status === 'OVERDUE' || c.sla_status === 'ESCALATED').length;
  const approvedCount = colleges.filter(c => c.sla_status === 'APPROVED').length;

  // Filtered colleges list
  const filteredColleges = colleges.filter(c => {
    const matchesSearch = c.institution_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.application_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.institution_permanent_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRegion = filterRegion === 'ALL' || c.region === filterRegion;
    const matchesStatus = filterStatus === 'ALL' || c.sla_status === filterStatus;
    return matchesSearch && matchesRegion && matchesStatus;
  });

  const getStatusBadge = (status, remDays) => {
    switch (status) {
      case 'ON_TRACK':
        return <span style={{ padding: '4px 10px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><CheckCircle2 size={12} /> ON TRACK ({remDays}d left)</span>;
      case 'DUE_SOON':
        return <span style={{ padding: '4px 10px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><AlertTriangle size={12} /> DUE SOON ({remDays}d left)</span>;
      case 'OVERDUE':
        return <span style={{ padding: '4px 10px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(244, 63, 94, 0.15)', color: '#f43f5e', border: '1px solid rgba(244, 63, 94, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Clock size={12} /> OVERDUE ({Math.abs(remDays)}d delay)</span>;
      case 'APPROVED':
        return <span style={{ padding: '4px 10px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><ShieldCheck size={12} /> APPROVED</span>;
      default:
        return <span style={{ padding: '4px 10px', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600, background: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' }}>{status}</span>;
    }
  };

  const getStageLabel = (stage) => {
    const map = {
      SUBMITTED: '1. Application Submitted',
      INITIAL_SCRUTINY: '2. Document Scrutiny',
      TECHNICAL_REVIEW: '3. Technical Review',
      EVC_INSPECTION: '4. EVC Inspection',
      REGIONAL_REVIEW: '5. Regional Review',
      APPROVED: '6. Bureau Approved',
      REJECTED: 'Rejected'
    };
    return map[stage] || stage;
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0a0e17', color: '#f8fafc', paddingBottom: '60px' }}>
      
      {/* Top Header */}
      <header style={{ borderBottom: '1px solid rgba(148, 163, 184, 0.12)', background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 30, padding: '16px 32px' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'linear-gradient(135deg, #0284c7, #38bdf8)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px rgba(56, 189, 248, 0.3)' }}>
              <Building2 color="#fff" size={24} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ fontSize: '1.35rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#fff' }}>NIRIKSHA</h1>
                <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', fontWeight: 600 }}>APPROVAL MONITOR</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>AICTE Institutional Workflow, Lifecycle & SLA Monitoring Platform</p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => { setShowAiModal(true); setAiResult(null); }}
              style={{ background: 'linear-gradient(135deg, #7c3aed, #a855f7)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', boxShadow: '0 0 15px rgba(168, 85, 247, 0.3)' }}
            >
              <Sparkles size={16} /> AI Update
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              style={{ background: 'linear-gradient(135deg, #059669, #10b981)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', boxShadow: '0 0 15px rgba(16, 185, 129, 0.3)' }}
            >
              <Plus size={16} /> Register College
            </button>
            <button
              onClick={fetchColleges}
              title="Refresh monitoring data"
              style={{ background: 'rgba(30, 41, 59, 0.8)', color: '#94a3b8', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <RefreshCw size={15} /> Refresh
            </button>
            <button
              onClick={handlePurgeAll}
              title="Wipe database completely"
              style={{ background: 'rgba(244, 63, 94, 0.1)', color: '#f43f5e', border: '1px solid rgba(244, 63, 94, 0.25)', borderRadius: '8px', padding: '9px 14px', cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Trash2 size={14} /> Wipe All
            </button>
          </div>

        </div>
      </header>

      {/* Main Content Container */}
      <main style={{ maxWidth: '1400px', margin: '24px auto', padding: '0 24px' }}>

        {/* KPI Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          
          <div style={{ background: 'rgba(18, 26, 45, 0.75)', border: '1px solid rgba(148, 163, 184, 0.12)', borderRadius: '12px', padding: '18px 20px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase' }}>Total Monitored</span>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '8px' }}>
              <span style={{ fontSize: '1.85rem', fontWeight: 700, color: '#fff' }}>{totalCount}</span>
              <Building2 size={24} color="#94a3b8" />
            </div>
          </div>

          <div style={{ background: 'rgba(18, 26, 45, 0.75)', border: '1px solid rgba(16, 185, 129, 0.25)', borderRadius: '12px', padding: '18px 20px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#10b981', textTransform: 'uppercase' }}>On Track</span>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '8px' }}>
              <span style={{ fontSize: '1.85rem', fontWeight: 700, color: '#10b981' }}>{onTrackCount}</span>
              <CheckCircle2 size={24} color="#10b981" />
            </div>
          </div>

          <div style={{ background: 'rgba(18, 26, 45, 0.75)', border: '1px solid rgba(245, 158, 11, 0.25)', borderRadius: '12px', padding: '18px 20px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f59e0b', textTransform: 'uppercase' }}>Due Soon (≤3 Days)</span>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '8px' }}>
              <span style={{ fontSize: '1.85rem', fontWeight: 700, color: '#f59e0b' }}>{dueSoonCount}</span>
              <AlertTriangle size={24} color="#f59e0b" />
            </div>
          </div>

          <div style={{ background: 'rgba(18, 26, 45, 0.75)', border: '1px solid rgba(244, 63, 94, 0.25)', borderRadius: '12px', padding: '18px 20px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f43f5e', textTransform: 'uppercase' }}>Overdue / Delayed</span>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '8px' }}>
              <span style={{ fontSize: '1.85rem', fontWeight: 700, color: '#f43f5e' }}>{overdueCount}</span>
              <Clock size={24} color="#f43f5e" />
            </div>
          </div>

          <div style={{ background: 'rgba(18, 26, 45, 0.75)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '12px', padding: '18px 20px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#38bdf8', textTransform: 'uppercase' }}>Bureau Approved</span>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '8px' }}>
              <span style={{ fontSize: '1.85rem', fontWeight: 700, color: '#38bdf8' }}>{approvedCount}</span>
              <ShieldCheck size={24} color="#38bdf8" />
            </div>
          </div>

        </div>

        {/* Filter & Search Bar */}
        <div style={{ background: 'rgba(18, 26, 45, 0.75)', border: '1px solid rgba(148, 163, 184, 0.12)', borderRadius: '12px', padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px', marginBottom: '20px' }}>
          
          <div style={{ position: 'relative', flex: '1', minWidth: '260px' }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search by college name, application number, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: '100%', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '8px 12px 8px 36px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={14} color="#94a3b8" />
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Region:</span>
              <select
                value={filterRegion}
                onChange={(e) => setFilterRegion(e.target.value)}
                style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#fff', borderRadius: '6px', padding: '6px 10px', fontSize: '0.8rem', outline: 'none' }}
              >
                <option value="ALL">All Regions</option>
                <option value="Western">Western</option>
                <option value="Northern">Northern</option>
                <option value="Southern">Southern</option>
                <option value="Eastern">Eastern</option>
                <option value="South-Western">South-Western</option>
                <option value="Central">Central</option>
                <option value="North-Western">North-Western</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Status:</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#fff', borderRadius: '6px', padding: '6px 10px', fontSize: '0.8rem', outline: 'none' }}
              >
                <option value="ALL">All Statuses</option>
                <option value="ON_TRACK">On Track</option>
                <option value="DUE_SOON">Due Soon</option>
                <option value="OVERDUE">Overdue</option>
                <option value="APPROVED">Approved</option>
              </select>
            </div>
          </div>

        </div>

        {/* Colleges Monitoring Table */}
        <div style={{ background: 'rgba(18, 26, 45, 0.75)', border: '1px solid rgba(148, 163, 184, 0.12)', borderRadius: '12px', overflow: 'hidden' }}>
          
          <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(148, 163, 184, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc' }}>
              Active Institutional Dossiers ({filteredColleges.length})
            </h2>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              Showing {filteredColleges.length} of {totalCount} colleges
            </span>
          </div>

          {loading ? (
            <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
              <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 12px auto' }} />
              <p>Connecting to database & loading colleges...</p>
            </div>
          ) : filteredColleges.length === 0 ? (
            <div style={{ padding: '80px 20px', textAlign: 'center' }}>
              <div style={{ width: '60px', height: '60px', borderRadius: '50%', background: 'rgba(56, 189, 248, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
                <Building2 size={32} color="#38bdf8" />
              </div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc', marginBottom: '6px' }}>No Colleges Found</h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', maxWidth: '420px', margin: '0 auto 20px auto' }}>
                {colleges.length === 0
                  ? 'Your database is currently empty. Click "Register College" or use "AI Update" to intake and monitor colleges.'
                  : 'No colleges match your current search and filter criteria.'}
              </p>
              {colleges.length === 0 && (
                <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                  <button
                    onClick={() => setShowAddModal(true)}
                    style={{ background: 'linear-gradient(135deg, #059669, #10b981)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Plus size={16} /> Register First College
                  </button>
                  <button
                    onClick={() => { setShowAiModal(true); setAiResult(null); }}
                    style={{ background: 'linear-gradient(135deg, #7c3aed, #a855f7)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Sparkles size={16} /> Update via AI
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(15, 23, 42, 0.5)', borderBottom: '1px solid rgba(148, 163, 184, 0.12)', color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                    <th style={{ padding: '12px 18px' }}>Institution & Identifiers</th>
                    <th style={{ padding: '12px 16px' }}>Region & Category</th>
                    <th style={{ padding: '12px 16px' }}>Current Approval Stage</th>
                    <th style={{ padding: '12px 16px' }}>SLA Deadline</th>
                    <th style={{ padding: '12px 16px' }}>SLA Status</th>
                    <th style={{ padding: '12px 18px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredColleges.map((college) => (
                    <tr
                      key={college.id}
                      style={{ borderBottom: '1px solid rgba(148, 163, 184, 0.08)', transition: 'background-color 0.15s ease' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(30, 41, 59, 0.4)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      {/* Name & ID */}
                      <td style={{ padding: '14px 18px' }}>
                        <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.9rem', marginBottom: '3px' }}>
                          {college.institution_name}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: '#94a3b8' }}>
                          <span>App: <code style={{ color: '#38bdf8' }}>{college.application_number}</code></span>
                          <span>•</span>
                          <span>PID: {college.institution_permanent_id}</span>
                        </div>
                      </td>

                      {/* Region & Type */}
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ color: '#f8fafc', fontWeight: 500 }}>{college.region}</div>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{college.state} • {college.institution_type}</div>
                      </td>

                      {/* Stage */}
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ display: 'inline-block', padding: '4px 10px', borderRadius: '6px', background: 'rgba(30, 41, 59, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0' }}>
                          {getStageLabel(college.current_stage)}
                        </span>
                      </td>

                      {/* Deadline */}
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ color: '#f8fafc', fontWeight: 500 }}>{college.sla_deadline || 'N/A'}</div>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>SLA: {college.sla_duration_days} working days</div>
                      </td>

                      {/* Status */}
                      <td style={{ padding: '14px 16px' }}>
                        {getStatusBadge(college.sla_status, college.working_days_remaining)}
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                          <button
                            onClick={() => openCollegeDetails(college.id)}
                            style={{ background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '6px', padding: '6px 12px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <Eye size={13} /> Where's Where
                          </button>
                          <button
                            onClick={() => {
                              setAiCollegeQuery(college.institution_name);
                              setShowAiModal(true);
                              setAiResult(null);
                            }}
                            title="Update via AI"
                            style={{ background: 'rgba(168, 85, 247, 0.1)', color: '#a855f7', border: '1px solid rgba(168, 85, 247, 0.3)', borderRadius: '6px', padding: '6px 10px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <Sparkles size={13} /> AI
                          </button>
                          <button
                            onClick={() => handleDeleteCollege(college.id, college.institution_name)}
                            title="Remove college"
                            style={{ background: 'transparent', color: '#94a3b8', border: 'none', padding: '6px', cursor: 'pointer', borderRadius: '4px' }}
                            onMouseEnter={(e) => e.currentTarget.style.color = '#f43f5e'}
                            onMouseLeave={(e) => e.currentTarget.style.color = '#94a3b8'}
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>

                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

        </div>

      </main>

      {/* ---------------- MODAL 1: REGISTER NEW COLLEGE ---------------- */}
      {showAddModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '20px' }}>
          <div style={{ background: '#0f172a', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '16px', maxWidth: '540px', width: '100%', padding: '24px', boxShadow: '0 20px 40px rgba(0,0,0,0.6)' }}>
            
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Building2 size={20} color="#10b981" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff' }}>Register New College</h3>
                  <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Add institutional application & baseline SLA monitoring</p>
                </div>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleRegisterCollege}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>
                  College / Institution Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sardar Patel Institute of Technology"
                  value={newCollege.institution_name}
                  onChange={(e) => setNewCollege({ ...newCollege, institution_name: e.target.value })}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>Region</label>
                  <select
                    value={newCollege.region}
                    onChange={(e) => setNewCollege({ ...newCollege, region: e.target.value })}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
                  >
                    <option value="Western">Western</option>
                    <option value="Northern">Northern</option>
                    <option value="Southern">Southern</option>
                    <option value="Eastern">Eastern</option>
                    <option value="South-Western">South-Western</option>
                    <option value="Central">Central</option>
                    <option value="North-Western">North-Western</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>State</label>
                  <input
                    type="text"
                    value={newCollege.state}
                    onChange={(e) => setNewCollege({ ...newCollege, state: e.target.value })}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>Program Category</label>
                  <select
                    value={newCollege.institution_type}
                    onChange={(e) => setNewCollege({ ...newCollege, institution_type: e.target.value })}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
                  >
                    <option value="ENGINEERING_TECH">Engineering & Tech</option>
                    <option value="MANAGEMENT">Management (MBA/PGDM)</option>
                    <option value="PHARMACY">Pharmacy</option>
                    <option value="ARCHITECTURE">Architecture & Planning</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>Initial Stage</label>
                  <select
                    value={newCollege.current_stage}
                    onChange={(e) => setNewCollege({ ...newCollege, current_stage: e.target.value })}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
                  >
                    <option value="SUBMITTED">1. Application Submitted</option>
                    <option value="INITIAL_SCRUTINY">2. Document Scrutiny</option>
                    <option value="TECHNICAL_REVIEW">3. Technical Review</option>
                    <option value="EVC_INSPECTION">4. EVC Inspection</option>
                    <option value="REGIONAL_REVIEW">5. Regional Review</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>
                  Applicable Working-Day SLA
                </label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={newCollege.sla_working_days}
                    onChange={(e) => setNewCollege({ ...newCollege, sla_working_days: parseInt(e.target.value) || 15 })}
                    style={{ width: '120px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
                  />
                  <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>working days (auto-excludes Sundays & gazetted holidays)</span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  style={{ background: 'transparent', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#94a3b8', borderRadius: '8px', padding: '9px 16px', fontSize: '0.85rem', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  style={{ background: 'linear-gradient(135deg, #059669, #10b981)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 18px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer' }}
                >
                  {submitting ? 'Registering...' : 'Register College'}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

      {/* ---------------- MODAL 2: "WHERE'S WHERE" LIFECYCLE DRAWER ---------------- */}
      {showTimelineModal && selectedCollege && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '20px' }}>
          <div style={{ background: '#0f172a', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '16px', maxWidth: '820px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '28px', boxShadow: '0 20px 40px rgba(0,0,0,0.6)' }}>
            
            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid rgba(148, 163, 184, 0.12)', paddingBottom: '16px', marginBottom: '20px' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#38bdf8', textTransform: 'uppercase' }}>Lifecycle & SLA Status</span>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginTop: '2px' }}>{selectedCollege.institution_name}</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                  <span>Application: <code>{selectedCollege.application_number}</code></span>
                  <span>•</span>
                  <span>Region: {selectedCollege.region}</span>
                  <span>•</span>
                  <span>Officer: {selectedCollege.assigned_officer}</span>
                </div>
              </div>
              <button
                onClick={() => setShowTimelineModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Visual Lifecycle Pipeline ("Where's Where") */}
            <div style={{ marginBottom: '28px' }}>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '14px' }}>
                Approval Stage Progression ("Where is Where")
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '8px' }}>
                {(selectedCollege.stages_pipeline || []).map((st, index) => {
                  const isCurrent = selectedCollege.current_stage === st.stage;
                  const isPast = ['SUBMITTED', 'INITIAL_SCRUTINY', 'TECHNICAL_REVIEW', 'EVC_INSPECTION', 'REGIONAL_REVIEW', 'APPROVED'].indexOf(selectedCollege.current_stage) > index;
                  return (
                    <div
                      key={st.stage}
                      style={{
                        padding: '12px 10px',
                        borderRadius: '8px',
                        textAlign: 'center',
                        background: isCurrent ? 'rgba(56, 189, 248, 0.15)' : (isPast ? 'rgba(16, 185, 129, 0.1)' : 'rgba(30, 41, 59, 0.4)'),
                        border: isCurrent ? '1px solid #38bdf8' : (isPast ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(148, 163, 184, 0.1)'),
                        boxShadow: isCurrent ? '0 0 15px rgba(56, 189, 248, 0.2)' : 'none'
                      }}
                    >
                      <div style={{ fontSize: '0.7rem', fontWeight: 600, color: isCurrent ? '#38bdf8' : (isPast ? '#10b981' : '#64748b'), marginBottom: '4px' }}>
                        STEP {index + 1}
                      </div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: isCurrent ? '#fff' : (isPast ? '#e2e8f0' : '#94a3b8') }}>
                        {st.stage.replace('_', ' ')}
                      </div>
                      {isCurrent && (
                        <span style={{ display: 'inline-block', marginTop: '6px', fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: '#38bdf8', color: '#0f172a', fontWeight: 700 }}>
                          CURRENT
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* SLA Status Card */}
            <div style={{ background: 'rgba(18, 26, 45, 0.8)', border: '1px solid rgba(148, 163, 184, 0.15)', borderRadius: '12px', padding: '16px 20px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Current Stage SLA Deadline:</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                  {selectedCollege.sla_deadline}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Working Days Remaining:</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: selectedCollege.working_days_remaining < 0 ? '#f43f5e' : (selectedCollege.working_days_remaining <= 3 ? '#f59e0b' : '#10b981'), marginTop: '2px' }}>
                  {selectedCollege.working_days_remaining !== null ? `${selectedCollege.working_days_remaining} working days` : 'Completed'}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Monitoring Verdict:</span>
                <div style={{ marginTop: '4px' }}>
                  {getStatusBadge(selectedCollege.sla_status, selectedCollege.working_days_remaining)}
                </div>
              </div>
            </div>

            {/* Update / Transition Stage Form */}
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(148, 163, 184, 0.15)', borderRadius: '12px', padding: '18px 20px', marginBottom: '24px' }}>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', marginBottom: '12px' }}>
                Advance or Revert Approval Stage
              </h4>
              <form onSubmit={handleTransition} style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr auto', gap: '12px', alignItems: 'flex-end' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>Target Stage</label>
                  <select
                    value={transitionStage}
                    onChange={(e) => setTransitionStage(e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '6px', padding: '8px 10px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                  >
                    <option value="">Select Stage...</option>
                    <option value="SUBMITTED">1. Submitted</option>
                    <option value="INITIAL_SCRUTINY">2. Document Scrutiny</option>
                    <option value="TECHNICAL_REVIEW">3. Technical Review</option>
                    <option value="EVC_INSPECTION">4. EVC Inspection</option>
                    <option value="REGIONAL_REVIEW">5. Regional Review</option>
                    <option value="APPROVED">6. Bureau Approved</option>
                    <option value="REJECTED">Reject Application</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>Officer Remarks / Reason</label>
                  <input
                    type="text"
                    placeholder="e.g. Scrutiny verified; forwarding to EVC inspection"
                    value={transitionReason}
                    onChange={(e) => setTransitionReason(e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '6px', padding: '8px 10px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting || !transitionStage}
                  style={{ background: 'linear-gradient(135deg, #0284c7, #38bdf8)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 16px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', height: '36px' }}
                >
                  {submitting ? 'Updating...' : 'Update Stage'}
                </button>
              </form>
            </div>

            {/* Audit History Timeline */}
            <div>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '12px' }}>
                Stage Transition Audit Log ({selectedCollege.history?.length || 0})
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(selectedCollege.history || []).map((h, i) => (
                  <div key={h.id || i} style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(148, 163, 184, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f8fafc', fontWeight: 600 }}>
                        <span>{h.from_stage}</span>
                        <ArrowRight size={12} color="#38bdf8" />
                        <span style={{ color: '#38bdf8' }}>{h.to_stage}</span>
                      </div>
                      <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '2px' }}>{h.reason}</p>
                    </div>
                    <div style={{ textAlign: 'right', color: '#64748b', fontSize: '0.75rem' }}>
                      <div>{h.actor_name}</div>
                      <div>{h.timestamp}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      )}

      {/* ---------------- MODAL 3: AI-POWERED DOSSIER UPDATE (SLM) ---------------- */}
      {showAiModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '20px' }}>
          <div style={{ background: '#0f172a', border: '1px solid rgba(168, 85, 247, 0.3)', borderRadius: '16px', maxWidth: '620px', width: '100%', padding: '26px', boxShadow: '0 20px 50px rgba(124, 58, 237, 0.25)' }}>
            
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'linear-gradient(135deg, #7c3aed, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(168, 85, 247, 0.4)' }}>
                  <Sparkles color="#fff" size={22} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff' }}>AI-Powered College Update</h3>
                  <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Powered by Qwen 2.5 SLM & Statutory Statechart Engine</p>
                </div>
              </div>
              <button
                onClick={() => setShowAiModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAiUpdate}>
              {/* College Selector / Input */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>
                  Target College / Institution Name *
                </label>
                {colleges.length > 0 && (
                  <select
                    value={aiCollegeQuery}
                    onChange={(e) => setAiCollegeQuery(e.target.value)}
                    style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none', marginBottom: '8px' }}
                  >
                    <option value="">Select from registered colleges...</option>
                    {colleges.map((c) => (
                      <option key={c.id} value={c.institution_name}>
                        {c.institution_name} ({c.application_number}) — {c.current_stage}
                      </option>
                    ))}
                  </select>
                )}
                <input
                  type="text"
                  placeholder="Or type college name or application ID directly..."
                  value={aiCollegeQuery}
                  onChange={(e) => setAiCollegeQuery(e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '9px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none' }}
                />
              </div>

              {/* Natural Language Update Note */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>
                  Natural Language Update Note *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. The EVC committee conducted inspection yesterday and verified all labs and workshops. Recommending regional review."
                  value={aiUpdateText}
                  onChange={(e) => setAiUpdateText(e.target.value)}
                  style={{ width: '100%', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '8px', padding: '10px 12px', color: '#fff', fontSize: '0.85rem', outline: 'none', resize: 'vertical' }}
                />
              </div>

              {/* Quick Template Pills */}
              <div style={{ marginBottom: '18px' }}>
                <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                  Quick Statutory Prompts:
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={() => setAiUpdateText("EVC inspection completed and all workshop facilities cleared; recommend regional review")}
                    style={{ background: 'rgba(124, 58, 237, 0.15)', border: '1px solid rgba(168, 85, 247, 0.3)', color: '#d8b4fe', padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', cursor: 'pointer' }}
                  >
                    EVC Cleared → Regional Review
                  </button>
                  <button
                    type="button"
                    onClick={() => setAiUpdateText("Initial scrutiny completed with all land & trust documents verified; forward to technical review")}
                    style={{ background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#bae6fd', padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', cursor: 'pointer' }}
                  >
                    Scrutiny Verified → Technical Review
                  </button>
                  <button
                    type="button"
                    onClick={() => setAiUpdateText("Regional committee review passed with zero deficiencies; recommended for full Bureau Approval")}
                    style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#a7f3d0', padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', cursor: 'pointer' }}
                  >
                    Regional Cleared → Bureau Approved
                  </button>
                  <button
                    type="button"
                    onClick={() => setAiUpdateText("Missing Fire Safety NOC detected; return dossier for correction")}
                    style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fecdd3', padding: '4px 8px', borderRadius: '6px', fontSize: '0.7rem', cursor: 'pointer' }}
                  >
                    Deficiency Found → Return for Correction
                  </button>
                </div>
              </div>

              {/* AI Processing Result Box */}
              {aiResult && (
                <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '10px', padding: '14px', marginBottom: '16px', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontWeight: 600, marginBottom: '6px' }}>
                    <CheckCircle2 size={16} /> AI Update Applied Successfully!
                  </div>
                  <div style={{ color: '#f8fafc', marginBottom: '4px' }}>
                    <strong>{aiResult.institution_name}</strong> moved from <span style={{ color: '#94a3b8' }}>{aiResult.previous_stage}</span> to <span style={{ color: '#38bdf8', fontWeight: 700 }}>{aiResult.new_stage}</span>
                  </div>
                  <div style={{ color: '#cbd5e1', fontSize: '0.75rem', marginBottom: '4px' }}>
                    <strong>SLM Reason:</strong> {aiResult.ai_reasoning}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.7rem', marginTop: '6px' }}>
                    <span>New Deadline: {aiResult.new_deadline}</span>
                    <span>Engine: {aiResult.engine_used} ({(aiResult.confidence * 100).toFixed(0)}% conf)</span>
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowAiModal(false)}
                  style={{ background: 'transparent', border: '1px solid rgba(148, 163, 184, 0.2)', color: '#94a3b8', borderRadius: '8px', padding: '9px 16px', fontSize: '0.85rem', cursor: 'pointer' }}
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={aiSubmitting}
                  style={{ background: 'linear-gradient(135deg, #7c3aed, #a855f7)', color: '#fff', border: 'none', borderRadius: '8px', padding: '9px 20px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {aiSubmitting ? <><RefreshCw size={14} className="animate-spin" /> Processing AI...</> : <><Sparkles size={14} /> Apply AI Update</>}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
}
