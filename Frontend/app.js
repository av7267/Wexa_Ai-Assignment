// ============================================================
// CONFIGURATION
// ============================================================

const API_BASE = (window.BACKEND_URL || "http://127.0.0.1:8000") + "/api";

const REQUEST_TIMEOUT = 30000;

const state = {
  accounts: [],
  cycles: [],
  fanouts: [],
  convergence: [],

  activeAccountId: null,

  loading: {
    accounts: false,
    transactions: false,
    cycles: false,
    fanout: false,
  },
};


// ============================================================
// DOM HELPERS
// ============================================================

function $(id) {
  return document.getElementById(id);
}


// ============================================================
// API
// ============================================================

async function apiGet(path) {

  const controller = new AbortController();

  const timeout = setTimeout(() => {
    controller.abort();
  }, REQUEST_TIMEOUT);

  try {

    const response = await fetch(
      `${API_BASE}${path}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        signal: controller.signal,
      }
    );

    if (!response.ok) {

      let message = `${response.status} ${response.statusText}`;

      try {
        const errorBody = await response.json();

        if (errorBody?.detail) {
          message = errorBody.detail;
        }

        if (errorBody?.message) {
          message = errorBody.message;
        }

      } catch {
        // Keep HTTP status message.
      }

      const error = new Error(message);

      error.status = response.status;

      throw error;
    }

    return await response.json();

  } catch (error) {

    if (error.name === "AbortError") {
      throw new Error(
        "The backend request timed out."
      );
    }

    if (
      error instanceof TypeError
    ) {
      throw new Error(
        "Unable to connect to the backend."
      );
    }

    throw error;

  } finally {
    clearTimeout(timeout);
  }
}


// ============================================================
// GENERAL HELPERS
// ============================================================

function asList(payload) {

  if (Array.isArray(payload)) {
    return payload;
  }

  if (
    payload &&
    Array.isArray(payload.results)
  ) {
    return payload.results;
  }

  if (
    payload &&
    Array.isArray(payload.items)
  ) {
    return payload.items;
  }

  return [];
}


function escapeHtml(value) {

  return String(value ?? "")
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
    return "—";
  }

  const number = Number(amount);

  if (Number.isNaN(number)) {
    return String(amount);
  }

  return `₹${number.toLocaleString("en-IN")}`;
}


function formatDate(value) {

  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString(
    "en-IN",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }
  );
}


function stateBlock(
  type,
  title,
  message
) {

  return `
    <div class="state-block ${type === "error" ? "error" : ""}">

      <p class="state-block__title">
        ${escapeHtml(title)}
      </p>

      <p class="state-block__sub">
        ${escapeHtml(message)}
      </p>

    </div>
  `;
}


function getAccountId(account) {

  return (
    account?.id ??
    account?.account_id ??
    account?.pk ??
    ""
  );
}


function getAccountName(account) {

  return (
    account?.name ??
    account?.owner_name ??
    account?.account_name ??
    "—"
  );
}


// ============================================================
// SKELETONS
// ============================================================

function skeletonTableRows(count = 7) {

  let html = `
    <div class="skeleton-table">
  `;

  for (let i = 0; i < count; i++) {

    html += `
      <div class="skeleton-table-row">

        <div
          class="skeleton skeleton-line"
          style="width: 65%"
        ></div>

        <div
          class="skeleton skeleton-line"
          style="width: 82%"
        ></div>

        <div
          class="skeleton skeleton-line"
          style="width: 45%"
        ></div>

        <div
          class="skeleton skeleton-line"
          style="width: 40%"
        ></div>

      </div>
    `;
  }

  html += `</div>`;

  return html;
}


function skeletonCards(count = 3) {

  let html = "";

  for (let i = 0; i < count; i++) {

    html += `
      <div class="skeleton-card">

        <div
          class="skeleton skeleton-line"
          style="width: 35%; height: 18px"
        ></div>

        <div
          class="skeleton skeleton-line"
          style="width: 78%"
        ></div>

        <div
          class="skeleton skeleton-line"
          style="width: 100%; height: 70px; margin-top: 12px"
        ></div>

        <div
          class="skeleton skeleton-line"
          style="width: 48%; margin-top: 12px"
        ></div>

      </div>
    `;
  }

  return html;
}


function skeletonDetail() {

  return `
    <div class="skeleton-detail-block">

      <div
        class="skeleton"
        style="width: 90px; height: 24px"
      ></div>

      <div
        class="skeleton"
        style="width: 230px; height: 24px"
      ></div>

      <div
        class="skeleton"
        style="width: 100%; height: 105px; border-radius: 10px"
      ></div>

      <div
        class="skeleton"
        style="width: 100%; height: 150px; border-radius: 10px"
      ></div>

    </div>
  `;
}


// ============================================================
// HEALTH
// ============================================================

async function checkHealth() {

  setHealth("checking");

  try {

    const data = await apiGet("/health");

    const explicitlyDown =
      data?.status === "down" ||
      data?.db === false ||
      data?.database === "down" ||
      data?.database?.status === "down";

    if (explicitlyDown) {
      setHealth("down");
    } else {
      setHealth("up");
    }

  } catch {

    setHealth("down");
  }
}


function setHealth(status) {

  const dot = $("healthDot");
  const label = $("healthLabel");
  const banner = $("errorBanner");

  dot.className =
    `health-dot ${status}`;

  if (status === "up") {

    label.textContent =
      "System operational";

    banner?.classList.add("hidden");

    return;
  }

  if (status === "checking") {

    label.textContent =
      "Checking system";

    return;
  }

  label.textContent =
    "Backend unavailable";

  banner?.classList.remove("hidden");
}


// ============================================================
// TABS
// ============================================================

function initTabs() {

  document
    .querySelectorAll(".tab-btn")
    .forEach((button) => {

      button.addEventListener(
        "click",
        () => {

          const target =
            button.dataset.tab;

          document
            .querySelectorAll(".tab-btn")
            .forEach((btn) => {

              const active =
                btn === button;

              btn.classList.toggle(
                "active",
                active
              );

              btn.setAttribute(
                "aria-selected",
                String(active)
              );
            });

          document
            .querySelectorAll(".view")
            .forEach((view) => {

              view.classList.toggle(
                "active",
                view.id === `view-${target}`
              );
            });

        }
      );

    });
}


// ============================================================
// CATEGORY NAVIGATION
// ============================================================

function initCategoryChips() {

  document
    .querySelectorAll(".category-chip")
    .forEach((chip) => {

      chip.addEventListener(
        "click",
        () => {

          const target =
            $(chip.dataset.jump);

          if (!target) {
            return;
          }

          target.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });

        }
      );

    });
}


// ============================================================
// OVERVIEW
// ============================================================

async function loadOverviewStats() {

  $("statTransactions").textContent = "…";

  try {

    const data =
      await apiGet("/transactions");

    const total =
      data?.transaction_count ??
      data?.count ??
      (Array.isArray(data)
        ? data.length
        : 0);

    $("statTransactions").textContent =
      Number(total).toLocaleString("en-IN");

  } catch {

    $("statTransactions").textContent =
      "—";
  }
}


function updateDetectionStats() {

  const total =
    state.cycles.length +
    state.fanouts.length +
    state.convergence.length;

  $("statSuspicious").textContent =
    total.toLocaleString("en-IN");

  $("statRings").textContent =
    state.cycles.length.toLocaleString("en-IN");
}


// ============================================================
// ACCOUNTS
// ============================================================

async function loadAccounts() {

  if (state.loading.accounts) {
    return;
  }

  state.loading.accounts = true;

  const workspace =
    $("accountsListState");

  const tableWrap =
    workspace.querySelector(".table-wrap");

  tableWrap.innerHTML =
    skeletonTableRows();

  $("accountsResultCount").textContent =
    "Loading…";

  $("statAccounts").textContent =
    "…";

  try {

    const data =
      await apiGet("/accounts");

    state.accounts =
      asList(data);

    $("statAccounts").textContent =
      state.accounts.length.toLocaleString("en-IN");

    renderAccountsTable(
      state.accounts
    );

  } catch (error) {

    $("statAccounts").textContent =
      "—";

    $("accountsResultCount").textContent =
      "Unavailable";

    tableWrap.innerHTML =
      stateBlock(
        "error",
        "Accounts unavailable",
        getFriendlyError(error)
      );

  } finally {

    state.loading.accounts = false;
  }
}


function renderAccountsTable(accounts) {

  const tableWrap =
    document.querySelector(
      "#accountsListState .table-wrap"
    );

  $("accountsResultCount").textContent =
    accounts.length === state.accounts.length
      ? `${accounts.length} account${accounts.length === 1 ? "" : "s"}`
      : `${accounts.length} of ${state.accounts.length} accounts`;

  if (accounts.length === 0) {

    tableWrap.innerHTML =
      stateBlock(
        "empty",
        "No accounts found",
        "No account matches the current search."
      );

    return;
  }

  tableWrap.innerHTML = `
    <table class="data-table">

      <thead>
        <tr>
          <th scope="col">Account</th>
          <th scope="col">Owner</th>
          <th scope="col">Type</th>
          <th scope="col">Activity</th>
        </tr>
      </thead>

      <tbody id="accountsTableBody">
      </tbody>

    </table>
  `;

  const tbody =
    $("accountsTableBody");

  tbody.innerHTML =
    accounts
      .map(renderAccountRow)
      .join("");

  tbody
    .querySelectorAll("tr[data-id]")
    .forEach((row) => {

      row.addEventListener(
        "click",
        () => {
          showAccountDetail(
            row.dataset.id
          );
        }
      );

    });
}


function renderAccountRow(account) {

  const id =
    getAccountId(account);

  const name =
    getAccountName(account);

  const type =
    account?.type ??
    account?.account_type ??
    "—";

  const activity =
    account?.transaction_count ??
    account?.txn_count ??
    account?.activity_count ??
    account?.num_transactions;

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
            ? `${escapeHtml(activity)} txns`
            : "—"
        }
      </td>

    </tr>
  `;
}


// ============================================================
// ACCOUNT SEARCH
// ============================================================

function initAccountSearch() {

  const input =
    $("accountSearch");

  input.addEventListener(
    "input",
    (event) => {

      const query =
        event.target.value
          .trim()
          .toLowerCase();

      if (!query) {

        renderAccountsTable(
          state.accounts
        );

        return;
      }

      const filtered =
        state.accounts.filter(
          (account) => {

            const id =
              String(
                getAccountId(account)
              ).toLowerCase();

            const name =
              String(
                getAccountName(account)
              ).toLowerCase();

            return (
              id.includes(query) ||
              name.includes(query)
            );
          }
        );

      renderAccountsTable(
        filtered
      );
    }
  );

  document.addEventListener(
    "keydown",
    (event) => {

      if (
        event.key === "/" &&
        document.activeElement !== input
      ) {

        event.preventDefault();

        input.focus();
      }
    }
  );
}


// ============================================================
// ACCOUNT DETAIL
// ============================================================

function showAccountDetail(id) {

  state.activeAccountId = id;

  $("accountsListState")
    .classList
    .add("hidden");

  $("accountDetailState")
    .classList
    .remove("hidden");

  $("accountDetailContent")
    .innerHTML =
    skeletonDetail();

  loadAccountDetail(id);
}


function initBackToAccounts() {

  $("backToAccounts")
    .addEventListener(
      "click",
      () => {

        state.activeAccountId =
          null;

        $("accountDetailState")
          .classList
          .add("hidden");

        $("accountsListState")
          .classList
          .remove("hidden");

      }
    );
}


async function loadAccountDetail(id) {

  if (state.loading.transactions) {
    return;
  }

  state.loading.transactions = true;

  try {

    const data =
      await apiGet(
        `/accounts/${encodeURIComponent(id)}/transactions`
      );

    renderAccountDetail(
      id,
      {
        outgoing:
          Array.isArray(data?.outgoing)
            ? data.outgoing
            : [],

        incoming:
          Array.isArray(data?.incoming)
            ? data.incoming
            : [],
      }
    );

  } catch (error) {

    $("accountDetailContent")
      .innerHTML =
      stateBlock(
        "error",
        "Transaction data unavailable",
        getFriendlyError(error)
      );

  } finally {

    state.loading.transactions = false;
  }
}


function renderAccountDetail(
  accountId,
  transactionData
) {

  const content =
    $("accountDetailContent");

  const outgoing =
    transactionData.outgoing ?? [];

  const incoming =
    transactionData.incoming ?? [];

  const transactions = [
    ...outgoing.map((transaction) => ({
      ...transaction,
      from_account: accountId,
      to_account:
        transaction.account_id ??
        transaction.to_account,
    })),

    ...incoming.map((transaction) => ({
      ...transaction,
      from_account:
        transaction.account_id ??
        transaction.from_account,
      to_account: accountId,
    })),
  ];

  const account =
    state.accounts.find(
      (item) =>
        String(
          getAccountId(item)
        ) === String(accountId)
    );

  const name =
    account
      ? getAccountName(account)
      : "";

  let html = `
    <div class="detail-header">

      <span class="detail-header__id">
        ${escapeHtml(accountId)}
      </span>

      ${
        name && name !== "—"
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

  if (transactions.length === 0) {

    html += stateBlock(
      "empty",
      "No transaction activity",
      "This account has no recorded incoming or outgoing transactions."
    );

    content.innerHTML =
      html;

    return;
  }


  const largest =
    [...transactions].sort(
      (a, b) =>
        (
          Number(
            b.amount ??
            b.value
          ) || 0
        ) -
        (
          Number(
            a.amount ??
            a.value
          ) || 0
        )
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
            ${escapeHtml(
              formatAmount(amount)
            )}
          </span>

          <div class="flow-arrow-line"></div>

        </div>

        <span class="flow-node">
          ${escapeHtml(to)}
        </span>

      </div>
    `;
  }


  html += `
    <p class="detail-sub">
      Recent transactions
    </p>

    <div class="txn-columns">

      <div class="txn-col">

        <h3>
          Outgoing
        </h3>

        <div class="txn-col-panel">

          ${
            outgoing.length
              ? outgoing
                  .map(
                    (transaction) =>
                      renderTxnLine(
                        transaction,
                        "out"
                      )
                  )
                  .join("")
              : stateBlock(
                  "empty",
                  "No outgoing transfers",
                  "This account has not sent any recorded funds."
                )
          }

        </div>

      </div>


      <div class="txn-col">

        <h3>
          Incoming
        </h3>

        <div class="txn-col-panel">

          ${
            incoming.length
              ? incoming
                  .map(
                    (transaction) =>
                      renderTxnLine(
                        transaction,
                        "in"
                      )
                  )
                  .join("")
              : stateBlock(
                  "empty",
                  "No incoming transfers",
                  "This account has not received any recorded funds."
                )
          }

        </div>

      </div>

    </div>
  `;

  content.innerHTML =
    html;
}


function renderTxnLine(
  transaction,
  direction
) {

  const peer =
    direction === "out"
      ? transaction.to_account ??
        transaction.receiver ??
        transaction.destination ??
        "Unknown"
      : transaction.from_account ??
        transaction.sender ??
        transaction.source ??
        "Unknown";

  const amount =
    transaction.amount ??
    transaction.value;

  const arrow =
    direction === "out"
      ? "→"
      : "←";

  return `
    <div class="txn-line">

      <span
        class="txn-line__amount ${direction}"
      >
        ${escapeHtml(
          formatAmount(amount)
        )}
      </span>

      <span class="txn-line__peer">
        ${arrow}
        ${escapeHtml(peer)}
      </span>

    </div>
  `;
}


// ============================================================
// DETECTIONS
// ============================================================

async function loadAllDetections() {

  await Promise.all([
    loadCycles(),
    loadFanoutAndConvergence(),
  ]);
}


// ============================================================
// CYCLES
// ============================================================

async function loadCycles() {

  if (state.loading.cycles) {
    return;
  }

  state.loading.cycles = true;

  const element =
    $("cyclesList");

  element.innerHTML =
    skeletonCards(3);

  $("chipCycles").textContent =
    "…";

  try {

    const data =
      await apiGet(
        "/detections/cycles"
      );

    const items =
      Array.isArray(data)
        ? data
        : Array.isArray(data?.cycles)
          ? data.cycles
          : Array.isArray(data?.results)
            ? data.results
            : [];

    state.cycles =
      items;

    $("chipCycles").textContent =
      items.length;

    element.innerHTML =
      items.length
        ? items
            .map(renderCyclePattern)
            .join("")
        : stateBlock(
            "empty",
            "No cycles detected",
            "The detection engine has not identified circular transaction flow."
          );

  } catch (error) {

    state.cycles = [];

    $("chipCycles").textContent =
      "—";

    element.innerHTML =
      stateBlock(
        "error",
        "Cycle detection unavailable",
        getFriendlyError(error)
      );

  } finally {

    state.loading.cycles = false;

    updateDetectionStats();
  }
}


// ============================================================
// FAN-OUT + CONVERGENCE
// ============================================================

async function loadFanoutAndConvergence() {

  if (state.loading.fanout) {
    return;
  }

  state.loading.fanout = true;

  const fanoutElement =
    $("fanoutList");

  const convergenceElement =
    $("convergenceList");

  fanoutElement.innerHTML =
    skeletonCards(3);

  convergenceElement.innerHTML =
    skeletonCards(3);

  $("chipFanout").textContent =
    "…";

  $("chipConvergence").textContent =
    "…";

  try {

    const data =
      await apiGet(
        "/detections/fanout"
      );

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

    state.fanouts =
      fanoutItems;

    state.convergence =
      convergenceItems;


    $("chipFanout").textContent =
      fanoutItems.length;

    $("chipConvergence").textContent =
      convergenceItems.length;


    fanoutElement.innerHTML =
      fanoutItems.length
        ? fanoutItems
            .map(renderFanoutPattern)
            .join("")
        : stateBlock(
            "empty",
            "No fan-outs detected",
            "No one-to-many transaction distribution matches the detection criteria."
          );


    convergenceElement.innerHTML =
      convergenceItems.length
        ? convergenceItems
            .map(
              renderConvergencePattern
            )
            .join("")
        : stateBlock(
            "empty",
            "No convergence detected",
            "No many-to-one transaction aggregation matches the detection criteria."
          );

  } catch (error) {

    state.fanouts = [];
    state.convergence = [];

    $("chipFanout").textContent =
      "—";

    $("chipConvergence").textContent =
      "—";

    fanoutElement.innerHTML =
      stateBlock(
        "error",
        "Fan-out detection unavailable",
        getFriendlyError(error)
      );

    convergenceElement.innerHTML =
      stateBlock(
        "error",
        "Convergence detection unavailable",
        getFriendlyError(error)
      );

  } finally {

    state.loading.fanout = false;

    updateDetectionStats();
  }
}


// ============================================================
// CYCLE RENDERER
// ============================================================

function renderCyclePattern(cycle) {

  const rawChain =
    cycle.accounts ??
    cycle.account_chain ??
    cycle.cycle ??
    cycle.nodes ??
    cycle.path ??
    cycle.account_ids ??
    cycle.nodes_in_cycle ??
    cycle.ring ??
    cycle.ring_accounts ??
    cycle.chain ??
    cycle.sequence ??
    cycle.account_sequence ??
    cycle.cycle_accounts ??
    cycle.members ??
    cycle.accounts_in_cycle ??
    [];

  const normalizedChain =
    Array.isArray(rawChain)
      ? rawChain.map(
          (node) =>
            typeof node === "object" &&
            node !== null
              ? (
                  node.account_id ??
                  node.id ??
                  node.account ??
                  JSON.stringify(node)
                )
              : node
        )
      : [];

  const window =
    cycle.time_window ??
    cycle.window ??
    cycle.duration ??
    cycle.span_hours ??
    "";

  const transactionCount =
    cycle.transaction_count ??
    cycle.txn_count ??
    cycle.transactions ??
    normalizedChain.length;


  if (
    normalizedChain.length === 0
  ) {

    return `
      <article class="pattern-card">

        <span class="pattern-card__badge">
          Cycle detected
        </span>

        <p class="pattern-card__desc">
          Circular transaction flow
        </p>

        ${stateBlock(
          "error",
          "Cycle details unavailable",
          "The backend returned a cycle without account nodes."
        )}

        <div class="pattern-card__meta">
          0 accounts ·
          ${escapeHtml(transactionCount)}
          transactions
        </div>

      </article>
    `;
  }


  const nodes =
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
    <article class="pattern-card">

      <span class="pattern-card__badge">
        Cycle detected
      </span>

      <p class="pattern-card__desc">
        Circular transaction flow
      </p>

      <div class="cycle-chain">

        ${nodes}

        <div class="cycle-loop-back">
          ↩ returns to
          ${escapeHtml(
            normalizedChain[0]
          )}
        </div>

      </div>

      <div class="pattern-card__meta">

        ${normalizedChain.length}
        accounts

        ·

        ${escapeHtml(
          transactionCount
        )}
        transactions

        ${
          window
            ? ` · ${escapeHtml(window)}`
            : ""
        }

      </div>

    </article>
  `;
}


// ============================================================
// FAN-OUT RENDERER
// ============================================================

function renderFanoutPattern(
  fanout
) {

  const source =
    fanout.source_account ??
    fanout.hub ??
    fanout.origin ??
    "Unknown";

  const targets =
    fanout.recipients ??
    fanout.target_accounts ??
    fanout.targets ??
    [];

  const normalizedTargets =
    Array.isArray(targets)
      ? targets.map(
          (target) =>
            typeof target === "object" &&
            target !== null
              ? (
                  target.account_id ??
                  target.id ??
                  target.account ??
                  JSON.stringify(target)
                )
              : target
        )
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


  const timestamp =
    fanout.window_start ??
    fanout.timestamp ??
    fanout.created_at;


  return `
    <article class="pattern-card">

      <span class="pattern-card__badge">
        Fan-out detected
      </span>

      <p class="pattern-card__desc">
        One account distributing funds across multiple destinations.
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

        ${normalizedTargets.length}
        recipients

        ${
          timestamp
            ? ` · ${escapeHtml(formatDate(timestamp))}`
            : ""
        }

      </div>

    </article>
  `;
}


// ============================================================
// CONVERGENCE RENDERER
// ============================================================

function renderConvergencePattern(
  convergence
) {

  const target =
    convergence.collector_account ??
    convergence.target_account ??
    convergence.hub ??
    convergence.destination ??
    "Unknown";

  const sources =
    convergence.recipients ??
    convergence.source_accounts ??
    convergence.sources ??
    convergence.senders ??
    [];

  const normalizedSources =
    Array.isArray(sources)
      ? sources.map(
          (source) =>
            typeof source === "object" &&
            source !== null
              ? (
                  source.account_id ??
                  source.id ??
                  source.account ??
                  JSON.stringify(source)
                )
              : source
        )
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
    convergence.span_hours ??
    convergence.time_window ??
    convergence.window ??
    "";


  return `
    <article class="pattern-card">

      <span class="pattern-card__badge">
        Convergence detected
      </span>

      <p class="pattern-card__desc">
        Multiple accounts funneling funds into one destination.
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

        ${normalizedSources.length}
        sources

        ${
          span
            ? ` · ${escapeHtml(span)} hour window`
            : ""
        }

      </div>

    </article>
  `;
}


// ============================================================
// ERROR MESSAGES
// ============================================================

function getFriendlyError(
  error
) {

  if (!error) {
    return "An unknown error occurred.";
  }

  if (
    error.message ===
    "Unable to connect to the backend."
  ) {

    return "The API server could not be reached. Check that the backend is running.";
  }

  if (
    error.message ===
    "The backend request timed out."
  ) {

    return "The API server took too long to respond.";
  }

  if (
    error.status === 404
  ) {

    return "The requested API endpoint was not found.";
  }

  if (
    error.status >= 500
  ) {

    return "The backend encountered an internal error.";
  }

  return error.message ||
    "Something went wrong while loading this data.";
}


// ============================================================
// GLOBAL RETRY
// ============================================================

async function retryEverything() {

  const button =
    $("errorBannerRetry");

  button.disabled = true;

  button.textContent =
    "Retrying…";

  try {

    await Promise.all([
      checkHealth(),
      loadAccounts(),
      loadOverviewStats(),
      loadAllDetections(),
    ]);

  } finally {

    button.disabled = false;

    button.textContent =
      "Retry connection";
  }
}


// ============================================================
// INITIALIZATION
// ============================================================

function init() {

  initTabs();

  initCategoryChips();

  initAccountSearch();

  initBackToAccounts();


  $("errorBannerRetry")
    .addEventListener(
      "click",
      retryEverything
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