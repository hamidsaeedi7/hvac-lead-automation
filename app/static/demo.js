const form = document.querySelector("#leadForm");
const submitButton = document.querySelector("#submitButton");
const resultPanel = document.querySelector("#automationResult");
const emptyResult = document.querySelector("#emptyResult");
const toast = document.querySelector("#toast");
const storageKey = "leadflow-static-leads-v1";

const emergencyKeywords = {
  "no heat": 5,
  "no heating": 5,
  "no cooling": 4,
  "gas smell": 8,
  "carbon monoxide": 10,
  "burning smell": 8,
  sparking: 8,
  "water leak": 6,
  leaking: 4,
  frozen: 3,
  "stopped working": 4,
  "not working": 3,
  baby: 2,
  elderly: 2,
};

const serviceWeights = {
  emergency_repair: 5,
  furnace_repair: 2,
  air_conditioning: 2,
  heat_pump: 1,
  water_heater: 2,
  maintenance: 0,
  installation_quote: 0,
  indoor_air_quality: 1,
};

const firstActionSeconds = { urgent: 5, high: 15, normal: 30 };
const followUpMilliseconds = {
  urgent: 10 * 60 * 1000,
  high: 2 * 60 * 60 * 1000,
  normal: 24 * 60 * 60 * 1000,
};

const scenarios = {
  emergency: {
    service_type: "emergency_repair",
    message: "No heat since last night and there is a baby in the house.",
    preferred_contact: "phone",
  },
  quote: {
    service_type: "installation_quote",
    message: "Looking for a heat pump quote for a detached home built in 1998.",
    preferred_contact: "email",
  },
};

function seedLeads() {
  const now = Date.now();
  return [
    {
      id: "demo-sarah",
      full_name: "Sarah Mitchell",
      postal_code: "K1T 2N4",
      service_type: "emergency_repair",
      priority: "urgent",
      assigned_to: "Emergency Dispatch",
      status: "urgent_dispatch",
      first_action_seconds: 5,
      created_at: new Date(now - 18 * 60 * 1000).toISOString(),
    },
    {
      id: "demo-daniel",
      full_name: "Daniel Cooper",
      postal_code: "K2J 4B7",
      service_type: "air_conditioning",
      priority: "high",
      assigned_to: "Service Coordinator",
      status: "qualified",
      first_action_seconds: 15,
      created_at: new Date(now - 74 * 60 * 1000).toISOString(),
    },
    {
      id: "demo-emily",
      full_name: "Emily Nguyen",
      postal_code: "K2L 3W1",
      service_type: "installation_quote",
      priority: "normal",
      assigned_to: "Comfort Advisor",
      status: "follow_up_scheduled",
      first_action_seconds: 30,
      created_at: new Date(now - 3 * 60 * 60 * 1000).toISOString(),
    },
  ];
}

function loadStoredLeads() {
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey));
    return Array.isArray(stored) && stored.length ? stored : seedLeads();
  } catch {
    return seedLeads();
  }
}

let cachedLeads = loadStoredLeads();

