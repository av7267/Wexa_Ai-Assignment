// ============================================================
// Config
// ============================================================

const API_BASE = "http://127.0.0.1:8000/api";

const state = {
  accounts: [],
  cycles: [],
  fanouts: [],
  convergence: [],
};

// ============================================================
// Small helpers
// ============================================================

function $(id) {
  return document.getElementById(id);
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);

  if (!res.ok) {
    const err = new Error(`${res.status} ${res.statusText}`);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

function asList(payload) {
  if (Array.isArray(payload)) return payload;

  if (payload && Array.isArray(payload.results)) {
    return payload.results;
  }

  return [];
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatAmount(amount) {
  if (
    amount === undefined ||
    amount === null ||
    amount === ""
  ) {
    return "";
  }

  const n = Number(amount);

  if (Number.isNaN(n)) {
    return String(amount);
  }

  return "₹" + n.toLocaleString("en-IN");
}

function formatDate(dateValue) {
  if (!dateValue) return "";

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return String(dateValue);
  }

  return date.toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function stateBlock(kind, title, sub) {
  return `
    <div class="state-block ${kind === "error" ? "error" : ""}">
      <p class="state-block__title">
        ${escapeHtml(title)}
      </p>

      <p class="state-block__sub">
        ${escapeHtml(sub)}
      </p>
    </div>
  `;
}

// ============================================================
// Skeletons
// ============================================================

function skeletonTableRows(n = 6) {
  let rows = "";

  for (let i = 0; i < n; i++) {
    rows += `
      <div class="skeleton-table-row">
        <div class="skeleton skeleton-line" style="width:70%"></div>
        <div class="skeleton skeleton-line" style="width:85%"></div>
        <div class="skeleton skeleton-line" style="width:50%"></div>
        <div class="skeleton skeleton-line" style="width:40%"></div>
      </div>
    `;
  }

  return rows;
}

function skeletonCards(n = 2) {
  let cards = "";

  for (let i = 0; i < n; i++) {
    cards += `
      <div class="skeleton-card">
        <div class="skeleton skeleton-line" style="width:35%"></div>
        <div class="skeleton skeleton-line" style="width:60%"></div>
        <div class="skeleton skeleton-line" style="width:45%"></div>
        <div class="skeleton skeleton-line" style="width:20%"></div>
      </div>
    `;
  }

  return cards;
}

function skeletonDetail() {
  return `
    <div class="skeleton-detail-block">
      <div
        class="skeleton skeleton-line"
        style="width:120px;height:22px;"
      ></div>

      <div
        class="skeleton skeleton-line"
        style="width:70%;height:44px;border-radius:12px;"
      ></div>

      <div
        class="skeleton skeleton-line"
        style="width:100%;height:120px;border-radius:12px;"
      ></div>
    </div>
  `;
}

// ============================================================
// Health check
// ============================================================

async function checkHealth() {
  $("healthDot").className = "health-dot checking";
  $("healthLabel").textContent = "Checking status…";

  try {
    const data = await apiGet("/health");

    const dbUp =
      data.status === "ok" ||
      data.db === true ||
      data.database === "up" ||
      data.database?.status === "up";

    const dbDown =
      data.status === "down" ||
      data.db === false ||
      data.database === "down" ||
      data.database?.status === "down";

    setHealth(dbDown && !dbUp ? false : true);

  } catch (e) {
    setHealth(false);
  }
}

function setHealth(isUp) {
  const dot = $("healthDot");
  const label = $("healthLabel");
  const banner = $("errorBanner");

  if (isUp) {
    dot.className = "health-dot up";
    label.textContent = "System operational";

    if (banner) {
      banner.classList.add("hidden");
    }
  } else {
    dot.className = "health-dot down";
    label.textContent = "Backend unavailable";

    if (banner) {
      banner.classList.remove("hidden");
    }
  }
}

// ============================================================
// Tabs
// ============================================================

function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");

      const target = btn.dataset.tab;

      document
        .querySelectorAll(".view")
        .forEach((v) => v.classList.remove("active"));

      $(`view-${target}`).classList.add("active");
    });
  });
}

