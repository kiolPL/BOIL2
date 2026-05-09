const MAX_SIZE = 10;

const elements = {
  sizeControls: document.getElementById("sizeControls"),
  nameControls: document.getElementById("nameControls"),
  matrixEditors: document.getElementById("matrixEditors"),
  results: document.getElementById("results"),
  balanceStatus: document.getElementById("balanceStatus"),
  resultStatus: document.getElementById("resultStatus"),
  solveButton: document.getElementById("solveButton"),
  exampleButton: document.getElementById("exampleButton"),
};

let state = createExample("transport");

document.addEventListener("click", handleClick);
document.addEventListener("input", handleInput);
document.addEventListener("change", handleChange);
elements.solveButton.addEventListener("click", solve);
elements.exampleButton.addEventListener("click", () => {
  state = createExample(state.mode);
  render();
  solve();
});

render();
solve();

function createExample(mode) {
  if (mode === "intermediary") {
    return {
      mode,
      calculateProfit: true,
      supplierCount: 3,
      receiverCount: 4,
      intermediaryCount: 2,
      supplierNames: ["D1", "D2", "D3"],
      receiverNames: ["O1", "O2", "O3", "O4"],
      intermediaryNames: ["P1", "P2"],
      supply: [20, 30, 25],
      demand: [10, 25, 25, 15],
      revenues: [
        [15, 14, 18, 16],
        [16, 17, 21, 15],
        [20, 16, 22, 14],
      ],
      costs: [],
      blocked: [],
      supplierToIntermediaryCosts: [
        [4, 7],
        [5, 3],
        [8, 4],
      ],
      supplierToIntermediaryBlocked: [
        [false, false],
        [false, false],
        [true, false],
      ],
      intermediaryToReceiverCosts: [
        [6, 4, 9, 8],
        [7, 5, 3, 6],
      ],
      intermediaryToReceiverBlocked: [
        [false, false, false, true],
        [false, false, false, false],
      ],
    };
  }

  return {
    mode,
    calculateProfit: true,
    supplierCount: 3,
    receiverCount: 4,
    intermediaryCount: 2,
    supplierNames: ["D1", "D2", "D3"],
    receiverNames: ["O1", "O2", "O3", "O4"],
    intermediaryNames: ["P1", "P2"],
    supply: [20, 30, 25],
    demand: [10, 25, 25, 15],
    revenues: [
      [15, 14, 18, 16],
      [16, 17, 21, 15],
      [20, 16, 22, 14],
    ],
    costs: [
      [8, 6, 10, 9],
      [9, 12, 13, 7],
      [14, 9, 16, 5],
    ],
    blocked: [
      [false, false, false, false],
      [false, true, false, false],
      [false, false, false, false],
    ],
    supplierToIntermediaryCosts: [
      [4, 7],
      [5, 3],
      [8, 4],
    ],
    supplierToIntermediaryBlocked: [
      [false, false],
      [false, false],
      [true, false],
    ],
    intermediaryToReceiverCosts: [
      [6, 4, 9, 8],
      [7, 5, 3, 6],
    ],
    intermediaryToReceiverBlocked: [
      [false, false, false, true],
      [false, false, false, false],
    ],
  };
}

function render() {
  document.querySelectorAll(".mode-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.mode === state.mode);
  });
  elements.sizeControls.innerHTML = renderSizeControls();
  elements.nameControls.innerHTML = renderNameControls();
  elements.matrixEditors.innerHTML = renderMatrixEditors();
  updateBalanceStatus();
}

function renderSizeControls() {
  const intermediaryField =
    state.mode === "intermediary"
      ? fieldHtml("Posrednicy", state.intermediaryCount, {
          type: "number",
          min: 1,
          max: MAX_SIZE,
          data: `data-count="intermediaryCount"`,
        })
      : "";

  return `
    ${fieldHtml("Dostawcy", state.supplierCount, {
      type: "number",
      min: 1,
      max: MAX_SIZE,
      data: `data-count="supplierCount"`,
    })}
    ${fieldHtml("Odbiorcy", state.receiverCount, {
      type: "number",
      min: 1,
      max: MAX_SIZE,
      data: `data-count="receiverCount"`,
    })}
    ${intermediaryField}
    <label class="toggle-row">
      <input type="checkbox" ${state.calculateProfit ? "checked" : ""} data-flag="calculateProfit" />
      <span>Licz zysk</span>
    </label>
  `;
}