function persistLeads() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(cachedLeads.slice(0, 50)));
  } catch {
    // The demo remains usable when browser storage is unavailable.
  }
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatService(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  return new Intl.DateTimeFormat("en-CA", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function classifyLead(serviceType, message) {
  const normalized = message.toLowerCase().trim();
  let score = serviceWeights[serviceType] || 0;
  const matched = [];

  Object.entries(emergencyKeywords).forEach(([keyword, weight]) => {
    if (normalized.includes(keyword)) {
      score += weight;
      matched.push(keyword);
    }
  });

  let priority;
  let assignedTo;
  let status;
  let recommendedActions;

  if (score >= 7) {
    priority = "urgent";
    assignedTo = "Emergency Dispatch";
    status = "urgent_dispatch";
    recommendedActions = [
      "Call the lead within 5 minutes",
      "Confirm safety and equipment status",
      "Offer the earliest emergency window",
    ];
  } else if (score >= 4) {
    priority = "high";
    assignedTo = "Service Coordinator";
    status = "qualified";
    recommendedActions = [
      "Review the request within 30 minutes",
      "Confirm service area and availability",
      "Send booking options",
    ];
  } else {
    priority = "normal";
    assignedTo = "Comfort Advisor";
    status = "follow_up_scheduled";
    recommendedActions = [
      "Send a helpful acknowledgement",
      "Collect equipment and home details",
      "Schedule a quote or maintenance follow-up",
    ];
  }

  let reason;
  if (matched.length) reason = `Matched urgency signals: ${matched.slice(0, 3).join(", ")}.`;
  else if (serviceType === "emergency_repair") reason = "Emergency repair was selected.";
  else if (["furnace_repair", "air_conditioning", "water_heater"].includes(serviceType)) {
    reason = "Repair request requires timely service coordination.";
  } else reason = "No immediate safety or outage signal was detected.";

  return { priority, score, reason, assignedTo, status, recommendedActions };
}

function processLead(data) {
  const classification = classifyLead(data.service_type, data.message);
  const createdAt = new Date();
  const followUpDue = new Date(createdAt.getTime() + followUpMilliseconds[classification.priority]);
  const id = crypto.randomUUID ? crypto.randomUUID() : `demo-${createdAt.getTime()}`;
  const notification = classification.priority === "urgent"
    ? `URGENT HVAC lead: ${data.full_name}, ${data.service_type}, ${data.postal_code}. Callback requested now.`
    : `New ${classification.priority} HVAC lead: ${data.full_name}. Next owner: ${classification.assignedTo}.`;

  const lead = {
    id,
    created_at: createdAt.toISOString(),
    ...data,
    priority: classification.priority,
    score: classification.score,
    reason: classification.reason,
    assigned_to: classification.assignedTo,
    status: classification.status,
    recommended_actions: classification.recommendedActions,
    first_action_seconds: firstActionSeconds[classification.priority],
  };
  cachedLeads.unshift(lead);
  persistLeads();

  return {
    ...lead,
    follow_up_due_at: followUpDue.toISOString(),
    simulated_notification: notification,
  };
}

function loadDashboard() {
  const urgent = cachedLeads.filter((lead) => lead.priority === "urgent").length;
  const average = cachedLeads.reduce((sum, lead) => sum + lead.first_action_seconds, 0) / cachedLeads.length;
  document.querySelector("#metricTotal").textContent = cachedLeads.length;
  document.querySelector("#metricUrgent").textContent = urgent;
  document.querySelector("#metricFollowUps").textContent = cachedLeads.length;
  document.querySelector("#metricResponse").textContent = `${Math.round(average)}s`;
}

function renderLeads() {
  const filter = document.querySelector("#priorityFilter").value;
  const rows = cachedLeads.filter((lead) => filter === "all" || lead.priority === filter);
  document.querySelector("#leadRows").innerHTML = rows.length
    ? rows.map((lead) => `
      <tr>
        <td><strong>${escapeHtml(lead.full_name)}</strong><small>${escapeHtml(lead.postal_code)}</small></td>
        <td>${escapeHtml(formatService(lead.service_type))}</td>
        <td><span class="table-priority ${escapeHtml(lead.priority)}">${escapeHtml(lead.priority)}</span></td>
        <td>${escapeHtml(lead.assigned_to)}</td>
        <td>${escapeHtml(formatService(lead.status))}</td>
        <td>${escapeHtml(formatDate(lead.created_at))}</td>
      </tr>`).join("")
    : '<tr><td colspan="6" class="loading-row">No leads match this filter.</td></tr>';
}

function showResult(result) {
  emptyResult.hidden = true;
  resultPanel.hidden = false;
  const badge = document.querySelector("#resultBadge");
  badge.textContent = result.priority;
  badge.className = `priority-badge ${result.priority}`;
  document.querySelector("#resultOwner").textContent = result.assigned_to;
  document.querySelector("#resultStatus").textContent = formatService(result.status);
  document.querySelector("#resultReason").textContent = result.reason;
  document.querySelector("#resultActions").innerHTML = result.recommended_actions
    .map((action) => `<li>${escapeHtml(action)}</li>`).join("");
  document.querySelector("#resultNotification").textContent = result.simulated_notification;
  document.querySelector("#resultFollowUp").textContent = formatDate(result.follow_up_due_at);
  document.querySelector("#resultState").textContent = "Complete";
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const data = Object.fromEntries(new FormData(form).entries());
  data.consent = form.elements.consent.checked;
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "Running workflow...";
  window.setTimeout(() => {
    const result = processLead(data);
    showResult(result);
    loadDashboard();
    renderLeads();
    showToast("Lead classified, routed and scheduled locally.");
    submitButton.disabled = false;
    submitButton.querySelector("span").textContent = "Run automation";
  }, 350);
});

document.querySelectorAll("[data-scenario]").forEach((button) => {
  button.addEventListener("click", () => {
    const scenario = scenarios[button.dataset.scenario];
    Object.entries(scenario).forEach(([name, value]) => { form.elements[name].value = value; });
    showToast(`${button.textContent} scenario loaded.`);
  });
});

document.querySelector("#priorityFilter").addEventListener("change", renderLeads);
document.querySelector("#refreshButton").addEventListener("click", () => {
  loadDashboard();
  renderLeads();
  showToast("Dashboard refreshed from browser storage.");
});

const themeToggle = document.querySelector("#themeToggle");
const savedTheme = localStorage.getItem("leadflow-theme");
if (savedTheme === "dark") document.documentElement.dataset.theme = "dark";
themeToggle.textContent = document.documentElement.dataset.theme === "dark" ? "☀" : "☾";
themeToggle.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("leadflow-theme", next);
  themeToggle.textContent = next === "dark" ? "☀" : "☾";
});

persistLeads();
loadDashboard();
renderLeads();