function initCategoryChips() {
  document.querySelectorAll(".category-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      $(chip.dataset.jump)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  });
}

// ============================================================
// Overview stats
// ============================================================

async function loadOverviewStats() {
  try {
    const data = await apiGet("/transactions");

    const totalTransactions =
      data.transaction_count ??
      data.count ??
      0;

    $("statTransactions").textContent =
      Number(totalTransactions).toLocaleString("en-IN");

  } catch (e) {
    $("statTransactions").textContent = "—";
  }
}


function updateDetectionStats() {
  const total =
    state.cycles.length +
    state.fanouts.length +
    state.convergence.length;

  $("statSuspicious").textContent = total;
  $("statRings").textContent = state.cycles.length;
}

// ============================================================
// Accounts
// ============================================================

async function loadAccounts() {
  const tbody = $("accountsTableBody");

  tbody.innerHTML = "";
  $("accountsResultCount").textContent = "";

  const wrap = document.querySelector(".table-wrap");

  tbody.parentElement.style.display = "none";

  wrap.insertAdjacentHTML(
    "afterbegin",
    `<div id="accountsSkeleton">${skeletonTableRows()}</div>`
  );

  try {
    const data = await apiGet("/accounts");

    const accounts = asList(data);

    state.accounts = accounts;

    $("statAccounts").textContent = accounts.length;

    renderAccountsTable(accounts);

  } catch (e) {
    $("accountsSkeleton")?.remove();

    tbody.parentElement.style.display = "";

    tbody.innerHTML = `
      <tr>
        <td colspan="4">
          ${stateBlock(
            "error",
            "Couldn't load accounts",
            e.message
          )}
        </td>
      </tr>
    `;
  }
}

function renderAccountsTable(accounts) {
  $("accountsSkeleton")?.remove();

  const table = document.querySelector(".data-table");

  table.style.display = "";

  const tbody = $("accountsTableBody");

  $("accountsResultCount").textContent =
    accounts.length === state.accounts.length
      ? `${accounts.length} account${accounts.length === 1 ? "" : "s"}`
      : `${accounts.length} of ${state.accounts.length} accounts`;

  if (accounts.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4">
          ${stateBlock(
            "empty",
            "No accounts found",
            "Try adjusting your search."
          )}
        </td>
      </tr>
    `;

    return;
  }

  tbody.innerHTML = accounts
    .map((acc) => {
      const id =
        acc.id ??
        acc.account_id ??
        acc.pk;

      const name =
        acc.name ??
        acc.owner_name ??
        acc.account_name ??
        "—";

      const type =
        acc.type ??
        acc.account_type ??
        "—";

      const activity =
        acc.transaction_count ??
        acc.txn_count ??
        acc.activity_count ??
        acc.num_transactions;

      return `
        <tr data-id="${escapeHtml(id)}">

          <td>
            ${escapeHtml(id)}
          </td>

          <td>
            ${escapeHtml(name)}
          </td>

          <td>
            ${escapeHtml(type)}
          </td>

          <td>
            ${
              activity !== undefined
                ? escapeHtml(activity) + " txns"
                : "—"
            }
          </td>

        </tr>
      `;
    })
    .join("");

  tbody
    .querySelectorAll("tr[data-id]")
    .forEach((row) => {
      row.addEventListener("click", () => {
        showAccountDetail(row.dataset.id);
      });
    });
}

// ============================================================
// Account search
// ============================================================

function initAccountSearch() {
  $("accountSearch").addEventListener("input", (e) => {
    const q = e.target.value
      .trim()
      .toLowerCase();

    if (!q) {
      renderAccountsTable(state.accounts);
      return;
    }

    const filtered = state.accounts.filter((acc) => {
      const id = String(
        acc.id ??
        acc.account_id ??
        acc.pk ??
        ""
      ).toLowerCase();

      const name = String(
        acc.name ??
        acc.owner_name ??
        acc.account_name ??
        ""
      ).toLowerCase();

      return (
        id.includes(q) ||
        name.includes(q)
      );
    });

    renderAccountsTable(filtered);
  });
}

// ============================================================
// Account details
// ============================================================

function showAccountDetail(id) {
  $("accountsListState").classList.add("hidden");
  $("accountDetailState").classList.remove("hidden");

  $("accountDetailContent").innerHTML =
    skeletonDetail();

  loadAccountDetail(id);
}

function initBackToAccounts() {
  $("backToAccounts").addEventListener("click", () => {
    $("accountDetailState").classList.add("hidden");
    $("accountsListState").classList.remove("hidden");
  });
}

async function loadAccountDetail(id) {
  const content = $("accountDetailContent");

  try {
    const data = await apiGet(
      `/accounts/${encodeURIComponent(id)}/transactions`
    );

    const outgoing = Array.isArray(data.outgoing)
      ? data.outgoing
      : [];

    const incoming = Array.isArray(data.incoming)
      ? data.incoming
      : [];

    renderAccountDetail(id, {
      outgoing,
      incoming,
    });

  } catch (e) {
    content.innerHTML = stateBlock(
      "error",
      "Couldn't load transactions",
      e.message
    );
  }
}

function renderAccountDetail(accountId, transactionData) {
  const content = $("accountDetailContent");

  const outgoing = transactionData.outgoing ?? [];
  const incoming = transactionData.incoming ?? [];

  const txns = [
    ...outgoing.map((t) => ({
      ...t,
      from_account: accountId,
      to_account: t.account_id,
    })),

    ...incoming.map((t) => ({
      ...t,
      from_account: t.account_id,
      to_account: accountId,
    })),
  ];

  const account = state.accounts.find(
    (a) =>
      String(
        a.id ??
        a.account_id ??
        a.pk
      ) === String(accountId)
  );

  const name =
    account?.name ??
    account?.owner_name ??
    account?.account_name ??
    "";

  let html = `
    <div class="detail-header">

      <span class="detail-header__id">
        ${escapeHtml(accountId)}
      </span>

      ${
        name
          ? `
            <span class="detail-header__name">
              ${escapeHtml(name)}
            </span>
          `
          : ""
      }

    </div>

    <p class="detail-sub">
      Transaction activity
    </p>
  `;

  if (txns.length === 0) {
    html += stateBlock(
      "empty",
      "No transaction activity",
      "This account has no recorded transactions."
    );

    content.innerHTML = html;

    return;
  }

  

  const largest = [...txns].sort(
    (a, b) =>
      (Number(b.amount ?? b.value) || 0) -
      (Number(a.amount ?? a.value) || 0)
  )[0];

  if (largest) {
    const from =
      largest.from_account ??
      largest.sender ??
      largest.source ??
      "?";

    const to =
      largest.to_account ??
      largest.receiver ??
      largest.destination ??
      "?";

    const amount =
      largest.amount ??
      largest.value;

    html += `
      <div class="flow-highlight">

        <span class="flow-node">
          ${escapeHtml(from)}
        </span>

        <div class="flow-arrow-wrap">

          <span class="amount">
            ${escapeHtml(formatAmount(amount))}
          </span>

          <div class="flow-arrow-line"></div>

        </div>

        <span class="flow-node">
          ${escapeHtml(to)}
        </span>

      </div>
    `;
  }

  const renderTxnLine = (t, direction) => {
    const peer =
      direction === "out"
        ? t.to_account ??
          t.receiver ??
          t.destination
        : t.from_account ??
          t.sender ??
          t.source;

    const amount =
      t.amount ??
      t.value;

    const arrow =
      direction === "out"
        ? "→"
        : "←";

    return `
      <div class="txn-line">

        <span class="txn-line__amount ${direction}">
          ${escapeHtml(formatAmount(amount))}
        </span>

        <span class="txn-line__peer">
          ${arrow}
          ${escapeHtml(peer)}
        </span>

      </div>
    `;
  };

  html += `
    <p
      class="detail-sub"
      style="margin-top:8px;"
    >
      Recent transactions
    </p>

    <div class="txn-columns">

      <div class="txn-col">

        <h3>Outgoing</h3>

        <div class="txn-col-panel">

          ${
            outgoing.length
              ? outgoing
                  .map((t) =>
                    renderTxnLine(t, "out")
                  )
                  .join("")
              : stateBlock(
                  "empty",
                  "No outgoing transfers",
                  "This account hasn't sent any money."
                )
          }

        </div>

      </div>

      <div class="txn-col">

        <h3>Incoming</h3>

        <div class="txn-col-panel">

          ${
            incoming.length
              ? incoming
                  .map((t) =>
                    renderTxnLine(t, "in")
                  )
                  .join("")
              : stateBlock(
                  "empty",
                  "No incoming transfers",
                  "This account hasn't received any money."
                )
          }

        </div>

      </div>

    </div>
  `;

  content.innerHTML = html;
}

// ============================================================
// DETECTIONS
// ============================================================

async function loadAllDetections() {
  /*
    IMPORTANT:

    Your backend exposes:

      GET /api/detections/cycles

    and

      GET /api/detections/fanout

    The fanout response contains BOTH:

      fanout
      convergence

    There is NO:
      /api/detections/convergence

    Therefore we make only two requests.
  */

  await Promise.all([
    loadCycles(),
    loadFanoutAndConvergence(),
  ]);
}

// ============================================================
// Cycles
// ============================================================

async function loadCycles() {
  const el = $("cyclesList");

  el.innerHTML = skeletonCards(2);

  try {
    const data = await apiGet("/detections/cycles");
    console.log("CYCLE RAW RESPONSE:", JSON.stringify(data, null, 2));

    /*
      Expected backend response is something
      like:

      {
        "count": 5,
        "cycles": [...]
      }
    */

    const items =
      Array.isArray(data)
        ? data
        : Array.isArray(data.cycles)
          ? data.cycles
          : Array.isArray(data.results)
            ? data.results
            : [];

    state.cycles = items;

    $("chipCycles").textContent =
      items.length;

    updateDetectionStats();

    el.innerHTML = items.length
      ? items
          .map(renderCyclePattern)
          .join("")
      : stateBlock(
          "empty",
          "No suspicious patterns detected",
          "The system hasn't identified any patterns matching this category."
        );

  } catch (e) {
    state.cycles = [];

    $("chipCycles").textContent = "!";

    el.innerHTML = stateBlock(
      "error",
      "Couldn't load cycles",
      e.message
    );

    updateDetectionStats();
  }
}

// ============================================================
// Fan-out + convergence
// ============================================================

async function loadFanoutAndConvergence() {
  const fanoutEl = $("fanoutList");
  const convergenceEl = $("convergenceList");

  fanoutEl.innerHTML =
    skeletonCards(2);

  convergenceEl.innerHTML =
    skeletonCards(2);

  try {
    const data = await apiGet(
      "/detections/fanout"
    );

    /*
      Your ACTUAL backend response:

      {
        "fanout": {
          "count": 8,
          "detections": [...]
        },

        "convergence": {
          "count": 3,
          "detections": [...]
        }
      }
    */

    const fanoutData =
      data?.fanout ?? {};

    const convergenceData =
      data?.convergence ?? {};

    const fanoutItems =
      Array.isArray(
        fanoutData.detections
      )
        ? fanoutData.detections
        : [];

    const convergenceItems =
      Array.isArray(
        convergenceData.detections
      )
        ? convergenceData.detections
        : [];

    state.fanouts = fanoutItems;
    state.convergence =
      convergenceItems;

    $("chipFanout").textContent =
      fanoutItems.length;

    $("chipConvergence").textContent =
      convergenceItems.length;

    updateDetectionStats();

    // --------------------------
    // Fan-outs
    // --------------------------

    fanoutEl.innerHTML =
      fanoutItems.length
        ? fanoutItems
            .map(renderFanoutPattern)
            .join("")
        : stateBlock(
            "empty",
            "No suspicious patterns detected",
            "The system hasn't identified any patterns matching this category."
          );

    // --------------------------
    // Convergence
    // --------------------------

    convergenceEl.innerHTML =
      convergenceItems.length
        ? convergenceItems
            .map(renderConvergencePattern)
            .join("")
        : stateBlock(
            "empty",
            "No suspicious patterns detected",
            "The system hasn't identified any patterns matching this category."
          );

  } catch (e) {
    state.fanouts = [];
    state.convergence = [];

    $("chipFanout").textContent = "!";
    $("chipConvergence").textContent = "!";

    fanoutEl.innerHTML = stateBlock(
      "error",
      "Couldn't load fan-outs",
      e.message
    );

    convergenceEl.innerHTML =
      stateBlock(
        "error",
        "Couldn't load convergence patterns",
        e.message
      );

    updateDetectionStats();
  }
}

// ============================================================
// Cycle renderer
// ============================================================

function renderCyclePattern(c) {
  /*
    We support the likely field names used by
    the detector.

    If the backend returns an array under one of
    these properties, it will render correctly.
  */

    const rawChain =
    c.accounts ?? c.account_chain ?? c.cycle ?? c.nodes ?? c.path ??
    c.account_ids ?? c.nodes_in_cycle ?? c.ring ?? c.ring_accounts ??
    c.chain ?? c.sequence ?? c.account_sequence ?? c.cycle_accounts ??
    c.members ?? c.accounts_in_cycle ?? [];

  // Handle both ["A014", "A027", ...] and [{account_id: "A014"}, ...]
  const normalizedChain = Array.isArray(rawChain)
    ? rawChain.map((n) => (typeof n === "object" && n !== null ? (n.account_id ?? n.id ?? n.account ?? JSON.stringify(n)) : n))
    : [];

  const window =
    c.time_window ??
    c.window ??
    c.duration ??
    c.span_hours ??
    "";

  const txnCount =
  c.transaction_count ??
  c.txn_count ??
  c.transactions ??
  normalizedChain.length;

  /*
    Don't show a fake cycle with "0 accounts".

    If your backend has not supplied nodes,
    clearly identify the issue.
  */

  if (normalizedChain.length === 0) {
    return `
      <div class="pattern-card">

        <span class="pattern-card__badge">
          Cycle detected
        </span>

        <p class="pattern-card__desc">
          Circular transaction flow
        </p>

        <div class="state-block">

          <p class="state-block__title">
            Cycle details unavailable
          </p>

          <p class="state-block__sub">
            The backend returned a cycle without account nodes.
          </p>

        </div>

        <div class="pattern-card__meta">

          0 accounts
          · ${escapeHtml(txnCount)}
          transactions

          ${
            window
              ? ` · window ${escapeHtml(window)}`
              : ""
          }

        </div>

      </div>
    `;
  }

  const nodesHtml =
    normalizedChain
      .map(
        (node, index) => `
          <div class="cycle-node-row">

            <span class="cycle-node">
              ${escapeHtml(node)}
            </span>

            ${
              index <
              normalizedChain.length - 1
                ? `
                  <span class="cycle-down-arrow">
                    ↓
                  </span>
                `
                : ""
            }

          </div>
        `
      )
      .join("");

  return `
    <div class="pattern-card">

      <span class="pattern-card__badge">
        Cycle detected
      </span>

      <p class="pattern-card__desc">
        Circular transaction flow
      </p>

      <div class="cycle-chain">

        ${nodesHtml}

        <div class="cycle-loop-back">
          ↩ back to
          ${escapeHtml(normalizedChain[0])}
        </div>

      </div>

      <div class="pattern-card__meta">

        ${escapeHtml(normalizedChain.length)}
        accounts

        ·

        ${escapeHtml(txnCount)}
        transactions

        ${
          window
            ? ` · window ${escapeHtml(window)}`
            : ""
        }

      </div>

    </div>
  `;
}

// ============================================================
// Fan-out renderer
// ============================================================

function renderFanoutPattern(f) {
  const source =
    f.source_account ??
    f.hub ??
    f.origin ??
    "Unknown";

  const targets =
    f.recipients ??
    f.target_accounts ??
    f.targets ??
    [];

  const normalizedTargets =
    Array.isArray(targets)
      ? targets
      : [];

  const rows =
    normalizedTargets
      .map(
        (target) => `
          <div class="branch-row">

            <span class="branch-row__arrow">
              →
            </span>

            <span class="flow-node">
              ${escapeHtml(target)}
            </span>

          </div>
        `
      )
      .join("");

  const windowStart =
    f.window_start ??
    f.timestamp ??
    f.created_at;

  return `
    <div class="pattern-card">

      <span class="pattern-card__badge">
        Fan-out detected
      </span>

      <p class="pattern-card__desc">
        One account sending funds to multiple accounts
      </p>

      <div class="branch-diagram">

        <span class="branch-hub">
          ${escapeHtml(source)}
        </span>

        <span class="branch-connector"></span>

        <div class="branch-rows">
          ${rows}
        </div>

      </div>

      <div class="pattern-card__meta">

        ${escapeHtml(normalizedTargets.length)}
        recipients

        ${
          windowStart
            ? ` · ${escapeHtml(formatDate(windowStart))}`
            : ""
        }

      </div>

    </div>
  `;
}

// ============================================================
// Convergence renderer
// ============================================================

function renderConvergencePattern(c) {
  const target =
    c.collector_account ??
    c.target_account ??
    c.hub ??
    c.destination ??
    "Unknown";

  const sources =
    c.recipients ??
    c.source_accounts ??
    c.sources ??
    c.senders ??
    [];

  const normalizedSources =
    Array.isArray(sources)
      ? sources
      : [];

  const rows =
    normalizedSources
      .map(
        (source) => `
          <div class="branch-row">

            <span class="flow-node">
              ${escapeHtml(source)}
            </span>

            <span class="branch-row__arrow">
              →
            </span>

          </div>
        `
      )
      .join("");

  const span =
    c.span_hours ??
    c.time_window ??
    c.window ??
    "";

  return `
    <div class="pattern-card">

      <span class="pattern-card__badge">
        Convergence detected
      </span>

      <p class="pattern-card__desc">
        Multiple accounts sending funds to one account
      </p>

      <div class="branch-diagram">

        <div class="branch-rows">
          ${rows}
        </div>

        <span class="branch-connector"></span>

        <span class="branch-hub">
          ${escapeHtml(target)}
        </span>

      </div>

      <div class="pattern-card__meta">

        ${escapeHtml(normalizedSources.length)}
        sources

        ${
          span
            ? ` · ${escapeHtml(span)} hour window`
            : ""
        }

      </div>

    </div>
  `;
}

// ============================================================
// Init
// ============================================================

function init() {
  initTabs();
  initAccountSearch();
  initBackToAccounts();
  initCategoryChips();

  $("errorBannerRetry").addEventListener(
    "click",
    () => {
      checkHealth();
      loadAccounts();
      loadOverviewStats();
      loadAllDetections();
    }
  );

  checkHealth();
  loadAccounts();
  loadOverviewStats();
  loadAllDetections();
}

document.addEventListener(
  "DOMContentLoaded",
  init
);