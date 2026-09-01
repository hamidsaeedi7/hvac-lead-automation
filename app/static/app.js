const form = document.querySelector("#leadForm");
const submitButton = document.querySelector("#submitButton");
const resultPanel = document.querySelector("#automationResult");
const emptyResult = document.querySelector("#emptyResult");
const toast = document.querySelector("#toast");
let cachedLeads = [];

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
  return new Intl.DateTimeFormat("en-CA", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = Array.isArray(payload.detail)
      ? payload.detail.map((item) => item.msg).join(", ")
      : payload.detail;
    throw new Error(detail || "The workflow could not be completed.");
  }
  return response.json();
}

async function loadDashboard() {
  const stats = await request("/api/dashboard");
  document.querySelector("#metricTotal").textContent = stats.total;
  document.querySelector("#metricUrgent").textContent = stats.urgent;
  document.querySelector("#metricFollowUps").textContent = stats.open_follow_ups;
  document.querySelector("#metricResponse").textContent = `${stats.average_routing_target_seconds}s`;
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

async function loadLeads() {
  cachedLeads = await request("/api/leads");
  renderLeads();
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
  document.querySelector("#resultActions").innerHTML = result.recommended_actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("");
  document.querySelector("#resultNotification").textContent = result.simulated_notification;
  document.querySelector("#resultFollowUp").textContent = formatDate(result.follow_up_due_at);
  document.querySelector("#resultState").textContent = "Complete";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  data.consent = form.elements.consent.checked;
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "Running workflow...";
  try {
    const result = await request("/api/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    showResult(result);
    await Promise.all([loadDashboard(), loadLeads()]);
    showToast("Lead classified, routed and scheduled.");
  } catch (error) {
    showToast(error.message);
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span").textContent = "Run automation";
  }
});

document.querySelectorAll("[data-scenario]").forEach((button) => {
  button.addEventListener("click", () => {
    const scenario = scenarios[button.dataset.scenario];
    Object.entries(scenario).forEach(([name, value]) => { form.elements[name].value = value; });
    showToast(`${button.textContent} scenario loaded.`);
  });
});

document.querySelector("#priorityFilter").addEventListener("change", renderLeads);
document.querySelector("#refreshButton").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await Promise.all([loadDashboard(), loadLeads()]);
    showToast("Dashboard refreshed.");
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
  }
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

Promise.all([loadDashboard(), loadLeads()]).catch((error) => showToast(error.message));
