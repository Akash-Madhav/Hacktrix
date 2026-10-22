import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Scale, 
  ShieldAlert, 
  FolderLock, 
  Bot, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  RefreshCw, 
  Zap, 
  Upload, 
  Send, 
  Eye, 
  Cpu, 
  ExternalLink,
  PlusCircle,
  Check
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('applications');
  const [applications, setApplications] = useState([]);
  const [currentAppId, setCurrentAppId] = useState(null);
  const [appStatusMap, setAppStatusMap] = useState({});
  const [currentRunId, setCurrentRunId] = useState(null);
  const [verdict, setVerdict] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [llmEnabled, setLlmEnabled] = useState(true);
  const [modelConfig, setModelConfig] = useState(null);

  // Modal State
  const [modalDoc, setModalDoc] = useState(null);

  // Add College Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [addForm, setAddForm] = useState({
    institution_name: 'National Institute of Advanced Technology',
    application_number: 'AICTE/2024/APP-5081',
    institution_type: 'NEW_TECHNICAL_INSTITUTION',
    application_type: 'NEW_INSTITUTION',
    state: 'Maharashtra',
    district: 'Pune',
    address: 'Survey No. 204/1, Hinjewadi Knowledge Zone, Pune - 411057',
    program_name: 'Computer Science & Engineering',
    level: 'UG',
    approved_intake: 120,
    total_area_acres: 8.5,
    is_single_plot: true,
    survey_khasra_no: 'Survey No. 204/1',
    land_registration_date: '2023-04-12',
    total_carpet_sqm: 9200,
    instructional_area_sqm: 4800,
    administrative_area_sqm: 2200,
    amenities_area_sqm: 2200,
    test_scenario: 'COMPLIANT'
  });

  function resetAddForm() {
    const randomSuffix = Math.floor(1000 + Math.random() * 9000);
    setAddForm({
      institution_name: 'National Institute of Advanced Technology',
      application_number: `AICTE/2024/APP-${randomSuffix}`,
      institution_type: 'NEW_TECHNICAL_INSTITUTION',
      application_type: 'NEW_INSTITUTION',
      state: 'Maharashtra',
      district: 'Pune',
      address: 'Survey No. 204/1, Hinjewadi Knowledge Zone, Pune - 411057',
      program_name: 'Computer Science & Engineering',
      level: 'UG',
      approved_intake: 120,
      total_area_acres: 8.5,
      is_single_plot: true,
      survey_khasra_no: 'Survey No. 204/1',
      land_registration_date: '2023-04-12',
      total_carpet_sqm: 9200,
      instructional_area_sqm: 4800,
      administrative_area_sqm: 2200,
      amenities_area_sqm: 2200,
      test_scenario: 'COMPLIANT'
    });
  }

  async function handleAddCollegeSubmit(e) {
    e.preventDefault();
    setIsAdding(true);
    try {
      const payload = {
        application_number: addForm.application_number || `AICTE/2024/APP-${Math.floor(1000 + Math.random() * 9000)}`,
        institution_name: addForm.institution_name,
        institution_type: addForm.institution_type,
        application_type: addForm.application_type,
        state: addForm.state,
        district: addForm.district,
        address: addForm.address,
        programs: [
          {
            program_name: addForm.program_name,
            level: addForm.level,
            approved_intake: parseInt(addForm.approved_intake, 10) || 60
          }
        ],
        land_detail: {
          total_area_acres: parseFloat(addForm.total_area_acres) || 8.0,
          is_single_plot: Boolean(addForm.is_single_plot),
          survey_khasra_no: addForm.survey_khasra_no,
          land_registration_date: addForm.land_registration_date
        },
        builtup_detail: {
          total_carpet_sqm: parseFloat(addForm.total_carpet_sqm) || 8500.0,
          instructional_area_sqm: parseFloat(addForm.instructional_area_sqm) || 4500.0,
          administrative_area_sqm: parseFloat(addForm.administrative_area_sqm) || 2000.0,
          amenities_area_sqm: parseFloat(addForm.amenities_area_sqm) || 2000.0
        },
        test_scenario: addForm.test_scenario,
        auto_validate: true
      };

      const res = await fetch('/applications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create college');
      }

      const created = await res.json();
      setIsAddModalOpen(false);

      // Refresh applications and select new college
      await fetchApplications();
      setCurrentAppId(created.id);
      setActiveTab('verdict');
      await fetchVerdict(created.id);
    } catch (err) {
      alert('Error creating institution: ' + err.message);
    } finally {
      setIsAdding(false);
    }
  }

  // Chat State
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content: 'Welcome Scrutiny Officer. I am BluePill, powered by **Qwen 2.5 (3B)** running locally. Select any institution dossier above and ask questions regarding land norms, carpet area, missing documents, or digital tampering flags.',
      engine: 'Qwen 2.5'
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Upload Form State
  const [uploadType, setUploadType] = useState('LAND_REGISTRATION');
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // 1. Initial Load
  useEffect(() => {
    fetchApplications();
    fetchModelConfig();
  }, []);

  // 2. When Current App Changes
  useEffect(() => {
    if (!currentAppId) return;
    fetchAppStatus(currentAppId);
    if (activeTab === 'verdict') fetchVerdict(currentAppId);
    if (activeTab === 'docs') fetchDocuments(currentAppId);
    if (activeTab === 'tamper') fetchTamperObservations(currentAppId);
  }, [currentAppId, activeTab]);

  async function fetchModelConfig() {
    try {
      const res = await fetch('/agent/config');
      if (res.ok) {
        const data = await res.json();
        setModelConfig(data);
        setLlmEnabled(data.llm_enabled);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function fetchApplications() {
    try {
      const res = await fetch('/applications');
      const data = await res.json();
      setApplications(data);

      if (data.length > 0 && !currentAppId) {
        setCurrentAppId(data[0].id);
      }

      // Fetch status for all
      const statuses = {};
      for (const app of data) {
        try {
          const sRes = await fetch(`/applications/${app.id}/status`);
          if (sRes.ok) {
            statuses[app.id] = await sRes.json();
          }
        } catch (e) {}
      }
      setAppStatusMap(statuses);
    } catch (err) {
      console.error('Failed to load applications:', err);
    }
  }

  async function fetchAppStatus(appId) {
    try {
      const res = await fetch(`/applications/${appId}/status`);
      if (res.ok) {
        const data = await res.json();
        setAppStatusMap(prev => ({ ...prev, [appId]: data }));
        setCurrentRunId(data.latest_run_id);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function fetchVerdict(appId) {
    setLoading(true);
    try {
      let runId = currentRunId;
      if (!runId) {
        const runRes = await fetch(`/applications/${appId}/validate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ engine_mode: llmEnabled ? 'HYBRID_WITH_LLM' : 'DETERMINISTIC_RULES' })
        });
        const runData = await runRes.json();
        runId = runData.id;
        setCurrentRunId(runId);
      }

      const res = await fetch(`/runs/${runId}/verdict`);
      if (res.ok) {
        const vData = await res.json();
        setVerdict(vData);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchTamperObservations(appId) {
    if (!verdict) {
      await fetchVerdict(appId);
    }
  }

  async function fetchDocuments(appId) {
    try {
      const res = await fetch(`/applications/${appId}/documents`);
      if (res.ok) {
        const docs = await res.json();
        setDocuments(docs);
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleRunAudit() {
    if (!currentAppId) return;
    setLoading(true);
    try {
      const res = await fetch(`/applications/${currentAppId}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine_mode: llmEnabled ? 'HYBRID_WITH_LLM' : 'DETERMINISTIC_RULES' })
      });
      const data = await res.json();
      setCurrentRunId(data.id);
      await fetchApplications();
      await fetchVerdict(currentAppId);
      setActiveTab('verdict');
    } catch (e) {
      alert('Audit failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleLlm() {
    const nextState = !llmEnabled;
    try {
      const res = await fetch(`/agent/config/toggle-llm?enable=${nextState}`, { method: 'POST' });
      const data = await res.json();
      setLlmEnabled(data.llm_enabled);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleReseed() {
    if (!window.confirm('Reset and re-seed the benchmark databases with 3 diverse applications?')) return;
    setLoading(true);
    try {
      const res = await fetch('/system/reseed', { method: 'POST' });
      if (res.ok) {
        alert('Benchmark applications & synthetic PDFs re-seeded successfully!');
        await fetchApplications();
      }
    } catch (e) {
      alert('Reseed failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadSubmit(e) {
    e.preventDefault();
    if (!uploadFile || !currentAppId) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('document_type', uploadType);
    formData.append('file', uploadFile);

    try {
      const res = await fetch(`/applications/${currentAppId}/documents/upload`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        alert('Document uploaded, verified, and digested into dossier!');
        setUploadFile(null);
        fetchDocuments(currentAppId);
        fetchApplications();
      } else {
        const err = await res.json();
        alert('Upload rejected: ' + (err.detail || 'Error'));
      }
    } catch (err) {
      alert('Upload error: ' + err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleClassifyDoc(docId) {
    try {
      const res = await fetch(`/agent/classify/${docId}`, { method: 'POST' });
      const data = await res.json();
      alert(`SA-01 Classification Report:\n• Declared Type: ${data.declared_type}\n• Verified Type: ${data.verified_type}\n• Confidence: ${(data.confidence * 100).toFixed(0)}%\n• Consistency: ${data.is_consistent ? 'MATCH' : 'MISMATCH'}\n\n${data.explanation}`);
    } catch (e) {
      alert('Classification agent error: ' + e.message);
    }
  }

  async function handleChatSubmit(e) {
    e.preventDefault();
    const query = chatInput.trim();
    if (!query || !currentAppId) return;

    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: query }]);
    setChatLoading(true);

    try {
      const res = await fetch('/agent/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          application_id: currentAppId,
          question: query,
          include_statutory_citations: true
        })
      });
      const data = await res.json();
      setChatMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          engine: data.engine_used,
          latency: data.latency_ms,
          sources: data.sources
        }
      ]);
    } catch (err) {
      setChatMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Inference error: ' + err.message }
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  // Active App Object
  const currentApp = applications.find(a => a.id === currentAppId);
  const currentStatus = appStatusMap[currentAppId] || {};

  // Stats Counters
  const readyAppsCount = Object.values(appStatusMap).filter(s => s.overall_readiness === 'READY_FOR_REVIEW').length;
  const incompleteAppsCount = Object.values(appStatusMap).filter(s => s.overall_readiness === 'INCOMPLETE').length;
  const issuesAppsCount = Object.values(appStatusMap).filter(s => s.overall_readiness === 'HAS_ISSUES' || s.overall_readiness === 'CRITICAL_ISSUES').length;

  return (
    <div className="app-layout">
      {/* Top Navbar */}
      <header className="top-nav">
        <div className="brand">
          <div className="brand-logo">💊</div>
          <div className="brand-text">
            <h1>AICTE BluePill</h1>
            <span className="sub-badge">React Scrutiny Workbench • APH 2024-25</span>
          </div>
        </div>

        <div className="header-actions">
          {/* Qwen Model Chip */}
          <div className="model-status-chip">
            <span className="status-dot active"></span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Local Model:</span>
            <strong style={{ color: '#fff' }}>Qwen 2.5 (3B)</strong>
            <button 
              className={`toggle-btn ${llmEnabled ? 'active' : ''}`}
              onClick={handleToggleLlm}
              title="Toggle LLM vs Deterministic Mode"
            >
              {llmEnabled ? 'LLM Active' : 'Deterministic Only'}
            </button>
          </div>

          <button 
            className="btn btn-success" 
            onClick={() => { resetAddForm(); setIsAddModalOpen(true); }}
            style={{ fontWeight: 600, padding: '7px 14px' }}
          >
            <PlusCircle size={15} style={{ display: 'inline', marginRight: 4 }} />
            Add Institution
          </button>

          <a href="/docs" target="_blank" rel="noreferrer" className="nav-link-btn">
            <ExternalLink size={14} style={{ display: 'inline', marginRight: 4 }} />
            API Swagger
          </a>
        </div>
      </header>

      <div className="body-container">
        {/* Sidebar */}
        <aside className="sidebar">
          <div>
            <div className="sidebar-section-title">SCRUTINY SUITE</div>
            <nav className="sidebar-nav">
              <button 
                className={`nav-item ${activeTab === 'applications' ? 'active' : ''}`}
                onClick={() => setActiveTab('applications')}
              >
                <FileText size={18} />
                <span>Applications</span>
                <span className="badge">{applications.length}</span>
              </button>

              <button 
                className={`nav-item ${activeTab === 'verdict' ? 'active' : ''}`}
                onClick={() => setActiveTab('verdict')}
              >
                <Scale size={18} />
                <span>Final Judgment</span>
              </button>

              <button 
                className={`nav-item ${activeTab === 'tamper' ? 'active' : ''}`}
                onClick={() => setActiveTab('tamper')}
              >
                <ShieldAlert size={18} />
                <span>Tamper Detection</span>
                {verdict?.actionable_checklist?.tampering_integrity_flags?.length > 0 && (
                  <span className="badge warning">
                    {verdict.actionable_checklist.tampering_integrity_flags.length}
                  </span>
                )}
              </button>

              <button 
                className={`nav-item ${activeTab === 'docs' ? 'active' : ''}`}
                onClick={() => setActiveTab('docs')}
              >
                <FolderLock size={18} />
                <span>Documents Vault</span>
              </button>

              <button 
                className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
                onClick={() => setActiveTab('chat')}
              >
                <Bot size={18} />
                <span>Ask BluePill (Qwen)</span>
              </button>
            </nav>
          </div>

          <div className="sidebar-footer">
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                Active Scrutiny Dossier:
              </label>
              <select 
                className="styled-select" 
                value={currentAppId || ''} 
                onChange={(e) => setCurrentAppId(e.target.value)}
              >
                {applications.map(app => (
                  <option key={app.id} value={app.id}>
                    {app.institution_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="system-indicator">
              <span className="pulse-indicator"></span>
              <span>Local Model Vault: /models</span>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          {/* TAB 1: Applications Overview */}
          {activeTab === 'applications' && (
            <div>
              <div className="section-header">
                <div>
                  <h2>Institutional Applications Directory</h2>
                  <p>AICTE procedural scrutiny status, document completeness counters, and compliance classification.</p>
                </div>
                <div className="header-buttons">
                  <button className="btn btn-success" onClick={() => { resetAddForm(); setIsAddModalOpen(true); }}>
                    <PlusCircle size={15} /> Add College / Run Test
                  </button>
                  <button className="btn btn-secondary" onClick={handleReseed} disabled={loading}>
                    <RefreshCw size={15} /> Re-seed Benchmarks
                  </button>
                  <button className="btn btn-primary" onClick={handleRunAudit} disabled={loading}>
                    <Zap size={15} /> Run Statutory Audit
                  </button>
                </div>
              </div>

              {/* Stats Cards */}
              <div className="stats-overview">
                <div className="stat-card">
                  <div className="stat-icon blue">📁</div>
                  <div>
                    <span className="stat-label">Total Applications</span>
                    <span className="stat-val">{applications.length}</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon green">✅</div>
                  <div>
                    <span className="stat-label">Ready For Review</span>
                    <span className="stat-val">{readyAppsCount}</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon amber">⏳</div>
                  <div>
                    <span className="stat-label">Incomplete Dossiers</span>
                    <span className="stat-val">{incompleteAppsCount}</span>
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-icon red">⚠️</div>
                  <div>
                    <span className="stat-label">Issues & Deficiencies</span>
                    <span className="stat-val">{issuesAppsCount}</span>
                  </div>
                </div>
              </div>

              {/* Application Cards Grid */}
              <div className="cards-grid">
                {applications.map(app => {
                  const s = appStatusMap[app.id] || {
                    overall_readiness: 'PENDING',
                    documents_count: 0,
                    required_documents_count: 5,
                    missing_documents_count: 5,
                    current_status: 'DRAFT'
                  };
                  const isSelected = app.id === currentAppId;

                  return (
                    <div key={app.id} className={`app-card ${isSelected ? 'selected' : ''}`}>
                      <div className="app-card-header">
                        <span className="app-number">{app.application_number}</span>
                        <span className={`readiness-pill ${s.overall_readiness}`}>
                          {s.overall_readiness.replace(/_/g, ' ')}
                        </span>
                      </div>

                      <h3 className="app-name">{app.institution_name}</h3>
                      <p className="app-location">
                        📍 {app.district}, {app.state} • {app.institution_type.replace(/_/g, ' ')}
                      </p>

                      <div className="app-stats-row">
                        <div>
                          <span className="stat-label">Uploaded Docs</span>
                          <strong>{s.documents_count} / {s.required_documents_count}</strong>
                        </div>
                        <div>
                          <span className="stat-label">Missing Items</span>
                          <strong style={{ color: s.missing_documents_count > 0 ? 'var(--warning)' : 'var(--success)' }}>
                            {s.missing_documents_count}
                          </strong>
                        </div>
                        <div>
                          <span className="stat-label">Status</span>
                          <strong>{s.current_status.replace(/_/g, ' ')}</strong>
                        </div>
                      </div>

                      <div className="app-card-actions">
                        <button 
                          className="btn btn-secondary" 
                          onClick={() => { setCurrentAppId(app.id); }}
                        >
                          Select Dossier
                        </button>
                        <button 
                          className="btn btn-primary" 
                          onClick={() => { setCurrentAppId(app.id); setActiveTab('verdict'); }}
                        >
                          View Judgment
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 2: Final Judgment Verdict */}
          {activeTab === 'verdict' && (
            <div>
              <div className="section-header">
                <div>
                  <h2>Final Statutory Judgment & Actionable Readiness</h2>
                  <p>Comprehensive determination of statutory readiness, missing documents, and required remediations.</p>
                </div>
                <button className="btn btn-primary" onClick={handleRunAudit} disabled={loading}>
                  <RefreshCw size={15} /> Re-Evaluate Application
                </button>
              </div>

              {loading && <div style={{ color: 'var(--primary)', padding: 20 }}>Evaluating AICTE statutory rules...</div>}

              {verdict && !loading && (
                <>
                  {/* Verdict Banner */}
                  <div className={`verdict-banner ${verdict.overall_readiness}`}>
                    <div className="verdict-info">
                      <span className={`readiness-pill ${verdict.overall_readiness}`} style={{ display: 'inline-block', marginBottom: 8 }}>
                        {verdict.overall_readiness.replace(/_/g, ' ')}
                      </span>
                      <h3>{verdict.verdict_headline}</h3>
                      <p>{verdict.verdict_explanation}</p>
                    </div>

                    <div className="verdict-gauge">
                      <div className={`gauge-circle ${verdict.overall_readiness}`}>
                        {verdict.readiness_score_pct}%
                      </div>
                      <span className="gauge-label">Compliance Norms</span>
                    </div>
                  </div>

                  {/* Actionable Checklist */}
                  <h3 style={{ fontSize: '1.15rem', color: '#fff', marginBottom: 16 }}>Actionable Scrutiny Checklist</h3>
                  <div className="checklist-grid">
                    {/* Missing Mandatory Items */}
                    <div className="check-box missing-box">
                      <div className="check-box-header">
                        <AlertTriangle color="var(--warning)" size={18} />
                        <h4>What's Missing (Mandatory Documents)</h4>
                        <span className="count-chip">
                          {verdict.actionable_checklist.missing_mandatory_documents?.length || 0}
                        </span>
                      </div>
                      <div>
                        {(!verdict.actionable_checklist.missing_mandatory_documents || verdict.actionable_checklist.missing_mandatory_documents.length === 0) ? (
                          <p style={{ color: 'var(--success)', fontSize: '0.85rem' }}>
                            ✓ All 5 statutory mandatory documents are uploaded and accounted for.
                          </p>
                        ) : (
                          verdict.actionable_checklist.missing_mandatory_documents.map((m, idx) => (
                            <div key={idx} className="checklist-item CRITICAL">
                              <div className="item-title">{m.name}</div>
                              <div className="item-desc">{m.description}</div>
                              <div className="item-mandate">Mandate: {m.regulatory_mandate}</div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Deficiencies */}
                    <div className="check-box deficiency-box">
                      <div className="check-box-header">
                        <XCircle color="var(--danger)" size={18} />
                        <h4>Statutory Deficiencies & Norm Failures</h4>
                        <span className="count-chip">
                          {verdict.actionable_checklist.critical_and_major_deficiencies?.length || 0}
                        </span>
                      </div>
                      <div>
                        {(!verdict.actionable_checklist.critical_and_major_deficiencies || verdict.actionable_checklist.critical_and_major_deficiencies.length === 0) ? (
                          <p style={{ color: 'var(--success)', fontSize: '0.85rem' }}>
                            ✓ No critical or major norm deficiencies recorded.
                          </p>
                        ) : (
                          verdict.actionable_checklist.critical_and_major_deficiencies.map((d, idx) => (
                            <div key={idx} className={`checklist-item ${d.severity}`}>
                              <div className="item-title">[{d.rule_id}] {d.check_name} ({d.severity})</div>
                              <div className="item-desc">{d.finding}</div>
                              <div className="item-mandate">Remedy: {d.required_remedy}</div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Norm Category Breakdown */}
                  <h3 style={{ fontSize: '1.15rem', color: '#fff', marginBottom: 16 }}>Compliance By Category</h3>
                  <div className="categories-grid">
                    {Object.values(verdict.category_breakdown || {}).map((c, idx) => (
                      <div key={idx} className="category-card">
                        <div className="cat-header">
                          <span className="cat-name">{c.category_name}</span>
                          <span className={`cat-status ${c.status}`}>{c.status}</span>
                        </div>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{c.summary}</p>
                      </div>
                    ))}
                  </div>

                  {/* Passed Checks */}
                  <h3 style={{ fontSize: '1.15rem', color: '#fff', marginBottom: 16 }}>Verified Passing Norms</h3>
                  <ul className="passed-checks-list">
                    {(verdict.actionable_checklist.passed_compliance_checks || []).map((p, idx) => (
                      <li key={idx}>✓ {p}</li>
                    ))}
                  </ul>

                  {/* Disclaimer */}
                  <div className="statutory-disclaimer-box">
                    ⚖️ {verdict.statutory_disclaimer}
                  </div>
                </>
              )}
            </div>
          )}

          {/* TAB 3: Tamper Detection */}
          {activeTab === 'tamper' && (
            <div>
              <div className="section-header">
                <div>
                  <h2>Digital Document Forensics & Tampering Analysis</h2>
                  <p>Autonomous V12 (Metadata Anomaly) and V13 (Revision & Incremental Save) Inspection Engine.</p>
                </div>
              </div>

              <div className="glass-card" style={{ marginBottom: 24, borderLeft: '4px solid var(--primary)' }}>
                <h4 style={{ color: '#fff', marginBottom: 6 }}>ISO 32000-1 Structural Authenticity Protocol</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                  Statutory certificates are scrutinized for multi-stream xref modifications, post-issuance tool signatures (e.g. Canva, PDFescape), and inverted creation timestamps.
                </p>
              </div>

              {(!verdict?.actionable_checklist?.tampering_integrity_flags || verdict.actionable_checklist.tampering_integrity_flags.length === 0) ? (
                <div className="glass-card" style={{ textAlign: 'center', padding: 48 }}>
                  <CheckCircle size={48} color="var(--success)" style={{ margin: '0 auto 12px' }} />
                  <h3 style={{ color: 'var(--success)', marginBottom: 6 }}>Zero Tampering Indicators Detected</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 600, margin: '0 auto' }}>
                    All uploaded statutory documents exhibit verified linear xref structures, authentic issuing metadata, and compliant creation timestamps.
                  </p>
                </div>
              ) : (
                verdict.actionable_checklist.tampering_integrity_flags.map((t, idx) => (
                  <div key={idx} className="tamper-card FLAG">
                    <div className="tamper-header">
                      <span className="tamper-rule">[{t.rule_id}] {t.observation_type}</span>
                      <span className="readiness-pill HAS_ISSUES">{t.severity}</span>
                    </div>
                    <div className="tamper-body">
                      <h4>Target Document: {t.document_name}</h4>
                      <p>{t.details}</p>
                      <div className="tamper-remedy">
                        <strong>Recommended Scrutiny Action:</strong> {t.recommendation}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* TAB 4: Documents Vault */}
          {activeTab === 'docs' && (
            <div>
              <div className="section-header">
                <div>
                  <h2>Document Dossier & Text Extraction Vault</h2>
                  <p>Cryptographic SHA-256 verification, raw extracted text streams, and SA-01 subagent classifier.</p>
                </div>
              </div>

              {/* Upload Form */}
              <div className="glass-card">
                <h3 style={{ fontSize: '1.05rem', color: '#fff', marginBottom: 14 }}>Upload Additional Statutory Document</h3>
                <form onSubmit={handleUploadSubmit} style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 240 }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                      Document Category:
                    </label>
                    <select 
                      className="styled-select" 
                      value={uploadType} 
                      onChange={(e) => setUploadType(e.target.value)}
                    >
                      <option value="LAND_REGISTRATION">Land Registration / Title Deed</option>
                      <option value="BUILDING_PLAN_APPROVAL">Sanctioned Building Plan Approval</option>
                      <option value="FIRE_SAFETY_NOC">Fire Safety NOC Certificate</option>
                      <option value="AFFIDAVIT_TRUST">Registered Trust / Society Affidavit</option>
                      <option value="ARCHITECT_CERTIFICATE">Architect Barrier-Free Certificate</option>
                      <option value="SUPPORTING_ATTACHMENT">Supporting Statutory Attachment</option>
                    </select>
                  </div>

                  <div style={{ flex: 1, minWidth: 240 }}>
                    <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                      Select PDF File:
                    </label>
                    <input 
                      type="file" 
                      accept=".pdf" 
                      required 
                      onChange={(e) => setUploadFile(e.target.files[0])}
                      style={{ width: '100%', padding: '6px', background: 'rgba(30,41,59,0.8)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', color: '#fff', fontSize: '0.8rem' }}
                    />
                  </div>

                  <button type="submit" className="btn btn-primary" disabled={uploading}>
                    <Upload size={15} /> {uploading ? 'Processing...' : 'Upload & Inspect'}
                  </button>
                </form>
              </div>

              {/* Documents Table */}
              <div className="glass-card">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Document Type</th>
                      <th>Filename</th>
                      <th>SHA-256 Hash</th>
                      <th>Size</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map(d => (
                      <tr key={d.id}>
                        <td><strong>{d.document_type}</strong></td>
                        <td>{d.original_filename}</td>
                        <td className="hash-mono">{d.sha256_hash.substring(0, 16)}...</td>
                        <td>{(d.file_size_bytes / 1024).toFixed(1)} KB</td>
                        <td><span className="readiness-pill READY_FOR_REVIEW">PROCESSED</span></td>
                        <td>
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '4px 10px', fontSize: '0.76rem', marginRight: 8 }}
                            onClick={() => setModalDoc(d)}
                          >
                            <Eye size={12} style={{ display: 'inline', marginRight: 4 }} /> View Text
                          </button>
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '4px 10px', fontSize: '0.76rem' }}
                            onClick={() => handleClassifyDoc(d.id)}
                          >
                            SA-01 Check
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: Ask BluePill Qwen Chat */}
          {activeTab === 'chat' && (
            <div>
              <div className="section-header">
                <div>
                  <h2>Ask BluePill — Intelligent Scrutiny Assistant</h2>
                  <p>Interactively cross-examine application dossier with <strong>Qwen 2.5 (3B)</strong> backed by exact document evidence citations.</p>
                </div>
              </div>

              <div className="chat-container glass-card">
                {/* Prompt Suggestions */}
                <div className="chat-suggestions">
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Suggestions:</span>
                  {[
                    "What is the land norm status and are there any deficiencies?",
                    "What statutory documents are currently missing from this application?",
                    "Are there any digital tampering or metadata integrity flags detected?",
                    "Does the built-up carpet area meet AICTE requirements?"
                  ].map((sugg, i) => (
                    <button 
                      key={i} 
                      className="sugg-chip"
                      onClick={() => setChatInput(sugg)}
                    >
                      {sugg}
                    </button>
                  ))}
                </div>

                {/* Messages Box */}
                <div className="chat-messages">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`chat-bubble ${msg.role}`}>
                      <div className="avatar">{msg.role === 'assistant' ? '💊' : '👤'}</div>
                      <div className="bubble-content">
                        {msg.engine && (
                          <div style={{ fontSize: '0.72rem', color: 'var(--ai-purple)', marginBottom: 4, fontWeight: 600 }}>
                            {msg.engine} {msg.latency && `• ${msg.latency.toFixed(0)}ms`}
                          </div>
                        )}
                        <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>

                        {/* Evidentiary Citations */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div style={{ marginTop: 10 }}>
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                              Statutory Evidence Citations:
                            </span>
                            {msg.sources.map((s, idx) => (
                              <div key={idx} className="citation-card">
                                <div className="citation-header">📄 {s.document_name} ({s.clause_or_page})</div>
                                <div>"{s.extracted_text_snippet}"</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {chatLoading && (
                    <div className="chat-bubble assistant">
                      <div className="avatar">💊</div>
                      <div className="bubble-content">
                        <span style={{ color: 'var(--primary)' }}>Qwen 2.5 analyzing evidence across documents...</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Input Bar */}
                <form onSubmit={handleChatSubmit} className="chat-input-bar">
                  <input 
                    type="text" 
                    placeholder="Ask any statutory question about this institutional application..." 
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    required
                  />
                  <button type="submit" className="btn btn-primary" disabled={chatLoading}>
                    <Send size={15} /> Ask AI
                  </button>
                </form>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Document Text Modal */}
      {modalDoc && (
        <div className="modal-backdrop" onClick={() => setModalDoc(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modalDoc.document_type} — {modalDoc.original_filename}</h3>
              <button className="close-modal-btn" onClick={() => setModalDoc(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: 8 }}>
                SHA-256: <code>{modalDoc.sha256_hash}</code> | Size: {(modalDoc.file_size_bytes / 1024).toFixed(1)} KB
              </div>
              <h4>Extracted Raw Text Stream:</h4>
              <pre className="extracted-text-box">
                {modalDoc.extracted_text || 'No text extracted from this PDF.'}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Add College & Run Test Modal */}
      {isAddModalOpen && (
        <div className="modal-backdrop" onClick={() => !isAdding && setIsAddModalOpen(false)}>
          <div className="modal-card wide-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-header-content">
                <h3>🏛️ Add New College / Institutional Application</h3>
                <p>Register institution profile, select statutory document scenario, and immediately execute AICTE compliance audit.</p>
              </div>
              <button className="close-modal-btn" onClick={() => !isAdding && setIsAddModalOpen(false)}>✕</button>
            </div>

            <form onSubmit={handleAddCollegeSubmit} style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div className="modal-body" style={{ maxHeight: '72vh', overflowY: 'auto' }}>
                
                {/* 1. Institution Profile */}
                <div className="form-section">
                  <div className="form-section-title">
                    📋 Institutional Identity & Location
                  </div>
                  <div className="form-row">
                    <div className="form-group" style={{ gridColumn: 'span 2' }}>
                      <label>Institution Name *</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        required
                        placeholder="e.g. Cambridge Institute of Technology" 
                        value={addForm.institution_name}
                        onChange={(e) => setAddForm({...addForm, institution_name: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Application Number *</label>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <input 
                          type="text" 
                          className="form-input" 
                          required
                          value={addForm.application_number}
                          onChange={(e) => setAddForm({...addForm, application_number: e.target.value})}
                        />
                        <button 
                          type="button" 
                          className="btn btn-secondary" 
                          style={{ padding: '0 8px', fontSize: '0.75rem' }}
                          title="Generate fresh ID"
                          onClick={() => {
                            const rnd = Math.floor(1000 + Math.random() * 9000);
                            setAddForm({...addForm, application_number: `AICTE/2024/APP-${rnd}`});
                          }}
                        >
                          🎲
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Institution Type</label>
                      <select 
                        className="form-select"
                        value={addForm.institution_type}
                        onChange={(e) => setAddForm({...addForm, institution_type: e.target.value})}
                      >
                        <option value="NEW_TECHNICAL_INSTITUTION">New Technical Institution</option>
                        <option value="EXISTING_INSTITUTION">Existing Institution Expansion</option>
                        <option value="DEEMED_UNIVERSITY">Deemed University Technical Campus</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>State *</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        required
                        value={addForm.state}
                        onChange={(e) => setAddForm({...addForm, state: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>District *</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        required
                        value={addForm.district}
                        onChange={(e) => setAddForm({...addForm, district: e.target.value})}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Campus Address</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      value={addForm.address}
                      onChange={(e) => setAddForm({...addForm, address: e.target.value})}
                    />
                  </div>
                </div>

                {/* 2. Academic Program */}
                <div className="form-section">
                  <div className="form-section-title">
                    🎓 Academic Program Proposed
                  </div>
                  <div className="form-row">
                    <div className="form-group" style={{ gridColumn: 'span 2' }}>
                      <label>Program / Discipline Name *</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        required
                        placeholder="e.g. Artificial Intelligence & Data Science" 
                        value={addForm.program_name}
                        onChange={(e) => setAddForm({...addForm, program_name: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Level</label>
                      <select 
                        className="form-select"
                        value={addForm.level}
                        onChange={(e) => setAddForm({...addForm, level: e.target.value})}
                      >
                        <option value="UG">Undergraduate (UG)</option>
                        <option value="PG">Postgraduate (PG)</option>
                        <option value="Diploma">Diploma</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Approved Intake (Seats)</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        min="30"
                        max="600"
                        step="30"
                        value={addForm.approved_intake}
                        onChange={(e) => setAddForm({...addForm, approved_intake: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                {/* 3. Land & Infrastructure Norms */}
                <div className="form-section">
                  <div className="form-section-title">
                    📐 Land & Built-up Infrastructure Norms
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Total Land Area (Acres) *</label>
                      <input 
                        type="number" 
                        step="0.1" 
                        min="1" 
                        className="form-input" 
                        value={addForm.total_area_acres}
                        onChange={(e) => setAddForm({...addForm, total_area_acres: e.target.value})}
                      />
                      <span className="form-hint">AICTE Norm: ≥ 7.5 Acres</span>
                    </div>
                    <div className="form-group">
                      <label>Survey / Khasra No *</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        required
                        value={addForm.survey_khasra_no}
                        onChange={(e) => setAddForm({...addForm, survey_khasra_no: e.target.value})}
                      />
                    </div>
                    <div className="form-group" style={{ justifyContent: 'center' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginTop: 18 }}>
                        <input 
                          type="checkbox" 
                          checked={addForm.is_single_plot}
                          onChange={(e) => setAddForm({...addForm, is_single_plot: e.target.checked})}
                          style={{ width: 16, height: 16, accentColor: 'var(--primary)' }}
                        />
                        <span>Single Contiguous Plot</span>
                      </label>
                    </div>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Total Carpet Area (sq.m) *</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        value={addForm.total_carpet_sqm}
                        onChange={(e) => setAddForm({...addForm, total_carpet_sqm: e.target.value})}
                      />
                      <span className="form-hint">AICTE Norm: ≥ 6,000 sq.m</span>
                    </div>
                    <div className="form-group">
                      <label>Instructional Area (sq.m) *</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        value={addForm.instructional_area_sqm}
                        onChange={(e) => setAddForm({...addForm, instructional_area_sqm: e.target.value})}
                      />
                      <span className="form-hint">AICTE Norm: ≥ 3,000 sq.m</span>
                    </div>
                    <div className="form-group">
                      <label>Administrative Area (sq.m)</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        value={addForm.administrative_area_sqm}
                        onChange={(e) => setAddForm({...addForm, administrative_area_sqm: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Amenities Area (sq.m)</label>
                      <input 
                        type="number" 
                        className="form-input" 
                        value={addForm.amenities_area_sqm}
                        onChange={(e) => setAddForm({...addForm, amenities_area_sqm: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                {/* 4. Automated Testing & Statutory Scenario */}
                <div className="form-section">
                  <div className="form-section-title">
                    ⚡ Statutory Testing & Document Scenario
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8 }}>
                    Select how the system should provision documents to test AICTE rules (Completeness, Land Norms, Consistency, and Tampering Detection):
                  </p>

                  <div className="scenario-grid">
                    {/* Scenario 1: Compliant */}
                    <div 
                      className={`scenario-card COMPLIANT ${addForm.test_scenario === 'COMPLIANT' ? 'active' : ''}`}
                      onClick={() => setAddForm({...addForm, test_scenario: 'COMPLIANT'})}
                    >
                      <div>
                        <div className="scenario-header">
                          <span className="scenario-title">🟢 Compliant Dossier</span>
                          <span className="scenario-target" style={{ background: 'var(--success-bg)', color: 'var(--success)' }}>
                            100% PASS
                          </span>
                        </div>
                        <p className="scenario-desc">
                          Generates all 5 mandatory statutory PDFs matching application specifications with valid metadata and confirmed simulated authority verifications.
                        </p>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--success)', fontWeight: 600 }}>
                        Expected: READY FOR REVIEW
                      </div>
                    </div>

                    {/* Scenario 2: Deficient */}
                    <div 
                      className={`scenario-card DEFICIENT_LAND ${addForm.test_scenario === 'DEFICIENT_LAND' ? 'active' : ''}`}
                      onClick={() => setAddForm({...addForm, test_scenario: 'DEFICIENT_LAND'})}
                    >
                      <div>
                        <div className="scenario-header">
                          <span className="scenario-title">🔴 Area Deficit & Mismatch</span>
                          <span className="scenario-target" style={{ background: 'var(--danger-bg)', color: 'var(--danger)' }}>
                            ISSUES
                          </span>
                        </div>
                        <p className="scenario-desc">
                          Generates deed with land deficit (5.2 acres) & plot number mismatch ("Plot-MISMATCH-999") + builtup carpet deficit to trigger V04, V05 & V07 rules.
                        </p>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--danger)', fontWeight: 600 }}>
                        Expected: HAS ISSUES (Deficit Flags)
                      </div>
                    </div>

                    {/* Scenario 3: Missing Docs */}
                    <div 
                      className={`scenario-card MISSING_DOCS ${addForm.test_scenario === 'MISSING_DOCS' ? 'active' : ''}`}
                      onClick={() => setAddForm({...addForm, test_scenario: 'MISSING_DOCS'})}
                    >
                      <div>
                        <div className="scenario-header">
                          <span className="scenario-title">🟡 Incomplete Dossier</span>
                          <span className="scenario-target" style={{ background: 'var(--warning-bg)', color: 'var(--warning)' }}>
                            INCOMPLETE
                          </span>
                        </div>
                        <p className="scenario-desc">
                          Generates only 2 documents; leaves Building Plan, Fire NOC, and Architect Certificate missing to test V01 Completeness rules.
                        </p>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--warning)', fontWeight: 600 }}>
                        Expected: INCOMPLETE (Missing Checklist)
                      </div>
                    </div>

                    {/* Scenario 4: Tampered PDF */}
                    <div 
                      className={`scenario-card TAMPERED_PDF ${addForm.test_scenario === 'TAMPERED_PDF' ? 'active' : ''}`}
                      onClick={() => setAddForm({...addForm, test_scenario: 'TAMPERED_PDF'})}
                    >
                      <div>
                        <div className="scenario-header">
                          <span className="scenario-title">🛡️ Tampered Anomaly</span>
                          <span className="scenario-target" style={{ background: 'var(--ai-purple-bg)', color: 'var(--ai-purple)' }}>
                            TAMPER FLAG
                          </span>
                        </div>
                        <p className="scenario-desc">
                          Generates Fire NOC altered with Canva tool metadata and 3 incremental %%EOF revision blocks to test V12 & V13 forensic integrity scanners.
                        </p>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--ai-purple)', fontWeight: 600 }}>
                        Expected: HAS ISSUES (Tamper Indicators)
                      </div>
                    </div>

                    {/* Scenario 5: None / Manual */}
                    <div 
                      className={`scenario-card ${addForm.test_scenario === 'NONE' ? 'active' : ''}`}
                      onClick={() => setAddForm({...addForm, test_scenario: 'NONE'})}
                    >
                      <div>
                        <div className="scenario-header">
                          <span className="scenario-title">📁 Empty Dossier (Manual)</span>
                          <span className="scenario-target" style={{ background: 'rgba(56, 189, 248, 0.1)', color: 'var(--primary)' }}>
                            BLANK
                          </span>
                        </div>
                        <p className="scenario-desc">
                          Creates profile with 0 documents. Test manual PDF uploads through the Documents Vault tab.
                        </p>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--primary)', fontWeight: 600 }}>
                        Upload your own PDFs
                      </div>
                    </div>
                  </div>
                </div>

              </div>

              {/* Modal Footer */}
              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  disabled={isAdding}
                  onClick={() => setIsAddModalOpen(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-success" 
                  disabled={isAdding}
                  style={{ minWidth: 200, justifyContent: 'center' }}
                >
                  {isAdding ? (
                    <>⏳ Running Statutory Audit...</>
                  ) : (
                    <>🚀 Ingest College & Run Audit</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