function renderNameControls() {
  return `
    <div class="small-label">Dostawcy i podaz</div>
    ${state.supplierNames
      .map(
        (name, index) => `
          <div class="person-row">
            ${fieldHtml("Nazwa", name, {
              data: `data-array="supplierNames" data-index="${index}"`,
            })}
            ${fieldHtml("Podaz", state.supply[index], {
              type: "number",
              min: 0,
              data: `data-array="supply" data-index="${index}"`,
            })}
          </div>
        `,
      )
      .join("")}

    <div class="small-label">Odbiorcy i popyt</div>
    ${state.receiverNames
      .map(
        (name, index) => `
          <div class="person-row">
            ${fieldHtml("Nazwa", name, {
              data: `data-array="receiverNames" data-index="${index}"`,
            })}
            ${fieldHtml("Popyt", state.demand[index], {
              type: "number",
              min: 0,
              data: `data-array="demand" data-index="${index}"`,
            })}
          </div>
        `,
      )
      .join("")}

    ${
      state.mode === "intermediary"
        ? `
          <div class="small-label">Posrednicy</div>
          ${state.intermediaryNames
            .map((name, index) =>
              fieldHtml("Nazwa", name, {
                data: `data-array="intermediaryNames" data-index="${index}"`,
              }),
            )
            .join("")}
        `
        : ""
    }
  `;
}

function renderMatrixEditors() {
  if (state.mode === "intermediary") {
    return `
      ${matrixHtml({
        title: "Dostawcy -> posrednicy",
        rowNames: state.supplierNames,
        colNames: state.intermediaryNames,
        matrixKey: "supplierToIntermediaryCosts",
        blockKey: "supplierToIntermediaryBlocked",
      })}
      ${matrixHtml({
        title: "Posrednicy -> odbiorcy",
        rowNames: state.intermediaryNames,
        colNames: state.receiverNames,
        matrixKey: "intermediaryToReceiverCosts",
        blockKey: "intermediaryToReceiverBlocked",
      })}
      ${state.calculateProfit ? revenueMatrixHtml() : ""}
    `;
  }

  return `
    ${matrixHtml({
      title: "Koszty i blokady dostawcy -> odbiorcy",
      rowNames: state.supplierNames,
      colNames: state.receiverNames,
      matrixKey: "costs",
      blockKey: "blocked",
    })}
    ${state.calculateProfit ? revenueMatrixHtml() : ""}
  `;
}

function revenueMatrixHtml() {
  return matrixHtml({
    title: "Przychody dostawcy -> odbiorcy",
    rowNames: state.supplierNames,
    colNames: state.receiverNames,
    matrixKey: "revenues",
    label: "przychod jedn.",
  });
}

