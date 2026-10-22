// AICTE BluePill Frontend Controller
document.addEventListener("DOMContentLoaded", () => {
  // State
  let applications = [];
  let currentAppId = null;
  let currentRunId = null;
  let currentVerdict = null;
  let llmEnabled = true;

  // DOM Elements
  const tabButtons = document.querySelectorAll(".nav-item");
  const tabContents = document.querySelectorAll(".tab-content");
  const appSelect = document.getElementById("appSelect");
  const appsCardsContainer = document.getElementById("appsCardsContainer");
  const btnReseed = document.getElementById("btnReseed");
  const btnValidateActive = document.getElementById("btnValidateActive");
  const btnRerunVerdict = document.getElementById("btnRerunVerdict");
  const toggleLlmBtn = document.getElementById("toggleLlmBtn");
  const activeModelName = document.getElementById("activeModelName");
  
  // Modal Elements
  const docModal = document.getElementById("docModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalMeta = document.getElementById("modalMeta");
  const modalText = document.getElementById("modalText");

  // Chat Elements
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatMessages = document.getElementById("chatMessages");
  const suggChips = document.querySelectorAll(".sugg-chip");

  // Upload Form
  const uploadForm = document.getElementById("uploadForm");

  // Tab Navigation
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  function switchTab(tabId) {
    tabButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-tab") === tabId));
    tabContents.forEach(c => c.classList.toggle("active", c.id === tabId));

    if (tabId === "verdict-tab" && currentAppId) {
      loadApplicationVerdict(currentAppId);
    } else if (tabId === "tamper-tab" && currentAppId) {
      loadTamperObservations(currentAppId);
    } else if (tabId === "docs-tab" && currentAppId) {
      loadApplicationDocuments(currentAppId);
    }
  }

  // App Selection Change
  appSelect.addEventListener("change", (e) => {
    currentAppId = e.target.value;
    onSelectedAppChanged();
  });

  function onSelectedAppChanged() {
    if (!currentAppId) return;
    loadApplicationStatus(currentAppId);
    // Refresh whatever tab is currently active
    const activeTab = document.querySelector(".tab-content.active");
    if (activeTab) {
      if (activeTab.id === "verdict-tab") loadApplicationVerdict(currentAppId);
      if (activeTab.id === "tamper-tab") loadTamperObservations(currentAppId);
      if (activeTab.id === "docs-tab") loadApplicationDocuments(currentAppId);
    }
  }

  // Fetch Initial Applications
  async function loadApplications() {
    try {
      const res = await fetch("/applications");
      applications = await res.json();
      
      // Populate select
      appSelect.innerHTML = applications.map(app => 
        `<option value="${app.id}">${app.institution_name} (${app.application_number})</option>`
      ).join("");

      if (applications.length > 0 && !currentAppId) {
        currentAppId = applications[0].id;
      }
      appSelect.value = currentAppId;

      document.getElementById("appCountBadge").innerText = applications.length;
      document.getElementById("statTotalApps").innerText = applications.length;

      renderApplicationsDirectory();
      if (currentAppId) {
        loadApplicationStatus(currentAppId);
      }
    } catch (err) {
      console.error("Error loading applications:", err);
    }
  }

  // Render Applications Directory Cards
  async function renderApplicationsDirectory() {
    appsCardsContainer.innerHTML = `<div class="empty-state">Loading application dossiers...</div>`;
    
    let readyCount = 0;
    let incompleteCount = 0;
    let issuesCount = 0;

    const cardsHtml = await Promise.all(applications.map(async (app) => {
      // Fetch status for each
      let statusData = {
        overall_readiness: "PENDING",
        documents_count: 0,
        required_documents_count: 5,
        missing_documents_count: 5,
        current_status: "DRAFT"
      };

      try {
        const sRes = await fetch(`/applications/${app.id}/status`);
        if (sRes.ok) statusData = await sRes.json();
      } catch (e) {}

      if (statusData.overall_readiness === "READY_FOR_REVIEW") readyCount++;
      else if (statusData.overall_readiness === "INCOMPLETE") incompleteCount++;
      else issuesCount++;

      const isSelected = app.id === currentAppId;

      return `
        <div class="app-card ${isSelected ? 'selected' : ''}" data-id="${app.id}">
          <div class="app-card-header">
            <span class="app-number">${app.application_number}</span>
            <span class="readiness-pill ${statusData.overall_readiness}">${statusData.overall_readiness.replace(/_/g, " ")}</span>
          </div>

          <h3 class="app-name">${app.institution_name}</h3>
          <p class="app-location">📍 ${app.district}, ${app.state} • ${app.institution_type.replace(/_/g, " ")}</p>

          <div class="app-stats-row">
            <div>
              <span class="stat-label">Uploaded Docs</span>
              <strong>${statusData.documents_count} / ${statusData.required_documents_count}</strong>
            </div>
            <div>
              <span class="stat-label">Missing Items</span>
              <strong style="color: ${statusData.missing_documents_count > 0 ? 'var(--warning)' : 'var(--success)'}">
                ${statusData.missing_documents_count}
              </strong>
            </div>
            <div>
              <span class="stat-label">Audit Status</span>
              <strong>${statusData.current_status.replace(/_/g, " ")}</strong>
            </div>
          </div>

          <div class="app-card-actions">
            <button class="btn btn-secondary select-app-btn" data-id="${app.id}">Select Dossier</button>
            <button class="btn btn-primary view-verdict-btn" data-id="${app.id}">View Verdict</button>
          </div>
        </div>
      `;
    }));

    appsCardsContainer.innerHTML = cardsHtml.join("");

    document.getElementById("statReadyApps").innerText = readyCount;
    document.getElementById("statIncompleteApps").innerText = incompleteCount;
    document.getElementById("statIssuesApps").innerText = issuesCount;

    // Attach card action listeners
    document.querySelectorAll(".select-app-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        currentAppId = btn.getAttribute("data-id");
        appSelect.value = currentAppId;
        onSelectedAppChanged();
        renderApplicationsDirectory();
      });
    });

    document.querySelectorAll(".view-verdict-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        currentAppId = btn.getAttribute("data-id");
        appSelect.value = currentAppId;
        onSelectedAppChanged();
        switchTab("verdict-tab");
      });
    });
  }

  // Load Application Status
  async function loadApplicationStatus(appId) {
    try {
      const res = await fetch(`/applications/${appId}/status`);
      if (!res.ok) return;
      const statusData = await res.json();
      currentRunId = statusData.latest_run_id;
    } catch (e) {
      console.error(e);
    }
  }

  // Load Final Judgment Verdict
  async function loadApplicationVerdict(appId) {
    const verdictBanner = document.getElementById("verdictBanner");
    const missingDocsList = document.getElementById("missingDocsList");
    const deficienciesList = document.getElementById("deficienciesList");
    const categoryCardsGrid = document.getElementById("categoryCardsGrid");
    const passedChecksList = document.getElementById("passedChecksList");
    const statutoryDisclaimerText = document.getElementById("statutoryDisclaimerText");

    verdictBanner.innerHTML = `<div class="empty-state">Computing statutory judgment...</div>`;

    try {
      // If we don't have a run yet, trigger one
      if (!currentRunId) {
        const runRes = await fetch(`/applications/${appId}/validate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ engine_mode: llmEnabled ? "HYBRID_WITH_LLM" : "DETERMINISTIC_RULES" })
        });
        const runData = await runRes.json();
        currentRunId = runData.id;
      }

      const res = await fetch(`/runs/${currentRunId}/verdict`);
      if (!res.ok) {
        // Fallback: trigger validation
        const runRes = await fetch(`/applications/${appId}/validate`, { method: "POST" });
        const runData = await runRes.json();
        currentRunId = runData.id;
        const vRes = await fetch(`/runs/${currentRunId}/verdict`);
        currentVerdict = await vRes.json();
      } else {
        currentVerdict = await res.json();
      }

      const v = currentVerdict;

      // Update Verdict Banner
      verdictBanner.innerHTML = `
        <div class="verdict-banner ${v.overall_readiness}">
          <div class="verdict-info">
            <span class="readiness-pill ${v.overall_readiness}" style="display:inline-block; margin-bottom: 8px;">
              ${v.overall_readiness.replace(/_/g, " ")}
            </span>
            <h3>${v.verdict_headline}</h3>
            <p>${v.verdict_explanation}</p>
          </div>
          <div class="verdict-gauge">
            <div class="gauge-circle ${v.overall_readiness}">
              ${v.readiness_score_pct}%
            </div>
            <span class="gauge-label">Compliance Norms</span>
          </div>
        </div>
      `;

      // Update Missing Documents
      const missing = v.actionable_checklist.missing_mandatory_documents || [];
      document.getElementById("missingDocsCount").innerText = missing.length;
      if (missing.length === 0) {
        missingDocsList.innerHTML = `<p class="empty-state" style="color:var(--success)">✓ All 5 statutory mandatory documents are uploaded and verified.</p>`;
      } else {
        missingDocsList.innerHTML = `
          <div class="item-list">
            ${missing.map(m => `
              <div class="checklist-item CRITICAL">
                <div class="item-title">${m.name}</div>
                <div class="item-desc">${m.description}</div>
                <div class="item-mandate">Mandate: ${m.regulatory_mandate}</div>
              </div>
            `).join("")}
          </div>
        `;
      }

      // Update Deficiencies
      const defs = v.actionable_checklist.critical_and_major_deficiencies || [];
      document.getElementById("deficienciesCount").innerText = defs.length;
      if (defs.length === 0) {
        deficienciesList.innerHTML = `<p class="empty-state" style="color:var(--success)">✓ No critical or major norm deficiencies recorded.</p>`;
      } else {
        deficienciesList.innerHTML = `
          <div class="item-list">
            ${defs.map(d => `
              <div class="checklist-item ${d.severity}">
                <div class="item-title">[${d.rule_id}] ${d.check_name} (${d.severity})</div>
                <div class="item-desc">${d.finding}</div>
                <div class="item-mandate">Remedy: ${d.required_remedy}</div>
              </div>
            `).join("")}
          </div>
        `;
      }

      // Update Category Breakdown
      const cats = v.category_breakdown || {};
      categoryCardsGrid.innerHTML = Object.keys(cats).map(catKey => {
        const c = cats[catKey];
        return `
          <div class="category-card">
            <div class="cat-header">
              <span class="cat-name">${c.category_name}</span>
              <span class="cat-status ${c.status}">${c.status}</span>
            </div>
            <p class="cat-summary">${c.summary}</p>
          </div>
        `;
      }).join("");

      // Update Passed Checks List
      const passed = v.actionable_checklist.passed_compliance_checks || [];
      passedChecksList.innerHTML = passed.map(p => `<li>${p}</li>`).join("");

      // Disclaimer
      statutoryDisclaimerText.innerText = v.statutory_disclaimer;

    } catch (err) {
      verdictBanner.innerHTML = `<div class="empty-state" style="color:var(--danger)">Error calculating verdict: ${err.message}</div>`;
    }
  }

  // Load Tamper Observations Tab
  async function loadTamperObservations(appId) {
    const container = document.getElementById("tamperObservationsList");
    container.innerHTML = `<div class="empty-state">Analyzing digital document streams & metadata...</div>`;

    try {
      if (!currentRunId) {
        await loadApplicationVerdict(appId);
      }
      
      const res = await fetch(`/runs/${currentRunId}/verdict`);
      const verdict = await res.json();
      const tamperFlags = verdict.actionable_checklist.tampering_integrity_flags || [];

      document.getElementById("tamperCountBadge").innerText = tamperFlags.length > 0 ? tamperFlags.length : "0";

      if (tamperFlags.length === 0) {
        container.innerHTML = `
          <div class="glass-card" style="text-align:center; padding: 40px;">
            <div style="font-size: 2.4rem; margin-bottom: 12px;">✅</div>
            <h3 style="color:var(--success); margin-bottom: 6px;">Zero Tampering Indicators Detected</h3>
            <p style="color:var(--text-muted); font-size: 0.9rem;">
              All uploaded statutory documents exhibit verified linear xref structures, authentic issuing metadata, and compliant creation timestamps.
            </p>
          </div>
        `;
      } else {
        container.innerHTML = tamperFlags.map(t => `
          <div class="tamper-card ${t.severity}">
            <div class="tamper-header">
              <span class="tamper-rule">[${t.rule_id}] ${t.observation_type}</span>
              <span class="readiness-pill HAS_ISSUES">${t.severity}</span>
            </div>
            <div class="tamper-body">
              <h4>Target Document: ${t.document_name}</h4>
              <p>${t.details}</p>
              <div class="tamper-remedy">
                <strong>Recommended Scrutiny Action:</strong> ${t.recommendation}
              </div>
            </div>
          </div>
        `).join("");
      }
    } catch (e) {
      container.innerHTML = `<div class="empty-state" style="color:var(--danger)">Failed to load tampering forensics: ${e.message}</div>`;
    }
  }

  // Load Documents Vault
  async function loadApplicationDocuments(appId) {
    const tbody = document.getElementById("docsTableBody");
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Loading document records...</td></tr>`;

    try {
      const res = await fetch(`/applications/${appId}/documents`);
      const docs = await res.json();

      if (docs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No documents uploaded yet for this application.</td></tr>`;
        return;
      }

      tbody.innerHTML = docs.map(d => {
        return `
          <tr>
            <td><strong>${d.document_type}</strong></td>
            <td>${d.original_filename}</td>
            <td class="hash-mono">${d.sha256_hash.substring(0, 16)}...</td>
            <td>${(d.file_size_bytes / 1024).toFixed(1)} KB</td>
            <td><span class="readiness-pill READY_FOR_REVIEW">PROCESSED</span></td>
            <td>
              <button class="btn btn-secondary view-doc-btn" data-id="${d.id}" style="padding: 4px 10px; font-size: 0.76rem;">View Text</button>
              <button class="btn btn-secondary classify-doc-btn" data-id="${d.id}" style="padding: 4px 10px; font-size: 0.76rem;">SA-01 Check</button>
            </td>
          </tr>
        `;
      }).join("");

      // Attach inspect listeners
      document.querySelectorAll(".view-doc-btn").forEach(btn => {
        btn.addEventListener("click", () => openDocModal(btn.getAttribute("data-id")));
      });

      document.querySelectorAll(".classify-doc-btn").forEach(btn => {
        btn.addEventListener("click", () => classifyDocumentSA01(btn.getAttribute("data-id")));
      });

    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state" style="color:var(--danger)">Error: ${e.message}</td></tr>`;
    }
  }

  // Document Modal Viewer
  async function openDocModal(docId) {
    try {
      const res = await fetch(`/documents/${docId}`);
      const doc = await res.json();

      modalTitle.innerText = `${doc.document_type} — ${doc.original_filename}`;
      modalMeta.innerHTML = `
        <div style="font-size: 0.8rem; color: var(--text-dim); margin-bottom: 8px;">
          <span>SHA-256: <code>${doc.sha256_hash}</code></span> | 
          <span>Size: ${(doc.file_size_bytes/1024).toFixed(1)} KB</span>
        </div>
      `;
      modalText.innerText = doc.extracted_text || "No text could be extracted from this PDF.";
      docModal.classList.add("show");
    } catch (e) {
      alert("Failed to load document text: " + e.message);
    }
  }

  btnCloseModal.addEventListener("click", () => docModal.classList.remove("show"));
  docModal.addEventListener("click", (e) => {
    if (e.target === docModal) docModal.classList.remove("show");
  });

  // SA-01 Subagent Classifier
  async function classifyDocumentSA01(docId) {
    try {
      const res = await fetch(`/agent/classify/${docId}`, { method: "POST" });
      const data = await res.json();
      alert(`SA-01 Classification Report:\n• Declared Type: ${data.declared_type}\n• Verified Type: ${data.verified_type}\n• Confidence: ${(data.confidence*100).toFixed(0)}%\n• Consistency: ${data.is_consistent ? "MATCH" : "MISMATCH"}\n\n${data.explanation}`);
    } catch (e) {
      alert("Classification agent error: " + e.message);
    }
  }

  // Document Upload
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const docType = document.getElementById("uploadDocType").value;
    const fileInput = document.getElementById("uploadFile");
    const submitBtn = document.getElementById("btnUploadSubmit");

    if (!fileInput.files || fileInput.files.length === 0) return;

    const formData = new FormData();
    formData.append("document_type", docType);
    formData.append("file", fileInput.files[0]);

    submitBtn.disabled = true;
    submitBtn.innerText = "Processing...";

    try {
      const res = await fetch(`/applications/${currentAppId}/documents/upload`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        alert("Document uploaded, hashed, and processed successfully!");
        uploadForm.reset();
        loadApplicationDocuments(currentAppId);
        loadApplications(); // update counters
      } else {
        const err = await res.json();
        alert("Upload error: " + (err.detail || "Unknown error"));
      }
    } catch (err) {
      alert("Upload network error: " + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = "Upload & Inspect";
    }
  });

  // Run Statutory Audit on Active Application
  btnValidateActive.addEventListener("click", async () => {
    if (!currentAppId) return;
    btnValidateActive.disabled = true;
    btnValidateActive.innerText = "Auditing...";
    try {
      const res = await fetch(`/applications/${currentAppId}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ engine_mode: llmEnabled ? "HYBRID_WITH_LLM" : "DETERMINISTIC_RULES" })
      });
      const data = await res.json();
      currentRunId = data.id;
      alert(`Audit Completed!\nReadiness Verdict: ${data.overall_readiness}\nFindings Logged: ${data.findings_count}`);
      loadApplications();
      switchTab("verdict-tab");
    } catch (e) {
      alert("Audit error: " + e.message);
    } finally {
      btnValidateActive.disabled = false;
      btnValidateActive.innerText = "⚡ Run Statutory Audit";
    }
  });

  btnRerunVerdict.addEventListener("click", () => {
    btnValidateActive.click();
  });

  // Toggle LLM Kill-Switch
  toggleLlmBtn.addEventListener("click", async () => {
    const newState = !llmEnabled;
    try {
      const res = await fetch(`/agent/config/toggle-llm?enable=${newState}`, { method: "POST" });
      const data = await res.json();
      llmEnabled = data.llm_enabled;
      updateLlmUi();
    } catch (e) {
      console.error(e);
    }
  });

  function updateLlmUi() {
    if (llmEnabled) {
      activeModelName.innerText = "Qwen 2.5 (3B)";
      toggleLlmBtn.querySelector(".toggle-text").innerText = "LLM On";
      toggleLlmBtn.style.background = "rgba(168, 85, 247, 0.3)";
    } else {
      activeModelName.innerText = "Deterministic Only";
      toggleLlmBtn.querySelector(".toggle-text").innerText = "LLM Off";
      toggleLlmBtn.style.background = "rgba(255, 255, 255, 0.1)";
    }
  }

  // Ask BluePill AI Chat
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query || !currentAppId) return;

    chatInput.value = "";

    // Append user message
    appendChatBubble("user", query);

    // Append placeholder assistant message
    const botMsgId = "bot-" + Date.now();
    appendChatBubble("assistant", "Analyzing regulatory evidence...", botMsgId);

    try {
      const res = await fetch("/agent/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          application_id: currentAppId,
          question: query,
          include_statutory_citations: true
        })
      });
      const data = await res.json();
      
      const botElem = document.getElementById(botMsgId);
      if (botElem) {
        let citationsHtml = "";
        if (data.sources && data.sources.length > 0) {
          citationsHtml = `
            <div style="margin-top: 10px;">
              <span style="font-size: 0.74rem; color: var(--text-dim); text-transform: uppercase;">Statutory Evidentiary Sources:</span>
              ${data.sources.map(s => `
                <div class="citation-card">
                  <div class="citation-header">📄 ${s.document_name} (${s.clause_or_page})</div>
                  <div>"${s.extracted_text_snippet}"</div>
                </div>
              `).join("")}
            </div>
          `;
        }

        botElem.querySelector(".bubble-content").innerHTML = `
          <div style="font-size: 0.72rem; color: var(--ai-purple); margin-bottom: 4px; font-weight: 600;">
            ${data.engine_used} • ${data.latency_ms}ms
          </div>
          <p>${data.answer.replace(/\n/g, "<br>")}</p>
          ${citationsHtml}
        `;
      }
    } catch (err) {
      const botElem = document.getElementById(botMsgId);
      if (botElem) {
        botElem.querySelector(".bubble-content").innerHTML = `<p style="color:var(--danger)">Error: ${err.message}</p>`;
      }
    }
  });

  function appendChatBubble(role, text, id = null) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    if (id) bubble.id = id;

    bubble.innerHTML = `
      <div class="avatar">${role === 'assistant' ? '💊' : '👤'}</div>
      <div class="bubble-content">
        <p>${text}</p>
      </div>
    `;

    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Suggestion Chips
  suggChips.forEach(chip => {
    chip.addEventListener("click", () => {
      chatInput.value = chip.getAttribute("data-q");
      chatForm.dispatchEvent(new Event("submit"));
    });
  });

  // Reseed Benchmark
  btnReseed.addEventListener("click", async () => {
    if (!confirm("Re-seed the database with benchmark applications (Compliant, Incomplete, Altered)?")) return;
    btnReseed.disabled = true;
    btnReseed.innerText = "Seeding...";
    try {
      const res = await fetch("/system/reseed", { method: "POST" });
      if (res.ok) {
        alert("Benchmark applications & synthetic PDFs re-seeded successfully!");
        await loadApplications();
      }
    } catch (e) {
      alert("Reseed failed: " + e.message);
    } finally {
      btnReseed.disabled = false;
      btnReseed.innerText = "🔄 Re-seed Benchmark Apps";
    }
  });

  // Add College Modal Controls
  const addCollegeModal = document.getElementById("addCollegeModal");
  const btnOpenAddModalTop = document.getElementById("btnOpenAddModalTop");
  const btnOpenAddModalApps = document.getElementById("btnOpenAddModalApps");
  const btnCloseAddModal = document.getElementById("btnCloseAddModal");
  const btnCancelAddModal = document.getElementById("btnCancelAddModal");
  const btnRndAppNum = document.getElementById("btnRndAppNum");
  const addCollegeForm = document.getElementById("addCollegeForm");
  const btnSubmitAddCollege = document.getElementById("btnSubmitAddCollege");
  const newAppNumInput = document.getElementById("newAppNum");

  function openAddModal() {
    if (newAppNumInput) {
      const rnd = Math.floor(1000 + Math.random() * 9000);
      newAppNumInput.value = `AICTE/2024/APP-${rnd}`;
    }
    if (addCollegeModal) addCollegeModal.style.display = "flex";
  }

  function closeAddModal() {
    if (addCollegeModal) addCollegeModal.style.display = "none";
  }

  if (btnOpenAddModalTop) btnOpenAddModalTop.addEventListener("click", openAddModal);
  if (btnOpenAddModalApps) btnOpenAddModalApps.addEventListener("click", openAddModal);
  if (btnCloseAddModal) btnCloseAddModal.addEventListener("click", closeAddModal);
  if (btnCancelAddModal) btnCancelAddModal.addEventListener("click", closeAddModal);

  if (btnRndAppNum) {
    btnRndAppNum.addEventListener("click", () => {
      const rnd = Math.floor(1000 + Math.random() * 9000);
      if (newAppNumInput) newAppNumInput.value = `AICTE/2024/APP-${rnd}`;
    });
  }

  // Global scenario selector
  window.selectScenario = function(sc) {
    const input = document.getElementById("selectedScenario");
    if (input) input.value = sc;
    document.querySelectorAll(".scenario-card").forEach(c => {
      c.classList.toggle("active", c.getAttribute("data-scenario") === sc);
    });
  };

  if (addCollegeForm) {
    addCollegeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      btnSubmitAddCollege.disabled = true;
      btnSubmitAddCollege.innerText = "⏳ Running Statutory Audit...";

      const scenario = document.getElementById("selectedScenario") ? document.getElementById("selectedScenario").value : "COMPLIANT";
      const payload = {
        application_number: newAppNumInput.value.trim(),
        institution_name: document.getElementById("newInstName").value.trim(),
        institution_type: document.getElementById("newInstType").value,
        application_type: "NEW_INSTITUTION",
        state: document.getElementById("newState").value.trim(),
        district: document.getElementById("newDistrict").value.trim(),
        address: document.getElementById("newAddress").value.trim(),
        programs: [
          {
            program_name: document.getElementById("newProgName").value.trim(),
            level: document.getElementById("newProgLevel").value,
            approved_intake: parseInt(document.getElementById("newIntake").value, 10) || 60
          }
        ],
        land_detail: {
          total_area_acres: parseFloat(document.getElementById("newLandAcres").value) || 8.0,
          is_single_plot: document.getElementById("newSinglePlot").checked,
          survey_khasra_no: document.getElementById("newSurveyNo").value.trim()
        },
        builtup_detail: {
          total_carpet_sqm: parseFloat(document.getElementById("newCarpetSqm").value) || 9000.0,
          instructional_area_sqm: parseFloat(document.getElementById("newInstructSqm").value) || 4500.0,
          administrative_area_sqm: parseFloat(document.getElementById("newAdminSqm").value) || 2000.0,
          amenities_area_sqm: parseFloat(document.getElementById("newAmenitiesSqm").value) || 2000.0
        },
        test_scenario: scenario,
        auto_validate: true
      };

      try {
        const res = await fetch("/applications", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Failed to create institution");
        }

        const data = await res.json();
        closeAddModal();
        await loadApplications();
        currentAppId = data.id;
        appSelect.value = currentAppId;
        switchTab("verdict-tab");
        await loadApplicationVerdict(currentAppId);
      } catch (err) {
        alert("Error adding institution: " + err.message);
      } finally {
        btnSubmitAddCollege.disabled = false;
        btnSubmitAddCollege.innerText = "🚀 Ingest College & Run Audit";
      }
    });
  }

  // Initial Boot
  loadApplications();
  updateLlmUi();
});
