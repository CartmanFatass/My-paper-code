/* Research support viewer application.
 *
 * Reads immutable frames from the local server and draws them. It never asks the server to
 * advance, reset or re-solve anything, because the server exposes no such endpoint.
 *
 * Three rules the drawing code follows everywhere:
 *   1. A missing value is drawn as missing. `null` with a validity reason renders as an
 *      explicit "not recorded" marker, never as zero and never as an empty region.
 *   2. A link that exists geometrically is styled differently from a link that carries
 *      traffic, and the two are separate layer toggles.
 *   3. Status is never colour alone: every state pairs a colour with a marker shape and a
 *      line pattern, so the scene survives a colour-vision difference and a greyscale print.
 */
(function () {
  "use strict";

  /* Two data sources, one renderer.
   *
   *  - served mode: a bootstrap block with a session token; data comes from /api/.
   *  - standalone mode: an embedded <script id="trace-data"> block, or a trace.json
   *    fetched from the same directory. The export bundle ships THIS file rather than a
   *    second implementation, so the offline replay and the live viewer cannot drift.
   */
  var bootNode = document.getElementById("bootstrap");
  var traceNode = document.getElementById("trace-data");
  var STANDALONE = !bootNode;
  var BOOT = bootNode ? JSON.parse(bootNode.textContent) : { token: null, meta: {} };
  var TOKEN = BOOT.token;
  var META = BOOT.meta || {};
  var OFFLINE = null;

  if (STANDALONE) {
    var embedded = null;
    if (traceNode && traceNode.textContent && traceNode.textContent.trim() !== "null") {
      embedded = JSON.parse(traceNode.textContent);
    }
    OFFLINE = embedded;
    META = {
      title: document.title || "Recorded replay",
      banner: "",
      mode: "replay",
      live_available: false,
      traces: [{ label: "trace", directory: "trace", manifest: (embedded && embedded.manifest) || {} }],
      reports: [],
      max_frames_per_request: 1e9
    };
  }

  /* Live polling cadence. The browser's animation rate never determines the simulator's
   * cadence: this only decides how often we ask for the newest published frame. */
  var LIVE_POLL_MS = 1000;
  var LIVE_BUFFER = 600;

  var state = {
    tab: "live",
    view: "2d",
    infoView: "truth",
    frozen: false,
    followLatest: true,
    followSelected: false,
    showTrails: false,
    trailLength: 24,
    selection: null,
    hover: null,
    frames: [],              // live ring buffer or replay window cache
    index: -1,
    right: { frames: [], index: -1, label: null },
    replay: { label: null, timeline: [], total: 0, cache: new Map(), playing: false, speed: 1, frameIndexPacing: false },
    compare: { left: null, right: null, alignment: "simulated-time" },
    layers: {},
    streamState: "WAITING",
    detail: null,
    health: null,
    cam: { x: 0, y: 0, k: 1 },
    cam3d: null,
    lastError: null
  };

  var LAYER_DEFS = [
    { id: "uavs", label: "UAVs", cap: "has_uav_positions" },
    { id: "ues", label: "Individual UEs", cap: "has_individual_ues" },
    { id: "demand", label: "Aggregate demand points", cap: "has_aggregate_demand" },
    { id: "sites", label: "Base stations / sites", cap: "has_sites" },
    { id: "access", label: "Access links", cap: "has_links" },
    { id: "backhaul", label: "Backhaul links", cap: "has_links" },
    { id: "core", label: "Wired core links", cap: "has_links" },
    { id: "available", label: "Available links (no traffic)", cap: "has_links" },
    { id: "active", label: "Active traffic-carrying links", cap: "has_links" },
    { id: "utilization", label: "Link utilization width", cap: "has_link_flows" },
    { id: "paths", label: "Selected paths", cap: "has_candidate_paths" },
    { id: "unknown", label: "Unknown / stale telemetry", cap: null },
    { id: "labels", label: "Entity labels", cap: null }
  ];
  LAYER_DEFS.forEach(function (d) { state.layers[d.id] = d.id !== "utilization" && d.id !== "labels"; });
  state.layers.utilization = true;

  /* ------------------------------------------------------------------ utils */

  /* The standalone export ships a smaller page than the served one, so several controls
   * are legitimately absent. A stub keeps the shared code free of existence checks; it
   * silently swallows writes to elements that this page does not have. */
  var STUB = {
    textContent: "", value: "", max: "", min: "", checked: false, hidden: true,
    disabled: false, title: "", className: "", style: {}, dataset: {},
    appendChild: function () {}, addEventListener: function () {},
    removeEventListener: function () {}, querySelector: function () { return STUB; },
    querySelectorAll: function () { return []; }, classList: { add: function () {}, remove: function () {}, toggle: function () {} },
    getBoundingClientRect: function () { return { left: 0, top: 0, width: 1, height: 1 }; },
    getContext: function () { return null; }, focus: function () {}, click: function () {},
    __stub: true
  };
  function $(id) { return document.getElementById(id) || STUB; }
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) { node.className = cls; }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }
  function tokens() {
    var s = getComputedStyle(document.documentElement);
    var get = function (n) { return s.getPropertyValue(n).trim(); };
    return {
      ink: get("--ink"), ink2: get("--ink-2"), ink3: get("--ink-3"),
      line: get("--line"), line2: get("--line-2"), panel: get("--panel"),
      accent: get("--accent"), uav: get("--uav"), site: get("--site"),
      served: get("--ue-served"), partial: get("--ue-partial"), unserved: get("--ue-unserved"),
      zero: get("--ue-zero"), unknown: get("--ue-unknown"), nobackhaul: get("--ue-nobackhaul"),
      available: get("--link-available"), active: get("--link-active"),
      access: get("--link-access"), backhaul: get("--link-backhaul"), core: get("--link-core"),
      mono: get("--mono") || "monospace",
      highContrast: document.documentElement.getAttribute("data-contrast") === "high"
    };
  }

  function fmt(value, digits) {
    if (value === null || value === undefined) { return "—"; }
    if (typeof value === "boolean") { return value ? "true" : "false"; }
    if (typeof value !== "number") { return String(value); }
    if (!isFinite(value)) { return "—"; }
    var d = digits === undefined ? 3 : digits;
    if (Math.abs(value) >= 1e6 || (value !== 0 && Math.abs(value) < 1e-4)) { return value.toExponential(2); }
    return String(Number(value.toFixed(d)));
  }

  /* A Measured is {value, validity, unit?, reason?}. An absent value keeps its reason. */
  function measured(m) {
    if (m === null || m === undefined) { return { absent: true, text: "not present", validity: "absent" }; }
    if (m.validity === "ok") {
      return { absent: false, text: fmt(m.value) + (m.unit ? " " + m.unit : ""), validity: "ok", value: m.value };
    }
    return { absent: true, text: m.validity + (m.reason ? " (" + m.reason + ")" : ""), validity: m.validity };
  }
  function mval(m) { return (m && m.validity === "ok") ? m.value : null; }

  /* Offline answers to the same route names the served API uses, so every consumer below
   * is identical in both modes. */
  function offlineApi(route, params) {
    var payload = OFFLINE || { frames: [], manifest: {}, index: {}, status: "unknown", problems: [] };
    var frames = payload.frames || [];
    if (route === "meta") { return Promise.resolve(META); }
    if (route === "frame") {
      return Promise.resolve({
        frame: null, state: "ENDED",
        detail: "this is a recorded replay bundle; there is no live producer to attach to"
      });
    }
    if (route === "health") { return Promise.resolve({ available: false }); }
    if (route === "trace/index") {
      return Promise.resolve({
        trace_id: (payload.manifest || {}).trace_id || "trace",
        status: payload.status, problems: payload.problems || [],
        truncated_after_sequence: payload.truncated_after_sequence,
        manifest: payload.manifest || {}, index: payload.index || {},
        n_frames: frames.length
      });
    }
    if (route === "trace/frames") {
      var start = Number((params || {}).start || 0);
      var count = Number((params || {}).count || frames.length);
      return Promise.resolve({
        label: (params || {}).label, start: start,
        frames: frames.slice(start, start + count),
        count: Math.min(count, Math.max(0, frames.length - start)), total: frames.length
      });
    }
    return Promise.reject(new Error("offline bundle has no route " + route));
  }

  function api(route, params) {
    if (STANDALONE) {
      if (OFFLINE) { return offlineApi(route, params); }
      // Bundle form: the trace lives beside the page and is fetched once.
      return fetch(window.RS_TRACE_URL || "trace.json", { cache: "no-store" })
        .then(function (r) {
          if (!r.ok) { throw new Error("cannot load trace.json (HTTP " + r.status + ")"); }
          return r.json();
        })
        .then(function (payload) { OFFLINE = payload; return offlineApi(route, params); });
    }
    var query = new URLSearchParams(params || {}).toString();
    return fetch("/api/" + route + (query ? "?" + query : ""), {
      headers: { "X-RS-Token": TOKEN },
      cache: "no-store"
    }).then(function (response) {
      if (!response.ok) {
        return response.json().catch(function () { return { error: "HTTP " + response.status }; })
          .then(function (body) { throw new Error(body.error || ("HTTP " + response.status)); });
      }
      return response.json();
    });
  }

  /* ---------------------------------------------------------------- shapes */

  /* Every ground-entity state gets its own marker geometry, so status never depends on
   * colour alone. `unknown` additionally gets hatching. */
  var STATUS_STYLE = {
    served:                 { shape: "disc",    colourKey: "served",      label: "served" },
    partially_served:       { shape: "half",    colourKey: "partial",     label: "partially served" },
    unserved:               { shape: "cross",   colourKey: "unserved",    label: "unserved" },
    zero_demand:            { shape: "dot",     colourKey: "zero",        label: "zero demand (measured)" },
    unknown_demand:         { shape: "hatch",   colourKey: "unknown",     label: "unknown demand" },
    unknown_service:        { shape: "hatch",   colourKey: "unknown",     label: "unknown service" },
    associated_no_backhaul: { shape: "dashsq",  colourKey: "nobackhaul",  label: "associated, no backhaul" }
  };
  function statusStyle(status) {
    return STATUS_STYLE[status] || { shape: "ring", colourKey: "ink3", label: status || "unclassified" };
  }

  function drawMarker(ctx, shape, x, y, r, colour) {
    ctx.save();
    ctx.strokeStyle = colour;
    ctx.fillStyle = colour;
    ctx.lineWidth = 1.4;
    switch (shape) {
      case "disc":
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
        break;
      case "half":
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(x, y, r, -Math.PI / 2, Math.PI / 2); ctx.closePath(); ctx.fill();
        break;
      case "cross":
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x - r * 0.7, y - r * 0.7); ctx.lineTo(x + r * 0.7, y + r * 0.7);
        ctx.moveTo(x + r * 0.7, y - r * 0.7); ctx.lineTo(x - r * 0.7, y + r * 0.7);
        ctx.stroke();
        break;
      case "dot":
        ctx.beginPath(); ctx.arc(x, y, Math.max(1.4, r * 0.35), 0, Math.PI * 2); ctx.fill();
        break;
      case "hatch":
        ctx.beginPath(); ctx.rect(x - r, y - r, r * 2, r * 2); ctx.stroke();
        ctx.beginPath();
        for (var o = -r; o <= r; o += 3) {
          ctx.moveTo(x + o, y - r); ctx.lineTo(x + o + r, y);
        }
        ctx.lineWidth = 0.8; ctx.stroke();
        break;
      case "dashsq":
        ctx.setLineDash([2, 2]);
        ctx.beginPath(); ctx.rect(x - r, y - r, r * 2, r * 2); ctx.stroke();
        ctx.setLineDash([]);
        break;
      case "triangle":
        ctx.beginPath();
        ctx.moveTo(x, y - r * 1.15); ctx.lineTo(x + r, y + r * 0.8); ctx.lineTo(x - r, y + r * 0.8);
        ctx.closePath(); ctx.fill();
        break;
      case "square":
        ctx.beginPath(); ctx.rect(x - r, y - r, r * 2, r * 2); ctx.fill();
        break;
      case "squarex":
        ctx.beginPath(); ctx.rect(x - r, y - r, r * 2, r * 2); ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x - r, y - r); ctx.lineTo(x + r, y + r);
        ctx.moveTo(x + r, y - r); ctx.lineTo(x - r, y + r);
        ctx.stroke();
        break;
      default:
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
    }
    ctx.restore();
  }

  var LINK_STYLE = {
    uav_access:          { group: "access",   colourKey: "access",   dash: [] },
    site_access:         { group: "access",   colourKey: "access",   dash: [] },
    uav_uav_backhaul:    { group: "backhaul", colourKey: "backhaul", dash: [6, 3] },
    site_uav_backhaul:   { group: "backhaul", colourKey: "backhaul", dash: [6, 3] },
    wired_core:          { group: "core",     colourKey: "core",     dash: [2, 2] }
  };
  function linkStyle(cls) {
    return LINK_STYLE[cls] || { group: "backhaul", colourKey: "ink3", dash: [3, 3] };
  }

  /* ------------------------------------------------------------- transform */

  function sceneBounds(frame) {
    var b = (frame && frame.geometry && frame.geometry.bounds_m) || [0, 0, 1000, 1000];
    return { minX: b[0], minY: b[1], maxX: b[2], maxY: b[3] };
  }

  /* Equal metric aspect is mandatory: one scale for both axes, letterboxed. */
  function makeTransform(frame, width, height) {
    var b = sceneBounds(frame);
    var w = Math.max(1e-6, b.maxX - b.minX);
    var h = Math.max(1e-6, b.maxY - b.minY);
    var pad = 34;
    var k = Math.min((width - pad * 2) / w, (height - pad * 2) / h) * state.cam.k;
    var cx = (b.minX + b.maxX) / 2, cy = (b.minY + b.maxY) / 2;
    return {
      k: k,
      toPx: function (x, y) {
        return [
          width / 2 + (x - cx) * k + state.cam.x,
          height / 2 - (y - cy) * k + state.cam.y
        ];
      },
      toWorld: function (px, py) {
        return [
          (px - width / 2 - state.cam.x) / k + cx,
          -(py - height / 2 - state.cam.y) / k + cy
        ];
      },
      bounds: b
    };
  }

  function entityIndex(frame) {
    var map = new Map();
    if (!frame) { return map; }
    ["uavs", "ground_entities", "sites"].forEach(function (section) {
      (frame[section] || []).forEach(function (item) {
        map.set(item.entity.key, { section: section, item: item });
      });
    });
    return map;
  }

  /* ------------------------------------------------------------ 2-D render */

  function fitCanvas(canvas) {
    var ratio = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    var w = Math.max(80, Math.round(rect.width));
    var h = Math.max(80, Math.round(rect.height));
    if (canvas.width !== w * ratio || canvas.height !== h * ratio) {
      canvas.width = w * ratio;
      canvas.height = h * ratio;
    }
    var ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { ctx: ctx, width: w, height: h };
  }

  function draw2d(canvas, frame, opts) {
    var surface = fitCanvas(canvas);
    var ctx = surface.ctx, W = surface.width, H = surface.height;
    var T = tokens();
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = T.panel;
    ctx.fillRect(0, 0, W, H);
    if (!frame) { return; }
    var tr = makeTransform(frame, W, H);
    var policy = state.infoView === "policy";
    var observation = frame.observation_view || null;

    drawFrameBox(ctx, tr, T, frame);
    resetLabels(W, H);

    var byKey = entityIndex(frame);
    if (state.layers.paths) { drawPaths(ctx, tr, T, frame, byKey); }
    drawLinks(ctx, tr, T, frame, byKey);
    if (state.layers.sites) { drawSites(ctx, tr, T, frame); }
    drawGround(ctx, tr, T, frame, policy, observation);
    if (state.showTrails) { drawTrails(ctx, tr, T, opts && opts.trailFrames); }
    if (state.layers.uavs) { drawUavs(ctx, tr, T, frame); }
    flushLabels(ctx, T);
    drawScaleBar(ctx, tr, T, W, H);
    if (state.frozen) { drawWatermark(ctx, T, W, "DISPLAY FROZEN - producer continues"); }
    else if (state.streamState === "STALE") { drawWatermark(ctx, T, W, "PRODUCER STALE - no new frame"); }
    else if (state.streamState === "ENDED") { drawWatermark(ctx, T, W, "STREAM ENDED"); }
  }

  function drawFrameBox(ctx, tr, T, frame) {
    var b = tr.bounds;
    var p0 = tr.toPx(b.minX, b.maxY);
    var p1 = tr.toPx(b.maxX, b.minY);
    ctx.save();
    ctx.strokeStyle = T.line;
    ctx.lineWidth = 1;
    ctx.strokeRect(p0[0], p0[1], p1[0] - p0[0], p1[1] - p0[1]);
    // Grid at quarters so a distance is readable without a mouse.
    ctx.strokeStyle = T.line2;
    ctx.setLineDash([2, 4]);
    for (var k = 1; k < 4; k += 1) {
      var gx = tr.toPx(b.minX + (b.maxX - b.minX) * k / 4, b.minY);
      var gy = tr.toPx(b.minX, b.minY + (b.maxY - b.minY) * k / 4);
      ctx.beginPath(); ctx.moveTo(gx[0], p0[1]); ctx.lineTo(gx[0], p1[1]); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(p0[0], gy[1]); ctx.lineTo(p1[0], gy[1]); ctx.stroke();
    }
    ctx.setLineDash([]);
    ctx.restore();
  }

  function drawLinks(ctx, tr, T, frame, byKey) {
    var links = frame.links || [];
    var maxFlow = 0;
    links.forEach(function (l) {
      var f = mval(l.flow_mbps);
      if (f !== null && f > maxFlow) { maxFlow = f; }
    });
    links.forEach(function (link) {
      var style = linkStyle(link.link_class);
      if (!state.layers[style.group]) { return; }
      var isActive = link.activity === "active";
      if (isActive && !state.layers.active) { return; }
      if (!isActive && !state.layers.available) { return; }
      var a = byKey.get(link.source), b = byKey.get(link.target);
      if (!a || !b) { return; }
      var p = tr.toPx(a.item.position_m[0], a.item.position_m[1]);
      var q = tr.toPx(b.item.position_m[0], b.item.position_m[1]);
      var width = 1;
      if (isActive) {
        width = 2;
        if (state.layers.utilization) {
          var u = mval(link.utilization);
          if (u !== null) { width = 1.6 + 3.4 * Math.max(0, Math.min(1, u)); }
          else if (maxFlow > 0) {
            var f = mval(link.flow_mbps);
            if (f !== null) { width = 1.6 + 3.4 * (f / maxFlow); }
          }
        }
      }
      ctx.save();
      ctx.strokeStyle = isActive ? T[style.colourKey] : T.available;
      ctx.globalAlpha = isActive ? 0.95 : 0.4;
      ctx.lineWidth = width;
      // An available-but-idle link is always dotted, so it cannot be mistaken for service.
      ctx.setLineDash(isActive ? style.dash : [1, 4]);
      ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]); ctx.stroke();
      ctx.setLineDash([]);
      if (isActive) { drawArrowHead(ctx, p, q, T[style.colourKey]); }
      ctx.restore();
    });
  }

  function drawArrowHead(ctx, p, q, colour) {
    var dx = q[0] - p[0], dy = q[1] - p[1];
    var len = Math.hypot(dx, dy);
    if (len < 12) { return; }
    var ux = dx / len, uy = dy / len;
    var tipX = p[0] + ux * (len * 0.62), tipY = p[1] + uy * (len * 0.62);
    ctx.save();
    ctx.fillStyle = colour;
    ctx.beginPath();
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(tipX - ux * 7 - uy * 3.5, tipY - uy * 7 + ux * 3.5);
    ctx.lineTo(tipX - ux * 7 + uy * 3.5, tipY - uy * 7 - ux * 3.5);
    ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  function drawPaths(ctx, tr, T, frame, byKey) {
    (frame.paths || []).forEach(function (path) {
      if (!path.selected) { return; }
      var points = (path.node_keys || []).map(function (key) {
        var hit = byKey.get(key);
        return hit ? tr.toPx(hit.item.position_m[0], hit.item.position_m[1]) : null;
      }).filter(Boolean);
      if (points.length < 2) { return; }
      ctx.save();
      ctx.strokeStyle = T.accent;
      ctx.globalAlpha = 0.22;
      ctx.lineWidth = 7;
      ctx.lineJoin = "round";
      ctx.beginPath();
      ctx.moveTo(points[0][0], points[0][1]);
      points.slice(1).forEach(function (pt) { ctx.lineTo(pt[0], pt[1]); });
      ctx.stroke();
      ctx.restore();
    });
  }

  function drawSites(ctx, tr, T, frame) {
    (frame.sites || []).forEach(function (site) {
      var p = tr.toPx(site.position_m[0], site.position_m[1]);
      var radioDown = site.radio_up === false;
      var coreDown = site.core_link_up === false;
      drawMarker(ctx, radioDown || coreDown ? "squarex" : "square", p[0], p[1], 7,
        radioDown || coreDown ? T.unserved : T.site);
      // Radio and wired core are separate capabilities: two small indicator ticks.
      ctx.save();
      ctx.font = "9px " + T.mono;
      ctx.fillStyle = T.ink3;
      var marks = [];
      if (site.radio_up === false) { marks.push("radio down"); }
      else if (site.radio_up === true) { marks.push("radio up"); }
      else { marks.push("radio ?"); }
      if (site.core_link_up === false) { marks.push("core down"); }
      else if (site.core_link_up === true) { marks.push("core up"); }
      else { marks.push("core ?"); }
      if (site.degraded) { marks.push("degraded"); }
      placeLabel(ctx, T, p[0], p[1], marks.join(" / "), T.ink3);
      if (state.layers.labels) {
        ctx.font = "10px " + T.mono;
        placeLabel(ctx, T, p[0], p[1], site.entity.label || site.entity.key, T.ink2);
      }
      ctx.restore();
    });
  }

  /* Demand markers use AREA proportional to the offered weight, with a size legend, so a
   * doubled demand looks twice as large in the quantity the eye integrates. */
  function demandRadius(value, maxValue) {
    var minR = 3.0, maxR = 16.0;
    if (value === null || maxValue <= 0) { return minR; }
    var area = Math.max(0, value) / maxValue;              // 0..1 in AREA
    return minR + (maxR - minR) * Math.sqrt(area);          // radius ~ sqrt(area)
  }

  function drawGround(ctx, tr, T, frame, policy, observation) {
    var entities = frame.ground_entities || [];
    var cap = frame.capability || {};
    var aggregate = cap.has_aggregate_demand;
    if (aggregate && !state.layers.demand) { return; }
    if (!aggregate && !state.layers.ues) { return; }

    var maxOffered = 0;
    entities.forEach(function (g) {
      var v = mval(g.offered_mbps);
      if (v !== null && v > maxOffered) { maxOffered = v; }
    });

    entities.forEach(function (g, i) {
      var p = tr.toPx(g.position_m[0], g.position_m[1]);
      var offered = g.offered_mbps;
      var delivered = g.delivered_mbps;
      var status = g.service_status;
      var observed = g.observed !== false;

      if (policy && observation) {
        // Policy-visible: replace truth with exactly what the recorded policy view held.
        // An absent entry stays absent. Nothing is back-filled from truth.
        var pv = (observation.values || {});
        var mask = (observation.masks || {}).demand_observed;
        var seen = mask ? !!mask[i] : observed;
        var po = pv.demand_offered_mbps ? pv.demand_offered_mbps[i] : undefined;
        var pd = pv.demand_delivered_mbps ? pv.demand_delivered_mbps[i] : undefined;
        offered = (seen && po !== null && po !== undefined)
          ? { value: po, validity: "ok", unit: "Mbps" }
          : { value: null, validity: "unknown", reason: "not in the policy-visible view" };
        delivered = (seen && pd !== null && pd !== undefined)
          ? { value: pd, validity: "ok", unit: "Mbps" }
          : { value: null, validity: "unknown", reason: "not in the policy-visible view" };
        status = seen ? status : "unknown_demand";
        observed = seen;
      }

      var offeredValue = mval(offered);
      var style = statusStyle(status);
      var r = aggregate ? demandRadius(offeredValue, maxOffered) : 4.5;
      if (offeredValue === null && aggregate) {
        // Unknown demand is not an empty region and not a zero-demand region.
        if (!state.layers.unknown) { return; }
        drawMarker(ctx, "hatch", p[0], p[1], 7, T.unknown);
      } else {
        drawMarker(ctx, style.shape, p[0], p[1], r, T[style.colourKey] || T.ink3);
      }

      if (!observed && state.layers.unknown) {
        ctx.save();
        ctx.strokeStyle = T.unknown;
        ctx.setLineDash([2, 2]);
        ctx.beginPath(); ctx.arc(p[0], p[1], r + 4, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();
      }
      if (state.selection === g.entity.key) { drawSelectionRing(ctx, T, p, r + 7); }
      if (state.layers.labels) {
        ctx.save();
        ctx.font = "9.5px " + T.mono;
        placeLabel(ctx, T, p[0] + r - 7, p[1], g.entity.label || g.entity.key, T.ink3);
        ctx.restore();
      }
      void delivered;
    });
  }

  function drawUavs(ctx, tr, T, frame) {
    (frame.uavs || []).forEach(function (uav) {
      var p = tr.toPx(uav.position_m[0], uav.position_m[1]);
      drawMarker(ctx, uav.active === false ? "ring" : "triangle", p[0], p[1], 7.5,
        uav.active === false ? T.ink3 : T.uav);
      var vel = uav.executed_velocity_mps || uav.requested_velocity_mps;
      if (vel) {
        var n = Math.hypot(vel[0], vel[1]);
        if (n > 1e-6) {
          ctx.save();
          ctx.strokeStyle = T.uav;
          ctx.lineWidth = 1.6;
          ctx.beginPath();
          ctx.moveTo(p[0], p[1]);
          ctx.lineTo(p[0] + (vel[0] / n) * 17, p[1] - (vel[1] / n) * 17);
          ctx.stroke();
          ctx.restore();
        }
      }
      ctx.save();
      ctx.fillStyle = T.ink2;
      ctx.font = "10px " + T.mono;
      var alt = uav.position_m[2];
      placeLabel(ctx, T, p[0], p[1],
        (uav.entity.label || uav.entity.key) + "  " + fmt(alt, 0) + " m", T.ink2);
      if (uav.team_skill_id !== null && uav.team_skill_id !== undefined) {
        placeLabel(ctx, T, p[0], p[1], "skill " + uav.team_skill_id, T.ink2);
      }
      ctx.restore();
      if (state.selection === uav.entity.key) { drawSelectionRing(ctx, T, p, 14); }
    });
  }

  function drawSelectionRing(ctx, T, p, r) {
    ctx.save();
    ctx.strokeStyle = T.accent;
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, Math.PI * 2); ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }

  /* Trails are drawn per stable entity key, so a reused array slot never inherits the
   * previous lifetime's history. A gap in recorded frames breaks the line rather than
   * interpolating across it. */
  function drawTrails(ctx, tr, T, frames) {
    if (!frames || frames.length < 2) { return; }
    var take = frames.slice(Math.max(0, frames.length - state.trailLength - 1));
    var byEntity = new Map();
    take.forEach(function (f, order) {
      (f.uavs || []).forEach(function (u) {
        if (!byEntity.has(u.entity.key)) { byEntity.set(u.entity.key, []); }
        byEntity.get(u.entity.key).push({
          p: u.position_m,
          episode: (f.identity || {}).episode_id,
          order: order
        });
      });
    });
    ctx.save();
    ctx.strokeStyle = T.uav;
    ctx.globalAlpha = 0.45;
    ctx.lineWidth = 1.4;
    byEntity.forEach(function (points) {
      var previous = null;
      ctx.beginPath();
      points.forEach(function (point) {
        var px = tr.toPx(point.p[0], point.p[1]);
        // Never connect across an episode boundary or a missing sample.
        var broken = previous && (previous.episode !== point.episode || point.order !== previous.order + 1);
        if (!previous || broken) { ctx.moveTo(px[0], px[1]); } else { ctx.lineTo(px[0], px[1]); }
        previous = point;
      });
      ctx.stroke();
    });
    ctx.restore();
  }

  function drawScaleBar(ctx, tr, T, W, H) {
    var targetPx = Math.min(180, W * 0.22);
    var metres = targetPx / tr.k;
    var pow = Math.pow(10, Math.floor(Math.log10(Math.max(1, metres))));
    var nice = [1, 2, 5, 10].map(function (m) { return m * pow; })
      .reduce(function (best, cand) {
        return Math.abs(cand - metres) < Math.abs(best - metres) ? cand : best;
      });
    var px = nice * tr.k;
    var x = 16, y = H - 18;
    ctx.save();
    ctx.strokeStyle = T.ink2;
    ctx.fillStyle = T.ink2;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, y); ctx.lineTo(x + px, y);
    ctx.moveTo(x, y - 4); ctx.lineTo(x, y + 4);
    ctx.moveTo(x + px, y - 4); ctx.lineTo(x + px, y + 4);
    ctx.stroke();
    ctx.font = "11px " + T.mono;
    ctx.fillText(nice >= 1000 ? (nice / 1000) + " km" : nice + " m", x, y - 8);
    ctx.fillText("equal metric aspect", x, y + 14);
    ctx.restore();
  }

  /* The scene key is DOM, not canvas. Painted into the scene it hid the very markers it
     described, and reserving a gutter big enough for it would have halved the map. */
  function renderSceneLegend(frame) {
    var host = $("scene-legend");
    if (!host) { return; }
    host.textContent = "";
    if (!frame) { host.hidden = true; return; }
    host.hidden = false;
    var T = tokens();
    var cap = frame.capability || {};
    var rows = [];
    if (cap.has_uav_positions) { rows.push(["triangle", T.uav, "UAV"]); }
    if (cap.has_sites) { rows.push(["square", T.site, "site / base station"]); }
    if (cap.has_individual_ues) {
      rows.push(["disc", T.served, "UE served"]);
      rows.push(["dashsq", T.nobackhaul, "UE associated, no backhaul"]);
      rows.push(["cross", T.unserved, "UE unserved"]);
    }
    if (cap.has_aggregate_demand) {
      rows.push(["disc", T.served, "aggregate demand point: served"]);
      rows.push(["half", T.partial, "aggregate demand point: partial"]);
      rows.push(["cross", T.unserved, "aggregate demand point: unserved"]);
      rows.push(["dot", T.zero, "zero demand (measured)"]);
      rows.push(["hatch", T.unknown, "unknown demand (not zero)"]);
    }
    rows.forEach(function (row) {
      var key = el("span", "key");
      var swatch = document.createElement("canvas");
      var dpr = window.devicePixelRatio || 1;
      swatch.width = Math.round(13 * dpr);
      swatch.height = Math.round(13 * dpr);
      var sctx = swatch.getContext("2d");
      sctx.scale(dpr, dpr);
      drawMarker(sctx, row[0], 6.5, 6.5, 5, row[1]);
      key.appendChild(swatch);
      key.appendChild(document.createTextNode(row[2]));
      host.appendChild(key);
    });
    if (cap.has_aggregate_demand) {
      host.appendChild(el("span", "key note",
        "marker AREA is proportional to offered demand"));
    }
    host.appendChild(el("span", "key note",
      "solid = carrying traffic, dotted = available with no traffic"));
  }

  /* Greedy non-overlapping label placement for the 2-D scene. Fixed offsets made a site's
     status text print straight through a nearby UAV's label whenever the two came within a
     few hundred metres of each other, which in this scenario is most of the episode. */
  var labelBoxes = [];
  var labelQueue = [];
  var labelBounds = { w: 0, h: 0 };
  var LABEL_OFFSETS = [
    [10, -9], [10, 10], [-10, -9], [-10, 10],
    [10, -22], [10, 23], [-10, -22], [-10, 23]
  ];

  function resetLabels(W, H) {
    labelBoxes = [];
    labelQueue = [];
    labelBounds = { w: W, h: H };
  }

  function placeLabel(ctx, T, x, y, text, colour) {
    var w = ctx.measureText(text).width;
    var chosen = null;
    for (var i = 0; i < LABEL_OFFSETS.length; i++) {
      var dx = LABEL_OFFSETS[i][0], dy = LABEL_OFFSETS[i][1];
      var left = dx >= 0 ? x + dx : x + dx - w;
      /* Clamp into the canvas instead of rejecting the candidate. Rejecting pushed a label
         for an entity near the right edge all the way across the scene, where it read as
         the status of whatever entity it landed next to. */
      left = Math.max(3, Math.min(left, labelBounds.w - w - 3));
      var box = [left - 3, y + dy - 10, left + w + 3, y + dy + 4];
      var clash = false;
      for (var j = 0; j < labelBoxes.length; j++) {
        var o = labelBoxes[j];
        if (box[0] < o[2] && o[0] < box[2] && box[1] < o[3] && o[1] < box[3]) { clash = true; break; }
      }
      if (!clash) { chosen = { box: box, left: left, dy: dy, moved: i > 0 }; break; }
    }
    if (chosen === null) {
      var fl = Math.max(3, Math.min(x + LABEL_OFFSETS[0][0], labelBounds.w - w - 3));
      chosen = {
        box: [fl - 3, y + LABEL_OFFSETS[0][1] - 10, fl + w + 3, y + LABEL_OFFSETS[0][1] + 4],
        left: fl, dy: LABEL_OFFSETS[0][1], moved: true
      };
    }
    labelBoxes.push(chosen.box);
    /* Queued, not drawn here: sites are painted before demand points and UAVs, so a label
       drawn in place was buried under markers added later in the same pass. */
    labelQueue.push({
      box: chosen.box, left: chosen.left, y: y + chosen.dy, anchor: [x, y],
      leader: chosen.moved, text: text, colour: colour, font: ctx.font
    });
  }

  function flushLabels(ctx, T) {
    ctx.save();
    ctx.textAlign = "left";
    labelQueue.forEach(function (item) {
      /* A displaced label gets a leader back to its entity, so a reader never has to guess
         which marker a status line belongs to. */
      if (item.leader) {
        var cx = Math.max(item.box[0], Math.min(item.anchor[0], item.box[2]));
        var cy = Math.max(item.box[1], Math.min(item.anchor[1], item.box[3]));
        if (Math.hypot(cx - item.anchor[0], cy - item.anchor[1]) > 2) {
          ctx.save();
          ctx.strokeStyle = T.line2;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(item.anchor[0], item.anchor[1]);
          ctx.lineTo(cx, cy);
          ctx.stroke();
          ctx.restore();
        }
      }
      plate(ctx, T, item.box[0], item.box[1], item.box[2] - item.box[0], item.box[3] - item.box[1]);
      ctx.font = item.font;
      ctx.fillStyle = item.colour;
      ctx.fillText(item.text, item.left, item.y);
    });
    ctx.restore();
    labelQueue = [];
  }

  /* A translucent rounded plate behind overlay text. Everything the viewer paints over the
     scene - the legend, entity labels, the scale bar - reads through it, and nothing the
     plate covers is a measurement the operator needs at that instant. */
  function plate(ctx, T, x, y, w, h) {
    ctx.save();
    ctx.globalAlpha = 0.82;
    ctx.fillStyle = T.panel;
    ctx.strokeStyle = T.line;
    ctx.lineWidth = 1;
    var r = 4;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawWatermark(ctx, T, W, text) {
    ctx.save();
    ctx.font = "600 12px " + T.mono;
    var w = ctx.measureText(text).width;
    plate(ctx, T, W / 2 - w / 2 - 7, 5, w + 14, 19);
    ctx.fillStyle = T.unserved;
    ctx.textAlign = "center";
    ctx.fillText(text, W / 2, 18);
    ctx.restore();
  }

  /* ------------------------------------------------------------ 3-D render */

  function draw3d(canvas, frame) {
    var surface = fitCanvas(canvas);
    var ctx = surface.ctx, W = surface.width, H = surface.height;
    var T = tokens();
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = T.panel;
    ctx.fillRect(0, 0, W, H);
    if (!frame) { return; }
    var b = sceneBounds(frame);
    if (!state.cam3d) {
      state.cam3d = new window.RSScene3D.Camera([b.minX, b.minY, b.maxX, b.maxY]);
    }
    var cam = state.cam3d;
    cam.bounds = [b.minX, b.minY, b.maxX, b.maxY];
    cam.zExaggeration = (frame.geometry && frame.geometry.vertical_exaggeration) || 1.0;
    cam.drawGround(ctx, W, H, T);

    var byKey = entityIndex(frame);
    var projected = new Map();
    byKey.forEach(function (hit, key) {
      var p = hit.item.position_m;
      projected.set(key, cam.project([p[0], p[1], p[2] || 0], W, H));
    });

    // Links first, depth-sorted back to front.
    var links = (frame.links || []).slice().filter(function (l) {
      var style = linkStyle(l.link_class);
      if (!state.layers[style.group]) { return false; }
      if (l.activity === "active") { return state.layers.active; }
      return state.layers.available;
    });
    links.sort(function (a, b2) {
      var pa = projected.get(a.source), pb = projected.get(b2.source);
      return ((pb && pb.depth) || 0) - ((pa && pa.depth) || 0);
    });
    links.forEach(function (link) {
      var p = projected.get(link.source), q = projected.get(link.target);
      if (!p || !q || !p.visible || !q.visible) { return; }
      var style = linkStyle(link.link_class);
      var isActive = link.activity === "active";
      ctx.save();
      ctx.strokeStyle = isActive ? T[style.colourKey] : T.available;
      ctx.globalAlpha = isActive ? 0.9 : 0.32;
      ctx.lineWidth = isActive ? 2 : 1;
      ctx.setLineDash(isActive ? style.dash : [1, 4]);
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
    });

    // Ground entities on the plane.
    var maxOffered = 0;
    (frame.ground_entities || []).forEach(function (g) {
      var v = mval(g.offered_mbps);
      if (v !== null && v > maxOffered) { maxOffered = v; }
    });
    (frame.ground_entities || []).forEach(function (g) {
      var p = projected.get(g.entity.key);
      if (!p || !p.visible) { return; }
      var style = statusStyle(g.service_status);
      var aggregate = (frame.capability || {}).has_aggregate_demand;
      var r = (aggregate ? demandRadius(mval(g.offered_mbps), maxOffered) : 4) * Math.max(0.5, Math.min(2.2, p.scale * 1.6));
      drawMarker(ctx, mval(g.offered_mbps) === null && aggregate ? "hatch" : style.shape,
        p.x, p.y, r, T[style.colourKey] || T.ink3);
      if (state.selection === g.entity.key) { drawSelectionRing(ctx, T, [p.x, p.y], r + 6); }
    });

    (frame.sites || []).forEach(function (site) {
      var top = cam.drawStalk(ctx, site.position_m, W, H, T);
      if (!top) { return; }
      var down = site.radio_up === false || site.core_link_up === false;
      drawMarker(ctx, down ? "squarex" : "square", top.x, top.y, 6, down ? T.unserved : T.site);
      if (state.selection === site.entity.key) { drawSelectionRing(ctx, T, [top.x, top.y], 12); }
    });

    (frame.uavs || []).forEach(function (uav) {
      var top = cam.drawStalk(ctx, uav.position_m, W, H, T);
      if (!top) { return; }
      drawMarker(ctx, "triangle", top.x, top.y, 7, uav.active === false ? T.ink3 : T.uav);
      ctx.save();
      ctx.fillStyle = T.ink2;
      ctx.font = "10px " + T.mono;
      ctx.fillText((uav.entity.label || uav.entity.key) + " " + fmt(uav.position_m[2], 0) + " m",
        top.x + 9, top.y - 7);
      ctx.restore();
      if (state.selection === uav.entity.key) { drawSelectionRing(ctx, T, [top.x, top.y], 13); }
    });

    /* Bottom-left, because the top strip belongs to the frozen/stale/ended watermark and the
       two were printing through each other. */
    ctx.save();
    ctx.fillStyle = T.ink3;
    ctx.font = "11px " + T.mono;
    var caption = [
      "3-D inspection - drag to orbit, wheel to zoom, double-click for top-down",
      "vertical exaggeration " + fmt(cam.zExaggeration, 2) + "x (1 = true scale); altitude in metres"
    ];
    if (!(frame.capability || {}).has_altitude) {
      caption.push("no elevation geometry recorded: flat-ground model, not reconstructed terrain");
    }
    caption.forEach(function (line, i) {
      ctx.fillText(line, 12, H - 10 - (caption.length - 1 - i) * 15);
    });
    ctx.restore();
    if (state.frozen) { drawWatermark(ctx, T, W, "DISPLAY FROZEN - producer continues"); }
  }

  /* ------------------------------------------------------------- charts */

  function seriesFromFrames(frames, names) {
    var out = {};
    names.forEach(function (n) { out[n] = []; });
    frames.forEach(function (f) {
      var t = (f.clock || {}).simulation_time_s;
      var m = f.interval_metrics || {};
      names.forEach(function (n) {
        var v = mval(m[n]);
        out[n].push({ t: t, v: v });
      });
    });
    return out;
  }

  function drawLineChart(canvas, series, opts) {
    var surface = fitCanvas(canvas);
    var ctx = surface.ctx, W = surface.width, H = surface.height;
    var T = tokens();
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = T.panel;
    ctx.fillRect(0, 0, W, H);
    var pad = { l: 46, r: 8, t: 20, b: 26 };
    var keys = Object.keys(series).filter(function (k) {
      return series[k].some(function (p) { return p.v !== null; });
    });
    ctx.save();
    ctx.font = "11px " + T.mono;
    ctx.fillStyle = T.ink2;
    ctx.fillText(opts.title, pad.l, 13);
    if (!keys.length) {
      ctx.fillStyle = T.ink3;
      ctx.fillText("not recorded: " + (opts.missing || Object.keys(series).join(", ")), pad.l, H / 2);
      ctx.restore();
      return;
    }
    var tMin = Infinity, tMax = -Infinity, vMin = 0, vMax = -Infinity;
    keys.forEach(function (k) {
      series[k].forEach(function (p) {
        if (p.t === null || p.t === undefined) { return; }
        tMin = Math.min(tMin, p.t); tMax = Math.max(tMax, p.t);
        if (p.v !== null) { vMin = Math.min(vMin, p.v); vMax = Math.max(vMax, p.v); }
      });
    });
    if (!isFinite(tMin)) { ctx.restore(); return; }
    if (tMax === tMin) { tMax = tMin + 1; }
    if (vMax === vMin) { vMax = vMin + 1; }
    var x = function (t) { return pad.l + (t - tMin) / (tMax - tMin) * (W - pad.l - pad.r); };
    var y = function (v) { return H - pad.b - (v - vMin) / (vMax - vMin) * (H - pad.t - pad.b); };

    ctx.strokeStyle = T.line2;
    ctx.lineWidth = 1;
    [0, 0.5, 1].forEach(function (f) {
      var vy = y(vMin + (vMax - vMin) * f);
      ctx.beginPath(); ctx.moveTo(pad.l, vy); ctx.lineTo(W - pad.r, vy); ctx.stroke();
      ctx.fillStyle = T.ink3;
      ctx.fillText(fmt(vMin + (vMax - vMin) * f, 2), 4, vy + 3);
    });
    ctx.fillStyle = T.ink3;
    ctx.fillText(fmt(tMin, 0) + " s", pad.l, H - 8);
    ctx.textAlign = "right";
    ctx.fillText(fmt(tMax, 0) + " s", W - pad.r, H - 8);
    ctx.textAlign = "left";

    var palette = [T.accent, T.served, T.unserved, T.backhaul, T.partial];
    var dashes = [[], [5, 3], [2, 2], [7, 2, 2, 2], [1, 3]];
    keys.forEach(function (k, i) {
      ctx.save();
      ctx.strokeStyle = palette[i % palette.length];
      ctx.setLineDash(dashes[i % dashes.length]);
      ctx.lineWidth = 1.7;
      ctx.beginPath();
      var open = false;
      series[k].forEach(function (p) {
        if (p.v === null || p.t === null || p.t === undefined) { open = false; return; }
        var px = x(p.t), py = y(p.v);
        if (!open) { ctx.moveTo(px, py); open = true; } else { ctx.lineTo(px, py); }
      });
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = palette[i % palette.length];
      ctx.fillText(k, pad.l + 4 + i * 0, pad.t + 2 + i * 12);
      ctx.restore();
    });

    // Linked cursor at the displayed frame's time.
    var cursorFrame = currentFrame();
    if (cursorFrame) {
      var ct = (cursorFrame.clock || {}).simulation_time_s;
      if (ct !== null && ct !== undefined && ct >= tMin && ct <= tMax) {
        ctx.save();
        ctx.strokeStyle = T.accent;
        ctx.setLineDash([3, 3]);
        ctx.beginPath(); ctx.moveTo(x(ct), pad.t); ctx.lineTo(x(ct), H - pad.b); ctx.stroke();
        ctx.restore();
      }
    }
    ctx.restore();
  }

  function drawTimeline(canvas, frames) {
    var surface = fitCanvas(canvas);
    var ctx = surface.ctx, W = surface.width, H = surface.height;
    var T = tokens();
    ctx.clearRect(0, 0, W, H);
    var frame = currentFrame();
    var events = [];
    var seen = new Set();
    frames.forEach(function (f) {
      (f.events || []).forEach(function (e) {
        var key = e.event_type + "@" + e.time_s + "@" + (e.entity || "");
        if (!seen.has(key)) { seen.add(key); events.push(e); }
      });
    });
    var tMin = Infinity, tMax = -Infinity;
    frames.forEach(function (f) {
      var t = (f.clock || {}).simulation_time_s;
      if (t === null || t === undefined) { return; }
      tMin = Math.min(tMin, t); tMax = Math.max(tMax, t);
    });
    ctx.save();
    ctx.font = "10.5px " + T.mono;
    if (!isFinite(tMin)) {
      ctx.fillStyle = T.ink3;
      ctx.fillText("no frames yet", 8, H / 2);
      ctx.restore();
      return;
    }
    if (tMax === tMin) { tMax = tMin + 1; }
    var x = function (t) { return 40 + (t - tMin) / (tMax - tMin) * (W - 60); };
    ctx.strokeStyle = T.line;
    ctx.beginPath(); ctx.moveTo(40, H - 20); ctx.lineTo(W - 20, H - 20); ctx.stroke();
    ctx.fillStyle = T.ink3;
    ctx.fillText(fmt(tMin, 0) + " s", 4, H - 16);
    ctx.fillText(fmt(tMax, 0) + " s", W - 46, H - 6);

    var EVENT_STYLE = {
      full_site_failure: { colour: T.unserved, shape: "squarex" },
      wired_backhaul_outage: { colour: T.unserved, shape: "dashsq" },
      capacity_degradation: { colour: T.partial, shape: "half" },
      repair: { colour: T.served, shape: "disc" },
      alarm: { colour: T.partial, shape: "triangle" }
    };
    events.forEach(function (e) {
      var style = EVENT_STYLE[e.event_type] || { colour: T.ink2, shape: "ring" };
      var px = x(e.time_s);
      ctx.save();
      ctx.strokeStyle = style.colour;
      ctx.setLineDash([2, 3]);
      ctx.beginPath(); ctx.moveTo(px, 10); ctx.lineTo(px, H - 20); ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
      drawMarker(ctx, style.shape, px, H - 20, 5, style.colour);
      ctx.fillStyle = T.ink2;
      ctx.fillText(e.event_type + " @" + fmt(e.time_s, 1) + "s", px + 7, 18);
    });
    if (frame) {
      var ct = (frame.clock || {}).simulation_time_s;
      if (ct !== null && ct !== undefined) {
        ctx.save();
        ctx.strokeStyle = T.accent;
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(x(ct), 6); ctx.lineTo(x(ct), H - 16); ctx.stroke();
        ctx.restore();
      }
    }
    ctx.restore();

    var legend = $("timeline-legend");
    legend.textContent = "";
    if (!events.length) {
      legend.appendChild(el("span", "note",
        "No event has been recorded up to the displayed time. Future faults are privileged "
        + "simulator knowledge and are not shown in a live timeline."));
    } else {
      Object.keys(EVENT_STYLE).forEach(function (kind) {
        if (!events.some(function (e) { return e.event_type === kind; })) { return; }
        var span = el("span");
        var swatch = el("em");
        swatch.style.background = EVENT_STYLE[kind].colour;
        span.appendChild(swatch);
        span.appendChild(el("span", null, kind));
        legend.appendChild(span);
      });
      legend.appendChild(el("span", "note", "repair is exogenous: configured restoration, not UAV-caused recovery"));
    }
  }

  /* ------------------------------------------------------------- inspector */

  function renderInspector(key) {
    var box = $("inspector");
    box.textContent = "";
    $("inspector-mode").textContent = state.infoView === "policy"
      ? "policy-visible" : "simulator truth (privileged)";
    var frame = currentFrame();
    if (!frame || !key) {
      box.appendChild(el("p", "note", "Hover an entity to preview it; click to pin it here."));
      return;
    }
    var hit = entityIndex(frame).get(key);
    if (!hit) {
      box.appendChild(el("p", "note", "Entity " + key + " is not present in the displayed frame."));
      return;
    }
    var item = hit.item;
    var table = el("table");
    var truthTable = el("table");
    var truthRows = 0;
    var policyView = state.infoView === "policy";
    /* `priv` marks a row read from the frame's simulator-truth records rather than from its
       observation_view. In the policy-visible mode those rows move to their own titled block:
       printing them under a "policy-visible" heading claimed a provenance they do not have. */
    function row(label, value, priv) {
      var tr = el("tr");
      tr.appendChild(el("td", null, label));
      var td = el("td");
      if (value && typeof value === "object" && "absent" in value) {
        if (value.absent) {
          td.appendChild(el("span", "absent", value.text));
        } else {
          td.appendChild(el("span", null, value.text));
        }
      } else {
        td.appendChild(el("span", null, value === null || value === undefined ? "—" : String(value)));
      }
      tr.appendChild(td);
      if (priv && policyView) { truthTable.appendChild(tr); truthRows += 1; }
      else { table.appendChild(tr); }
    }
    row("stable id", item.entity.key);
    row("kind", item.entity.kind + (item.entity.kind === "aggregate_demand_point"
      ? " (aggregate of a source grid cell, not a person)" : ""));
    row("array slot", item.entity.slot);
    row("lifetime generation", item.entity.generation);
    row("label", item.entity.label || "—");
    row("position (m)", item.position_m.map(function (v) { return fmt(v, 1); }).join(", "));
    row("active", item.active);

    if (hit.section === "uavs") {
      row("executed velocity (m/s)", item.executed_velocity_mps
        ? item.executed_velocity_mps.map(function (v) { return fmt(v, 2); }).join(", ")
        : { absent: true, text: "not recorded" }, true);
      row("requested velocity", item.requested_velocity_mps
        ? item.requested_velocity_mps.map(function (v) { return fmt(v, 3); }).join(", ")
        : { absent: true, text: "not recorded" });
      row("team skill", item.team_skill_id === null || item.team_skill_id === undefined
        ? { absent: true, text: "no skill layer on this route" } : item.team_skill_id);
      row("individual skill", item.individual_skill_id === null || item.individual_skill_id === undefined
        ? { absent: true, text: "no skill layer on this route" } : item.individual_skill_id);
      row("skill age", measured(item.skill_age_s));
      row("energy", measured(item.energy), true);
    } else if (hit.section === "ground_entities") {
      var offered = item.offered_mbps, delivered = item.delivered_mbps, status = item.service_status;
      if (state.infoView === "policy") {
        var idx = (frame.ground_entities || []).indexOf(item);
        var ov = frame.observation_view || {};
        var mask = (ov.masks || {}).demand_observed;
        var seen = mask ? !!mask[idx] : item.observed !== false;
        var po = ((ov.values || {}).demand_offered_mbps || [])[idx];
        var pd = ((ov.values || {}).demand_delivered_mbps || [])[idx];
        offered = seen && po !== null && po !== undefined
          ? { value: po, validity: "ok", unit: "Mbps" }
          : { value: null, validity: "unknown", reason: "absent from the policy-visible view" };
        delivered = seen && pd !== null && pd !== undefined
          ? { value: pd, validity: "ok", unit: "Mbps" }
          : { value: null, validity: "unknown", reason: "absent from the policy-visible view" };
        if (!seen) { status = "unknown_demand"; }
        var age = ((ov.ages_s || {}).demand_age_s || [])[idx];
        row("telemetry age (s)", age === null || age === undefined
          ? { absent: true, text: "not recorded" } : fmt(age, 2));
      }
      row("offered", measured(offered));
      row("delivered", measured(delivered));
      row("service status", statusStyle(status).label);
      row("observed", item.observed, true);
      row("age", measured(item.age_s), true);
      row("associated to", item.associated_to || { absent: true, text: "no association recorded" }, true);
      row("SINR", measured(item.sinr_db), true);
      row("represents", item.represents_count + " source unit(s)");
    } else if (hit.section === "sites") {
      row("radio up", item.radio_up === null || item.radio_up === undefined
        ? { absent: true, text: "not recorded" } : item.radio_up, true);
      row("core link up", item.core_link_up === null || item.core_link_up === undefined
        ? { absent: true, text: "not recorded" } : item.core_link_up, true);
      row("access capacity scale", measured(item.access_capacity_scale), true);
      row("backhaul capacity scale", measured(item.backhaul_capacity_scale), true);
      row("degraded", item.degraded, true);
    }
    box.appendChild(table);
    if (policyView && truthRows) {
      box.appendChild(el("h4", "truth-block",
        "simulator truth - not read from the observation view"));
      box.appendChild(truthTable);
    }

    // Links touching this entity, with the bottleneck view the owner needs.
    var links = (frame.links || []).filter(function (l) {
      return l.source === key || l.target === key;
    });
    if (links.length) {
      box.appendChild(el("h4", policyView ? "truth-block" : null,
        "Links (" + links.length + ")"
        + (policyView ? " - simulator truth, not read from the observation view" : "")));
      var lt = el("table");
      links.slice(0, 24).forEach(function (l) {
        var tr = el("tr");
        tr.appendChild(el("td", null, l.link_class + (l.activity === "active" ? " ●" : " ○")));
        var td = el("td");
        var flow = measured(l.flow_mbps), util = measured(l.utilization), capv = measured(l.capacity_mbps);
        td.appendChild(el("div", flow.absent ? "absent" : null, "flow " + flow.text));
        td.appendChild(el("div", capv.absent ? "absent" : null, "isolated capacity " + capv.text));
        td.appendChild(el("div", util.absent ? "absent" : null, "utilization " + util.text));
        if (l.resource_domain) { td.appendChild(el("div", null, "domain " + l.resource_domain)); }
        tr.appendChild(td);
        lt.appendChild(tr);
      });
      box.appendChild(lt);
      if (links.length > 24) {
        box.appendChild(el("p", "note", (links.length - 24) + " further links not listed"));
      }
      box.appendChild(el("p", "note",
        "Isolated link capacity is what the link would carry if it owned its radio resource; "
        + "it does not imply the flow is schedulable. A saturated link is a measurement, not a "
        + "cause."));
    }
  }

  function renderCapability(frame) {
    var box = $("capability");
    box.textContent = "";
    if (!frame) { return; }
    var cap = frame.capability || {};
    Object.keys(cap).filter(function (k) { return k !== "notes"; }).sort().forEach(function (k) {
      var chip = el("span", "cap" + (cap[k] ? " on" : ""), k.replace(/^has_/, ""));
      chip.title = cap[k] ? "recorded by this route" : "not available on this route";
      box.appendChild(chip);
    });
    var prov = frame.provenance || {};
    var list = el("ul", "cap-notes");
    [
      "route: " + prov.route,
      "environment: " + prov.environment_id,
      "source: " + prov.source_kind,
      "policy: " + prov.policy_kind + (prov.checkpoint_identity ? " (" + prov.checkpoint_identity + ")" : ""),
      "information condition: " + prov.information_condition,
      "capture resolution: " + prov.capture_resolution,
      "real activity data: " + (prov.is_real_activity_data ? "yes" : "no"),
      "dataset hash: " + (prov.dataset_hash || "not recorded")
    ].forEach(function (line) { list.appendChild(el("li", null, line)); });
    (cap.notes || []).forEach(function (n) { list.appendChild(el("li", null, n)); });
    (prov.measured_fields || []).forEach(function (n) { list.appendChild(el("li", null, "measured: " + n)); });
    (prov.derived_fields || []).forEach(function (n) { list.appendChild(el("li", null, "derived: " + n)); });
    (prov.notes || []).forEach(function (n) { list.appendChild(el("li", null, n)); });
    box.appendChild(list);
  }

  function renderEntityTable(frame) {
    var thead = $("entity-table").querySelector("thead");
    var tbody = $("entity-table").querySelector("tbody");
    thead.textContent = "";
    tbody.textContent = "";
    if (!frame) { return; }
    var headRow = el("tr");
    ["id", "kind", "x", "y", "z", "status", "offered", "delivered"].forEach(function (h) {
      headRow.appendChild(el("th", null, h));
    });
    thead.appendChild(headRow);
    var rows = [];
    (frame.uavs || []).forEach(function (u) { rows.push({ e: u, kind: "uav" }); });
    (frame.sites || []).forEach(function (s) { rows.push({ e: s, kind: "site" }); });
    (frame.ground_entities || []).forEach(function (g) { rows.push({ e: g, kind: g.entity.kind }); });
    rows.forEach(function (row) {
      var tr = el("tr");
      if (state.selection === row.e.entity.key) { tr.className = "sel"; }
      var offered = measured(row.e.offered_mbps), delivered = measured(row.e.delivered_mbps);
      [
        row.e.entity.label || row.e.entity.key,
        row.kind,
        fmt(row.e.position_m[0], 0),
        fmt(row.e.position_m[1], 0),
        fmt(row.e.position_m[2], 0),
        row.e.service_status || (row.e.degraded ? "degraded" : "—"),
        offered.absent ? offered.text : offered.text,
        delivered.absent ? delivered.text : delivered.text
      ].forEach(function (v, i) {
        var td = el("td", (i >= 6 && (i === 6 ? offered : delivered).absent) ? "absent" : null, v);
        tr.appendChild(td);
      });
      tr.addEventListener("click", function () {
        state.selection = row.e.entity.key;
        render();
      });
      tbody.appendChild(tr);
    });
  }

  function renderLayers(frame) {
    var box = $("layer-controls");
    box.textContent = "";
    var cap = (frame && frame.capability) || {};
    LAYER_DEFS.forEach(function (def) {
      var available = !def.cap || !!cap[def.cap];
      var row = el("div", "row" + (available ? "" : " disabled"));
      var label = el("label", "check");
      var input = el("input");
      input.type = "checkbox";
      input.checked = !!state.layers[def.id] && available;
      input.disabled = !available;
      input.addEventListener("change", function () {
        state.layers[def.id] = input.checked;
        render();
      });
      label.appendChild(input);
      label.appendChild(el("span", null, def.label));
      row.appendChild(label);
      if (!available) {
        row.appendChild(el("span", "why", "not recorded"));
      }
      box.appendChild(row);
    });
  }

  function renderIdentity(frame) {
    var box = $("identity");
    box.textContent = "";
    var id = (frame && frame.identity) || {};
    var prov = (frame && frame.provenance) || {};
    var pairs = [
      ["run", id.run_id],
      ["route", prov.route],
      ["environment", prov.environment_id],
      ["policy", prov.policy_kind],
      ["episode", id.episode_id],
      ["lane", id.lane_id],
      ["world", id.world_id],
      ["source", prov.source_kind]
    ];
    pairs.forEach(function (pair) {
      var wrap = el("div");
      wrap.appendChild(el("dt", null, pair[0]));
      var text = pair[1] === null || pair[1] === undefined ? "—" : String(pair[1]);
      var dd = el("dd", null, text);
      // The cell may be ellipsised at narrow widths; the full value stays available on hover
      // and, for the world identity, in the capability panel. Provenance is never truncated
      // in the data, only in this one presentation.
      dd.title = text;
      wrap.appendChild(dd);
      box.appendChild(wrap);
    });
  }

  function renderFooter(frame) {
    var clock = (frame && frame.clock) || {};
    var health = (frame && frame.stream_health) || {};
    $("f-sim").textContent = clock.simulation_time_s === undefined ? "—" : fmt(clock.simulation_time_s, 2) + " s";
    $("f-geom").textContent = clock.geometry_time_s === undefined ? "—" : fmt(clock.geometry_time_s, 2) + " s";
    $("f-window").textContent = (clock.measurement_start_s === null || clock.measurement_start_s === undefined)
      ? "not an interval measurement"
      : fmt(clock.measurement_start_s, 2) + " – " + fmt(clock.measurement_end_s, 2) + " s";
    $("f-age").textContent = state.sampleAge === undefined || state.sampleAge === null
      ? "—" : fmt(state.sampleAge, 1) + " s";
    $("f-resolution").textContent = ((frame && frame.provenance) || {}).capture_resolution || "—";
    $("f-seq").textContent = ((frame && frame.identity) || {}).sequence === undefined
      ? "—" : String(frame.identity.sequence);
    $("f-drops").textContent = health.dropped_display_frames === undefined ? "—" : String(health.dropped_display_frames);
    $("f-gated").textContent = health.refused_by_gate === undefined ? "—" : String(health.refused_by_gate);
    $("f-trace").textContent = health.trace_status || "—";
    $("f-error").textContent = state.lastError || health.last_error || "";
  }

  function setStreamState(value, detail) {
    state.streamState = value;
    state.detail = detail || null;
    var node = $("stream-state");
    node.textContent = value;
    node.className = "state state-" + String(value).toLowerCase();
    node.title = detail || "";
  }

  /* --------------------------------------------------------------- frames */

  function activeFrames() {
    if (state.tab === "replay" || state.tab === "compare") { return state.frames; }
    return state.frames;
  }

  function currentFrame() {
    var frames = activeFrames();
    if (!frames.length) { return null; }
    var i = state.index < 0 || state.index >= frames.length ? frames.length - 1 : state.index;
    return frames[i];
  }

  function pushLiveFrame(frame) {
    var last = state.frames[state.frames.length - 1];
    if (last && (last.identity || {}).sequence === (frame.identity || {}).sequence) { return false; }
    state.frames.push(frame);
    if (state.frames.length > LIVE_BUFFER) { state.frames.shift(); }
    if (state.followLatest && !state.frozen) { state.index = state.frames.length - 1; }
    return true;
  }

  /* --------------------------------------------------------------- render */

  var renderQueued = false;
  function render() {
    if (renderQueued) { return; }
    renderQueued = true;
    requestAnimationFrame(function () {
      renderQueued = false;
      doRender();
    });
  }

  function doRender() {
    var frame = currentFrame();
    var compare = state.tab === "compare";
    $("scene2d-right").hidden = !(compare && state.view === "2d");
    $("scene2d").hidden = state.view !== "2d";
    $("scene3d").hidden = state.view !== "3d";
    $("playback-group").hidden = !(state.tab === "replay" || state.tab === "compare");
    $("live-group").hidden = state.tab !== "live";

    var empty = $("scene-empty");
    if (!frame) {
      empty.classList.add("show");
      empty.textContent = "";
      empty.appendChild(el("div", null, state.detail || "No frame to display yet."));
      if (state.tab === "live" && !META.live_available) {
        empty.appendChild(el("div", "note",
          "This viewer was started without a stream directory, so there is nothing to attach "
          + "to. An already running uninstrumented process cannot be inspected retroactively: "
          + "no debugger is attached and nothing is restarted. Instrument its next authorized "
          + "execution with:"));
        empty.appendChild(el("code", null,
          "python -m tools.research_support demo --route service-restoration "
          + "--config configs/uav_service_restoration/smoke_fixture.json "
          + "--controller backhaul_aware_greedy --seed 17 --live"));
      }
    } else {
      empty.classList.remove("show");
    }

    renderIdentity(frame);
    renderLayers(frame);
    renderCapability(frame);
    renderEntityTable(frame);
    renderInspector(state.hover || state.selection);
    renderFooter(frame);
    renderSceneLegend(frame);

    if (state.view === "2d") {
      draw2d($("scene2d"), frame, { trailFrames: activeFrames() });
      if (compare) {
        var rightFrame = state.right.frames.length
          ? state.right.frames[Math.min(state.right.index < 0 ? state.right.frames.length - 1 : state.right.index,
            state.right.frames.length - 1)]
          : null;
        draw2d($("scene2d-right"), rightFrame, { trailFrames: state.right.frames });
      }
    } else {
      draw3d($("scene3d"), frame);
    }

    var frames = activeFrames();
    var service = seriesFromFrames(frames, ["offered_mbit_interval", "delivered_mbit_interval", "unmet_mbit_interval"]);
    drawLineChart($("chart-service"), service, {
      title: "service per interval (Mbit) - raw recorded values, no smoothing",
      missing: "offered/delivered/unmet interval totals"
    });
    var util = {};
    var lastFrame = frame;
    if (lastFrame) {
      (lastFrame.resource_domains || []).forEach(function (d) {
        util["domain " + d.domain_id] = frames.map(function (f) {
          var found = (f.resource_domains || []).find(function (x) { return x.domain_id === d.domain_id; });
          return { t: (f.clock || {}).simulation_time_s, v: found ? mval(found.utilization) : null };
        });
      });
    }
    if (!Object.keys(util).length) {
      util["backhaul_route_edges_without_sinr_adjacency"] =
        seriesFromFrames(frames, ["backhaul_route_edges_without_sinr_adjacency"]).backhaul_route_edges_without_sinr_adjacency;
      util.ues_associated = seriesFromFrames(frames, ["ues_associated"]).ues_associated;
    }
    drawLineChart($("chart-util"), util, {
      title: "shared-resource utilization / topology diagnostics",
      missing: "resource-domain utilization"
    });
    drawTimeline($("timeline"), frames);

    var total = state.tab === "replay" || state.tab === "compare" ? state.replay.total : frames.length;
    var scrubber = $("scrubber");
    scrubber.max = String(Math.max(0, total - 1));
    scrubber.value = String(state.index < 0 ? Math.max(0, total - 1) : state.index);
    $("scrubber-label").textContent = total
      ? (Number(scrubber.value) + 1) + " / " + total
      : "—";
    $("scrubber-note").textContent = state.tab === "live"
      ? "live buffer; the simulation continues while you scrub"
      : (state.replay.frameIndexPacing ? "frame-index pacing" : "honouring recorded simulated intervals");
  }

  /* ------------------------------------------------------------- polling */

  function pollLive() {
    if (STANDALONE || state.tab !== "live") { return; }
    api("frame").then(function (payload) {
      state.lastError = null;
      state.sampleAge = payload.sample_age_s;
      if (payload.frame) {
        var changed = pushLiveFrame(payload.frame);
        var health = payload.frame.stream_health || {};
        setStreamState(state.frozen ? "LIVE" : (health.state || payload.state), payload.detail);
        if (changed || state.frozen) { render(); } else { renderFooter(currentFrame()); }
      } else {
        setStreamState(payload.state, payload.detail);
        render();
      }
      return api("health");
    }).then(function (health) {
      state.health = health;
      if (health && health.stream_health && !state.frozen) {
        var s = health.stream_health.state;
        if (s && s !== "LIVE") { setStreamState(s, state.detail); }
      }
    }).catch(function (error) {
      state.lastError = String(error.message || error);
      setStreamState("ERROR", state.lastError);
      render();
    });
  }

  /* ------------------------------------------------------------- replay */

  function loadTrace(label, side) {
    return api("trace/index", { label: label }).then(function (index) {
      if (side === "right") {
        state.right.label = label;
      } else {
        state.replay.label = label;
        state.replay.total = index.n_frames;
        state.replay.status = index.status;
        state.replay.problems = index.problems || [];
      }
      if (index.status !== "closed") {
        setStreamState(index.status === "incomplete" ? "INCOMPLETE_TRACE" : "ENDED",
          (index.problems || []).join("; ") || "trace status " + index.status);
      } else {
        setStreamState("ENDED", "recorded trace, complete");
      }
      return api("trace/frames", { label: label, start: 0, count: Math.min(index.n_frames, 400) });
    }).then(function (window_) {
      if (side === "right") {
        state.right.frames = window_.frames;
        state.right.index = window_.frames.length - 1;
        // Align immediately. Landing on the right trace's last frame while the left sits at
        // its first put two unrelated simulated times side by side under a banner that says
        // the panes are synchronised.
        syncRightByAlignment();
      } else {
        state.frames = window_.frames;
        state.index = 0;
        state.replay.total = window_.total;
      }
      render();
    }).catch(function (error) {
      state.lastError = String(error.message || error);
      setStreamState("ERROR", state.lastError);
      render();
    });
  }

  var playTimer = null;
  function stopPlayback() {
    if (playTimer) { clearTimeout(playTimer); playTimer = null; }
    state.replay.playing = false;
    $("pb-play").textContent = "▶";
  }
  function stepPlayback() {
    var frames = activeFrames();
    if (!frames.length) { stopPlayback(); return; }
    if (state.index >= frames.length - 1) { stopPlayback(); return; }
    var from = frames[state.index];
    state.index += 1;
    syncRightByAlignment();
    render();
    var to = frames[state.index];
    var dt = 250;
    if (!state.replay.frameIndexPacing) {
      var a = (from.clock || {}).simulation_time_s, b = (to.clock || {}).simulation_time_s;
      if (typeof a === "number" && typeof b === "number" && b > a) {
        dt = Math.max(30, Math.min(4000, (b - a) * 1000));
      }
    }
    playTimer = setTimeout(stepPlayback, dt / Math.max(0.05, state.replay.speed));
  }

  /* Align the right trace to the left by simulated time, never by wall-clock progress and
   * never beyond the shorter trace's recorded coverage. */
  function syncRightByAlignment() {
    if (state.tab !== "compare" || !state.right.frames.length) { return; }
    var left = currentFrame();
    if (!left) { return; }
    var target = (left.clock || {}).simulation_time_s;
    if (typeof target !== "number") { return; }
    var best = -1, bestDelta = Infinity;
    state.right.frames.forEach(function (f, i) {
      var t = (f.clock || {}).simulation_time_s;
      if (typeof t !== "number") { return; }
      var d = Math.abs(t - target);
      if (d < bestDelta) { bestDelta = d; best = i; }
    });
    state.right.index = best;
    var note = $("scrubber-note");
    var rightLast = state.right.frames[state.right.frames.length - 1];
    var rightMax = rightLast ? (rightLast.clock || {}).simulation_time_s : null;
    if (typeof rightMax === "number" && target > rightMax) {
      note.textContent = "right trace ends at " + fmt(rightMax, 1)
        + " s; no frame is invented beyond its recorded coverage";
    }
  }

  /* ----------------------------------------------------------- interaction */

  function hitTest(canvas, frame, clientX, clientY) {
    if (!frame) { return null; }
    var rect = canvas.getBoundingClientRect();
    var px = clientX - rect.left, py = clientY - rect.top;
    if (state.view === "3d") {
      if (!state.cam3d) { return null; }
      var best = null, bestD = 16;
      entityIndex(frame).forEach(function (hit, key) {
        var p = hit.item.position_m;
        var q = state.cam3d.project([p[0], p[1], p[2] || 0], rect.width, rect.height);
        if (!q.visible) { return; }
        var d = Math.hypot(q.x - px, q.y - py);
        if (d < bestD) { bestD = d; best = key; }
      });
      return best;
    }
    var tr = makeTransform(frame, rect.width, rect.height);
    var bestKey = null, bestDist = 14;
    entityIndex(frame).forEach(function (hit, key) {
      var q = tr.toPx(hit.item.position_m[0], hit.item.position_m[1]);
      var d = Math.hypot(q[0] - px, q[1] - py);
      if (d < bestDist) { bestDist = d; bestKey = key; }
    });
    return bestKey;
  }

  function wireScene(canvas) {
    var dragging = false, last = null, moved = false;
    canvas.addEventListener("mousedown", function (e) {
      dragging = true; moved = false; last = [e.clientX, e.clientY];
    });
    window.addEventListener("mouseup", function () { dragging = false; });
    canvas.addEventListener("mousemove", function (e) {
      if (dragging && last) {
        var dx = e.clientX - last[0], dy = e.clientY - last[1];
        if (Math.abs(dx) + Math.abs(dy) > 2) { moved = true; }
        last = [e.clientX, e.clientY];
        if (state.view === "3d" && state.cam3d) {
          state.cam3d.orbit(dx * 0.008, -dy * 0.006);
        } else {
          // Camera pan only. Environment coordinates are never touched.
          state.cam.x += dx;
          state.cam.y += dy;
        }
        render();
        return;
      }
      var key = hitTest(canvas, currentFrame(), e.clientX, e.clientY);
      var tip = $("tooltip");
      if (key) {
        var hit = entityIndex(currentFrame()).get(key);
        var lines = [key];
        if (hit.item.service_status) { lines.push("status: " + statusStyle(hit.item.service_status).label); }
        var offered = measured(hit.item.offered_mbps);
        if (offered.absent) { lines.push("offered: " + offered.text); } else { lines.push("offered: " + offered.text); }
        lines.push("pos: " + hit.item.position_m.map(function (v) { return fmt(v, 0); }).join(", ") + " m");
        tip.textContent = lines.join("\n");
        var rect = canvas.getBoundingClientRect();
        tip.style.left = (e.clientX - rect.left + 12) + "px";
        tip.style.top = (e.clientY - rect.top + 12) + "px";
        tip.hidden = false;
        if (state.hover !== key) { state.hover = key; renderInspector(key); }
      } else {
        tip.hidden = true;
        if (state.hover) { state.hover = null; renderInspector(state.selection); }
      }
    });
    canvas.addEventListener("mouseleave", function () {
      $("tooltip").hidden = true;
      state.hover = null;
      renderInspector(state.selection);
    });
    canvas.addEventListener("click", function (e) {
      if (moved) { return; }
      var key = hitTest(canvas, currentFrame(), e.clientX, e.clientY);
      state.selection = key;
      render();
    });
    canvas.addEventListener("dblclick", function () {
      if (state.view === "3d" && state.cam3d) { state.cam3d.topDown(); render(); }
    });
    canvas.addEventListener("wheel", function (e) {
      e.preventDefault();
      var factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      if (state.view === "3d" && state.cam3d) { state.cam3d.zoom(1 / factor); }
      else { state.cam.k = Math.max(0.15, Math.min(24, state.cam.k * factor)); }
      render();
    }, { passive: false });
    canvas.addEventListener("keydown", function (e) {
      var step = e.shiftKey ? 40 : 12;
      var handled = true;
      switch (e.key) {
        case "ArrowLeft": state.cam.x += step; break;
        case "ArrowRight": state.cam.x -= step; break;
        case "ArrowUp": state.cam.y += step; break;
        case "ArrowDown": state.cam.y -= step; break;
        case "+": case "=": state.cam.k *= 1.15; break;
        case "-": state.cam.k /= 1.15; break;
        case "0": state.cam = { x: 0, y: 0, k: 1 }; if (state.cam3d) { state.cam3d.reset(); } break;
        case "f": state.frozen = !state.frozen; break;
        default: handled = false;
      }
      if (handled) { e.preventDefault(); render(); }
    });
  }

  /* ------------------------------------------------------------- tabs */

  function setTab(name) {
    state.tab = name;
    stopPlayback();
    // Entering the comparison must not show an unaligned pair even for one frame.
    if (name === "compare") { syncRightByAlignment(); }
    Array.prototype.forEach.call(document.querySelectorAll("#tabs button"), function (b) {
      b.classList.toggle("active", b.dataset.tab === name);
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-panel]"), function (section) {
      section.hidden = section.dataset.panel.split(" ").indexOf(name) < 0;
    });
    if (STANDALONE) {
      // The bundle has one scene panel and no tab strip; the scene stays visible.
      Array.prototype.forEach.call(document.querySelectorAll("[data-panel]"), function (s) {
        s.hidden = false;
      });
    }
    if (name === "live") {
      state.frames = [];
      state.index = -1;
      pollLive();
    } else if (name === "replay") {
      var labels = (META.traces || []).map(function (t) { return t.label; });
      if (labels.length) {
        syncTracePickers(name);
        loadTrace(state.replay.label || labels[0], "left");
      } else {
        state.frames = [];
        setStreamState("DISCONNECTED", "No trace was passed to this viewer. Record one first.");
      }
    } else if (name === "compare") {
      var t = (META.traces || []).map(function (x) { return x.label; });
      if (t.length >= 2) {
        syncTracePickers(name);
        var leftLabel = state.replay.label || t[0];
        var rightLabel = state.right.label && state.right.label !== leftLabel
          ? state.right.label
          : t.find(function (x) { return x !== leftLabel; });
        loadTrace(leftLabel, "left").then(function () { return loadTrace(rightLabel, "right"); })
          .then(compareGuard);
      } else {
        state.frames = [];
        setStreamState("DISCONNECTED",
          "Comparison needs two traces. Start the viewer with --trace A --trace B.");
      }
    } else if (name === "report") { renderReportTab(); }
    else if (name === "runconfig") { renderRunConfigTab(); }
    else if (name === "data") { renderDataTab(); }
    render();
  }

  /* Populate and show the trace pickers for the tab being entered. */
  function syncTracePickers(tab) {
    var labels = (META.traces || []).map(function (t) { return t.label; });
    var group = $("trace-group");
    group.hidden = labels.length < 2;
    if (group.hidden) { return; }
    var left = $("trace-pick");
    var right = $("trace-pick-right");
    var showRight = tab === "compare";
    $("trace-pick-right-label").hidden = !showRight;
    right.hidden = !showRight;
    $("trace-pick-label").textContent = showRight ? "Compare" : "Trace";
    fillOptions(left, labels, state.replay.label || labels[0]);
    if (showRight) {
      var chosen = state.right.label && state.right.label !== left.value
        ? state.right.label
        : labels.find(function (x) { return x !== left.value; });
      fillOptions(right, labels, chosen);
    }
  }

  function fillOptions(select, labels, chosen) {
    select.textContent = "";
    labels.forEach(function (label) {
      var option = document.createElement("option");
      option.value = label;
      option.textContent = label;
      select.appendChild(option);
    });
    if (chosen) { select.value = chosen; }
  }

  /* Refuse to present two traces as the same world unless their world identity matches. */
  function compareGuard() {
    var left = currentFrame();
    var right = state.right.frames[state.right.frames.length - 1];
    var banner = $("banner");
    if (!left || !right) { return; }
    var lw = (left.identity || {}).world_id, rw = (right.identity || {}).world_id;
    if (lw && rw && lw === rw) {
      banner.hidden = false;
      banner.textContent = "Same exogenous world verified (identical world identity). "
        + "Synchronised by simulated time.";
      banner.style.background = "";
    } else {
      banner.hidden = false;
      banner.textContent = "DIFFERENT EXOGENOUS WORLDS: left " + (lw || "unknown")
        + " vs right " + (rw || "unknown")
        + ". Shown side by side as an illustrative display only; this is not a paired "
        + "comparison and no pooled summary is offered.";
    }
  }

  function renderReportTab() {
    var body = $("report-body");
    body.textContent = "";
    var reports = META.reports || [];
    if (!reports.length) {
      body.appendChild(prose([
        ["p", "No report directory was passed to this viewer, so there is nothing to show here "
          + "rather than an empty chart frame."],
        ["h4", "Produce one"],
        ["cmd", "python -m tools.research_support report --spec <comparison.json> "
          + "--charts capability --output <new_report_directory>"],
        ["h4", "Then serve it"],
        ["cmd", "python -m tools.research_support serve --report capability=<new_report_directory>"],
        ["p", "A report command may legitimately answer \"not recorded\" for a panel. That is "
          + "preferable to recording everything continuously in case a chart wants it later."]
      ]));
      return;
    }
    reports.forEach(function (label) {
      var card = el("div");
      card.appendChild(el("h4", null, label));
      // Path-based, so the report's own relative references to figures/ resolve.
      var href = "/report/" + encodeURIComponent(TOKEN) + "/"
        + encodeURIComponent(label) + "/index.html";
      var link = el("a", null, "open in a new tab");
      link.href = href;
      link.target = "_blank";
      link.rel = "noreferrer";
      var list = el("div", "filelist");
      list.appendChild(link);
      card.appendChild(list);
      // Shown inline as well as linked: a report the operator has to leave the viewer to
      // read is a report they will not read while looking at the run it describes. It is a
      // same-origin, read-only document this server already serves.
      var frame = document.createElement("iframe");
      frame.className = "report-frame";
      frame.src = href;
      frame.title = "Capability report: " + label;
      frame.loading = "lazy";
      card.appendChild(frame);
      body.appendChild(card);
    });
  }

  function renderRunConfigTab() {
    var body = $("runconfig-body");
    body.textContent = "";
    var frame = currentFrame();
    if (frame) {
      var prov = frame.provenance || {};
      var table = el("table");
      Object.keys(prov).sort().forEach(function (k) {
        var tr = el("tr");
        tr.appendChild(el("td", null, k));
        tr.appendChild(el("td", null, JSON.stringify(prov[k])));
        table.appendChild(tr);
      });
      var card = el("div", "inspector");
      card.appendChild(el("h4", null, "Provenance of the displayed frame"));
      card.appendChild(table);
      body.appendChild(card);
    }
    body.appendChild(prose([
      ["h4", "Static inspection, then an explicit probe"],
      ["p", "Static inspection reads recorded settings and never imports an environment, loads a "
        + "checkpoint or starts a process. Constructing the environment to report resolved "
        + "values is a separate, explicitly named command."],
      ["cmd", "python -m tools.research_support inspect-run --run <run_root> --output <new_dir>"],
      ["cmd", "python -m tools.research_support inspect-env --route service-restoration "
        + "--config configs/uav_service_restoration/smoke_fixture.json"],
      ["cmd", "python -m tools.research_support inspect-env --route service-restoration "
        + "--config configs/uav_service_restoration/smoke_fixture.json --probe"],
      ["p", "Declared and observed boundary semantics are reported separately. A manifest that "
        + "declares a truncation mode without the runtime resolution flags leaves the executed "
        + "behaviour unverified; that is not the same as correct."]
    ]));
  }

  function renderDataTab() {
    var body = $("data-body");
    body.textContent = "";
    var frame = currentFrame();
    if (frame) {
      var prov = frame.provenance || {};
      body.appendChild(prose([
        ["h4", "Displayed frame's data provenance"],
        ["p", "real activity data: " + (prov.is_real_activity_data ? "yes" : "no")
          + " | dataset hash: " + (prov.dataset_hash || "not recorded")],
        ["p", (frame.capability || {}).has_aggregate_demand
          ? "Ground markers are AGGREGATE DEMAND POINTS: one marker per source grid cell's "
            + "aggregated activity, mapped to a demand proxy. They are not people, not "
            + "subscribers and not measured Mbps."
          : "Ground markers are individual simulated UEs. This route has no traffic-demand "
            + "model, so offered and delivered rates are reported as not applicable."]
      ]));
    }
    body.appendChild(prose([
      ["h4", "Dataset and scenario reports"],
      ["cmd", "python -m tools.research_support dataset-report --dataset <prepared_cache> --output <new_dir>"],
      ["cmd", "python -m tools.research_support scenario-report --config <scenario.json> "
        + "--dataset <prepared_cache> --episodes-file <episodes.json> --output <new_dir>"],
      ["p", "Missing source intervals are reported as missing, never as low demand. Normalization "
        + "is fitted on the training split only. A peak is a peak: no concert, evacuation or "
        + "commute is inferred from one."]
    ]));
  }

  function prose(rows) {
    var box = el("div", "prose");
    rows.forEach(function (row) {
      if (row[0] === "cmd") { box.appendChild(el("code", "cmd", row[1])); }
      else { box.appendChild(el(row[0], null, row[1])); }
    });
    return box;
  }

  /* ------------------------------------------------------------- controls */

  function wireControls() {
    Array.prototype.forEach.call(document.querySelectorAll("#tabs button"), function (b) {
      b.addEventListener("click", function () { setTab(b.dataset.tab); });
    });
    var traces = META.traces || [];
    if (!META.live_available) { document.querySelector('#tabs button[data-tab="live"]').title =
      "No stream directory was passed; live attach is unavailable."; }
    if (!traces.length) { document.querySelector('#tabs button[data-tab="replay"]').disabled = true; }
    if (traces.length < 2) { document.querySelector('#tabs button[data-tab="compare"]').disabled = true; }

    $("view-mode").addEventListener("change", function (e) {
      state.view = e.target.value;
      render();
    });
    $("info-view").addEventListener("change", function (e) {
      state.infoView = e.target.value;
      render();
    });
    $("freeze").addEventListener("click", function () {
      state.frozen = true;
      $("freeze").classList.add("on");
      $("resume").classList.remove("on");
      render();
    });
    $("resume").addEventListener("click", function () {
      state.frozen = false;
      state.followLatest = true;
      $("follow-latest").checked = true;
      $("freeze").classList.remove("on");
      state.index = state.frames.length - 1;
      render();
    });
    $("follow-latest").addEventListener("change", function (e) {
      state.followLatest = e.target.checked;
      if (state.followLatest) { state.index = state.frames.length - 1; }
      render();
    });
    $("follow-selected").addEventListener("change", function (e) {
      state.followSelected = e.target.checked;
      if (state.followSelected && state.selection) {
        var frame = currentFrame();
        var hit = frame && entityIndex(frame).get(state.selection);
        if (hit) {
          var rect = $("scene2d").getBoundingClientRect();
          var tr = makeTransform(frame, rect.width, rect.height);
          var p = tr.toPx(hit.item.position_m[0], hit.item.position_m[1]);
          state.cam.x += rect.width / 2 - p[0];
          state.cam.y += rect.height / 2 - p[1];
        }
      }
      render();
    });
    $("show-trails").addEventListener("change", function (e) {
      state.showTrails = e.target.checked;
      render();
    });
    $("trail-length").addEventListener("input", function (e) {
      state.trailLength = Number(e.target.value);
      $("trail-length-label").textContent = e.target.value;
      render();
    });
    $("reset-camera").addEventListener("click", function () {
      state.cam = { x: 0, y: 0, k: 1 };
      if (state.cam3d) { state.cam3d.reset(); }
      render();
    });
    $("capture-frame").addEventListener("click", function () {
      var frame = currentFrame();
      if (!frame) { return; }
      // Client-side download only. The server has no write endpoint.
      var blob = new Blob([JSON.stringify(frame, null, 2)], { type: "application/json" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "scene_" + ((frame.identity || {}).sequence || 0) + ".json";
      a.click();
      setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
    });
    $("trace-pick").addEventListener("change", function (e) {
      stopPlayback();
      state.index = 0;
      loadTrace(e.target.value, "left").then(function () {
        if (state.tab !== "compare") { return; }
        syncTracePickers("compare");
        // A new left trace can collide with the right one; move the right pane off it so
        // the comparison never shows one trace against itself.
        var right = $("trace-pick-right").value;
        return loadTrace(right, "right").then(compareGuard);
      });
    });
    $("trace-pick-right").addEventListener("change", function (e) {
      stopPlayback();
      loadTrace(e.target.value, "right").then(compareGuard);
    });
    $("scrubber").addEventListener("input", function (e) {
      stopPlayback();
      state.index = Number(e.target.value);
      state.followLatest = false;
      $("follow-latest").checked = false;
      syncRightByAlignment();
      render();
    });
    $("pb-play").addEventListener("click", function () {
      if (state.replay.playing) { stopPlayback(); }
      else { state.replay.playing = true; $("pb-play").textContent = "❙❙"; stepPlayback(); }
    });
    $("pb-first").addEventListener("click", function () { stopPlayback(); state.index = 0; syncRightByAlignment(); render(); });
    $("pb-last").addEventListener("click", function () { stopPlayback(); state.index = activeFrames().length - 1; syncRightByAlignment(); render(); });
    $("pb-prev").addEventListener("click", function () { stopPlayback(); state.index = Math.max(0, state.index - 1); syncRightByAlignment(); render(); });
    $("pb-next").addEventListener("click", function () { stopPlayback(); state.index = Math.min(activeFrames().length - 1, state.index + 1); syncRightByAlignment(); render(); });
    $("pb-speed").addEventListener("change", function (e) { state.replay.speed = Number(e.target.value); });
    $("pb-frame-index").addEventListener("change", function (e) { state.replay.frameIndexPacing = e.target.checked; render(); });

    $("entity-search").addEventListener("input", function (e) {
      var q = e.target.value.trim().toLowerCase();
      var box = $("search-results");
      box.textContent = "";
      if (!q) { return; }
      var frame = currentFrame();
      if (!frame) { return; }
      var matches = [];
      entityIndex(frame).forEach(function (hit, key) {
        var label = (hit.item.entity.label || "").toLowerCase();
        if (key.toLowerCase().indexOf(q) >= 0 || label.indexOf(q) >= 0) { matches.push(key); }
      });
      matches.slice(0, 40).forEach(function (key) {
        var button = el("button", null, key);
        button.addEventListener("click", function () { state.selection = key; render(); });
        box.appendChild(button);
      });
      if (!matches.length) { box.appendChild(el("span", "note", "no entity matches in this frame")); }
    });

    $("theme-toggle").addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", current);
      render();
    });
    $("contrast-toggle").addEventListener("click", function () {
      var high = document.documentElement.getAttribute("data-contrast") === "high";
      document.documentElement.setAttribute("data-contrast", high ? "normal" : "high");
      render();
    });

    window.addEventListener("resize", render);
  }

  /* ------------------------------------------------------------- start */

  function start() {
    document.documentElement.setAttribute("data-theme",
      window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    $("title-text").textContent = META.title || "HMASD research support";
    if (META.banner) {
      $("banner").hidden = false;
      $("banner").textContent = META.banner;
    }
    wireControls();
    [$("scene2d"), $("scene3d"), $("scene2d-right")].forEach(function (canvas) {
      if (!canvas.__stub) { wireScene(canvas); }
    });
    setTab(META.live_available ? "live" : ((META.traces || []).length ? "replay" : "report"));
    if (!STANDALONE) { setInterval(pollLive, LIVE_POLL_MS); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
}());
