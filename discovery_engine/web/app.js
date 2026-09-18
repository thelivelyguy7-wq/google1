/* Discovery Engine workspace: vanilla JS, no build step.
   Every number shown comes from the discovery bundle or the evidence API;
   the UI never computes a finding the backend did not produce, except simple
   sums/differences that are labelled as such (e.g. "unsuccessful" = sum of outcomes). */
(() => {
  "use strict";

  // ---------------------------------------------------------------- utilities
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const attr = (obj) => esc(JSON.stringify(obj));
  const sum = (a) => a.reduce((x, y) => x + y, 0);

  const state = {
    bundle: null, meta: null, review: null,
    drawer: [], askLog: [], sorts: {},
    reviewTab: "needs",
    explore: { query: "", filters: {}, results: null, loading: false },
  };

  async function api(path, body) {
    const res = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  }

  // ---------------------------------------------------------------- vocabulary
  const SOURCE = { google_play: "Google Play", app_store: "App Store", reddit: "Reddit", google_photos_community: "Photos Community", social_media: "Social media", youtube: "YouTube", forums: "Forums" };
  const OUTCOME = { found: "Found", partially_found: "Partly found", uncertain: "Uncertain", not_found: "Not found", abandoned: "Abandoned", not_stated: "Not stated" };
  const OUTCOME_ORDER = ["found", "partially_found", "uncertain", "not_found", "abandoned", "not_stated"];
  const UNSUCCESSFUL = ["partially_found", "uncertain", "not_found", "abandoned"];
  const QOUT = { found: "Found", too_many_results: "Too many results", wrong_results: "Wrong results", not_found: "Nothing found", unclear: "Unclear" };
  const QOUT_ORDER = ["found", "too_many_results", "wrong_results", "not_found", "unclear"];
  const FAIL = {
    A_memory_expression: ["Can't express the memory", "Remembers it, but can't turn it into search terms"],
    B_system_understanding: ["Search misreads the clue", "Gives a meaningful clue that search doesn't interpret"],
    C_retrieval: ["Photo never surfaces", "The photo exists but doesn't appear in results"],
    D_result_evaluation: ["Can't pick it out", "The photo may be there, but can't be told apart from similar ones"],
    E_refinement: ["Stuck after the first miss", "Doesn't know what to try next"],
    F_data_index_limitation: ["Data missing or unsearchable", "Needed information isn't available or indexed"],
    G_other: ["Other breakdown", "Recurring failure outside A–F"],
    none_observed: ["No breakdown described", ""],
    unclear: ["Breakdown unclear", ""],
  };
  const OPP = {
    context_to_query_translation: "Turning context into search terms",
    approximate_time_anchoring: "Anchoring a rough sense of time",
    multi_clue_combination: "Combining several weak clues",
    candidate_recognition: "Recognising the right photo",
    recovery_after_failed_search: "Recovering after a failed search",
    text_in_image_recall: "Recalling what the text said",
    index_coverage_gaps: "Missing or unsearchable data",
    trust_in_search_completeness: "Trusting \"no results\"",
  };
  const LEVELS = { HIGH: 4, MEDIUM: 3, LOW: 2, DIRECTIONAL: 1 };
  const SIG_KIND = { remembered: "Remembered", forgotten: "Forgotten", query: "Query", failure: "Breakdown", workaround: "Workaround", other: "Behaviour & other" };
  const SUGGESTED = [
    "Show me conversations where users remembered the place but not the date.",
    "Find examples of people trying to retrieve a photo using an event description.",
    "What information do users remember most frequently?",
    "What information do users commonly forget?",
    "Show me retrieval attempts that ended in abandonment.",
    "Compare travel-photo retrieval problems with document retrieval problems.",
    "What workarounds do users use after search failure?",
    "Which retrieval failure points appear most frequently?",
    "Which opportunity areas have evidence across multiple sources?",
    "Show evidence that contradicts the leading opportunity.",
    "Generate interview hypotheses for the leading opportunity.",
  ];

  const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);
  function nice(label) {
    if (label == null || label === "") return "—";
    const s = String(label);
    if (FAIL[s]) return FAIL[s][0];
    if (OPP[s]) return OPP[s];
    if (OUTCOME[s]) return OUTCOME[s];
    if (SOURCE[s]) return SOURCE[s];
    const proposed = s.startsWith("proposed:");
    const core = s.replace(/^proposed:/, "").replace(/^remembered_/, "").replace(/_unknown$/, "").replace(/_memory$/, "").replace(/_/g, " ");
    return (proposed ? "Proposed · " : "") + cap(core);
  }
  // Backend narrative strings embed raw labels ("F_data_index_limitation") and Python dict reprs.
  // Rewrite only those tokens; the numbers and wording are left untouched.
  function prettyText(s) {
    return String(s ?? "")
      .replace(/\{([^{}]*)\}/g, (m, inner) => {
        const pairs = [...inner.matchAll(/'([a-z_]+)':\s*(\d+)/g)];
        return pairs.length ? pairs.map(([, k, v]) => `${nice(k)} ${v}`).join(" · ") : m;
      })
      .replace(/'([A-Za-z]+_[A-Za-z_]+)'/g, "$1")
      .replace(/\b([A-G]_[a-z_]+|[a-z]+(?:_[a-z]+)+)\b/g, (t, _m, offset, str) => {
        const n = nice(t);
        const before = str.slice(0, offset).trimEnd();
        const sentenceStart = !before || /[:.(]$/.test(before);
        return sentenceStart || FAIL[t] || OPP[t] ? n : n[0].toLowerCase() + n.slice(1);
      });
  }
  const pct = (r) => (r && r.pct != null ? `${r.pct}%` : "—");
  const frac = (r) => (r ? `${r.numerator}/${r.denominator}` : "—");
  const dirMark = (r) => (r && r.directional ? `<span class="dir" aria-label="directional">†</span>` : "");
  function rateTip(name, r, extra = "") {
    if (!r) return "";
    return `<b>${esc(name)}</b><br>${r.numerator} of ${r.denominator} records (${pct(r)})<br><span class="tt-sub">Denominator: ${esc(r.denominator_definition || "")}</span>` +
      (r.directional ? `<br><span class="tt-sub">† Small sample: directional only</span>` : "") + extra;
  }

  // ---------------------------------------------------------------- icons
  const I = {
    overview: '<path d="M4 13h6V4H4zM14 20h6v-9h-6zM4 20h6v-4H4zM14 4v4h6V4z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    journey: '<path d="M4 17c3 0 3-10 8-10s5 10 8 10" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="4" cy="17" r="2" fill="currentColor"/><circle cx="20" cy="17" r="2" fill="currentColor"/>',
    memory: '<path d="M9 4a4 4 0 0 0-4 4v1a3 3 0 0 0 0 6v1a4 4 0 0 0 7 2.6M15 4a4 4 0 0 1 4 4v1a3 3 0 0 1 0 6v1a4 4 0 0 1-7 2.6V6.5A2.5 2.5 0 0 1 15 4z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    search: '<circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M16 16l4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    scenarios: '<rect x="3.5" y="5" width="17" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="9" cy="10" r="1.8" fill="currentColor"/><path d="M4 17l5-4 4 3 3-2 4 3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    segments: '<circle cx="9" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 19c.8-3.2 3-5 5.5-5s4.7 1.8 5.5 5M16 5.5a3 3 0 0 1 0 5.8M17.5 14c1.6.6 2.6 2.4 3 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    opps: '<path d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.4 6.7 19.4l1.2-6L3.4 9.3l6-.7z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    research: '<path d="M8 4h8l3 3v13H5V4zM9 11h6M9 15h6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    explore: '<path d="M5 18l2-5L18 4l2 2-9 11z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M4 21h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    review: '<path d="M9 12l2 2 4-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 3l7 3v5c0 5-3.2 8.3-7 10-3.8-1.7-7-5-7-10V6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    info: '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 11v5M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    back: '<path d="M19 12H5M11 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    close: '<path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    sun: '<circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>',
    check: '<path d="M5 12l4 4 10-10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    x: '<path d="M7 7l10 10M17 7L7 17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    copy: '<rect x="8" y="8" width="12" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" fill="none" stroke="currentColor" stroke-width="1.8"/>',
    download: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
  };
  const icon = (n, s = 16) => `<svg viewBox="0 0 24 24" width="${s}" height="${s}" aria-hidden="true">${I[n] || ""}</svg>`;

  // ---------------------------------------------------------------- routes
  const NAV = [
    { group: "Understand" },
    { id: "overview", label: "Overview", icon: "overview", title: "Overview" },
    { id: "journey", label: "Retrieval journey", icon: "journey", title: "Retrieval journey" },
    { id: "memory", label: "Memory gap", icon: "memory", title: "Memory gap" },
    { id: "search", label: "Search behaviour", icon: "search", title: "Search behaviour" },
    { id: "scenarios", label: "Scenarios", icon: "scenarios", title: "Scenarios" },
    { group: "Decide" },
    { id: "segments", label: "Segments", icon: "segments", title: "Segments" },
    { id: "opportunities", label: "Opportunities", icon: "opps", title: "Opportunities", count: () => state.bundle?.opportunities.length },
    { group: "Hand off" },
    { id: "research", label: "Research plan", icon: "research", title: "Research plan" },
    { group: "Investigate" },
    { id: "explore", label: "Ask & explore", icon: "explore", title: "Ask & explore" },
    { id: "review", label: "Review queue", icon: "review", title: "Review queue", count: () => state.review?.needs_review_total },
  ];

  function parseRoute() {
    const h = location.hash.replace(/^#\/?/, "");
    const [path, query = ""] = h.split("?");
    const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
    return { view: parts[0] || "overview", id: parts[1], params: new URLSearchParams(query) };
  }
  const go = (hash) => { if (location.hash !== hash) location.hash = hash; else render(); };

  // ---------------------------------------------------------------- components
  function card(title, body, { sub = "", actions = "", cls = "" } = {}) {
    return `<section class="card ${cls}">${title ? `<div class="card-head"><div><h2>${title}</h2>${sub ? `<div class="card-sub">${sub}</div>` : ""}</div>${actions}</div>` : ""}${body}</section>`;
  }
  const kpi = (v, l, d = "", tip = "") => `<div class="card kpi" ${tip ? `data-tip="${esc(tip)}"` : ""}><div class="v">${v}</div><div class="l">${l}</div>${d ? `<div class="d">${d}</div>` : ""}</div>`;
  const drillAttr = (title, filters, query = "") => `data-drill="${attr({ title, filters, query })}"`;

  // scale: "count" when every row shares one denominator; "pct" when denominators differ, so bar length
  // matches the percentage printed beside it (e.g. find rates across categories of different sizes).
  function bars(rows, { name = (r) => nice(r.label), drill = null, limit = 12, cls = "", scale = "count" } = {}) {
    rows = rows.slice(0, limit);
    if (!rows.length) return empty("Nothing extracted for this yet.");
    const val = (r) => (scale === "pct" ? r.pct || 0 : r.numerator || 0);
    const max = scale === "pct" ? 100 : Math.max(1, ...rows.map(val));
    return `<div class="bars">${rows.map((r) => {
      const n = name(r);
      const d = drill ? drill(r) : null;
      return `<button class="bar ${cls}" ${d ? drillAttr(d.title, d.filters) : "tabindex='-1'"} data-tip="${esc(rateTip(n, r, r.source_count != null ? `<br><span class='tt-sub'>${r.source_count} source${r.source_count === 1 ? "" : "s"}</span>` : ""))}" ${d ? "" : "style='cursor:default'"}>
        <span class="name">${esc(n)}</span>
        <span class="track"><span class="fill" style="width:${(100 * val(r)) / max}%"></span></span>
        <span class="val"><b>${pct(r)}</b> <span class="muted">${frac(r)}</span>${dirMark(r)}</span></button>`;
    }).join("")}</div>`;
  }

  function segbar(counts, order, color, name, { tall = false } = {}) {
    const total = sum(order.map((k) => counts[k] || 0)) || 1;
    return `<div class="segbar ${tall ? "tall" : ""}">${order.filter((k) => counts[k]).map((k) =>
      `<span style="width:${(100 * counts[k]) / total}%;background:${color(k)}" data-tip="${esc(`<b>${esc(name(k))}</b><br>${counts[k]} of ${total} (${((100 * counts[k]) / total).toFixed(1)}%)`)}"></span>`).join("")}</div>`;
  }
  const legend = (order, color, name) => `<div class="legend">${order.map((k) => `<span><i style="background:${color(k)}"></i>${esc(name(k))}</span>`).join("")}</div>`;
  const outColor = (k) => `var(--s${OUTCOME_ORDER.indexOf(k) + 1})`;
  const qColor = (k) => `var(--s${QOUT_ORDER.indexOf(k) + 1})`;

  function strength(es, { compact = false } = {}) {
    const lvl = es?.level || es || "DIRECTIONAL";
    const n = LEVELS[lvl] || 1;
    const tip = es?.checks ? `<b>Evidence strength: ${lvl}</b><br>${es.checks.map(esc).join("<br>")}${(es.caveats || []).map((c) => `<br><span class='tt-sub'>${esc(c)}</span>`).join("")}` : `<b>Evidence strength: ${lvl}</b>`;
    return `<span class="strength" data-tip="${esc(tip)}"><span class="meter4">${[1, 2, 3, 4].map((i) => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</span>${compact ? "" : esc(lvl[0] + lvl.slice(1).toLowerCase())}</span>`;
  }

  function heatmap(ct, { rowName = nice, colName = nice, drill }) {
    const cols = ct.cols;
    const max = Math.max(1, ...ct.rows.flatMap((r) => cols.map((c) => ct.cells[r]?.[c] || 0)));
    const shade = (v) => { const t = v / max; return t > .8 ? "var(--seq-5)" : t > .55 ? "var(--seq-4)" : t > .3 ? "var(--seq-3)" : t > .12 ? "var(--seq-2)" : "var(--seq-1)"; };
    const ink = (v) => (v / max > .55 ? "#fff" : "var(--text-primary)");
    return `<div class="table-wrap"><table class="heat"><thead><tr><th></th>${cols.map((c) => `<th><div>${esc(colName(c))}</div></th>`).join("")}</tr></thead><tbody>
      ${ct.rows.map((r) => `<tr><th>${esc(rowName(r))}</th>${cols.map((c) => {
        const v = ct.cells[r]?.[c] || 0;
        if (!v) return `<td class="zero">0</td>`;
        const d = drill(r, c);
        return `<td style="background:${shade(v)};color:${ink(v)}" ${drillAttr(d.title, d.filters)} data-tip="${esc(`<b>${esc(rowName(r))} × ${esc(colName(c))}</b><br>${v} ${esc(ct.unit)}<br><span class='tt-sub'>Click to read the evidence</span>`)}">${v}</td>`;
      }).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  const sourceChip = (s) => `<span class="chip">${esc(SOURCE[s] || s)}</span>`;
  const empty = (msg) => `<div class="empty">${icon("info", 22)}<div>${esc(msg)}</div></div>`;

  function quote(e, { label = true } = {}) {
    if (!e) return "";
    return `<div class="quote clickable" data-rec="${esc(e.record_id)}" role="button" tabindex="0">
      <div class="q">“${esc((e.quote || "").trim())}”</div>
      <div class="meta">${sourceChip(e.source)}${label && e.label ? `<span>${esc(nice(e.label))}</span>` : ""}${e.evidence_id ? `<span class="num">${esc(e.evidence_id)}</span>` : ""}<span class="spacer"></span><span class="link">Inspect ${icon("arrow", 12)}</span></div></div>`;
  }
  const quotes = (items, k = 3) => (items && items.length ? `<div class="quotes">${items.slice(0, k).map((e) => quote(e)).join("")}</div>` : empty("No validated quotes for this."));

  // Highlight extracted quotes inside raw text, by signal kind.
  const KIND_GROUP = (k) => (["remembered", "forgotten", "query", "failure", "workaround"].includes(k) ? k : "other");
  const KIND_PRIORITY = { failure: 0, forgotten: 1, remembered: 2, query: 3, workaround: 4, other: 5 };
  function highlight(text, signals) {
    text = text || "";
    const lower = text.toLowerCase();
    const ranges = [];
    for (const s of signals || []) {
      if (!s.quote || s.quote_valid === 0) continue;
      let pos = 0;
      for (const frag of s.quote.split(/\.\.\.|…/).map((f) => f.trim().toLowerCase()).filter((f) => f.length >= 3)) {
        const i = lower.indexOf(frag, pos);
        if (i < 0) break;
        ranges.push({ start: i, end: i + frag.length, group: KIND_GROUP(s.kind), labels: [`${SIG_KIND[KIND_GROUP(s.kind)]}: ${nice(s.label)}`] });
        pos = i + frag.length;
      }
    }
    ranges.sort((a, b) => KIND_PRIORITY[a.group] - KIND_PRIORITY[b.group] || (b.end - b.start) - (a.end - a.start));
    const kept = [];
    for (const r of ranges) {
      const hit = kept.find((k) => r.start < k.end && k.start < r.end);
      if (hit) { if (!hit.labels.includes(r.labels[0])) hit.labels.push(r.labels[0]); continue; }
      kept.push(r);
    }
    kept.sort((a, b) => a.start - b.start);
    let out = "", cur = 0;
    for (const r of kept) {
      out += esc(text.slice(cur, r.start));
      out += `<mark data-k="${r.group}" data-tip="${esc(r.labels.map(esc).join("<br>"))}">${esc(text.slice(r.start, r.end))}</mark>`;
      cur = r.end;
    }
    return out + esc(text.slice(cur));
  }
  const hlLegend = () => `<div class="legend hl-legend">${Object.keys(SIG_KIND).map((k) => `<span><i style="background:var(--${{ remembered: "s1", forgotten: "s2", query: "s3", failure: "s8", workaround: "s7", other: "s4" }[k]})"></i>${SIG_KIND[k]}</span>`).join("")}</div>`;

  function resultCard(r) {
    return `<article class="result" data-rec="${esc(r.record_id)}" tabindex="0" role="button">
      ${r.title ? `<div class="title">${esc(r.title)}</div>` : ""}
      <div class="text">${highlight(r.text, r.signals)}</div>
      <div class="meta">${sourceChip(r.source)}
        ${r.scenario && r.scenario !== "other" ? `<span class="chip">${esc(nice(r.scenario))}</span>` : ""}
        ${r.success_status && r.success_status !== "not_stated" ? `<span class="chip"><span class="dot" style="background:${outColor(r.success_status)}"></span>${esc(nice(r.success_status))}</span>` : ""}
        ${r.failure_stage && !["none_observed", "unclear"].includes(r.failure_stage) ? `<span class="chip">${esc(nice(r.failure_stage))}</span>` : ""}
        ${r.is_synthetic && state.bundle.provenance?.note ? `<span class="chip" data-tip="${esc("This record's text was generated, not collected from a real user.")}">Generated</span>` : ""}
        <span class="spacer"></span><span class="muted small num">${esc(r.date ? r.date.slice(0, 10) : "")}</span></div></article>`;
  }

  function sortableTable(id, rows, cols, { rowAttrs = () => "", defaultSort = null } = {}) {
    const s = state.sorts[id] || defaultSort;
    let data = rows;
    if (s) {
      const col = cols.find((c) => c.key === s.key);
      if (col && col.sort) data = [...rows].sort((a, b) => { const x = col.sort(a), y = col.sort(b); return (x > y ? 1 : x < y ? -1 : 0) * s.dir; });
    }
    return `<div class="table-wrap"><table class="data"><thead><tr>${cols.map((c) =>
      `<th class="${c.sort ? "sortable" : ""} ${c.num ? "n" : ""}" ${c.sort ? `data-sort="${attr({ id, key: c.key })}"` : ""} ${c.tip ? `data-tip="${esc(c.tip)}"` : ""}>${c.h}${s && s.key === c.key ? `<span class="arr">${s.dir < 0 ? "▼" : "▲"}</span>` : ""}</th>`).join("")}</tr></thead>
      <tbody>${data.map((r) => `<tr ${rowAttrs(r)}>${cols.map((c) => `<td class="${c.num ? "n" : ""}">${c.v(r)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }
  const mini = (r, name) => `<div class="mini" data-tip="${esc(rateTip(name, r))}"><span class="num">${pct(r)}${dirMark(r)}</span><span class="t"><span style="width:${r?.pct || 0}%"></span></span></div>`;

  function pageHead(eyebrow, title, lede, actions = "") {
    return `<div class="page-head fade-in"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1>${lede ? `<p class="lede">${lede}</p>` : ""}</div>${actions ? `<div class="row">${actions}</div>` : ""}</div>`;
  }

  function provenanceNotice() {
    const note = state.bundle.provenance?.note;
    if (!note) return "";
    return `<div class="notice warn fade-in" style="margin-bottom:18px">${icon("info", 18)}<div><b>Data provenance.</b> ${esc(note)} The engine processes these records exactly like any other.</div></div>`;
  }

  const oppById = (id) => state.bundle.opportunities.find((o) => o.opportunity === id);
  // "match" covers two failure codes, so drilling it asks for both.
  const FAILURE_OF_STAGE = { express: ["A_memory_expression"], match: ["B_system_understanding", "C_retrieval"],
    recognize: ["D_result_evaluation"], recover: ["E_refinement"], data: ["F_data_index_limitation"], other: ["G_other"] };
  const STAGE_NAME = { recall: "Recall", express: "Express", match: "Match", recognize: "Recognize",
    recover: "Recover", data: "Data & index", other: "Other" };

  // Part 2: the business metric broken into the stage outcomes that make it up.
  function decompositionCard({ compact = false } = {}) {
    const d = state.bundle.decomposition;
    if (!d) return "";
    const rows = d.stages.filter((x) => x.in_journey || x.breaks_here.numerator > 0);
    const max = Math.max(1, ...rows.map((x) => x.max_headroom_pts));
    const body = `<div class="grid g3" style="gap:12px;margin-bottom:16px">
        <div class="card kpi" data-tip="${esc(rateTip("Attempts ending in a confirmed find", d.baseline))}"><div class="v">${pct(d.baseline)}</div><div class="l">Attempts end in a confirmed find</div><div class="d">${frac(d.baseline)} · today's baseline</div></div>
        <div class="card kpi" data-tip="${esc(rateTip("Attempts that did not fully succeed", d.unresolved))}"><div class="v">${pct(d.unresolved)}</div><div class="l">Did not fully succeed</div><div class="d">${frac(d.unresolved)} · the metric's headroom</div></div>
        <div class="card kpi"><div class="v">${esc(STAGE_NAME[d.largest_headroom?.stage] || "—")}</div><div class="l">Largest single stage</div><div class="d">up to ${d.largest_headroom?.max_headroom_pts ?? 0} pts recoverable</div></div>
      </div>
      <div class="stage-chain">${d.stages.filter((x) => x.in_journey).map((x, i) => `<span class="sc" data-tip="${esc(x.condition || "")}"><i>${i + 1}</i>${esc(STAGE_NAME[x.stage])}</span>`).join(`<span class="ar">→</span>`)}<span class="plus">+ ${esc(STAGE_NAME.data)}</span></div>
      <div class="table-wrap"><table class="data decomp"><thead><tr>
        <th>Stage</th><th>Product outcome to influence</th><th class="n">Breaks here</th><th class="n">Still unresolved</th><th>Max headroom <span class="tag hyp">INTERPRETATION</span></th><th>Opportunity areas</th></tr></thead><tbody>
        ${rows.map((x) => `<tr class="clickable" ${drillAttr(`Breaks down at: ${STAGE_NAME[x.stage]}`, { failure_stages: FAILURE_OF_STAGE[x.stage] || [], attempts_only: true })}>
          <td data-tip="${esc(x.condition || "")}"><b class="nowrap">${esc(STAGE_NAME[x.stage])}</b>${x.in_journey ? "" : `<div class="small muted">outside the<br>user's journey</div>`}</td>
          <td><div>${esc(x.product_outcome)}</div><div class="small muted">${esc(x.outcome_detail)}</div>${x.components?.length ? `<div class="row small muted" style="margin-top:6px">${x.components.map((cp) => `<span class="chip">${esc(cp.label)} ${cp.breaks_here.numerator}</span>`).join("")}</div>` : ""}</td>
          <td class="n" data-tip="${esc(rateTip("Attempts that break down here", x.breaks_here))}">${pct(x.breaks_here)} <span class="muted">${frac(x.breaks_here)}</span></td>
          <td class="n" data-tip="${esc(rateTip("Break down here and do not succeed", x.unresolved_here))}">${frac(x.unresolved_here)}</td>
          <td><div class="mini"><span class="num">+${x.max_headroom_pts} pts</span><span class="t"><span style="width:${(100 * x.max_headroom_pts) / max}%"></span></span></div></td>
          <td>${x.opportunities.map(([o, n]) => `<span class="chip">${esc(nice(o))} ${n}</span>`).join("") || "<span class='muted small'>—</span>"}</td></tr>`).join("")}
      </tbody></table></div>
      <div class="notice small" style="margin-top:12px">${icon("info", 16)}<div>${esc(d.headroom_note)}</div></div>
      ${compact ? "" : `<div class="small muted" style="margin-top:8px">${pct(d.no_breakdown_described)} of attempts describe no breakdown at all, and ${pct(d.breakdown_unclear)} are unclear. Rows are clickable: read the attempts behind each stage.</div>`}`;
    return card("From business metric to product outcomes", body,
      { sub: `${esc(d.business_metric)} — ${esc(d.definition)}` });
  }
  const unsuccessfulOf = (outcomes) => sum(UNSUCCESSFUL.map((k) => outcomes?.[k]?.numerator ?? outcomes?.[k] ?? 0));

  // The North Star: the one business outcome this engine exists to move, stated as the very first
  // thing on Overview. Reuses the same decomposition numbers as Opportunities so the two pages can
  // never disagree; this view just leads with them instead of burying them under Decide.
  function northStarCard() {
    const d = state.bundle.decomposition;
    if (!d) return "";
    const stages = d.stages.filter((x) => x.in_journey || x.breaks_here.numerator > 0);
    const chips = stages.map((x) => `<button class="lever-chip" data-nav="#/opportunities" data-tip="${esc(`<b>${esc(STAGE_NAME[x.stage])}</b><br>${esc(x.product_outcome)}`)}">
        <span class="lever-name">${esc(STAGE_NAME[x.stage])}</span>
        <span class="lever-pts">+${x.max_headroom_pts} pts</span>
      </button>`).join("");
    return `<section class="card hero-goal fade-in">
      <div class="row" style="align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:20px">
        <div style="flex:1;min-width:280px">
          <div class="eyebrow">The business goal this engine exists to move</div>
          <p class="hero-goal-statement">${esc(d.business_metric)}</p>
          <p class="small secondary" style="margin:6px 0 0;max-width:620px">${esc(d.definition)}</p>
        </div>
        <div class="hero-goal-stat" data-tip="${esc(rateTip("Attempts ending in a confirmed find", d.baseline))}">
          <div class="v">${pct(d.baseline)}</div>
          <div class="l">succeed today</div>
          <div class="d">${frac(d.baseline)} · current baseline</div>
        </div>
      </div>
      <div class="divider"></div>
      <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:10px;gap:12px">
        <b class="small">Where the other ${pct(d.unresolved)} could still be won, stage by stage</b>
        <button class="btn subtle sm" data-nav="#/opportunities">Full breakdown ${icon("arrow", 13)}</button>
      </div>
      <div class="lever-row">${chips}</div>
    </section>`;
  }

  // ---------------------------------------------------------------- views
  const views = {};

  views.overview = () => {
    const b = state.bundle, o = b.overview;
    const attempts = o.retrieval_attempts.numerator;
    const unsucc = unsuccessfulOf(o.outcomes);
    const failing = b.failures.filter((f) => !["none_observed", "unclear"].includes(f.label));
    const topQ = Object.entries(b.search.query_types)[0];

    const qcard = (q, view, items, extra = "") => `<button class="card interactive" data-nav="#/${view}" style="text-align:left">
      <div class="eyebrow" style="color:var(--text-muted)">${q}</div>
      ${items[0] ? `<div style="font-size:18px;font-weight:600;letter-spacing:-.01em;margin:2px 0 4px">${esc(items[0].name)}</div>
      <div class="small secondary num">${esc(items[0].stat)}</div>` : empty("Not enough evidence")}
      ${items.slice(1).map((i) => `<div class="row small" style="margin-top:8px"><span class="secondary">${esc(i.name)}</span><span class="spacer"></span><span class="muted num">${esc(i.stat)}</span></div>`).join("")}
      ${extra}<div class="row small" style="margin-top:12px;color:var(--accent);font-weight:500">Explore ${icon("arrow", 13)}</div></button>`;
    const st = (r) => `${pct(r)} · ${frac(r)} attempts`;

    const journeyStrip = `<div class="journey">${b.journey.map((j, i) => stageCard(j, i, Math.max(...b.journey.map((x) => x.records_with_difficulty.pct || 0)))).join("")}</div>`;
    const outcomes = Object.fromEntries(Object.entries(o.outcomes).map(([k, v]) => [k, v.numerator]));
    const srcRows = Object.entries(b.scope.sources).map(([k, v]) => ({ label: k, numerator: v, denominator: o.unique_records - 0, pct: +((100 * v) / o.unique_records).toFixed(1), denominator_definition: "unique records" }));

    return `${provenanceNotice()}
      ${pageHead("Discovery overview", "What happens when people try to find a photo they can't precisely describe",
        `${esc(b.scope.label)}. Every number links to the quotes behind it.`)}
      ${northStarCard()}
      <div class="grid g4 fade-in">
        ${kpi(o.unique_records.toLocaleString(), "Unique records", `${o.total_records.toLocaleString()} ingested · ${o.duplicates_excluded} duplicates set aside`,
          `<b>Unique records</b><br>${o.total_records} rows ingested, ${o.duplicates_excluded} duplicates set aside`)}
        ${kpi(pct(o.relevant), "About photo retrieval", `${frac(o.relevant)} unique records`, rateTip("About photo retrieval", o.relevant))}
        ${kpi(attempts.toLocaleString(), "Retrieval attempts", `${pct(o.retrieval_attempts)} of relevant records`, rateTip("Retrieval attempts", o.retrieval_attempts))}
        ${kpi(`${((100 * unsucc) / Math.max(1, attempts)).toFixed(1)}%`, "Attempts that didn't fully succeed", `${unsucc}/${attempts} · not found, abandoned, partly found, uncertain`)}
      </div>
      <h3>Answers to the core discovery questions</h3>
      <div class="grid g3">
        ${qcard("What are users trying to retrieve?", "scenarios", b.scenarios.filter((s) => s.label !== "other").slice(0, 3).map((s) => ({ name: nice(s.label), stat: st(s) })))}
        ${qcard("What do they remember?", "memory", b.memory.slice(0, 3).map((s) => ({ name: nice(s.label), stat: st(s) })))}
        ${qcard("What have they forgotten?", "memory", b.forgotten.slice(0, 3).map((s) => ({ name: nice(s.label), stat: st(s) })))}
        ${qcard("How do they search?", "search", topQ ? [{ name: `${nice(topQ[0])} queries`, stat: `${pct(topQ[1])} of quoted queries` }, { name: "Median query length", stat: `${b.search.median_query_words ?? "—"} words` }, { name: "Tried 2+ queries", stat: st(b.search.multiple_attempts) }] : [])}
        ${qcard("Where does retrieval break down?", "journey", failing.slice(0, 3).map((s) => ({ name: nice(s.label), stat: st(s) })))}
        ${qcard("What do they do instead?", "journey", b.workarounds.slice(0, 3).map((s) => ({ name: nice(s.label), stat: st(s) })))}
      </div>
      <div class="mt-lg">${card("Retrieval journey", journeyStrip, { sub: "Share of attempts showing any difficulty at each stage. An attempt can show difficulty at more than one stage, so these do not sum to 100%. Click a stage for examples.", actions: `<button class="btn subtle sm" data-nav="#/journey">Full journey ${icon("arrow", 13)}</button>` })}</div>
      <div class="grid g2 mt">
        ${card("How attempts ended", segbar(outcomes, OUTCOME_ORDER, outColor, nice, { tall: true }) + legend(OUTCOME_ORDER.filter((k) => outcomes[k]), outColor, nice) +
          `<div class="divider"></div>${bars(OUTCOME_ORDER.filter((k) => o.outcomes[k]).map((k) => ({ ...o.outcomes[k], label: k })), { drill: (r) => ({ title: `Outcome: ${nice(r.label)}`, filters: { success_status: [r.label], attempts_only: true } }) })}`,
          { sub: "Outcome of each first-person retrieval attempt" })}
        ${card("Where the evidence comes from", bars(srcRows, { drill: (r) => ({ title: `Source: ${nice(r.label)}`, filters: { sources: [r.label] } }) }) +
          `<div class="divider"></div><div class="row small muted">${icon("info", 14)} Analyzer: ${Object.entries(b.scope.analyzers).map(([k, v]) => `${esc(k)} (${v} chunks)`).join(", ")} · ${o.quote_validation.quotes_invalid}/${o.quote_validation.quotes_total.toLocaleString()} quotes failed the verbatim check</div>`,
          { sub: "Unique records per source after removing duplicates" })}
      </div>`;
  };

  function stageCard(j, i, maxPct) {
    const r = j.records_with_difficulty;
    const cond = (state.bundle.decomposition?.stages || []).find((x) => x.stage === j.stage)?.condition;
    const tip = (cond ? cond + " " : "") + rateTip(`${STAGE_NAME[j.stage] || cap(j.stage)}: attempts with a difficulty`, r);
    return `<button class="stage ${r.pct && r.pct === maxPct ? "hot" : ""}" data-stage="${i}" data-tip="${esc(tip)}">
      <div class="idx">${String(i + 1).padStart(2, "0")}</div><div class="nm">${esc(STAGE_NAME[j.stage] || j.stage)}</div>
      <div class="pct">${pct(r)}</div><div class="cap num">${frac(r)} attempts</div>
      <div class="meter"><span style="width:${maxPct ? (100 * (r.pct || 0)) / maxPct : 0}%"></span></div></button>`;
  }

  views.journey = () => {
    const b = state.bundle;
    const failing = b.failures.filter((f) => !["none_observed", "unclear"].includes(f.label));
    const none = b.failures.find((f) => f.label === "none_observed");
    return `${provenanceNotice()}
      ${pageHead("Understand", "The retrieval journey", "Recall → Express → Match → Recognize → Recover. Five things that must go right; find where attempts break down, and what people do next.")}
      ${card("Difficulty by stage", `<div class="journey">${b.journey.map((j, i) => stageCard(j, i, Math.max(...b.journey.map((x) => x.records_with_difficulty.pct || 0)))).join("")}</div>`,
        { sub: "Share of attempts showing any difficulty at each stage. An attempt can show difficulty at more than one stage, so these shares overlap and do not sum to 100%. The decomposition on Opportunities counts only the one decisive breakdown per attempt, so its shares are lower. Click a stage to read examples." })}
      <div class="grid g-main mt">
        ${card("Where retrieval breaks down", bars(failing, { drill: (r) => ({ title: `Breakdown: ${nice(r.label)}`, filters: { failure_stages: [r.label], attempts_only: true } }) }) +
          `<div class="divider"></div><div class="grid g2" style="gap:10px">${failing.slice(0, 6).map((f) => `<div class="small"><b>${esc(nice(f.label))}</b><div class="muted">${esc(FAIL[f.label]?.[1] || f.description)}</div></div>`).join("")}</div>` +
          (none ? `<div class="notice small" style="margin-top:14px">${icon("info", 16)}<div>${pct(none)} of attempts (${frac(none)}) describe no breakdown at all.</div></div>` : ""),
          { sub: "Failure taxonomy A–F, share of attempts" })}
        ${card("What people do instead", bars(b.workarounds, { drill: (r) => ({ title: `Workaround: ${nice(r.label)}`, filters: { workarounds: [r.label] } }) }), { sub: "Workarounds mentioned in attempts" })}
      </div>
      <div class="mt">${card("Where each scenario breaks down", heatmap(b.crosstab_scenario_failure, { drill: (r, c) => ({ title: `${nice(r)} · ${nice(c)}`, filters: { scenarios: [r], failure_stages: [c], attempts_only: true } }) }),
        { sub: "Attempt records by scenario and failure stage. Darker means more." })}</div>
      <div class="grid g2 mt">${failing.slice(0, 4).map((f) => card(esc(nice(f.label)), quotes(f.examples, 2), { sub: esc(f.description) })).join("")}</div>`;
  };

  views.memory = () => {
    const b = state.bundle;
    const fgt = b.forgotten;
    const dumb = fgt.map((f) => {
      const a = f.unsuccessful_when_forgotten, n = f.unsuccessful_when_not_forgotten;
      const gap = (a.pct ?? 0) - (n.pct ?? 0);
      return `<div class="row" style="display:grid;grid-template-columns:minmax(120px,1.2fr) 2fr 90px;gap:12px;padding:6px 0;border-bottom:1px solid var(--border)">
        <span class="small">${esc(nice(f.label))}${dirMark(a)}</span>
        <div class="dumbbell"><div class="axis"></div><div class="line" style="left:${Math.min(a.pct ?? 0, n.pct ?? 0)}%;width:${Math.abs(gap)}%"></div>
          <div class="pt" style="left:${n.pct ?? 0}%;background:var(--s1)" data-tip="${esc(rateTip(`Unsuccessful when ${nice(f.label).toLowerCase()} is NOT forgotten`, n))}"></div>
          <div class="pt" style="left:${a.pct ?? 0}%;background:var(--s2)" data-tip="${esc(rateTip(`Unsuccessful when ${nice(f.label).toLowerCase()} is forgotten`, a))}"></div></div>
        <span class="small num" style="text-align:right">${gap >= 0 ? "+" : ""}${gap.toFixed(1)} pts</span></div>`;
    }).join("");
    const precRows = b.memory.filter((m) => (m.precision.exact || 0) + (m.precision.approximate || 0) > 0);
    return `${provenanceNotice()}
      ${pageHead("Understand", "The memory gap", "What people still remember about a photo, what they've lost, and whether the gap goes with failure.")}
      <div class="grid g2">
        ${card(`<span class="dot" style="background:var(--s1)"></span> What users remember`, bars(b.memory, { limit: 15, drill: (r) => ({ title: `Remembered: ${nice(r.label)}`, filters: { remembered: [r.label], attempts_only: true } }) }), { sub: "Share of attempts mentioning each clue" })}
        ${card(`<span class="dot" style="background:var(--s2)"></span> What users have forgotten`, bars(fgt, { limit: 15, drill: (r) => ({ title: `Forgotten: ${nice(r.label)}`, filters: { forgotten: [r.label], attempts_only: true } }) }), { sub: "Share of attempts stating each missing piece" })}
      </div>
      <div class="grid g-main mt">
        ${card("Does forgetting it go with failure?", `<div class="legend" style="margin:0 0 8px"><span><i style="background:var(--s2)"></i>Unsuccessful when forgotten</span><span><i style="background:var(--s1)"></i>Unsuccessful otherwise</span></div>${dumb || empty("No forgotten information extracted.")}
          <div class="notice small" style="margin-top:14px">${icon("info", 16)}<div>These are associations, not causes. ${fgt[0] ? `The text itself links the gap to the failure in ${pct(fgt[0].explicitly_blocks_retrieval)} of "${esc(nice(fgt[0].label).toLowerCase())}" cases.` : ""}</div></div>`,
          { sub: "Unsuccessful-outcome rate with and without each gap (0–100%)" })}
        ${card("Exact or approximate?", precRows.slice(0, 10).map((m) => `<div style="margin-bottom:10px"><div class="row small"><span>${esc(nice(m.label))}</span><span class="spacer"></span><span class="muted num">${m.precision.exact || 0} exact · ${m.precision.approximate || 0} approx.</span></div>
          ${segbar({ exact: m.precision.exact || 0, approximate: m.precision.approximate || 0 }, ["exact", "approximate"], (k) => (k === "exact" ? "var(--seq-4)" : "var(--seq-2)"), cap)}</div>`).join("") +
          legend(["exact", "approximate"], (k) => (k === "exact" ? "var(--seq-4)" : "var(--seq-2)"), cap), { sub: "How precisely each remembered clue is stated" })}
      </div>
      <div class="mt">${card("What each scenario forgets", heatmap(b.crosstab_scenario_forgotten, { drill: (r, c) => ({ title: `${nice(r)} · forgot ${nice(c).toLowerCase()}`, filters: { scenarios: [r], forgotten: [c], attempts_only: true } }) }), { sub: "Attempt records by scenario and forgotten information" })}</div>`;
  };

  views.search = () => {
    const s = state.bundle.search;
    const toRows = (obj) => Object.entries(obj).map(([k, v]) => ({ ...v, label: k }));
    return `${provenanceNotice()}
      ${pageHead("Understand", "How people search with incomplete memory", "The words users type, what those queries are built around, and what comes back.")}
      <div class="grid g4">
        ${kpi(s.queries_extracted.toLocaleString(), "Queries quoted by users")}
        ${kpi(pct(s.attempts_with_quoted_query), "Attempts quoting a query", frac(s.attempts_with_quoted_query), rateTip("Attempts quoting a query", s.attempts_with_quoted_query))}
        ${kpi(pct(s.multiple_attempts), "Tried two or more queries", frac(s.multiple_attempts), rateTip("Tried two or more queries", s.multiple_attempts))}
        ${kpi(s.median_query_words ?? "—", "Median words per query")}
      </div>
      <div class="grid g2 mt">
        ${card("Kind of query", bars(toRows(s.query_types)), { sub: "Share of quoted queries" })}
        ${card("What the query is built around", bars(toRows(s.orientation)), { sub: "Share of queries (one query can have several)" })}
      </div>
      <div class="grid g-main mt">
        ${card("What comes back, by query type", Object.entries(s.outcome_by_query_type).map(([t, o]) => `<div style="margin-bottom:12px"><div class="row small"><b>${esc(nice(t))}</b><span class="spacer"></span><span class="muted num">${sum(Object.values(o))} queries</span></div>${segbar(o, QOUT_ORDER, qColor, (k) => QOUT[k] || nice(k), { tall: true })}</div>`).join("") + legend(QOUT_ORDER, qColor, (k) => QOUT[k]),
          { sub: "Result the user reports after each query" })}
        ${card("Search strategies", bars(s.strategies, { drill: (r) => ({ title: `Strategy: ${nice(r.label)}`, filters: { behaviors: [r.label], attempts_only: true } }) }), { sub: "Share of attempts" })}
      </div>
      <div class="mt">${card("Queries in users' own words", `<div class="grid g2" style="gap:8px">${(s.examples || []).map((e) => quote(e)).join("")}</div>`, { sub: "Verbatim, drawn from different sources" })}</div>`;
  };

  views.scenarios = () => {
    const b = state.bundle;
    const unsucc = (r) => sum(UNSUCCESSFUL.map((k) => r.outcomes[k]?.numerator || 0));
    const table = sortableTable("scenarios", b.scenarios, [
      { key: "label", h: "Scenario", v: (r) => `<b>${esc(nice(r.label))}</b>`, sort: (r) => nice(r.label) },
      { key: "n", h: "Attempts", num: 1, v: (r) => mini(r, `${nice(r.label)} attempts`), sort: (r) => r.numerator },
      { key: "src", h: "Sources", num: 1, v: (r) => r.source_count, sort: (r) => r.source_count },
      { key: "out", h: "How attempts ended", v: (r) => `<div style="min-width:140px">${segbar(Object.fromEntries(Object.entries(r.outcomes).map(([k, v]) => [k, v.numerator])), OUTCOME_ORDER, outColor, nice)}</div>` },
      { key: "u", h: "Unsuccessful", num: 1, tip: "Not found + abandoned + partly found + uncertain, as a share of the scenario's attempts", v: (r) => `${((100 * unsucc(r)) / Math.max(1, r.numerator)).toFixed(0)}% <span class="muted">${unsucc(r)}/${r.numerator}</span>`, sort: (r) => unsucc(r) / Math.max(1, r.numerator) },
      { key: "f", h: "Top breakdown", v: (r) => esc(nice(Object.keys(r.failure_stages).find((k) => !["none_observed", "unclear"].includes(k)))) },
      { key: "fg", h: "Most forgotten", v: (r) => `<span class="small secondary">${r.top_forgotten.slice(0, 2).map(([l]) => esc(nice(l))).join(", ") || "—"}</span>` },
    ], { rowAttrs: (r) => `class="clickable" ${drillAttr(`Scenario: ${nice(r.label)}`, { scenarios: [r.label], attempts_only: true })}`, defaultSort: { key: "n", dir: -1 } });
    return `${provenanceNotice()}
      ${pageHead("Understand", "What people are trying to retrieve", "Scenarios compared on volume, outcomes and where they break down. Sort any column, or click a row to read the attempts.")}
      ${card("", table, { cls: "pad-0" })}${legend(OUTCOME_ORDER, outColor, nice)}
      <div class="grid g2 mt">
        ${card("Scenario × breakdown", heatmap(b.crosstab_scenario_failure, { drill: (r, c) => ({ title: `${nice(r)} · ${nice(c)}`, filters: { scenarios: [r], failure_stages: [c], attempts_only: true } }) }), { sub: "Attempt records" })}
        ${card("Scenario × forgotten information", heatmap(b.crosstab_scenario_forgotten, { drill: (r, c) => ({ title: `${nice(r)} · forgot ${nice(c).toLowerCase()}`, filters: { scenarios: [r], forgotten: [c], attempts_only: true } }) }), { sub: "Attempt records" })}
      </div>`;
  };

  // ---------------------------------------------------------------- Segments: retrieval behaviour
  // Two primary segments (Direct, Contextual). Retrieval state (below) is a separate, five-way lens.
  const SEG_COLOR = { direct: "var(--s1)", contextual: "var(--s2)" };
  const STATE_COLOR = { direct_low_effort: "var(--s1)", candidate_heavy: "var(--s3)", recovery_dependent: "var(--s4)", unresolved: "var(--s2)", unavailable: "var(--border-strong)" };
  const STAGE_LABEL = { recall: "Recall", express: "Express", match: "Match", recognize: "Recognize", recover: "Recover" };
  const segByKey = (k) => (state.bundle.segments || []).find((s) => s.key === k);
  const segDrill = (s, title = s.segment) => drillAttr(title, { segment: s.key, attempts_only: true });

  const OPP_NEXTLEAP_RANK = {
    multi_clue_combination: { rank: 1, label: "#1", badge: "Rank #1 · NextLeap Lead", rationale: "HIGH evidence strength, 269 records (7 sources), 95.5% vague-memory cases, 81.4% failure, 28.3% abandonment. Addresses root cause of intersecting multiple partial clues." },
    recovery_after_failed_search: { rank: 2, label: "#2", badge: "Rank #2 · Severity Lead", rationale: "MEDIUM evidence strength, 466 records (7 sources), 95.1% vague-memory cases, 85.0% failure, 40.1% abandonment. Highest total failure volume." },
    text_in_image_recall: { rank: 3, label: "#3", badge: "Rank #3 · Vague Memory Purity", rationale: "MEDIUM evidence strength, 118 records (7 sources), 96.6% vague-memory cases, 80.5% failure, 19.5% abandonment. High precision text-in-scene recall." },
    candidate_recognition: { rank: 4, label: "#4", badge: "Rank #4 · Recognition Friction", rationale: "MEDIUM evidence strength, 153 records (7 sources), 94.8% vague-memory cases, 88.2% failure, 30.1% abandonment. High friction at candidate evaluation." },
    context_to_query_translation: { rank: 5, label: "#5", badge: "Rank #5 · Mental Model Gap", rationale: "MEDIUM evidence strength, 169 records (7 sources), 95.3% vague-memory cases, 78.7% failure, 17.2% abandonment. Gap between natural memory & system query." },
    trust_in_search_completeness: { rank: 6, label: "#6", badge: "Rank #6 · Search Uncertainty", rationale: "MEDIUM evidence strength, 51 records (7 sources), 94.1% vague-memory cases, 100.0% failure, 49.0% abandonment. Severe trust erosion." },
    index_coverage_gaps: { rank: 7, label: "#7", badge: "Rank #7 · Infrastructure Gap", rationale: "HIGH evidence strength, 228 records (7 sources), 68.9% vague-memory cases, 57.5% failure, 16.7% abandonment. Less specific to vague memory." },
    approximate_time_anchoring: { rank: 8, label: "#8", badge: "Rank #8 · Directional Clue", rationale: "LOW evidence strength, 146 records (7 sources), 100.0% vague-memory cases, 75.3% failure, 19.9% abandonment." },
  };

  views.segments = () => {
    const b = state.bundle, so = b.segment_overview, segs = b.segments || [];
    if (!so) return `${pageHead("Decide", "How people retrieve", "")}${empty("Rebuild to generate the behavioural segments.")}`;
    const chosen = b.target_segment;
    const n = so.attempts;
    const fit = b.research_fit || {};

    const banner = chosen
      ? `<div class="notice" style="margin-bottom:16px">${icon("check", 16)}<div><b>Target segment for interviews:</b> ${esc(chosen)}. The research plan, screener and problem definition use this. <button class="link" data-clear-segment="1">Clear</button></div></div>`
      : b.target_segment_stale
        ? `<div class="notice warn" style="margin-bottom:16px">${icon("info", 16)}<div>Your earlier choice, <b>${esc(b.target_segment_stale)}</b>, is not one of these segments any more, so it has been set aside. Pick a behavioural segment below.</div></div>`
        : `<div class="notice warn" style="margin-bottom:16px">${icon("info", 16)}<div>No target segment chosen yet. The research plan falls back to a mix covering the tested opportunities. Pick one below when you're ready.</div></div>`;

    // 1. Where the attempts sit: one bar across all of them. Binary and exhaustive, so this always sums to 100%.
    const counts = Object.fromEntries(so.partition.map((p) => [p.key, p.rate.numerator]));
    const order = so.partition.map((p) => p.key);
    const nameOf = (k) => so.names[k];
    const partition = card(`Where the ${n} retrieval attempts sit`,
      `${segbar(counts, order, (k) => SEG_COLOR[k], nameOf, { tall: true })}${legend(order.filter((k) => counts[k]), (k) => SEG_COLOR[k], nameOf)}
       <p class="small muted" style="margin:10px 0 0">Direct and Contextual are the whole population: every attempt is one or the other, so the shares add up to 100%. Contextual is the complement of Direct by definition, not a rival category - it is the starting condition for almost every attempt.</p>`,
      { sub: "First-person retrieval attempts, placed by what the person actually did" });

    // 2. One card per segment.
    const segCard = (s) => {
      const f = fit[s.segment];
      const isTarget = s.segment === chosen;
      return `<article class="card seg-card ${isTarget ? "is-target" : ""}" style="--seg:${SEG_COLOR[s.key]}">
        <div class="row" style="margin-bottom:8px">
          <span class="seg-num">${s.number}</span>
          <b class="seg-name" style="font-size:15px">${esc(s.segment)}</b>
        </div>
        <p class="small secondary seg-def">${esc(s.definition)}</p>
        <button class="seg-share" ${segDrill(s)} data-tip="${esc(rateTip("Share of all attempts", s.share_of_attempts))}">
          <span class="v">${pct(s.share_of_attempts)}</span><span class="small muted">${frac(s.share_of_attempts)} attempts</span></button>
        <div class="seg-stats">
          <div data-tip="${esc(rateTip("Found the photo", s.found))}"><span class="muted small">Found</span><b>${pct(s.found)}${dirMark(s.found)}</b></div>
          <div data-tip="${esc(rateTip("Abandonment", s.abandonment_signals))}"><span class="muted small">Gave up</span><b>${pct(s.abandonment_signals)}${dirMark(s.abandonment_signals)}</b></div>
          <div><span class="muted small">Evidence</span>${strength(s.evidence_strength)}</div>
        </div>
        <div class="row small" style="gap:6px;margin:10px 0">${s.journey_stages.map((j) => `<span class="chip">${esc(STAGE_LABEL[j] || j)}</span>`).join("")}</div>
        ${f ? `<div class="small" style="margin-bottom:12px"><span class="chip accent">${esc(f.role.headline)}</span></div>` : ""}
        <div class="row" style="margin-top:auto">
          <button class="btn subtle sm" data-segment="${esc(s.segment)}">Profile ${icon("arrow", 13)}</button><span class="spacer"></span>
          ${isTarget ? `<span class="chip accent">Target</span>` : `<button class="btn ghost sm" data-pick-segment="${esc(s.segment)}" data-tip="Set as the target segment for the interviews">Select</button>`}
        </div></article>`;
    };

    // 3. Side by side, sortable.
    const table = sortableTable("segments", segs, [
      { key: "seg", h: "Segment", v: (r) => `<span class="row" style="gap:8px;flex-wrap:nowrap"><i class="dot" style="background:${SEG_COLOR[r.key]}"></i><b>${esc(r.segment)}</b></span>`, sort: (r) => r.number },
      { key: "share", h: "Share of attempts", num: 1, v: (r) => mini(r.share_of_attempts, "Share of attempts"), sort: (r) => r.share_of_attempts.pct },
      { key: "found", h: "Found", num: 1, v: (r) => mini(r.found, "Found"), sort: (r) => r.found.pct },
      { key: "ab", h: "Gave up", num: 1, v: (r) => mini(r.abandonment_signals, "Abandonment"), sort: (r) => r.abandonment_signals.pct },
      { key: "vag", h: "Vague memory", num: 1, tip: "Attempts that mention both something remembered and something forgotten", v: (r) => mini(r.vague_memory_cases, "Vague-memory cases"), sort: (r) => r.vague_memory_cases.pct },
      { key: "dom", h: "Breaks at", v: (r) => esc(nice(r.dominant_failure_stage || "none_observed")), sort: (r) => r.dominant_failure_stage || "" },
      { key: "src", h: "Sources", num: 1, v: (r) => r.unique_sources, sort: (r) => r.unique_sources },
      { key: "str", h: "Strength", v: (r) => strength(r.evidence_strength), sort: (r) => LEVELS[r.evidence_strength.level] },
      { key: "target", h: "Target", v: (r) => r.segment === chosen ? `<span class="chip accent">Target</span>` : `<button class="btn ghost sm" data-pick-segment="${esc(r.segment)}" data-tip="Set as target segment">Select</button>`, sort: (r) => r.segment === chosen ? 0 : 1 },
    ], { rowAttrs: (r) => `class="clickable" data-segment="${esc(r.segment)}"`, defaultSort: { key: "share", dir: -1 } });

    const shade = (v) => (v >= 80 ? "var(--seq-5)" : v >= 55 ? "var(--seq-4)" : v >= 30 ? "var(--seq-3)" : v >= 10 ? "var(--seq-2)" : "var(--seq-1)");
    const ink = (v) => (v >= 55 ? "#fff" : "var(--text-primary)");

    // 4. Retrieval state: how attempts actually played out (candidate-heavy, recovery-dependent, ...),
    // and which primary segment they came from. Not exclusive: every attempt gets exactly one state.
    const states = b.retrieval_states || [];
    const stateCounts = Object.fromEntries(states.map((s) => [s.key, s.share_of_attempts.numerator]));
    const stateOrder = states.map((s) => s.key);
    const retrievalStates = `${segbar(stateCounts, stateOrder, (k) => STATE_COLOR[k], (k) => states.find((s) => s.key === k).state, { tall: true })}
      ${legend(stateOrder, (k) => STATE_COLOR[k], (k) => states.find((s) => s.key === k).state)}
      <div class="table-wrap mt"><table class="heat"><thead><tr><th>State</th><th>Definition</th><th>Share</th><th>Sources</th><th>Mostly in</th><th>Strength</th></tr></thead><tbody>
      ${states.map((s) => `<tr><th><span class="row" style="gap:8px;flex-wrap:nowrap"><i class="dot" style="background:${STATE_COLOR[s.key]}"></i>${esc(s.state)}</span></th>
        <td class="small secondary">${esc(s.definition)}</td>
        <td>${mini(s.share_of_attempts, "Share of attempts")}</td><td>${s.unique_sources}</td>
        <td class="small">${s.primary_mix.map(([k, n]) => `${esc(so.names[k] || k)} (${n})`).join(", ")}</td>
        <td>${strength(s.evidence_strength)}</td></tr>`).join("")}
      </tbody></table></div>
      <p class="small muted" style="margin:10px 0 0">Assigned by precedence: a data/index limitation is Unavailable; otherwise a crowded result set is Candidate-heavy; otherwise a changed route after a failed first try is Recovery-dependent; a clean find is Direct/low-effort; anything else is Unresolved.</p>`;

    // 5. How attempts are placed.
    const rules = `<div class="stack">${segs.map((s) => `<div style="padding:8px 0;border-bottom:1px solid var(--border)">
        <div class="row" style="gap:8px"><i class="dot" style="background:${SEG_COLOR[s.key]}"></i><b>${esc(s.segment)}</b></div>
        <div class="small secondary" style="margin-top:3px">${esc(s.rule)}</div></div>`).join("")}</div>
      <div class="notice small mt">${icon("info", 15)}<div>${esc(so.note_on_direct)}</div></div>`;

    // 6. Secondary segmentation: memory state, retrieval complexity, retrieval state, each across the two segments.
    const lensKey = state.segLens || "memory_state";
    const L = so.secondary[lensKey];
    const lensTabs = `<div class="tabs" role="tablist">${Object.entries(so.secondary).map(([k, v]) =>
      `<button role="tab" class="${lensKey === k ? "on" : ""}" data-seglens="${k}">${esc(v.name)}</button>`).join("")}</div>`;
    const allRow = Object.fromEntries(L.categories.map((c) => [c.key, c.rate]));
    const lensRows = [...segs.map((s) => ({ key: s.key, label: s.segment, dist: L.by_segment[s.key] })), { key: null, label: "All attempts", dist: allRow }];
    const lensTable = `<div class="table-wrap"><table class="heat cooc lens"><thead><tr><th></th>${L.categories.map((c) =>
      `<th data-tip="${esc(`<b>${esc(c.label)}</b><br>${esc(c.definition)}`)}"><div>${esc(c.label)}</div></th>`).join("")}</tr></thead><tbody>
      ${lensRows.map((r) => `<tr class="${r.key ? "" : "all"}"><th>${esc(r.label)}</th>${L.categories.map((c) => {
        const x = r.dist[c.key]; const v = x?.pct || 0;
        if (!x?.numerator) return `<td class="zero">0</td>`;
        const t = `${r.label}: ${c.label}`;
        return `<td class="clickable" style="background:${shade(v)};color:${ink(v)}" ${drillAttr(t, { ...(r.key ? { segment: r.key } : {}), lens: lensKey, lens_cat: c.key, attempts_only: true })}
          data-tip="${esc(rateTip(t, x) + "<br><span class='tt-sub'>Click to read the attempts</span>")}">${Math.round(v)}%</td>`;
      }).join("")}</tr>`).join("")}</tbody></table></div>
      <p class="small muted" style="margin:10px 0 0">Each row adds up to 100%. Darker means a larger share of that row.</p>`;
    // How each category fares. Retrieval state is itself the outcome, so it shows its size instead.
    const fares = lensKey === "retrieval_state"
      ? bars(L.categories.map((c) => ({ ...c.rate, label: c.key })), { name: (r) => L.categories.find((c) => c.key === r.label).label, limit: 10 })
      : `${bars(L.categories.filter((c) => c.found.denominator).map((c) => ({ ...c.found, label: c.key })), { name: (r) => L.categories.find((c) => c.key === r.label).label, scale: "pct" })}
         <h3>The photo was not there to find</h3>
         ${bars(L.categories.map((c) => ({ ...c.data_missing, label: c.key })), { name: (r) => L.categories.find((c) => c.key === r.label).label, cls: "muted-bar", scale: "pct" })}
         <div class="notice warn small mt">${icon("info", 15)}<div><b>Read as composition, not cause.</b> People who failed write longer posts and list more of what they remember (median 497 characters against 390 for posts that found the photo), so some of any gradient here is how people write. The memory card in the interviews measures this properly.</div></div>`;
    const lenses = card("Secondary segmentation", `${lensTabs}
      <p class="secondary" style="margin:12px 0 4px"><b>${esc(L.question)}</b></p>
      <p class="small muted" style="margin:0 0 14px">${esc(L.rule)}</p>
      ${L.categories.length > 5
        // Many categories: the table needs the full width, and the bars sit underneath.
        ? `${lensTable}<div class="mt-lg" style="max-width:720px"><h3 style="margin-top:0">Share of all attempts</h3>${fares}</div>`
        : `<div class="grid g-main" style="gap:18px">
            <div>${lensTable}</div>
            <div><h3 style="margin-top:0">Found the photo (of attempts that say how they ended)</h3>${fares}</div>
          </div>`}`, { sub: "Direct vs Contextual is the primary cut. Each lens below cuts across it." });

    const im = so.impact_map;
    const impactMap = `<div class="stack">
      <div><b>WHY</b> — ${esc(im.why)}</div>
      <div><b>WHO</b> — ${esc(im.who)}</div>
      <div><b>HOW</b> — ${esc(im.how)}</div>
      <div><b>WHAT</b> — ${esc(im.what_note)}</div>
      </div>
      <div class="notice small mt">${icon("info", 15)}<div><b>Target segment hypothesis (to validate, not a conclusion):</b> ${esc(so.target_segment_hypothesis)}</div></div>`;

    return `${provenanceNotice()}
      ${pageHead("Decide", "How people retrieve", "Direct vs Contextual retrieval. Every attempt is placed in exactly one; retrieval state, memory state and complexity characterize what happens inside each.")}
      ${banner}
      ${partition}
      <div class="grid g4 mt-lg seg-grid">${segs.map(segCard).join("")}</div>
      <div class="mt-lg">${card("Side by side", table, { cls: "pad-0", sub: "Click any column header to re-sort; click a row for the full profile." })}</div>
      <div class="mt-lg">${card("Impact mapping", impactMap, { sub: "WHY -> WHO -> HOW -> WHAT. No solution is chosen until HOW is validated by primary research." })}</div>
      <div class="mt-lg">${card("Retrieval states", retrievalStates, { sub: "How attempts actually played out, and which primary segment they came from. Not exclusive: every attempt gets exactly one state." })}</div>
      <div class="mt-lg">${lenses}</div>
      <div class="mt-lg">${card("How attempts are placed", rules, { sub: "Every rule is applied to the extracted signals; the quotes behind each segment are in its profile" })}</div>`;
  };

  function oppMap(opps) {
    // Numbered bubbles + a ranked side legend: clustered opportunities never produce overlapping labels.
    const W = 640, H = 360, L = 52, R = 20, T = 16, B = 46;
    const ranked = [...opps].sort((a, b) => b.records - a.records);
    const xs = ranked.map((o) => o.unsuccessful.pct || 0), ys = ranked.map((o) => o.abandonment_signals.pct || 0);
    const x0 = Math.max(0, Math.floor((Math.min(...xs) - 6) / 10) * 10), x1 = Math.min(100, Math.ceil((Math.max(...xs) + 3) / 10) * 10);
    const y1 = Math.max(10, Math.ceil((Math.max(...ys) + 5) / 10) * 10);
    const sx = (v) => L + ((v - x0) / Math.max(1, x1 - x0)) * (W - L - R);
    const sy = (v) => H - B - (v / y1) * (H - T - B);
    const maxRec = Math.max(...ranked.map((o) => o.records));
    const rad = (n) => 11 + 11 * Math.sqrt(n / maxRec);
    const fill = { HIGH: "var(--seq-5)", MEDIUM: "var(--seq-4)", LOW: "var(--seq-3)", DIRECTIONAL: "var(--seq-2)" };
    const ink = { HIGH: "var(--surface-1)", MEDIUM: "#fff", LOW: "#fff", DIRECTIONAL: "var(--text-primary)" };
    const pts = ranked.map((o, i) => ({ o, n: i + 1, x: sx(o.unsuccessful.pct || 0), y: sy(o.abandonment_signals.pct || 0), r: rad(o.records) }));
    const ticksX = []; for (let v = x0; v <= x1; v += 10) ticksX.push(v);
    const ticksY = []; for (let v = 0; v <= y1; v += 10) ticksY.push(v);
    const tip = (p) => esc(`<b>${p.n}. ${esc(nice(p.o.opportunity))}</b><br>${p.o.records} records · ${p.o.unique_sources} sources<br>Unsuccessful ${pct(p.o.unsuccessful)} · Abandonment ${pct(p.o.abandonment_signals)}<br>Evidence: ${p.o.evidence_strength.level}`);
    const svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Opportunity map: unsuccessful outcomes against abandonment signals; bubble size shows supporting records">
      ${ticksY.map((v) => `<line x1="${L}" x2="${W - R}" y1="${sy(v)}" y2="${sy(v)}" stroke="var(--border)"/><text x="${L - 8}" y="${sy(v) + 4}" font-size="11" text-anchor="end" fill="var(--text-muted)">${v}%</text>`).join("")}
      ${ticksX.map((v) => `<text x="${sx(v)}" y="${H - B + 18}" font-size="11" text-anchor="middle" fill="var(--text-muted)">${v}%</text>`).join("")}
      <line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" stroke="var(--border-strong)"/>
      <text x="${(L + W - R) / 2}" y="${H - 6}" font-size="12" text-anchor="middle" fill="var(--text-secondary)">Unsuccessful outcomes →</text>
      <text x="13" y="${(T + H - B) / 2}" font-size="12" text-anchor="middle" fill="var(--text-secondary)" transform="rotate(-90 13 ${(T + H - B) / 2})">Abandonment signals →</text>
      ${[...pts].sort((a, b) => b.r - a.r).map((p) => `<g class="map-dot" data-nav="#/opportunities/${encodeURIComponent(p.o.opportunity)}" data-tip="${tip(p)}">
        <circle cx="${p.x}" cy="${p.y}" r="${p.r}" fill="${fill[p.o.evidence_strength.level]}" stroke="var(--surface-1)" stroke-width="2.5"/>
        <text x="${p.x}" y="${p.y + 4}" font-size="11.5" font-weight="700" text-anchor="middle" fill="${ink[p.o.evidence_strength.level]}" style="pointer-events:none">${p.n}</text></g>`).join("")}
    </svg>`;
    const list = `<div class="map-legend">${pts.map((p) => `<button data-nav="#/opportunities/${encodeURIComponent(p.o.opportunity)}" data-tip="${tip(p)}">
      <span class="map-num" style="background:${fill[p.o.evidence_strength.level]};color:${ink[p.o.evidence_strength.level]}">${p.n}</span>
      <span><span style="font-weight:600">${esc(nice(p.o.opportunity))}</span><br><span class="small muted num">${p.o.records} records · ${pct(p.o.unsuccessful)} unsuccessful</span></span>
      ${strength(p.o.evidence_strength, { compact: true })}</button>`).join("")}</div>`;
    return `<div class="map-grid"><div>${svg}<div class="legend">${Object.keys(fill).map((k) => `<span><i style="background:${fill[k]};border-radius:50%"></i>${cap(k.toLowerCase())} evidence</span>`).join("")}<span class="muted">Bubble size = supporting records</span></div></div>${list}</div>`;
  }

  views.opportunities = (id) => {
    if (id) return oppDetail(id);
    const b = state.bundle;
    const refute = (o) => sum(o.contradictions.filter((c) => c.type === "explicit_counter_evidence").map((c) => c.records));
    const targetOpp = b.target_opportunity || b.leading?.leading;

    const banner = b.target_opportunity
      ? `<div class="notice" style="margin-bottom:16px">${icon("check", 16)}<div><b>Target opportunity for discovery focus:</b> ${esc(nice(b.target_opportunity))}. Prioritized for deep primary research hypotheses and problem definition. <button class="link" data-clear-opportunity="1">Clear</button></div></div>`
      : "";

    const oppRankSummary = `<div class="card" style="margin-top:16px;background:var(--surface-1);border-left:4px solid var(--accent)">
      <div class="row" style="gap:8px;margin-bottom:6px"><span class="chip accent" style="font-weight:700">NextLeap PM Framework</span><b>Opportunity Ranking & Prioritization</b></div>
      <p class="secondary small" style="margin:0 0 10px">Ranked across 4 NextLeap criteria: <b>Evidence Strength Gate</b> (HIGH/MEDIUM empirical grounding across 7 independent sources), <b>Strategic Relevance</b> (% vague-memory cases), <b>Customer Severity</b> (failure & abandonment rates), and <b>Volume</b>.</p>
      <div class="row small" style="gap:10px;flex-wrap:wrap">
        <span class="chip accent"><b>Rank #1: Multi-Clue Combination</b> (Lead Focus · HIGH evidence, 269 records)</span>
        <span class="chip"><b>Rank #2: Recovery After Failed Search</b> (MEDIUM evidence, 466 records, 40.1% abandon)</span>
        <span class="chip"><b>Rank #3: Text-In-Image Recall</b> (MEDIUM evidence, 118 records)</span>
        <span class="chip"><b>Rank #4: Candidate Recognition</b> (MEDIUM evidence, 153 records, 88.2% fail)</span>
        <span class="chip"><b>Rank #5: Context To Query Translation</b> (MEDIUM evidence, 169 records)</span>
      </div>
    </div>`;

    const table = sortableTable("opps", b.opportunities, [
      { key: "rank", h: "Rank", num: 1, v: (r) => `<span class="chip ${OPP_NEXTLEAP_RANK[r.opportunity]?.rank === 1 ? "accent" : ""}" style="font-weight:700">#${OPP_NEXTLEAP_RANK[r.opportunity]?.rank || 9}</span>`, sort: (r) => OPP_NEXTLEAP_RANK[r.opportunity]?.rank || 99 },
      { key: "name", h: "Opportunity area", v: (r) => {
          const isTgt = r.opportunity === targetOpp;
          const isRun = !isTgt && r.opportunity === b.leading?.runner_up;
          return `<div><b>${esc(nice(r.opportunity))}</b>${isTgt ? ` <span class="chip accent">Target Lead</span>` : isRun ? ` <span class="chip">Runner-up</span>` : ""}</div><div class="small muted" style="max-width:360px">${esc(r.description)}</div>`;
        }, sort: (r) => nice(r.opportunity) },
      { key: "rec", h: "Records", num: 1, v: (r) => r.records, sort: (r) => r.records },
      { key: "src", h: "Sources", num: 1, v: (r) => r.unique_sources, sort: (r) => r.unique_sources },
      { key: "vag", h: "Vague memory", num: 1, v: (r) => mini(r.vague_memory_cases, "Vague-memory cases"), sort: (r) => r.vague_memory_cases.pct },
      { key: "uns", h: "Unsuccessful", num: 1, v: (r) => mini(r.unsuccessful, "Unsuccessful"), sort: (r) => r.unsuccessful.pct },
      { key: "ab", h: "Abandon", num: 1, v: (r) => mini(r.abandonment_signals, "Abandonment"), sort: (r) => r.abandonment_signals.pct },
      { key: "ref", h: "Refuting", num: 1, tip: "Records whose counter-evidence refutes this opportunity", v: (r) => refute(r), sort: refute },
      { key: "str", h: "Strength", v: (r) => strength(r.evidence_strength), sort: (r) => LEVELS[r.evidence_strength.level] },
      { key: "target", h: "Target", v: (r) => r.opportunity === targetOpp ? `<span class="chip accent">Target</span>` : `<button class="btn ghost sm" data-pick-opportunity="${esc(r.opportunity)}" data-tip="Select as target opportunity">Select</button>`, sort: (r) => r.opportunity === targetOpp ? 0 : 1 },
    ], { rowAttrs: (r) => `class="clickable" data-nav="#/opportunities/${encodeURIComponent(r.opportunity)}"`, defaultSort: { key: "rank", dir: 1 } });
    return `${provenanceNotice()}
      ${pageHead("Decide", "Where the metric is lost, and which problem spaces sit there",
        "First the business metric broken into stage outcomes, then the opportunity areas that sit under each stage. Problem spaces, not features.")}
      ${banner}
      ${decompositionCard()}
      <div class="mt-lg">${card("Opportunity map", oppMap(b.opportunities), { sub: "Severity at a glance. Click a bubble to open its evidence." })}</div>
      ${oppRankSummary}
      <div class="mt">${card("", table, { cls: "pad-0" })}</div>
      ${b.leading ? `<div class="notice small mt">${icon("info", 16)}<div><b>How the lead opportunity is chosen:</b> ${esc(b.leading.rule)}</div></div>` : ""}`;
  };

  function oppDetail(id) {
    const b = state.bundle, o = oppById(id);
    if (!o) return empty("Opportunity not found. It may have changed after a rebuild.");
    const es = o.evidence_strength;
    const tagCls = { OBSERVATION: "obs", INSIGHT: "ins", HYPOTHESIS: "hyp", INTERPRETATION: "int" };
    const chainNames = { symptom: "Symptom", behavior: "Behaviour", barrier: "Barrier", potential_root_cause: "Potential root cause" };
    const hyp = b.hypotheses.find((h) => h.opportunity === id);
    const isTarget = b.target_opportunity === id || (!b.target_opportunity && b.leading?.leading === id);
    const rk = OPP_NEXTLEAP_RANK[id];
    return `${provenanceNotice()}
      <div class="page-head fade-in"><div style="max-width:820px">
        <div class="eyebrow">${rk ? `<span class="chip ${rk.rank === 1 ? "accent" : ""}" style="margin-right:6px">Rank #${rk.rank}</span> ` : ""}Opportunity area${isTarget ? " · Target Lead" : b.leading?.runner_up === id ? " · Runner-up" : ""}${o.proposed ? " · Proposed by analyzer" : ""}</div>
        <h1>${esc(nice(o.opportunity))}</h1><p class="lede">${esc(o.description)}</p>
        <div class="row" style="margin-top:12px">${strength(es)}<span class="chip num">${o.supporting_evidence_count.toLocaleString()} signals</span></div></div>
        <div class="row">
          <button class="btn" ${drillAttr(`All evidence: ${nice(id)}`, { opportunities: [id] })}>Read all ${o.records} records</button>
          ${isTarget ? `<button class="btn accent" data-clear-opportunity="1">✓ Target Lead (Clear)</button>` : `<button class="btn ghost" data-pick-opportunity="${esc(o.opportunity)}">Select as Target Opportunity</button>`}
          ${hyp ? `<button class="btn ghost" data-nav="#/research">Hypothesis</button>` : ""}
        </div></div>
      <div class="grid g3">
        ${kpi(o.records, "Supporting records", `${o.unique_sources} independent sources`)}
        ${kpi(pct(o.vague_memory_cases), "Vague-memory cases", frac(o.vague_memory_cases), rateTip("Vague-memory cases", o.vague_memory_cases, `<br><span class='tt-sub'>${esc(o.strategic_relevance.note)}</span>`))}
        ${kpi(pct(o.unsuccessful), "Unsuccessful", `${frac(o.unsuccessful)} · abandonment ${pct(o.abandonment_signals)}`, rateTip("Unsuccessful", o.unsuccessful))}
      </div>
      <h3 class="mt-lg">Evidence chain</h3>
      <div class="chain">${Object.entries(o.root_cause_chain).map(([k, v]) => `<div class="chain-step"><div class="k"><span>${chainNames[k] || nice(k)}</span><span class="tag ${tagCls[v.level] || ""}">${esc(v.level)}</span></div><p>${esc(prettyText(v.text))}</p>
        ${v.evidence?.length ? `<details><summary class="small link">${v.evidence.length} quote${v.evidence.length > 1 ? "s" : ""}</summary><div class="quotes" style="margin-top:8px">${v.evidence.map((e) => quote(e)).join("")}</div></details>` : ""}</div>`).join("")}</div>
      <div class="grid g-main mt">
        ${card("Insights", o.insights.map((i) => `<div style="padding:10px 0;border-bottom:1px solid var(--border)"><div class="row"><span class="tag ${tagCls[i.level] || ""}">${esc(i.level)}</span><span>${esc(prettyText(i.text))}</span></div>
          ${i.evidence?.length ? `<details style="margin-top:6px"><summary class="small link">Evidence</summary><div class="quotes" style="margin-top:8px">${i.evidence.slice(0, 3).map((e) => quote(e)).join("")}</div></details>` : ""}</div>`).join(""),
          { sub: "Observations are counted; insights combine counts; hypotheses need interviews" })}
        ${card("Why this strength?", `<div style="margin-bottom:10px">${strength(es)}</div><ul class="rules">${es.checks.map((c) => { const pass = c.startsWith("PASS"); return `<li><span style="color:${pass ? "var(--ok-ink)" : "var(--s8)"}">${icon(pass ? "check" : "x", 15)}</span><span class="small">${esc(c.replace(/^(PASS|FAIL) /, ""))}</span></li>`; }).join("")}</ul>
          <div class="small muted" style="margin-top:8px">Contradiction ratio ${es.contradiction_ratio} · first-person share ${es.behavioral_share}</div>
          ${es.caveats.map((c) => `<div class="notice warn small" style="margin-top:10px">${icon("info", 15)}<div>${esc(c)}</div></div>`).join("")}`, { sub: "Explicit rules; the first level whose checks all pass" })}
      </div>
      <div class="grid g2 mt">
        ${card("What challenges this", o.contradictions.length ? o.contradictions.map((c) => `<details style="padding:8px 0;border-bottom:1px solid var(--border)"><summary style="cursor:pointer"><b>${esc(nice(c.type))}</b> <span class="muted num">· ${c.records} records${c.weighted_records != null ? ` (weighted ${c.weighted_records})` : ""}</span></summary><p class="small secondary">${esc(prettyText(c.description))}</p>${c.evidence?.length ? `<div class="quotes">${c.evidence.slice(0, 3).map((e) => quote(e)).join("")}</div>` : ""}</details>`).join("") : empty("No challenging evidence found. Check whether the search was too narrow."),
          { sub: "Counter-evidence searched for automatically" })}
        ${card("Still unknown", `<ul class="plain">${o.unresolved_questions.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>`, { sub: "Carry these into interviews" })}
      </div>
      <div class="grid g2 mt">
        ${card("Scenarios affected", bars(o.scenarios.map(([s, n]) => ({ label: s, numerator: n, denominator: o.records, pct: +((100 * n) / o.records).toFixed(1), denominator_definition: "supporting records" })), { drill: (r) => ({ title: `${nice(id)} · ${nice(r.label)}`, filters: { opportunities: [id], scenarios: [r.label] } }) }))}
        ${card("Sources", bars(Object.entries(o.source_distribution).map(([s, n]) => ({ label: s, numerator: n, denominator: o.records, pct: +((100 * n) / o.records).toFixed(1), denominator_definition: "supporting records" })), { drill: (r) => ({ title: `${nice(id)} · ${nice(r.label)}`, filters: { opportunities: [id], sources: [r.label] } }) }), { sub: `Largest single-source share: ${Math.round((o.max_single_source_share || 0) * 100)}%` })}
      </div>`;
  }

  const LEVEL_CLASS = { OBSERVATION: "obs", INSIGHT: "ins", HYPOTHESIS: "hyp", INTERPRETATION: "int", DRAFT: "hyp", GIVEN: "obs", OPEN: "int" };
  const emptyNote = (msg) => `<div class="notice warn">${icon("info", 18)}<div>${esc(msg)}</div></div>`;
  const levelTag = (l) => `<span class="tag ${LEVEL_CLASS[l] || ""}">${esc(l)}</span>`;
  const ul = (items) => `<ul class="plain">${(items || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;

  // Part 3: how the research will actually be run, and why this method.
  function methodologyBlock(m) {
    if (!m) return emptyNote("No methodology in this bundle. Rebuild to generate it.");
    return `<div class="grid g-main">
      ${card("Method", `<div style="font-size:15px;font-weight:600;margin-bottom:4px">${esc(m.method)}</div>
        ${m.one_line ? `<p class="small secondary" style="margin:0 0 10px">${esc(m.one_line)}</p>` : ""}
        <h3 style="margin-top:0">Why this method</h3>${ul(m.why)}
        ${m.design ? `<h3>What each part of the session buys</h3>${m.design.map((d) => `<div style="padding:8px 0;border-bottom:1px solid var(--border)"><b>${esc(d.element)}</b><div class="small">${esc(d.what)}</div><div class="small muted" style="margin-top:3px"><b>Buys:</b> ${esc(d.buys)}</div></div>`).join("")}` : ""}
        <h3>Participants</h3><p class="small secondary" style="margin:0">${esc(m.participants)}</p>
        <h3>Session plan</h3><ol class="guide">${m.session.map((x) => `<li><span>${esc(x)}</span></li>`).join("")}</ol>`)}
      <div class="stack">
        ${card("What to capture in every episode", ul(m.instrumentation), { sub: "Coded with the same taxonomy as the engine, so interviews and corpus compare directly" })}
        ${card("Analysis plan", ul(m.analysis))}
      </div>
    </div>
    <div class="mt-lg">${m.adapted_for
      ? card(`Adapted for the target segment: ${m.adapted_for}`, researchFitBlock(m.adapted_for, { compact: true }),
          { sub: "Recruiting, observability and privacy change the session. Chosen on the Segments page." })
      : card("Not yet adapted to a segment", `<div class="notice warn">${icon("info", 18)}<div>The session above is the default shape.
          Recruiting, how much of it can be a live task, and whether a screen share is allowed all depend on who you interview.
          Choose a segment and this becomes a specific plan: its own screener, its own session balance, its own privacy rules.</div></div>
          <div class="row mt"><button class="btn" data-nav="#/segments">Choose a target segment ${icon("arrow", 14)}</button></div>`)}</div>
    <div class="grid g3 mt">
      ${card("Alternatives considered", m.alternatives_considered.map((a) => `<div style="padding:6px 0;border-bottom:1px solid var(--border)"><b>${esc(a.method)}</b><div class="small muted">${esc(a.rejected_because)}</div></div>`).join(""), { sub: "Why they were not chosen for this decision" })}
      ${card("Ethics & privacy", ul(m.ethics_and_privacy))}
      ${card("Threats to validity", ul(m.validity_threats), { sub: "And how each is mitigated" })}
    </div>`;
  }

  // Part 4: the problem definition, assembled from evidence and still a draft.
  function problemBlock(pd) {
    if (!pd || !pd.status) return emptyNote("No problem definition yet: no opportunity in this bundle carries enough evidence to draft one. Rebuild after correcting the evidence, or work from the opportunity areas directly.");
    const field = (key, label, extra = "") => {
      const f = pd[key];
      if (!f) return "";
      return `<div class="card" style="margin-bottom:12px">
        <div class="row" style="margin-bottom:6px">${levelTag(f.level)}<b>${label}</b>${f.confirm_in_research ? `<span class="spacer"></span><span class="chip">interviews decide</span>` : ""}</div>
        <div style="font-size:14.5px;line-height:1.6">${esc(f.text)}</div>
        ${f.evidence_basis ? `<div class="small muted mt">${esc(f.evidence_basis)}</div>` : ""}
        ${f.counts ? `<div class="row small" style="margin-top:8px">${f.counts.map(([l, n]) => `<span class="chip">${esc(nice(l))} ${n}</span>`).join("")}</div>` : ""}
        ${extra}
        ${f.confirm_in_research ? `<div class="notice small" style="margin-top:10px">${icon("info", 15)}<div><b>To settle in interviews:</b> ${esc(f.confirm_in_research)}</div></div>` : ""}
        ${f.open_questions ? `<div class="small muted" style="margin-top:8px"><b>Open, and not answerable from public posts:</b>${ul(f.open_questions)}</div>` : ""}
        ${f.evidence?.length ? `<details style="margin-top:8px"><summary class="small link">Evidence (${f.evidence.length})</summary><div class="quotes" style="margin-top:8px">${f.evidence.slice(0, 3).map((e) => quote(e)).join("")}</div></details>` : ""}
      </div>`;
    };
    const chain = `<div class="chain">${pd.evolution.map((e) => `<div class="chain-step"><div class="k"><span>${esc(e.step)}</span>${levelTag(e.level)}</div><p>${esc(e.text)}</p></div>`).join("")}</div>`;
    const o = pd.product_outcome;
    return `<div class="notice warn" style="margin-bottom:16px">${icon("info", 18)}<div>${esc(pd.status)}</div></div>
      <h3>How the thinking evolved</h3>
      <div style="overflow-x:auto"><div class="chain" style="grid-template-columns:repeat(5, minmax(210px, 1fr));min-width:900px">${pd.evolution.map((e) => `<div class="chain-step"><div class="k"><span>${esc(e.step)}</span>${levelTag(e.level)}</div><p>${esc(e.text)}</p></div>`).join("")}</div></div>
      <div class="grid g2 mt-lg">
        <div>
          ${field("target_user_segment", "Target user segment")}
          ${field("retrieval_scenario", "Retrieval scenario")}
          ${field("product_outcome", "Product outcome to influence",
            o && o.max_headroom_pts != null ? `<div class="row small" style="margin-top:8px"><span class="chip">Baseline ${pct(o.baseline)}</span><span class="chip">Up to +${o.max_headroom_pts} pts if this stage stops failing</span></div><div class="small muted" style="margin-top:6px">${esc(o.note || "")}</div>` : "")}
          ${field("root_cause", "Root cause of retrieval failure")}
        </div>
        <div>
          ${field("existing_workarounds", "Existing user workarounds")}
          ${field("user_value", "Why solving it creates user value")}
          ${field("business_rationale", "Why it makes business sense")}
          ${field("competing_explanation", "Competing explanation to rule out")}
        </div>
      </div>
      <div class="card" style="border-color:var(--accent)">
        <div class="row" style="margin-bottom:6px">${levelTag(pd.not_this_problem.level)}<b>What this problem is not</b></div>
        <div style="font-size:14.5px;line-height:1.6">${esc(pd.not_this_problem.text)}</div>
      </div>`;
  }

  views.research = () => {
    const b = state.bundle, rb = b.research_brief || {};
    if (!rb.status) return `${pageHead("Hand off", "Research plan", "")}${empty("No opportunity has enough evidence to plan interviews yet.")}`;
    const lead = b.leading;
    const list = (items) => `<ul class="plain">${(items || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
    const checks = (items) => `<ul class="checks">${(items || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
    const tab = state.researchTab || "plan";
    const tabs = [["plan", "Plan & hypotheses"], ["method", "Method"], ["problem", "Problem definition"]];
    const tabBar = `<div class="tabs" role="tablist" style="margin-bottom:18px">${tabs.map(([k, l]) => `<button role="tab" class="${tab === k ? "on" : ""}" data-researchtab="${k}">${l}</button>`).join("")}</div>`;
    if (tab === "method") {
      return `${provenanceNotice()}${pageHead("Hand off", "How the research will be run", "The method, why it was chosen over the alternatives, and how the sessions are analysed.")}${tabBar}${methodologyBlock(rb.methodology)}`;
    }
    if (tab === "problem") {
      return `${provenanceNotice()}${pageHead("Hand off", "Problem definition", "Assembled from the discovery evidence. Interviews confirm, refine or kill each field.")}${tabBar}${problemBlock(b.problem_definition)}`;
    }
    return `${provenanceNotice()}
      ${pageHead("Hand off", "Research plan for 5–6 interviews", "Hypotheses to test, who to talk to, and what would prove the evidence wrong.",
        `<a class="btn ghost" href="/api/brief.md" target="_blank" rel="noopener">${icon("download", 14)} Brief (.md)</a><a class="btn ghost" href="/api/report.md" target="_blank" rel="noopener">${icon("download", 14)} Full report (.md)</a>`)}
      ${tabBar}
      <div class="notice" style="margin-bottom:16px">${icon("info", 18)}<div><b>Plan only.</b> No interview findings exist yet. Don't fill these sections with assumed results.</div></div>
      <div class="grid g-main">
        ${card("Who to interview", `<div class="row" style="margin-bottom:6px">${rb.target_segment_chosen_by_pm ? `<span class="chip accent">Chosen by you</span>` : `<span class="chip">Suggested mix</span><button class="btn subtle sm" data-nav="#/segments">Choose a segment</button>`}</div>
          <div style="font-size:18px;font-weight:600">${esc(rb.target_segment || "—")}</div><p class="secondary small">${esc(rb.target_segment_rationale)}</p>
          <div class="row">${(rb.retrieval_scenarios || []).map((s) => `<span class="chip">${esc(nice(s))}</span>`).join("")}</div>
          <h3>Screener</h3>${list(rb.screener)}`)}
        ${card("Opportunities under test", `${(rb.top_opportunity_areas || []).filter(Boolean).map((id, i) => { const o = oppById(id); return o ? `<button class="card interactive" style="width:100%;text-align:left;margin-bottom:8px" data-nav="#/opportunities/${encodeURIComponent(id)}"><div class="row"><span class="tag">${i === 0 ? "Lead" : "Runner-up"}</span>${strength(o.evidence_strength, { compact: true })}</div><div style="font-weight:600;margin-top:6px">${esc(nice(id))}</div><div class="small muted">${o.records} records · ${pct(o.unsuccessful)} unsuccessful</div></button>` : ""; }).join("")}
          ${lead ? `<details class="small"><summary class="link">Ranking table</summary><div class="table-wrap" style="margin-top:8px"><table class="data"><thead><tr><th>Opportunity</th><th>Strength</th><th class="n">Vague %</th><th class="n">Unsucc. %</th><th class="n">Sources</th></tr></thead><tbody>${lead.table.map((t) => `<tr><td>${esc(nice(t.opportunity))}</td><td>${esc(t.strength)}</td><td class="n">${t.vague_memory_pct}</td><td class="n">${t.unsuccessful_pct}</td><td class="n">${t.sources}</td></tr>`).join("")}</tbody></table></div></details>` : ""}`)}
      </div>
      <h3 class="mt-lg">Hypotheses</h3>
      <div class="stack">${(rb.hypotheses || []).map((h) => `<article class="hyp fade-in">
        <div class="hyp-head"><div class="row"><span class="tag hyp">Hypothesis</span><span class="chip">${esc(nice(h.opportunity))}</span>${strength(h.evidence_strength)}<span class="spacer"></span><button class="btn subtle sm" data-copy="${attr([h.we_believe, "BECAUSE", ...h.because, "WE EXPECT TO OBSERVE", ...h.we_expect_to_observe, "WE NEED TO VALIDATE", ...h.we_need_to_validate, "WOULD FALSIFY", ...h.falsification_signals].join("\n"))}">${icon("copy", 13)} Copy</button></div>
          <div class="hyp-belief">${esc(h.we_believe)}</div></div>
        <div class="hyp-body">
          <div><h4>Because</h4><ul>${h.because.map((x) => `<li>${esc(prettyText(x))}</li>`).join("")}</ul></div>
          <div><h4>We expect to observe</h4><ul>${h.we_expect_to_observe.map((x) => `<li>${esc(x)}</li>`).join("")}</ul><h4 style="margin-top:12px">We need to validate</h4><ul>${h.we_need_to_validate.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
          <div><h4>Would falsify it</h4><ul>${h.falsification_signals.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
            ${h.evidence?.length ? `<details style="margin-top:10px"><summary class="small link">Evidence (${h.evidence.length})</summary><div class="quotes" style="margin-top:8px">${h.evidence.slice(0, 3).map((e) => quote(e)).join("")}</div></details>` : ""}</div>
        </div></article>`).join("")}</div>
      <h3 class="mt-lg">Jobs to be done</h3>
      <div class="grid g3">${b.jtbd.map((j) => card(`<span class="tag int">Interpretation</span>`, `<p style="margin:0 0 8px;line-height:1.55">${esc(j.jtbd)}</p><div class="small muted">Stated goal in ${j.records_with_stated_goal}/${j.supporting_records} records · ${esc(nice(j.opportunity))}</div>${j.goal_evidence?.length ? `<details style="margin-top:8px"><summary class="small link">Goals in users' words</summary><div class="quotes" style="margin-top:8px">${j.goal_evidence.map((e) => quote(e, { label: false })).join("")}</div></details>` : ""}`)).join("")}</div>
      <div class="grid g-main mt-lg">
        ${card("Interview guide", `<ol class="guide">${(rb.interview_questions || []).map((q) => `<li><span>${esc(q)}</span></li>`).join("")}</ol>`,
          { sub: "Past behaviour only. Leading and solution-naming questions are filtered out.", actions: `<button class="btn ghost sm" data-copy="${attr((rb.interview_questions || []).map((q, i) => `${i + 1}. ${q}`).join("\n"))}">${icon("copy", 13)} Copy</button>` })}
        <div class="stack">
          ${card("Objectives", list(rb.interview_objectives))}
          ${card("Method notes", list(rb.method_notes))}
        </div>
      </div>
      <div class="grid g3 mt">
        ${card("Behaviours to observe", checks(rb.behaviors_to_observe))}
        ${card("Signals that would falsify", checks(rb.falsification_signals))}
        ${card("Unknowns to resolve", checks(rb.unknowns))}
      </div>`;
  };

  views.explore = (_, params) => {
    const q = params?.get("q");
    if (q && !state.askLog.some((e) => e.q === q && e.fresh)) setTimeout(() => runAsk(q), 0);
    const f = state.explore.filters;
    const m = state.meta || {};
    const facet = (key, label, options, name = nice) => `<select class="select" data-facet="${key}" aria-label="${label}"><option value="">${label}</option>${options.map((o) => `<option value="${esc(o)}" ${f[key]?.[0] === o ? "selected" : ""}>${esc(name(o))}</option>`).join("")}</select>`;
    return `${pageHead("Investigate", "Ask the evidence", "Questions are turned into a search plan. Every answer is assembled from stored evidence; nothing is generated.")}
      <section class="ask-hero">
        <form class="ask-box" id="askForm"><input id="askInput" placeholder="e.g. Show me attempts where users remembered the place but not the date" autocomplete="off" aria-label="Question"><button class="btn" type="submit">Ask ${icon("arrow", 14)}</button></form>
        <div class="suggestions">${SUGGESTED.map((s) => `<button data-ask="${esc(s)}">${esc(s)}</button>`).join("")}</div>
      </section>
      <div class="stack mt" id="askLog">${state.askLog.map(renderAnswer).join("")}</div>
      <h3 class="mt-lg">Evidence search</h3>
      <section class="card">
        <form class="row" id="searchForm" style="margin-bottom:10px">
          <input class="input" id="searchInput" style="flex:1;min-width:220px" placeholder="Free text, e.g. wedding outside the venue" value="${esc(state.explore.query)}">
          <button class="btn" type="submit">Search</button>
        </form>
        <div class="row">
          ${facet("scenarios", "Any scenario", m.scenarios || [])}
          ${facet("failure_stages", "Any breakdown", Object.keys(m.failure_stages || {}))}
          ${facet("remembered", "Remembered…", m.memory_signals || [])}
          ${facet("forgotten", "Forgotten…", m.forgotten || [])}
          ${facet("success_status", "Any outcome", m.success_status || [])}
          ${facet("sources", "Any source", m.sources || [])}
          <label class="row small secondary" style="gap:6px"><input type="checkbox" id="attemptsOnly" ${f.attempts_only ? "checked" : ""}> Attempts only</label>
        </div>
        <div id="searchResults" class="mt">${renderSearchResults()}</div>
      </section>`;
  };

  function renderSearchResults() {
    const r = state.explore.results;
    if (state.explore.loading) return `<div class="skeleton" style="height:120px"></div>`;
    if (!r) return `<div class="small muted">Search by text, filters, or both. Results are spread across sources.</div>`;
    if (!r.results.length) return empty("No records match. Try removing a filter.");
    return `<div class="row small muted" style="margin-bottom:10px">${r.total_matches} matching records · showing ${r.results.length} · ${Object.entries(r.source_distribution).map(([s, n]) => `${esc(nice(s))} ${n}`).join(" · ")}</div>${hlLegend()}<div class="stack mt">${r.results.map(resultCard).join("")}</div>`;
  }

  async function runSearch() {
    state.explore.loading = true;
    $("#searchResults") && ($("#searchResults").innerHTML = renderSearchResults());
    try { state.explore.results = await api("/api/search", { query: state.explore.query, filters: state.explore.filters, k: 20 }); }
    catch (e) { toast(`Search failed: ${e.message}`); }
    state.explore.loading = false;
    $("#searchResults") && ($("#searchResults").innerHTML = renderSearchResults());
  }

  async function runAsk(q) {
    q = (q || "").trim();
    if (!q) return;
    const entry = { q, loading: true, fresh: true, id: Date.now() };
    state.askLog.unshift(entry);
    if (parseRoute().view !== "explore") { go("#/explore"); } else { const log = $("#askLog"); if (log) log.innerHTML = state.askLog.map(renderAnswer).join(""); }
    try { entry.result = await api("/api/ask", { question: q }); }
    catch (e) { entry.error = e.message; }
    entry.loading = false;
    const log = $("#askLog");
    if (log) log.innerHTML = state.askLog.map(renderAnswer).join("");
  }

  function renderAnswer(e) {
    let body = "";
    if (e.loading) body = `<div class="skeleton" style="height:90px"></div>`;
    else if (e.error) body = `<div class="notice warn">${icon("info", 16)}<div>${esc(e.error)}</div></div>`;
    else body = answerBody(e.result);
    const p = e.result?.plan;
    const planChips = p ? [
      `<span class="tag">Read as</span><span class="chip accent">${esc(nice(p.intent))}</span>`,
      ...["remembered", "forgotten", "scenarios", "success_status", "failure_stages", "workarounds", "compare_scenarios"].flatMap((k) => (p[k] || []).map((v) => `<span class="chip">${esc(nice(k))}: ${esc(nice(v))}</span>`)),
      p.opportunity ? `<span class="chip">Opportunity: ${esc(nice(p.opportunity))}</span>` : "",
      p.attempts_only ? `<span class="chip">Attempts only</span>` : "",
    ].join("") : "";
    return `<article class="answer fade-in"><div class="answer-q"><span class="who">Q</span><div style="font-weight:600;padding-top:2px">${esc(e.q)}</div></div>
      ${p ? `<div class="answer-plan">${planChips}</div>` : ""}<div class="answer-body">${body}</div></article>`;
  }

  function answerBody(r) {
    if (!r) return "";
    if (r.evidence) return renderEvidenceBlock(r.evidence);
    if (Array.isArray(r.table) && r.table.length && r.table[0].numerator !== undefined) {
      return bars(r.table, { limit: 10 }) + (r.table[0].examples ? `<h3>Examples</h3><div class="grid g2" style="gap:8px">${r.table.slice(0, 4).map((t) => t.examples?.[0] ? quote(t.examples[0]) : "").join("")}</div>` : "");
    }
    if (Array.isArray(r.table)) {
      return r.table.length ? `<div class="stack">${r.table.map((o) => `<button class="card interactive" style="text-align:left" data-nav="#/opportunities/${encodeURIComponent(o.opportunity)}"><div class="row"><b>${esc(nice(o.opportunity))}</b><span class="spacer"></span>${strength(o.evidence_strength)}</div><div class="small muted mt" style="margin-top:6px">${o.records} records from ${o.unique_sources} sources: ${Object.entries(o.source_distribution).map(([s, n]) => `${esc(nice(s))} ${n}`).join(" · ")}</div></button>`).join("")}</div>` : empty("No opportunity has evidence from three or more sources.");
    }
    if (r.table && r.table.query_types) {
      const s = r.table;
      return `<div class="grid g3">${kpi(pct(s.attempts_with_quoted_query), "Attempts quoting a query")}${kpi(s.median_query_words ?? "—", "Median words")}${kpi(pct(s.multiple_attempts), "Tried 2+ queries")}</div><div class="mt">${bars(Object.entries(s.query_types).map(([k, v]) => ({ ...v, label: k })))}</div>`;
    }
    if (r.comparison) {
      const names = Object.keys(r.comparison);
      const rows = [["Attempts", (p) => p.records], ["Sources", (p) => p.unique_sources], ["Vague-memory cases", (p) => `${pct(p.vague_memory_cases)} <span class="muted">${frac(p.vague_memory_cases)}</span>`], ["Unsuccessful", (p) => `${pct(p.unsuccessful)} <span class="muted">${frac(p.unsuccessful)}</span>`], ["Abandonment", (p) => pct(p.abandonment_signals)], ["Dominant breakdown", (p) => esc(nice(p.dominant_failure_stage))], ["Most remembered", (p) => p.top_remembered.slice(0, 3).map(([l, n]) => `${esc(nice(l))} (${n})`).join(", ")], ["Most forgotten", (p) => p.top_forgotten.slice(0, 3).map(([l, n]) => `${esc(nice(l))} (${n})`).join(", ")], ["Workarounds", (p) => p.top_workarounds.slice(0, 3).map(([l, n]) => `${esc(nice(l))} (${n})`).join(", ")]];
      return `${names.length < 2 ? `<div class="notice warn small" style="margin-bottom:10px">${icon("info", 15)}<div>Only one scenario was recognised. Name two to compare, e.g. "travel" and "document".</div></div>` : ""}<div class="table-wrap"><table class="data"><thead><tr><th></th>${names.map((n) => `<th>${esc(nice(n))}</th>`).join("")}</tr></thead><tbody>${rows.map(([l, fn]) => `<tr><td class="muted">${l}</td>${names.map((n) => `<td>${fn(r.comparison[n])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    }
    if (r.contradictions) return `<p class="small secondary" style="margin-top:0">Challenging evidence for <b>${esc(nice(r.opportunity))}</b></p>` + (r.contradictions.length ? r.contradictions.map((c) => `<div style="padding:8px 0;border-bottom:1px solid var(--border)"><b>${esc(nice(c.type))}</b> <span class="muted num">· ${c.records} records</span><p class="small secondary">${esc(c.description)}</p>${c.evidence?.length ? `<div class="quotes">${c.evidence.slice(0, 2).map((x) => quote(x)).join("")}</div>` : ""}</div>`).join("") : empty("No challenging evidence found."));
    if (r.hypotheses) return r.hypotheses.map((h) => `<div class="hyp-belief" style="margin:0 0 10px">${esc(h.we_believe)}</div><div class="grid g2"><div><h3 style="margin-top:0">Because</h3><ul class="plain small">${h.because.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div><div><h3 style="margin-top:0">Expect to observe</h3><ul class="plain small">${h.we_expect_to_observe.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div></div>`).join("") || empty("No hypothesis available.");
    return empty("No matching answer. Try one of the suggested questions.");
  }

  function renderEvidenceBlock(ev) {
    if (!ev.results.length) return empty("No evidence matches this question.");
    return `<div class="row small muted" style="margin-bottom:10px">${ev.total_matches} matching records · showing ${ev.results.length}, spread across sources</div>${hlLegend()}<div class="stack mt">${ev.results.slice(0, 6).map(resultCard).join("")}</div>`;
  }

  views.review = () => {
    const r = state.review;
    if (!r) { loadReview(); return `${pageHead("Investigate", "Review queue", "")}<div class="skeleton" style="height:240px"></div>`; }
    const tabs = [["needs", "Needs review", r.needs_review_total], ["proposed", "Proposed labels", r.proposed_labels.length], ["quotes", "Quote failures", r.invalid_quotes.length], ["log", "Change log", r.overrides.length]];
    let body = "";
    if (state.reviewTab === "needs") {
      body = r.needs_review.length ? `<div class="stack">${r.needs_review.map((n) => `<article class="result" data-rec="${esc(n.record_id)}" tabindex="0" role="button">
        <div class="row" style="margin-bottom:6px">${n.reasons.map((x) => `<span class="chip accent">${esc(cap(x))}</span>`).join("")}${n.has_override ? `<span class="chip">Corrected</span>` : ""}<span class="spacer"></span><span class="small muted num">confidence ${n.confidence ?? "—"}</span></div>
        <div class="text">${esc(n.text)}${n.text.length >= 280 ? "…" : ""}</div>
        <div class="meta">${sourceChip(n.source)}<span class="chip">${esc(nice(n.perspective))}</span><span class="chip">${esc(nice(n.scenario))}</span><span class="chip">${esc(nice(n.failure_stage))}</span></div></article>`).join("")}${r.needs_review_total > r.needs_review.length ? `<p class="small muted">Showing ${r.needs_review.length} of ${r.needs_review_total}.</p>` : ""}</div>` : empty("Nothing needs review.");
    } else if (state.reviewTab === "proposed") {
      body = r.proposed_labels.length ? `<div class="grid g2">${r.proposed_labels.map((p) => card(esc(nice(p.label)), `<div class="quotes">${p.examples.map((e) => quote({ ...e, label: "" }, { label: false })).join("")}</div>`, { sub: `${esc(p.kind)} · ${p.records} records` })).join("")}</div>` : empty("No proposed labels. Every extraction fits the current taxonomy.");
    } else if (state.reviewTab === "quotes") {
      body = r.invalid_quotes.length ? r.invalid_quotes.map((q) => `<div class="sig invalid"><div class="body"><div class="lab">${esc(nice(q.label))} <span class="muted small">· ${esc(q.kind)}</span></div><div class="qt">“${esc(q.quote)}”</div></div><button class="btn subtle sm" data-rec="${esc(q.record_id)}">Inspect</button></div>`).join("") : empty("Every extracted quote was found word for word in its source.");
    } else {
      body = r.overrides.length ? sortableTable("log", r.overrides, [
        { key: "t", h: "When", v: (o) => `<span class="num small">${esc(o.created_at.replace("T", " ").slice(0, 16))}</span>`, sort: (o) => o.created_at },
        { key: "f", h: "Change", v: (o) => `<b>${esc(nice(o.field))}</b> on ${esc(o.target_type)}<div class="small muted num">${esc(o.target_id)}</div>` },
        { key: "o", h: "From → to", v: (o) => `<span class="small">${esc(o.old_value)} → <b>${esc(o.new_value)}</b></span>` },
        { key: "n", h: "Reason", v: (o) => `<span class="small secondary">${esc(o.note || "—")}</span>` },
      ]) : empty("No PM corrections yet. Open any record to challenge the AI.");
    }
    return `${pageHead("Investigate", "Review queue", "Where the AI is least sure, labels that don't fit the taxonomy, and every correction made so far.", `<button class="btn ghost" data-action="reload-review">Refresh</button>`)}
      <div class="tabs" role="tablist" style="margin-bottom:16px">${tabs.map(([k, l, c]) => `<button role="tab" class="${state.reviewTab === k ? "on" : ""}" data-reviewtab="${k}">${l}<span class="c">${c}</span></button>`).join("")}</div>
      ${state.reviewTab === "log" ? card("", body, { cls: "pad-0" }) : body}`;
  };

  async function loadReview() {
    try { state.review = await api("/api/review"); } catch (e) { toast(`Couldn't load review queue: ${e.message}`); return; }
    renderNav();
    if (parseRoute().view === "review") render();
  }

  // ---------------------------------------------------------------- drawer
  const drawer = $("#drawer"), scrim = $("#scrim");
  function openDrawer(entry) { state.drawer.push(entry); paintDrawer(); }
  function closeDrawer() { state.drawer = []; drawer.classList.remove("open"); drawer.setAttribute("aria-hidden", "true"); scrim.hidden = true; }
  async function paintDrawer() {
    const e = state.drawer[state.drawer.length - 1];
    if (!e) return closeDrawer();
    drawer.classList.add("open"); drawer.setAttribute("aria-hidden", "false"); scrim.hidden = false;
    drawer.innerHTML = `<div class="drawer-head">${state.drawer.length > 1 ? `<button class="icon-btn" data-action="drawer-back" aria-label="Back">${icon("back")}</button>` : ""}<div class="t">${esc(e.title)}</div><button class="icon-btn" data-action="drawer-close" aria-label="Close">${icon("close")}</button></div><div class="drawer-body" id="drawerBody"><div class="skeleton" style="height:160px"></div></div>`;
    try { $("#drawerBody").innerHTML = await e.render(); }
    catch (err) { $("#drawerBody").innerHTML = `<div class="notice warn">${icon("info", 16)}<div>${esc(err.message)}</div></div>`; }
    $(".drawer-head .icon-btn:last-child", drawer)?.focus({ preventScroll: true });
  }

  function openEvidence({ title, filters, query = "" }) {
    openDrawer({
      title,
      render: async () => {
        // Segment and lens-category filters are precomputed record sets; send the ids, show one readable chip each.
        const seg = filters.segment ? segByKey(filters.segment) : null;
        const lens = filters.lens ? state.bundle.segment_overview?.secondary?.[filters.lens] : null;
        const cat = lens ? lens.categories.find((c) => c.key === filters.lens_cat) : null;
        const { segment, lens: _l, lens_cat: _c, ...rest } = filters;
        let ids = seg ? seg.record_ids : null;
        if (cat) ids = ids ? cat.record_ids.filter((r) => ids.includes(r)) : cat.record_ids;
        const sent = ids ? { ...rest, record_ids: ids.length ? ids : ["__none__"] } : rest;
        const res = await api("/api/search", { query, filters: sent, k: 30 });
        const chips = [...(seg ? [`<span class="chip">Segment: ${esc(seg.segment)}</span>`] : []),
          ...(cat ? [`<span class="chip">${esc(lens.name)}: ${esc(cat.label)}</span>`] : []),
          ...Object.entries(rest).flatMap(([k, v]) => (Array.isArray(v) ? v.map((x) => `<span class="chip">${esc(nice(k))}: ${esc(nice(x))}</span>`) : v === true ? [`<span class="chip">${esc(nice(k))}</span>`] : []))];
        if (!res.results.length) return `<div class="row">${chips.join("")}</div>${empty("No records match.")}`;
        return `<div class="row" style="margin-bottom:10px">${chips.join("")}</div>
          <div class="kpi" style="margin-bottom:6px"><div class="v">${res.total_matches}</div><div class="l">matching records · showing ${res.results.length}, spread across sources</div></div>
          <div class="row small muted" style="margin-bottom:10px">${Object.entries(res.source_distribution).map(([s, n]) => `${esc(nice(s))} ${n}`).join(" · ")}</div>
          ${hlLegend()}<div class="stack mt">${res.results.map(resultCard).join("")}</div>`;
      },
    });
  }

  const CHALLENGE_FIELDS = [
    ["relevant", "About photo retrieval"], ["perspective", "Perspective"], ["describes_retrieval_attempt", "Retrieval attempt"],
    ["retrieval_scenario", "Scenario"], ["success_status", "Outcome"], ["failure_stage", "Breakdown"], ["opportunity_areas", "Opportunity areas"],
  ];
  function fieldOptions(field) {
    const m = state.meta || {};
    return {
      relevant: [true, false], describes_retrieval_attempt: [true, false], perspective: m.perspectives, retrieval_scenario: m.scenarios,
      success_status: m.success_status, failure_stage: Object.keys(m.failure_stages || {}), opportunity_areas: Object.keys(m.opportunities || {}),
    }[field] || [];
  }
  const showVal = (v) => (Array.isArray(v) ? (v.length ? v.map(nice).join(", ") : "None") : typeof v === "boolean" ? (v ? "Yes" : "No") : nice(v));

  function openRecord(recordId) {
    openDrawer({
      title: "Evidence inspector",
      recordId,
      render: async () => {
        const d = await api(`/api/record/${encodeURIComponent(recordId)}`);
        const raw = d.raw_evidence, ai = d.ai_interpretation[0];
        const valid = d.signals.filter((s) => s.quote_valid);
        const invalid = d.signals.filter((s) => !s.quote_valid);
        const groups = {};
        valid.forEach((s) => (groups[KIND_GROUP(s.kind)] ||= []).push(s));
        const eng = Object.entries(raw.engagement || {});
        return `<div class="row" style="margin-bottom:10px">${sourceChip(raw.source)}${raw.platform && raw.platform !== raw.source ? `<span class="chip">${esc(raw.platform)}</span>` : ""}<span class="chip num">${esc((raw.created_at || "no date").slice(0, 10))}</span>${raw.is_synthetic && state.bundle.provenance?.note ? `<span class="pill-prov" data-tip="${esc("This record's text was generated, not collected from a real user.")}">Generated record</span>` : ""}${raw.duplicate_of ? `<span class="chip">Duplicate of ${esc(raw.duplicate_of)}</span>` : ""}</div>
          <div class="small muted num" style="margin-bottom:12px">${esc(raw.record_id)}${raw.source_url ? ` · <a href="${esc(raw.source_url)}" target="_blank" rel="noopener">source link</a>` : " · no source URL"}</div>
          <h3 style="margin-top:0">Raw evidence</h3>
          <div class="card" style="box-shadow:none;background:var(--surface-2)">${raw.title ? `<div style="font-weight:600;margin-bottom:6px">${esc(raw.title)}</div>` : ""}<div style="line-height:1.7;font-size:14.5px">${highlight(raw.text, valid)}</div>${hlLegend()}</div>
          ${raw.thread_context ? `<div class="small muted mt">Thread: ${esc(raw.thread_context)}</div>` : ""}
          ${eng.length ? `<div class="row small muted mt">${eng.map(([k, v]) => `<span>${esc(nice(k))}: <b>${esc(v)}</b></span>`).join(" · ")}</div>` : ""}
          ${raw.replies?.length ? `<details class="mt"><summary class="small link">${raw.replies.length} replies</summary><div class="quotes" style="margin-top:8px">${raw.replies.map((x) => `<div class="quote"><div class="q">${esc(x)}</div></div>`).join("")}</div></details>` : ""}
          <h3>AI interpretation</h3>
          ${ai ? `<div class="small muted" style="margin-bottom:10px">${esc(ai.analyzer)}${ai.model ? ` · ${esc(ai.model)}` : ""} · ${esc(ai.prompt_version)} · confidence ${ai.confidence}${ai.pm_overrides ? ` · <b>${ai.pm_overrides.length} PM correction(s) applied</b>` : ""}</div>
          <div class="kv">${CHALLENGE_FIELDS.map(([f, l]) => `<div class="k">${l}</div><div class="v">${esc(showVal(ai.payload[f]))}${(ai.pm_overrides || []).some((o) => o.field === f) ? ` <span class="chip accent">corrected</span>` : ""}</div><button class="btn subtle sm" data-challenge="${attr({ analysis_id: ai.analysis_id, field: f, record_id: recordId })}">Challenge</button><div class="challenge" id="ch-${f}" hidden></div>`).join("")}</div>
          ${ai.payload.user_goal ? `<div class="notice small mt">${icon("info", 15)}<div><b>Stated goal:</b> ${esc(ai.payload.user_goal)}</div></div>` : ""}
          ${ai.payload.interpretation ? `<p class="small muted"><span class="tag int">Interpretation</span> ${esc(ai.payload.interpretation)}</p>` : ""}` : empty("This record hasn't been analysed (it may be a duplicate).")}
          <h3>Extracted signals <span class="muted">(${valid.length})</span></h3>
          ${Object.entries(groups).sort((a, b) => KIND_PRIORITY[a[0]] - KIND_PRIORITY[b[0]]).map(([g, list]) => `<div style="margin-bottom:10px"><div class="small" style="font-weight:600;color:var(--text-secondary);margin:8px 0 2px">${SIG_KIND[g]}</div>${list.map((s) => `<div class="sig"><div class="body"><div class="lab">${esc(nice(s.label))} <span class="muted small">· ${esc(s.kind)}</span></div><div class="qt">“${esc(s.quote)}”</div><div class="small muted num">${esc(s.evidence_id)}</div><div class="challenge" id="rj-${esc(s.evidence_id)}" hidden></div></div><button class="btn subtle sm" data-reject="${attr({ evidence_id: s.evidence_id, record_id: recordId })}">Reject</button></div>`).join("")}</div>`).join("") || empty("No validated signals.")}
          ${invalid.length ? `<details><summary class="small link">${invalid.length} quote(s) failed the verbatim check and are excluded</summary>${invalid.map((s) => `<div class="sig invalid"><div class="body"><div class="lab">${esc(nice(s.label))}</div><div class="qt">“${esc(s.quote)}”</div></div></div>`).join("")}</details>` : ""}
          ${d.overrides.length ? `<h3>Corrections on this record</h3>${d.overrides.map((o) => `<div class="sig"><div class="body"><div class="lab">${esc(nice(o.field))}: ${esc(o.old_value)} → ${esc(o.new_value)}</div><div class="qt">${esc(o.note || "No reason given")} · ${esc(o.created_at.slice(0, 16).replace("T", " "))}</div></div></div>`).join("")}` : ""}
          ${d.analysis_history.length > 1 ? `<details class="mt"><summary class="small link">Analysis history (${d.analysis_history.length})</summary>${d.analysis_history.map((h) => `<div class="small muted num">${esc(h.created_at)} · ${esc(h.analyzer)} · ${esc(h.prompt_version)}${h.is_current ? " · current" : ""}</div>`).join("")}</details>` : ""}`;
      },
    });
  }

  function showChallenge({ analysis_id, field, record_id }) {
    const box = $(`#ch-${field}`);
    if (!box) return;
    if (!box.hidden) { box.hidden = true; return; }
    const opts = fieldOptions(field);
    const control = field === "opportunity_areas"
      ? `<div class="row">${opts.map((o) => `<label class="chip" style="cursor:pointer"><input type="checkbox" value="${esc(o)}"> ${esc(nice(o))}</label>`).join("")}</div>`
      : `<select class="select" style="max-width:100%">${opts.map((o) => `<option value="${attr(o)}">${esc(showVal(o))}</option>`).join("")}</select>`;
    box.innerHTML = `<div class="small" style="font-weight:600">Correct “${esc(CHALLENGE_FIELDS.find((f) => f[0] === field)[1])}”</div>${control}
      <input class="input" placeholder="Why? (kept in the audit log)" aria-label="Reason">
      <div class="row"><button class="btn sm" data-save-challenge="${attr({ analysis_id, field, record_id })}">Save correction</button><button class="btn subtle sm" data-action="cancel-inline">Cancel</button><span class="small muted">The original AI output is kept.</span></div>`;
    box.hidden = false;
    $("select, input[type=checkbox]", box)?.focus();
  }

  async function saveChallenge({ analysis_id, field, record_id }, btn) {
    const box = $(`#ch-${field}`);
    const note = $("input.input", box).value.trim();
    let value;
    if (field === "opportunity_areas") value = $$("input[type=checkbox]:checked", box).map((c) => c.value);
    else value = JSON.parse($("select", box).value);
    btn.disabled = true;
    try {
      await api("/api/override", { target_type: "analysis", target_id: analysis_id, field, new_value: value, note });
      state.review = null;
      toast("Correction saved. Rebuild to update every number.", { label: "Rebuild now", fn: rebuild });
      state.drawer.pop(); openRecord(record_id);
    } catch (e) { toast(`Couldn't save: ${e.message}`); btn.disabled = false; }
  }

  function showReject({ evidence_id, record_id }) {
    const box = $(`#rj-${CSS.escape(evidence_id)}`);
    if (!box) return;
    if (!box.hidden) { box.hidden = true; return; }
    box.innerHTML = `<input class="input" placeholder="Why is this signal wrong?" aria-label="Reason"><div class="row"><button class="btn sm" data-save-reject="${attr({ evidence_id, record_id })}">Reject signal</button><button class="btn subtle sm" data-action="cancel-inline">Cancel</button></div>`;
    box.hidden = false; $("input", box).focus();
  }

  async function saveReject({ evidence_id, record_id }, btn) {
    const box = $(`#rj-${CSS.escape(evidence_id)}`);
    btn.disabled = true;
    try {
      await api("/api/override", { target_type: "signal", target_id: evidence_id, field: "rejected", new_value: true, note: $("input", box).value.trim() });
      state.review = null;
      toast("Signal rejected. Rebuild to update every number.", { label: "Rebuild now", fn: rebuild });
      state.drawer.pop(); openRecord(record_id);
    } catch (e) { toast(`Couldn't save: ${e.message}`); btn.disabled = false; }
  }

  const SENS_CLASS = { high: "s8", medium: "s3", low: "s5" };

  // Part 3: what it would actually take to research this segment.
  function researchFitBlock(name, { compact = false } = {}) {
    const f = (state.bundle.research_fit || {})[name];
    if (!f) return "";
    const sens = f.sensitivity, obs = f.observability, rec = f.recruitability;
    const cell = (label, head, why, extra = "") => `<div class="card" data-tip="${esc(why)}"><div class="l small muted">${label}</div><div style="font-weight:600;font-size:13.5px">${head}</div>${extra}</div>`;
    const head = `<div class="grid g2" style="gap:10px">
      ${cell("Role in the study", esc(f.role.headline), f.role.why, `<div class="small muted" style="margin-top:4px">${esc(f.role.why)}</div>`)}
      ${cell("Recruiting", esc(rec.headline), rec.why, `<div class="small muted" style="margin-top:4px">${esc(rec.why)}</div>`)}
      ${cell("In a session", esc(obs.headline), obs.why, `<div class="small muted" style="margin-top:4px">${esc(obs.why)}</div>`)}
      ${cell("Content sensitivity", `<i class="dot" style="background:var(--${SENS_CLASS[sens.level]})"></i> ${esc(cap(sens.level))} · ${pct(sens.rate)}`, sens.rule, `<div class="small muted" style="margin-top:4px">${esc(sens.means)}</div>`)}
    </div>`;
    const changes = `<h3>What changes in the session</h3><ul class="plain">${f.session_shape.changes.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
    const screener = `<details ${compact ? "" : "open"} style="margin-top:10px"><summary class="small link">Screener for this segment (${f.screener.length} questions)</summary>
      <ol class="guide" style="margin-top:8px">${f.screener.map((q) => `<li><span>${esc(q)}</span></li>`).join("")}</ol></details>`;
    return `${head}${changes}${screener}
      ${f.sample_note ? `<div class="notice small mt">${icon("info", 15)}<div>${esc(f.sample_note)}</div></div>` : ""}`;
  }

  function openSegment(name) {
    const b = state.bundle;
    const s = (b.segments || []).find((x) => x.segment === name);
    if (!s) return;
    const so = b.segment_overview;
    const list = (pairs) => pairs.length ? pairs.map(([l, n]) => `<div class="row small" style="padding:3px 0"><span>${esc(nice(l))}</span><span class="spacer"></span><span class="muted num">${n}</span></div>`).join("") : `<div class="small muted">—</div>`;
    const stateMeta = { direct_low_effort: "Direct / low-effort", candidate_heavy: "Candidate-heavy", recovery_dependent: "Recovery-dependent", unresolved: "Unresolved", unavailable: "Unavailable" };
    const also = Object.entries(s.retrieval_states || {}).map(([k, r]) => ({ ...r, label: k }));
    openDrawer({
      title: `${s.number}. ${s.segment}`,
      render: async () => `<p class="secondary" style="margin:0 0 12px">${esc(s.definition)}</p>
        <div class="row" style="margin-bottom:12px">${strength(s.evidence_strength)}<span class="chip num">${s.records} attempts · ${s.unique_sources} sources</span>
          <span class="spacer"></span><button class="btn subtle sm" ${segDrill(s, `${s.segment}: all attempts`)}>Read all ${s.records} ${icon("arrow", 13)}</button></div>
        <div class="grid g2" style="gap:10px">${[["Share of all attempts", s.share_of_attempts], ["Found the photo", s.found], ["Did not fully succeed", s.unsuccessful], ["Gave up", s.abandonment_signals]].map(([l, r]) => `<div class="card kpi" data-tip="${esc(rateTip(l, r))}"><div class="v" style="font-size:20px">${pct(r)}${dirMark(r)}</div><div class="l">${l}</div><div class="d">${frac(r)}</div></div>`).join("")}</div>
        <h3>How an attempt lands here</h3><p class="small secondary" style="margin:0">${esc(s.rule)}</p>
        <h3>In their words</h3>${quotes(s.defining_evidence, 4)}
        <h3>How these attempts ended</h3>${segbar(s.outcomes, OUTCOME_ORDER, outColor, nice, { tall: true })}${legend(OUTCOME_ORDER.filter((k) => s.outcomes[k]), outColor, nice)}
        <h3>Retrieval states within this segment</h3>${bars(also, { name: (r) => stateMeta[r.label] || r.label, limit: 5 })}
        ${s.recovery_routes.length ? `<h3>Routes they took after the first try</h3>${list(s.recovery_routes)}` : ""}
        <div class="grid g3 mt" style="gap:14px"><div><h3 style="margin-top:0">Remembered</h3>${list(s.top_remembered)}</div><div><h3 style="margin-top:0">Forgotten</h3>${list(s.top_forgotten)}</div><div><h3 style="margin-top:0">Workarounds</h3>${list(s.top_workarounds)}</div></div>
        <div class="notice small mt">${icon("info", 15)}<div><b>Your judgement:</b> ${esc(s.feasibility_of_primary_research)} ${esc(s.potential_for_intervention)}</div></div>
        <h2 class="drawer-h2">Taking this segment into research</h2>
        ${researchFitBlock(s.segment)}
        <div class="row mt">${b.target_segment === s.segment
          ? `<span class="chip accent">Current target segment for interviews</span>`
          : `<button class="btn" data-pick-segment="${esc(s.segment)}">Take this segment into research</button>`}</div>`,
    });
  }

  function openStage(i) {
    const j = state.bundle.journey[i];
    openDrawer({
      title: `Stage ${i + 1}: ${cap(j.stage)}`,
      render: async () => `<div class="grid g2" style="gap:10px">${[["Attempts with this step", j.records_with_step], ["Attempts with a difficulty here", j.records_with_difficulty]].map(([l, r]) => `<div class="card kpi"><div class="v" style="font-size:22px">${pct(r)}</div><div class="l">${l}</div><div class="d">${frac(r)}</div></div>`).join("")}</div>
        <h3>Difficulties in users' words</h3>${quotes(j.examples, 6)}`,
    });
  }

  // ---------------------------------------------------------------- palette
  const palette = $("#palette"), pInput = $("#paletteInput"), pList = $("#paletteList");
  let pItems = [], pIndex = 0;
  function openPalette() { palette.hidden = false; pInput.value = ""; paintPalette(); setTimeout(() => pInput.focus(), 0); }
  function closePalette() { palette.hidden = true; }
  function paintPalette() {
    const q = pInput.value.trim().toLowerCase();
    const navItems = NAV.filter((n) => n.id).map((n) => ({ type: "nav", label: n.label, hash: `#/${n.id}`, icon: n.icon }));
    const oppItems = (state.bundle?.opportunities || []).map((o) => ({ type: "nav", label: nice(o.opportunity), hash: `#/opportunities/${encodeURIComponent(o.opportunity)}`, icon: "opps" }));
    const sugg = SUGGESTED.map((s) => ({ type: "ask", label: s, icon: "explore" }));
    const match = (i) => !q || i.label.toLowerCase().includes(q);
    const sections = [];
    if (q) sections.push(["Ask", [{ type: "ask", label: pInput.value.trim(), icon: "search" }]]);
    sections.push(["Suggested questions", sugg.filter(match).slice(0, q ? 4 : 6)]);
    sections.push(["Go to", [...navItems, ...oppItems].filter(match).slice(0, 8)]);
    pItems = sections.flatMap(([, items]) => items);
    pIndex = Math.min(pIndex, Math.max(0, pItems.length - 1));
    let k = 0;
    pList.innerHTML = sections.filter(([, items]) => items.length).map(([name, items]) => `<div class="palette-sec">${name}</div>${items.map((it) => { const idx = k++; return `<div class="palette-item ${idx === pIndex ? "on" : ""}" data-pidx="${idx}">${icon(it.icon, 15)}<span>${it.type === "ask" && name === "Ask" ? `Ask: <b>${esc(it.label)}</b>` : esc(it.label)}</span><span class="kind">${it.type === "ask" ? "Ask" : "Open"}</span></div>`; }).join("")}`).join("");
  }
  function choosePalette(i) {
    const it = pItems[i];
    if (!it) return;
    closePalette();
    if (it.type === "nav") go(it.hash); else runAsk(it.label);
  }
  pInput.addEventListener("input", () => { pIndex = 0; paintPalette(); });
  pInput.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { pIndex = Math.min(pItems.length - 1, pIndex + 1); paintPalette(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { pIndex = Math.max(0, pIndex - 1); paintPalette(); e.preventDefault(); }
    else if (e.key === "Enter") { choosePalette(pIndex); e.preventDefault(); }
    else if (e.key === "Escape") closePalette();
  });
  palette.addEventListener("click", (e) => {
    const it = e.target.closest("[data-pidx]");
    if (it) choosePalette(+it.dataset.pidx);
    else if (e.target === palette) closePalette();
  });

  // ---------------------------------------------------------------- tooltip & toast
  const tooltip = $("#tooltip");
  let tipEl = null;
  document.addEventListener("mouseover", (e) => {
    const t = e.target.closest("[data-tip]");
    if (t === tipEl) return;
    tipEl = t;
    if (!t || !t.dataset.tip) { tooltip.classList.remove("show"); return; }
    tooltip.innerHTML = t.dataset.tip;
    tooltip.classList.add("show");
  });
  document.addEventListener("mousemove", (e) => {
    if (!tooltip.classList.contains("show")) return;
    const w = tooltip.offsetWidth, h = tooltip.offsetHeight;
    let x = e.clientX + 14, y = e.clientY + 16;
    if (x + w > innerWidth - 8) x = e.clientX - w - 14;
    if (y + h > innerHeight - 8) y = e.clientY - h - 12;
    tooltip.style.left = `${x}px`; tooltip.style.top = `${y}px`;
  });
  document.addEventListener("scroll", () => tooltip.classList.remove("show"), true);

  function toast(msg, action) {
    const el = document.createElement("div");
    el.className = "toast";
    el.innerHTML = `<span>${esc(msg)}</span>${action ? `<button class="btn sm">${esc(action.label)}</button>` : ""}`;
    if (action) $("button", el).onclick = () => { el.remove(); action.fn(); };
    $("#toasts").appendChild(el);
    setTimeout(() => el.remove(), action ? 9000 : 4000);
  }

  async function pickSegment(segment) {
    try {
      await api("/api/override", { target_type: "study", target_id: "research", field: "target_segment",
        new_value: segment, note: segment ? "Target segment for primary research" : "Cleared target segment" });
      closeDrawer();
      toast(segment ? `Target segment set: ${segment}` : "Target segment cleared", { label: "Rebuild plan", fn: rebuild });
    } catch (e) { toast(`Couldn't save: ${e.message}`); }
  }

  async function pickOpportunity(opp) {
    try {
      await api("/api/override", { target_type: "study", target_id: "research", field: "target_opportunity",
        new_value: opp, note: opp ? `Target opportunity selected by PM: ${opp}` : "Cleared target opportunity" });
      closeDrawer();
      toast(opp ? `Target opportunity set: ${nice(opp)}` : "Target opportunity cleared", { label: "Rebuild plan", fn: rebuild });
    } catch (e) { toast(`Couldn't save: ${e.message}`); }
  }

  async function rebuild() {
    const btn = $("#rebuildBtn");
    btn.disabled = true;
    toast("Rebuilding every number from current analyses and corrections…");
    try {
      state.bundle = await api("/api/rebuild", {});
      state.review = null;
      render(); renderNav();
      toast("Rebuilt. All views reflect the latest evidence.");
    } catch (e) { toast(`Rebuild failed: ${e.message}`); }
    btn.disabled = false;
  }

  async function copyText(text) {
    try { await navigator.clipboard.writeText(text); toast("Copied to clipboard"); }
    catch (e) { toast("Copy isn't available in this browser"); }
  }

  // ---------------------------------------------------------------- events
  document.addEventListener("click", (e) => {
    const t = e.target;
    const el = (sel) => t.closest(sel);
    let x;
    if ((x = el("[data-save-challenge]"))) return saveChallenge(JSON.parse(x.dataset.saveChallenge), x);
    if ((x = el("[data-save-reject]"))) return saveReject(JSON.parse(x.dataset.saveReject), x);
    if ((x = el("[data-challenge]"))) return showChallenge(JSON.parse(x.dataset.challenge));
    if ((x = el("[data-reject]"))) return showReject(JSON.parse(x.dataset.reject));
    if ((x = el("[data-action]"))) {
      const a = x.dataset.action;
      if (a === "drawer-close") return closeDrawer();
      if (a === "drawer-back") { state.drawer.pop(); return paintDrawer(); }
      if (a === "cancel-inline") { x.closest(".challenge").hidden = true; return; }
      if (a === "reload-review") { state.review = null; return render(); }
    }
    if ((x = el("[data-copy]"))) return copyText(JSON.parse(x.dataset.copy));
    if ((x = el("[data-rec]")) && !el("details summary")) return openRecord(x.dataset.rec);
    if ((x = el("[data-drill]"))) { const d = JSON.parse(x.dataset.drill); return openEvidence(d); }
    if ((x = el("[data-sort]"))) {
      const { id, key } = JSON.parse(x.dataset.sort);
      const cur = state.sorts[id];
      state.sorts[id] = { key, dir: cur && cur.key === key ? -cur.dir : -1 };
      return render({ keepScroll: true });
    }
    if ((x = el("[data-pick-segment]"))) return pickSegment(x.dataset.pickSegment);
    if ((x = el("[data-clear-segment]"))) return pickSegment(null);
    if ((x = el("[data-segment]"))) return openSegment(x.dataset.segment);
    if ((x = el("[data-stage]"))) return openStage(+x.dataset.stage);
    if ((x = el("[data-reviewtab]"))) { state.reviewTab = x.dataset.reviewtab; return render({ keepScroll: true }); }
    if ((x = el("[data-researchtab]"))) { state.researchTab = x.dataset.researchtab; return render(); }
    if ((x = el("[data-seglens]"))) { state.segLens = x.dataset.seglens; return render({ keepScroll: true }); }
    if ((x = el("[data-ask]"))) return runAsk(x.dataset.ask);
    if ((x = el("[data-nav]"))) { e.preventDefault(); closeDrawer(); return go(x.dataset.nav); }
  });
  scrim.addEventListener("click", closeDrawer);

  document.addEventListener("submit", (e) => {
    if (e.target.id === "askForm") { e.preventDefault(); const i = $("#askInput"); runAsk(i.value); i.value = ""; }
    if (e.target.id === "searchForm") { e.preventDefault(); state.explore.query = $("#searchInput").value; runSearch(); }
  });
  document.addEventListener("change", (e) => {
    const f = e.target.closest("[data-facet]");
    if (f) { if (f.value) state.explore.filters[f.dataset.facet] = [f.value]; else delete state.explore.filters[f.dataset.facet]; state.explore.query = $("#searchInput")?.value || ""; runSearch(); }
    if (e.target.id === "attemptsOnly") { state.explore.filters.attempts_only = e.target.checked; runSearch(); }
  });
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); palette.hidden ? openPalette() : closePalette(); return; }
    if (e.key === "Escape") { if (!palette.hidden) return closePalette(); if (state.drawer.length) return closeDrawer(); $("#sidebar").classList.remove("open"); }
    if (e.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) { e.preventDefault(); openPalette(); }
    if (e.key === "Enter" && document.activeElement?.matches?.("[role=button][data-rec]")) openRecord(document.activeElement.dataset.rec);
  });

  $("#askTrigger").addEventListener("click", openPalette);
  $("#rebuildBtn").addEventListener("click", rebuild);
  $("#menuBtn").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
  function paintTheme() {
    const t = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    $("#themeBtn").innerHTML = icon(t === "dark" ? "sun" : "moon", 17);
    $("#themeBtn").setAttribute("aria-label", t === "dark" ? "Switch to light theme" : "Switch to dark theme");
  }
  $("#themeBtn").addEventListener("click", () => {
    const cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("de-theme", next); } catch (err) { /* storage unavailable: theme lasts this visit */ }
    paintTheme();
  });

  // ---------------------------------------------------------------- shell rendering
  function renderNav() {
    const { view } = parseRoute();
    $("#nav").innerHTML = NAV.map((n) => n.group ? `<div class="group">${n.group}</div>` :
      `<a href="#/${n.id}" class="${view === n.id ? "on" : ""}" ${view === n.id ? 'aria-current="page"' : ""}>${icon(n.icon, 17)}<span>${n.label}</span>${n.count && n.count() != null ? `<span class="count num">${n.count()}</span>` : ""}</a>`).join("");
    const b = state.bundle;
    if (b) {
      $("#sidebarFoot").innerHTML = `<div><span>Dataset</span><b>${esc(Object.keys(b.scope.sources).length)} sources</b></div><div><span>Unique records</span><b class="num">${b.overview.unique_records}</b></div><div><span>Analyzer</span><b>${esc(Object.keys(b.scope.analyzers).join(", "))}</b></div><div><span>Built</span><b class="num">${esc(b.generated_at.slice(0, 16).replace("T", " "))}</b></div><div style="margin-top:6px"><a href="/classic" style="color:var(--text-muted)">Classic dashboard</a></div>`;
      const prov = b.provenance || {};
      const dsName = (prov.datasets || []).join(", ") || "dataset";
      $("#provenancePill").innerHTML = prov.note
        ? `<span class="pill-prov" data-tip="${esc(`<b>Data provenance</b><br>${esc(prov.note)}`)}">${icon("info", 13)}<span>Generated data</span></span>`
        // Neutral: name the dataset, claim nothing about where the text came from.
        : `<span class="pill-prov real" data-tip="${esc(`<b>Dataset</b><br>${esc(dsName)} · ${b.overview.total_records} records, ${b.overview.unique_records} unique`)}">${icon("info", 13)}<span>${esc(dsName.length > 26 ? dsName.slice(0, 24) + "…" : dsName)}</span></span>`;
    }
  }

  function renderCrumbs(route) {
    const nav = NAV.find((n) => n.id === route.view);
    let html = `<a href="#/overview">Discovery</a><span>/</span>`;
    if (route.view === "opportunities" && route.id) html += `<a href="#/opportunities">Opportunities</a><span>/</span><b>${esc(nice(route.id))}</b>`;
    else html += `<b>${esc(nav?.title || "Overview")}</b>`;
    $("#crumbs").innerHTML = html;
    document.title = `${route.id ? nice(route.id) : nav?.title || "Overview"} · Discovery Engine`;
  }

  function render({ keepScroll = false } = {}) {
    const route = parseRoute();
    renderNav(); renderCrumbs(route);
    const main = $("#main");
    const y = scrollY;
    if (!state.bundle) { main.innerHTML = loadingView(); return; }
    const fn = views[route.view] || views.overview;
    try { main.innerHTML = fn(route.id, route.params); }
    catch (err) { console.error(err); main.innerHTML = `<div class="notice warn">${icon("info", 18)}<div><b>This view couldn't be drawn.</b> ${esc(err.message)}</div></div>`; }
    $("#sidebar").classList.remove("open");
    if (keepScroll) scrollTo(0, y); else { scrollTo(0, 0); main.focus({ preventScroll: true }); }
  }

  const loadingView = () => `<div class="skeleton" style="height:34px;width:40%;margin-bottom:12px"></div><div class="skeleton" style="height:18px;width:60%;margin-bottom:24px"></div>
    <div class="grid g4">${"<div class='skeleton' style='height:92px'></div>".repeat(4)}</div><div class="grid g-main mt"><div class="skeleton" style="height:260px"></div><div class="skeleton" style="height:260px"></div></div>`;

  window.addEventListener("hashchange", () => { closeDrawer(); render(); });

  async function boot() {
    paintTheme();
    render();
    try {
      const [bundle, meta] = await Promise.all([api("/api/bundle"), api("/api/meta")]);
      state.bundle = bundle; state.meta = meta;
      render();
      loadReview();
    } catch (e) {
      $("#main").innerHTML = `${pageHead("Discovery Engine", "No evidence to show yet", "")}<div class="notice warn">${icon("info", 18)}<div><b>The discovery bundle couldn't load.</b> ${esc(e.message)}<br>Ingest and analyse a dataset first:<br><code>python -m discovery_engine ingest dataset_flat.csv --dataset dataset_flat --synthetic</code><br><code>python -m discovery_engine analyze</code><br><code>python -m discovery_engine synthesize</code></div></div>`;
    }
  }
  boot();
})();