function matrixHtml({ title, rowNames, colNames, matrixKey, blockKey = "", label = "koszt / blokada" }) {
  const matrix = state[matrixKey];
  const blocked = blockKey ? state[blockKey] : [];
  return `
    <div class="matrix-block">
      <div class="matrix-title">
        <span>${escapeHtml(title)}</span>
        <span class="muted">${escapeHtml(label)}</span>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th class="row-head"></th>
              ${colNames.map((name) => `<th>${escapeHtml(name)}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${rowNames
              .map(
                (rowName, row) => `
                  <tr>
                    <th class="row-head">${escapeHtml(rowName)}</th>
                    ${colNames
                      .map((_, col) => {
                        const isLocked = blockKey ? Boolean(blocked[row]?.[col]) : false;
                        return `
                          <td class="${isLocked ? "blocked-cell" : ""}">
                            <div class="${blockKey ? "route-cell" : "value-cell"}">
                              <input class="matrix-input" type="number" min="0" step="1"
                                value="${display(matrix[row]?.[col] ?? 0)}"
                                data-matrix="${matrixKey}" data-row="${row}" data-col="${col}" />
                              ${
                                blockKey
                                  ? `<button class="icon-button ${isLocked ? "is-locked" : ""}"
                                      type="button"
                                      aria-label="${isLocked ? "Odblokuj trase" : "Zablokuj trase"}"
                                      title="${isLocked ? "Odblokuj trase" : "Zablokuj trase"}"
                                      data-block="${blockKey}" data-row="${row}" data-col="${col}">
                                      ${lockIcon(isLocked)}
                                    </button>`
                                  : ""
                              }
                            </div>
                          </td>
                        `;
                      })
                      .join("")}
                  </tr>
                `,
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function fieldHtml(label, value, options = {}) {
  const type = options.type || "text";
  const min = options.min ?? "";
  const max = options.max ?? "";
  return `
    <div class="field">
      <label>${escapeHtml(label)}</label>
      <input type="${type}" value="${escapeHtml(String(value ?? ""))}"
        ${min !== "" ? `min="${min}"` : ""}
        ${max !== "" ? `max="${max}"` : ""}
        ${options.data || ""} />
    </div>
  `;
}

function handleClick(event) {
  const modeButton = event.target.closest("[data-mode]");
  if (modeButton) {
    const mode = modeButton.dataset.mode;
    state.mode = mode;
    ensureShape();
    render();
    return;
  }

  const lockButton = event.target.closest("[data-block]");
  if (lockButton) {
    const matrix = state[lockButton.dataset.block];
    const row = Number(lockButton.dataset.row);
    const col = Number(lockButton.dataset.col);
    matrix[row][col] = !matrix[row][col];
    render();
  }
}

function handleInput(event) {
  const input = event.target;
  if (!(input instanceof HTMLInputElement)) return;

  if (input.dataset.array) {
    const array = state[input.dataset.array];
    const index = Number(input.dataset.index);
    array[index] = input.type === "number" ? numberValue(input.value) : input.value;
    updateBalanceStatus();
  }

  if (input.dataset.matrix) {
    const matrix = state[input.dataset.matrix];
    const row = Number(input.dataset.row);
    const col = Number(input.dataset.col);
    matrix[row][col] = numberValue(input.value);
  }
}

function handleChange(event) {
  const input = event.target;
  if (!(input instanceof HTMLInputElement)) return;

  if (input.dataset.flag) {
    state[input.dataset.flag] = input.checked;
    render();
    solve();
    return;
  }

  if (input.dataset.count) {
    state[input.dataset.count] = clamp(Number(input.value) || 1, 1, MAX_SIZE);
    ensureShape();
    render();
    return;
  }

  if (input.dataset.array && input.dataset.array.endsWith("Names")) {
    render();
  }
}

function ensureShape() {
  resizeArray(state.supplierNames, state.supplierCount, (index) => `D${index + 1}`);
  resizeArray(state.receiverNames, state.receiverCount, (index) => `O${index + 1}`);
  resizeArray(state.intermediaryNames, state.intermediaryCount, (index) => `P${index + 1}`);
  resizeArray(state.supply, state.supplierCount, () => 0);
  resizeArray(state.demand, state.receiverCount, () => 0);
  resizeMatrix(state.costs, state.supplierCount, state.receiverCount, 0);
  resizeMatrix(state.revenues, state.supplierCount, state.receiverCount, 0);
  resizeMatrix(state.blocked, state.supplierCount, state.receiverCount, false);
  resizeMatrix(state.supplierToIntermediaryCosts, state.supplierCount, state.intermediaryCount, 0);
  resizeMatrix(state.supplierToIntermediaryBlocked, state.supplierCount, state.intermediaryCount, false);
  resizeMatrix(state.intermediaryToReceiverCosts, state.intermediaryCount, state.receiverCount, 0);
  resizeMatrix(state.intermediaryToReceiverBlocked, state.intermediaryCount, state.receiverCount, false);
}

function resizeArray(array, length, factory) {
  while (array.length < length) array.push(factory(array.length));
  array.length = length;
}

function resizeMatrix(matrix, rows, cols, fill) {
  while (matrix.length < rows) matrix.push([]);
  matrix.length = rows;
  for (let row = 0; row < rows; row += 1) {
    while (matrix[row].length < cols) matrix[row].push(fill);
    matrix[row].length = cols;
  }
}

function updateBalanceStatus() {
  const supply = sum(state.supply);
  const demand = sum(state.demand);
  const diff = Math.abs(supply - demand);
  elements.balanceStatus.textContent =
    diff < 0.0001 ? "Zbilansowane" : supply > demand ? `Nadwyzka ${display(diff)}` : `Brak ${display(diff)}`;
}

async function solve() {
  elements.solveButton.disabled = true;
  elements.resultStatus.textContent = "Liczenie";
  elements.resultStatus.classList.remove("is-error");

  try {
    const response = await fetch("/api/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    const result = await response.json();
    renderResults(result);
  } catch (error) {
    renderResults({ success: false, message: `Nie mozna polaczyc z backendem: ${error.message}` });
  } finally {
    elements.solveButton.disabled = false;
  }
}

function renderResults(result) {
  if (!result.success) {
    elements.resultStatus.textContent = "Blad";
    elements.resultStatus.classList.add("is-error");
    elements.results.className = "";
    elements.results.innerHTML = `
      <div class="message warning">${escapeHtml(result.message || "Nie udalo sie wykonac obliczen.")}</div>
    `;
    return;
  }

  elements.resultStatus.textContent = "Gotowe";
  elements.resultStatus.classList.remove("is-error");
  elements.results.className = "";

  const profitEnabled = result.profitEnabled !== false;
  const messages = [
    `<div class="message">${escapeHtml(result.message)}</div>`,
    ...(result.warnings || []).map((warning) => `<div class="message warning">${escapeHtml(warning)}</div>`),
  ].join("");
  const profitMetrics = profitEnabled
    ? `
      <div class="metric"><span>Przychod</span><strong>${display(result.totalRevenue)}</strong></div>
      <div class="metric"><span>Zysk</span><strong class="${profitClass(result.totalProfit)}">${display(result.totalProfit)}</strong></div>
    `
    : "";

  elements.results.innerHTML = `
    <div class="summary-grid ${profitEnabled ? "" : "cost-only"}">
      <div class="metric"><span>Koszt calkowity</span><strong>${display(result.totalCost)}</strong></div>
      ${profitMetrics}
      <div class="metric"><span>Iteracje</span><strong>${result.iterations.length}</strong></div>
    </div>
    <div class="message-list">${messages}</div>
    <div class="result-split">
      <div class="subpanel">
        <h3>Macierz koncowa</h3>
        ${allocationTable(result, result.allocations)}
      </div>
      <div class="subpanel">
        <h3>Trasy z przydzialem</h3>
        <div class="route-list">
          ${
            result.routeSummary.length
              ? result.routeSummary.map((route) => routeItem(route, profitEnabled)).join("")
              : `<div class="message warning">Brak dodatnich przydzialow.</div>`
          }
        </div>
      </div>
    </div>
    <div class="iterations">
      <h3>Wyniki posrednie</h3>
      ${result.iterations.map((iteration) => iterationCard(result, iteration, profitEnabled)).join("")}
    </div>
  `;
}

function routeItem(route, profitEnabled) {
  const details = profitEnabled
    ? `koszt ${display(route.cost)}, przychod ${display(route.revenue)}`
    : `koszt ${display(route.cost)}, koszt jedn. ${display(route.unitCost)}`;
  const value = profitEnabled
    ? `<div class="route-cost ${profitClass(route.profit)}">${display(route.profit)}</div>`
    : `<div class="route-cost">${display(route.cost)}</div>`;
  return `
    <div class="route-item">
      <div>
        <strong>${escapeHtml(route.path.label)}</strong>
        <span>${escapeHtml(route.supplier)} -> ${escapeHtml(route.receiver)}, ilosc ${display(route.amount)}, ${details}</span>
      </div>
      ${value}
    </div>
  `;
}

function iterationCard(result, iteration, profitEnabled) {
  const supplier = result.supplierNames[iteration.supplierIndex];
  const receiver = result.receiverNames[iteration.receiverIndex];
  const stepLine = profitEnabled
    ? `koszt ${display(iteration.stepCost)} | zysk ${display(iteration.stepProfit)}`
    : `koszt kroku ${display(iteration.stepCost)}`;
  const totalLine = profitEnabled
    ? `Koszt: ${display(iteration.totalCostSoFar)} | Zysk: ${display(iteration.totalProfitSoFar)}`
    : `Suma kosztu: ${display(iteration.totalCostSoFar)}`;
  return `
    <article class="iteration-card">
      <div class="iteration-head">
        <div>
          <h4>Krok ${iteration.step}: ${escapeHtml(supplier)} -> ${escapeHtml(receiver)}</h4>
          <span>${escapeHtml(iteration.path.label)} | ilosc ${display(iteration.amount)} | ${stepLine}</span>
        </div>
        <span>${totalLine}</span>
      </div>
      <div>
        <div class="graph-wrap">${graphSvg(result, iteration)}</div>
        ${iteration.warning ? `<div class="iteration-note">${escapeHtml(iteration.warning)}</div>` : ""}
      </div>
      <div>
        ${allocationTable(result, iteration.allocations, iteration)}
      </div>
    </article>
  `;
}

function allocationTable(result, allocations, current = null) {
  return `
    <div class="table-scroll">
      <table class="allocation-table">
        <thead>
          <tr>
            <th class="row-head"></th>
            ${result.receiverNames.map((name) => `<th>${escapeHtml(name)}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          ${result.supplierNames
            .map(
              (name, row) => `
                <tr>
                  <th class="row-head">${escapeHtml(name)}</th>
                  ${result.receiverNames
                    .map((_, col) => {
                      const value = Number(allocations[row]?.[col] || 0);
                      const isCurrent = current && row === current.supplierIndex && col === current.receiverIndex;
                      const isBlocked = result.blocked[row]?.[col];
                      const className = [
                        isCurrent ? "is-current" : "",
                        value > 0 ? "has-allocation" : "",
                        isBlocked ? "is-blocked" : "",
                      ]
                        .filter(Boolean)
                        .join(" ");
                      return `<td class="${className}">${isBlocked && value <= 0 ? "X" : display(value)}</td>`;
                    })
                    .join("")}
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function graphSvg(result, iteration) {
  return result.mode === "intermediary"
    ? intermediaryGraphSvg(result, iteration)
    : transportGraphSvg(result, iteration);
}

function transportGraphSvg(result, iteration) {
  const width = 760;
  const height = Math.max(300, Math.max(result.supplierNames.length, result.receiverNames.length) * 62 + 70);
  const suppliers = result.supplierNames.map((name, index) => ({
    name,
    x: 78,
    y: spreadY(index, result.supplierNames.length, height),
  }));
  const receivers = result.receiverNames.map((name, index) => ({
    name,
    x: width - 78,
    y: spreadY(index, result.receiverNames.length, height),
  }));

  const edges = [];
  for (let row = 0; row < suppliers.length; row += 1) {
    for (let col = 0; col < receivers.length; col += 1) {
      const amount = Number(iteration.allocations[row]?.[col] || 0);
      const isCurrent = row === iteration.supplierIndex && col === iteration.receiverIndex;
      const isBlocked = result.blocked[row]?.[col];
      edges.push(edgeLine(suppliers[row], receivers[col], amount, isCurrent, isBlocked, result.costs[row]?.[col]));
    }
  }

  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Graf transportowy kroku ${iteration.step}">
      ${edges.join("")}
      ${suppliers.map((node) => graphNode(node, "D")).join("")}
      ${receivers.map((node) => graphNode(node, "O")).join("")}
    </svg>
  `;
}

function intermediaryGraphSvg(result, iteration) {
  const width = 820;
  const maxNodes = Math.max(
    result.supplierNames.length,
    result.intermediaryNames.length || 1,
    result.receiverNames.length,
  );
  const height = Math.max(330, maxNodes * 62 + 80);
  const suppliers = result.supplierNames.map((name, index) => ({
    name,
    x: 70,
    y: spreadY(index, result.supplierNames.length, height),
  }));
  const intermediaries = result.intermediaryNames.map((name, index) => ({
    name,
    x: width / 2,
    y: spreadY(index, result.intermediaryNames.length, height),
  }));
  const receivers = result.receiverNames.map((name, index) => ({
    name,
    x: width - 70,
    y: spreadY(index, result.receiverNames.length, height),
  }));
  const aggregates = aggregateIntermediarySegments(result, iteration.allocations);
  const currentPath = iteration.path || {};
  const parts = [];

  const s2mBlocked = result.segments.supplierToIntermediaryBlocked || [];
  const m2rBlocked = result.segments.intermediaryToReceiverBlocked || [];

  for (let row = 0; row < suppliers.length; row += 1) {
    for (let mid = 0; mid < intermediaries.length; mid += 1) {
      const amount = aggregates.s2m[`${row}-${mid}`] || 0;
      const current = currentPath.type === "intermediary" && row === iteration.supplierIndex && mid === currentPath.intermediaryIndex;
      parts.push(edgeLine(suppliers[row], intermediaries[mid], amount, current, s2mBlocked[row]?.[mid], ""));
    }
  }

  for (let mid = 0; mid < intermediaries.length; mid += 1) {
    for (let col = 0; col < receivers.length; col += 1) {
      const amount = aggregates.m2r[`${mid}-${col}`] || 0;
      const current = currentPath.type === "intermediary" && col === iteration.receiverIndex && mid === currentPath.intermediaryIndex;
      parts.push(edgeLine(intermediaries[mid], receivers[col], amount, current, m2rBlocked[mid]?.[col], ""));
    }
  }

  aggregates.direct.forEach(({ row, col, amount }) => {
    const current = row === iteration.supplierIndex && col === iteration.receiverIndex;
    parts.push(edgeLine(suppliers[row], receivers[col], amount, current, false, ""));
  });

  return `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Graf posrednika kroku ${iteration.step}">
      ${parts.join("")}
      ${suppliers.map((node) => graphNode(node, "D")).join("")}
      ${intermediaries.map((node) => graphNode(node, "P")).join("")}
      ${receivers.map((node) => graphNode(node, "O")).join("")}
    </svg>
  `;
}

function aggregateIntermediarySegments(result, allocations) {
  const s2m = {};
  const m2r = {};
  const direct = [];

  for (let row = 0; row < allocations.length; row += 1) {
    for (let col = 0; col < allocations[row].length; col += 1) {
      const amount = Number(allocations[row][col] || 0);
      if (amount <= 0) continue;
      const path = result.paths[row]?.[col];
      if (path?.type === "intermediary") {
        const mid = path.intermediaryIndex;
        s2m[`${row}-${mid}`] = (s2m[`${row}-${mid}`] || 0) + amount;
        m2r[`${mid}-${col}`] = (m2r[`${mid}-${col}`] || 0) + amount;
      } else {
        direct.push({ row, col, amount });
      }
    }
  }

  return { s2m, m2r, direct };
}

function edgeLine(from, to, amount, isCurrent, isBlocked, cost) {
  const hasAmount = Number(amount) > 0;
  const stroke = isCurrent ? "#b78120" : hasAmount ? "#3169b1" : isBlocked ? "#c4532d" : "#aab7af";
  const width = isCurrent ? 5 : hasAmount ? Math.min(5, 2 + Math.sqrt(amount) / 3) : 1.2;
  const opacity = isCurrent ? 1 : hasAmount ? 0.72 : isBlocked ? 0.32 : 0.22;
  const dash = isBlocked ? `stroke-dasharray="7 7"` : "";
  const label = hasAmount || isCurrent ? display(amount) : "";
  const labelX = (from.x + to.x) / 2;
  const labelY = (from.y + to.y) / 2 - 6;

  return `
    <g>
      <line x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}"
        stroke="${stroke}" stroke-width="${width}" opacity="${opacity}" ${dash} />
      ${
        label !== ""
          ? `<text class="edge-label" x="${labelX}" y="${labelY}" text-anchor="middle">${escapeHtml(String(label))}</text>`
          : ""
      }
    </g>
  `;
}

function graphNode(node, prefix) {
  const width = 96;
  const height = 34;
  return `
    <g>
      <rect x="${node.x - width / 2}" y="${node.y - height / 2}" width="${width}" height="${height}" rx="6"
        fill="#ffffff" stroke="#087f72" stroke-width="1.8" />
      <text class="node-label" x="${node.x}" y="${node.y + 5}" text-anchor="middle">${escapeHtml(node.name || prefix)}</text>
    </g>
  `;
}

function spreadY(index, total, height) {
  if (total <= 1) return height / 2;
  const margin = 44;
  return margin + (index * (height - margin * 2)) / (total - 1);
}

function lockIcon(locked) {
  if (locked) {
    return `
      <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="4" y="10" width="16" height="10" rx="2"></rect>
        <path d="M8 10V7a4 4 0 0 1 8 0v3"></path>
      </svg>
    `;
  }
  return `
    <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="4" y="10" width="16" height="10" rx="2"></rect>
      <path d="M8 10V7a4 4 0 0 1 7.4-2.1"></path>
    </svg>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function numberValue(value) {
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 ? number : 0;
}

function display(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return value;
  return Math.abs(number - Math.round(number)) < 0.0001 ? String(Math.round(number)) : number.toFixed(2);
}

function profitClass(value) {
  return Number(value) < 0 ? "profit-negative" : "profit-positive";
}

function sum(values) {
  return values.reduce((total, value) => total + numberValue(value), 0);
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
