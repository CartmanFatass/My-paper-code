(() => {
  "use strict";

  const state = { snapshot: null, view: "portfolio" };
  const view = document.getElementById("view");
  const notice = document.getElementById("notice");
  const generated = document.getElementById("generated");
  const revision = document.getElementById("revision");
  const health = document.getElementById("health");

  const esc = (value) => String(value ?? "—");
  const cell = (value, className = "") => {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = esc(value);
    return span;
  };

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function section(name) {
    return state.snapshot?.data?.[name] || {
      status: "missing",
      data: {},
      warnings: ["section unavailable"],
      revision_refs: {},
    };
  }

  function badge(status) {
    const span = document.createElement("span");
    span.className = `badge badge-${status || "unknown"}`;
    span.textContent = status || "unknown";
    return span;
  }

  function heading(title, subtitle, status) {
    const header = document.createElement("div");
    header.className = "view-heading";
    const copy = document.createElement("div");
    const h2 = document.createElement("h2");
    h2.textContent = title;
    copy.appendChild(h2);
    if (subtitle) {
      const p = document.createElement("p");
      p.className = "muted";
      p.textContent = subtitle;
      copy.appendChild(p);
    }
    header.append(copy, badge(status));
    return header;
  }

  function warningsFor(sectionData) {
    if (!sectionData.warnings?.length) return null;
    const box = document.createElement("div");
    box.className = "warnings";
    const strong = document.createElement("strong");
    strong.textContent = "Projection notes";
    box.appendChild(strong);
    const list = document.createElement("ul");
    sectionData.warnings.forEach((warning) => {
      const item = document.createElement("li");
      item.textContent = warning;
      list.appendChild(item);
    });
    box.appendChild(list);
    return box;
  }

  function table(headers, rows, empty) {
    const wrapper = document.createElement("div");
    wrapper.className = "table-wrap";
    if (!rows.length) {
      const p = document.createElement("p");
      p.className = "empty";
      p.textContent = empty;
      wrapper.appendChild(p);
      return wrapper;
    }
    const tableNode = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headers.forEach((header) => {
      const th = document.createElement("th");
      th.scope = "col";
      th.textContent = header;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    tableNode.appendChild(thead);
    const tbody = document.createElement("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      row.forEach((value) => {
        const td = document.createElement("td");
        if (value instanceof Node) td.appendChild(value);
        else td.appendChild(cell(value));
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tableNode.appendChild(tbody);
    wrapper.appendChild(tableNode);
    return wrapper;
  }

  function renderPortfolio() {
    const current = section("portfolio");
    const data = current.data || {};
    const directions = Array.isArray(data.directions) ? data.directions : [];
    const node = document.createDocumentFragment();
    node.appendChild(heading("Portfolio", "Lifecycle, dependencies, and compact direction state", current.status));
    if (data.goal) {
      const goal = document.createElement("div");
      goal.className = "goal-card";
      goal.append(cell("Portfolio goal reference", "label"));
      goal.append(cell(data.goal.path, "mono"), cell(`sha ${String(data.goal.sha256 || "").slice(0, 12)}…`, "muted mono"));
      node.appendChild(goal);
    }
    const rows = directions.map((direction) => {
      const research = direction.research_state || {};
      const engineering = direction.engineering_state || {};
      const dependencies = Array.isArray(direction.dependencies) ? direction.dependencies.join(", ") : "—";
      const status = direction.lifecycle || direction.research_state_status || "—";
      return [
        cell(`${direction.abbreviation || "—"} · ${direction.id || "—"}`, "strong"),
        badge(status.toLowerCase()),
        dependencies,
        `${research.phase || "—"} / ${engineering.phase || "—"}`,
        direction.external_round_count ?? 0,
      ];
    });
    node.appendChild(table(["Direction", "Lifecycle", "Dependencies", "Research / engineering", "Review rounds"], rows, "No directions registered."));
    view.replaceChildren(node);
  }

  function renderClerk() {
    const current = section("clerk");
    const directions = Array.isArray(current.data?.directions) ? current.data.directions : [];
    const rows = directions.map((direction) => [
      cell(direction.direction_id, "strong"),
      badge(String(direction.lifecycle || "unknown").toLowerCase()),
      badge(String(direction.owner_stage || "unknown").toLowerCase()),
      direction.next_event || "—",
      `${direction.native_task_id || "UNKNOWN"} / ${direction.native_task_status || "UNOBSERVED"}`,
      direction.observed_at || "UNOBSERVED",
      direction.delivery_state || "UNOBSERVED",
      direction.control_release_adoption || "UNOBSERVED",
      direction.assignment_id || direction.return_id || "UNKNOWN",
      direction.defect || "—",
    ]);
    const node = document.createDocumentFragment();
    node.appendChild(heading("Workflow Clerk", "Latest native observation and durable-state provenance; refreshing this view does not refresh task observations", current.status));
    node.appendChild(table(["Direction", "Lifecycle", "Owner stage", "Next event", "Native task", "Observed", "Delivery", "Release", "Assignment / RETURN", "Defect"], rows, "No directions are visible."));
    view.replaceChildren(node);
  }

  function renderRuns() {
    const current = section("runs");
    const runs = Array.isArray(current.data?.runs) ? current.data.runs : [];
    const results = Array.isArray(current.data?.results) ? current.data.results : [];
    const rows = runs.map((run) => [
      cell(run.run_id, "strong"),
      run.direction_id,
      badge(String(run.status || "unknown").toLowerCase()),
      run.resources ? `${run.resources.workers ?? "—"} × ${run.resources.threads_per_worker ?? "—"}` : "—",
      run.process?.exit_code ?? "—",
      run.process?.terminal_reason || "—",
    ]);
    const resultRows = results.map((result) => [
      cell(result.result_id, "strong"),
      result.direction_id,
      result.source_run?.run_id || "—",
      result.promoted_at || "—",
      Object.keys(result.metrics || {}).join(", ") || "—",
    ]);
    const node = document.createDocumentFragment();
    node.appendChild(heading("Runs", "Local terminal state, safe resource summaries, and promoted result references", current.status));
    node.appendChild(table(["Run", "Direction", "Status", "Workers × threads", "Exit", "Terminal reason"], rows, "No local run manifests are visible."));
    const subheading = document.createElement("h3");
    subheading.textContent = "Promoted results";
    node.appendChild(subheading);
    node.appendChild(table(["Result", "Direction", "Source run", "Promoted", "Metrics"], resultRows, "No promoted results are visible."));
    view.replaceChildren(node);
  }

  function renderExternal() {
    const current = section("external_reviews");
    const rounds = Array.isArray(current.data?.rounds) ? current.data.rounds : [];
    const rows = rounds.map((round) => [
      cell(round.round_id, "strong mono"),
      badge(String(round.status || "unknown").toLowerCase()),
      round.question_sha256 ? String(round.question_sha256).slice(0, 12) + "…" : "—",
      round.created_at || "—",
      round.completed_at || "—",
      Object.keys(round.providers || {}).join(", ") || "—",
    ]);
    const node = document.createDocumentFragment();
    node.appendChild(heading("External reviews", "Round state, operation references, and archive/handoff pointers only", current.status));
    node.appendChild(table(["Round", "Status", "Question SHA", "Created", "Completed", "Providers"], rows, "No external review rounds are visible."));
    view.replaceChildren(node);
  }

  function render() {
    const renderers = {
      portfolio: renderPortfolio,
      clerk: renderClerk,
      runs: renderRuns,
      external_reviews: renderExternal,
    };
    (renderers[state.view] || renderPortfolio)();
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.view === state.view);
    });
    const current = section(state.view);
    const note = warningsFor(current);
    notice.replaceChildren();
    notice.hidden = !note;
    if (note) notice.appendChild(note);
  }

  async function refresh() {
    try {
      const response = await fetch("/api/snapshot", { cache: "no-store" });
      const payload = await response.json();
      if (!response.ok && response.status !== 409) throw new Error(`snapshot HTTP ${response.status}`);
      state.snapshot = payload;
      generated.textContent = `Generation ${payload.generated_at || "unknown"}`;
      const refs = payload.revision_refs || {};
      revision.textContent = `Registry revision ${refs.registry ?? "—"}`;
      health.textContent = response.status === 409 ? "Changing · retrying" : `Snapshot ${payload.status || "unknown"}`;
      health.className = `health health-${payload.status || "unknown"}`;
      render();
    } catch (error) {
      health.textContent = "Unavailable";
      health.className = "health health-invalid";
      notice.hidden = false;
      notice.replaceChildren(cell(`Dashboard snapshot unavailable: ${error.message}`, "error"));
    }
  }

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      state.view = tab.dataset.view || "portfolio";
      render();
    });
  });
  refresh();
  window.setInterval(refresh, 5000);
})();
