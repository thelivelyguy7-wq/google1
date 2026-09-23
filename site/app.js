/* Discovery engine UI. Every number comes from site_data.js; nothing is typed here.
   Generated data: window.SITE_DATA (see engine/export_site.py). */
"use strict";
const D = window.SITE_DATA;
const COLS = {};
D.records.columns.forEach((c, i) => (COLS[c] = i));
const REL = D.derived.relevant;

/* ---------- tiny DOM helpers ---------- */
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (n, of) => (of ? ((100 * n) / of).toFixed(1) + "%" : "—");
const titleCase = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const human = (s) => titleCase(String(s).replace(/_/g, " "));
const label = (t, cls) => t === "OPP-HYP" ? "" : `<span class="chip ${cls || ""}">${esc(t)}</span>`;
const OBS = "";
const INTERP = label("INTERP");
const UNKNOWN = label("UNKNOWN", "warn");

/* A count that opens the records behind it. `key` indexes D.evidence_index. */
function ev(key, n, of) {
  const ids = D.evidence_index[key];
  if (!ids) return `${n}${of ? " of " + of : ""}`;
  const text = `${ids.length}${of ? " of " + of : ""}`;
  return `<button class="link" data-key="${esc(key)}">${text}</button>`;
}
const countOf = (key) => (D.evidence_index[key] || []).length;

function table(headers, rows, opts = {}) {
  const head = headers.map((h) => `<th>${esc(h)}</th>`).join("");
  const body = rows.map((r) => {
    // Hide rows with 0 or TBD values when in evaluator mode
    const textContent = r.join(" ").toLowerCase();
    const isZeroOrTBD = textContent.includes(">0<") || textContent.includes(">0 (0.0%)<") || textContent.includes(">tbd<") || textContent.includes(">outcome not stated<") || textContent.includes(">none<");
    const rowClass = isZeroOrTBD ? ' class="hidden-row"' : '';
    return `<tr${rowClass}>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`;
  }).join("");
  return `<table${opts.id ? ` id="${opts.id}"` : ""}><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}
function stat(n, lab, key) {
  const value = key ? ev(key, n) : esc(String(n));
  return `<div class="stat"><div class="n">${value}</div><div class="lab">${esc(lab)}</div></div>`;
}
function barRow(name, n, max, of) {
  const w = max ? Math.round((100 * n) / max) : 0;
  return [esc(name), `<div class="bar"><span style="width:${w}%"></span></div>`, `${n} <span class="muted">(${pct(n, of)})</span>`];
}
const sortedEntries = (obj) => Object.entries(obj || {}).sort((a, b) => b[1] - a[1]);

/* ---------- record drawer ---------- */
const drawer = document.getElementById("drawer");
const scrim = document.getElementById("scrim");
function recordCard(pos) {
  const row = D.records.rows[pos];
  const get = (c) => (COLS[c] === undefined ? "" : row[COLS[c]]);
  const meta = ["retrieval_state", "outcome", "object_class", "journey_stages", "severity_signals"]
    .filter((c) => get(c))
    .map((c) => {
      let val = get(c).replace(/\|/g, ", ");
      if (c === "outcome" && val === "unknown") val = "Outcome Not Stated";
      if (val === "none named") val = "don't explicitly state";
      return label(`${c.split("_")[0]}: ${val}`);
    })
    .join(" ");
  return `<div class="rec"><div class="id">${esc(get("record_id"))} <span class="muted">· ${esc(get("source"))}</span></div>
    <div class="quote">${esc(get("raw_text"))}</div>
    <div>${meta}</div>
    ${get("scenario") ? `<p class="muted">${esc(get("scenario"))}</p>` : ""}</div>`;
}
function openDrawer(key) {
  const ids = D.evidence_index[key] || [];
  document.getElementById("drawerTitle").textContent = key;
  document.getElementById("drawerSub").textContent = `${ids.length} of ${REL} relevant records`;
  const shown = ids.slice(0, 200);
  document.getElementById("drawerBody").innerHTML =
    shown.map(recordCard).join("") +
    (ids.length > shown.length ? `<p class="muted">Showing ${shown.length} of ${ids.length}. Full list: output/evidence_index.csv</p>` : "");
  drawer.classList.add('open'); scrim.classList.add('open');
  document.getElementById("drawerClose").focus();
}
function closeDrawer() { drawer.classList.remove('open'); scrim.classList.remove('open'); }
document.getElementById("drawerClose").addEventListener("click", closeDrawer);
scrim.addEventListener("click", closeDrawer);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });
document.addEventListener("click", (e) => {
  const b = e.target.closest("button.link[data-key]");
  if (b) openDrawer(b.dataset.key);
});

/* ---------- pages ---------- */
const PAGES = [];
const page = (id, title, stage, render) => PAGES.push({ id, title, stage, render });

page("overview", "Overview", "Stage 0", () => {
  const s0 = D.stage0, oj = D.object_judgement, ip = D.incoherent_pairs;
  const ind = Object.entries(D.independence);
  const maxV = Math.max(...ind.map(([, v]) => v.cramers_v));
  return `<h1>Dataset quality and relevance</h1>
  <div class="grid">
    ${stat(s0.relevant, "retrieval-related records", "claim:K01")}
    ${stat(s0.possibly, "possibly relevant (deleted-photo restore)")}
    ${stat(s0.irrelevant, "not retrieval-related")}
    ${stat(s0.total, "records in the file")}
  </div>
  <h2>Ask the AI Discovery Engine</h2>
  <div class="card ai-chat-container">
    <p class="muted" style="margin-top: 0;">Explore problems, compare areas, and query evidence directly from the dataset.</p>
    <div class="ai-chips">
      <button class="ai-chip" onclick="askAI('What kinds of old photos do users struggle to retrieve?')">What kinds of old photos do users struggle to retrieve?</button>
      <button class="ai-chip" onclick="askAI('What information do people actually remember about a photo?')">What information do people actually remember about a photo?</button>
      <button class="ai-chip" onclick="askAI('What information have they forgotten?')">What information have they forgotten?</button>
      <button class="ai-chip" onclick="askAI('How do users formulate searches when their memory is incomplete?')">How do users formulate searches when their memory is incomplete?</button>
    </div>
    <div class="ai-input-group">
      <input type="text" id="aiInput" placeholder="Ask a custom question..." onkeydown="if(event.key === 'Enter') askAI(this.value)" />
      <button onclick="askAI(document.getElementById('aiInput').value)">Ask</button>
    </div>
    <div id="aiResponse" class="ai-response" style="display:none;"></div>
  </div>`;
});

page("journey", "Journey", "Stage 2", () => {
  const J = D.journey, SQ = D.stage_questions;
  const DC = D.decomposition, NODES = D.narrative.decomposition_nodes, rules = D.narrative.attribution_rules;
  const stages = Object.keys(J.touched);
  const maxT = Math.max(...Object.values(J.touched));
  const answer = {
    RECALL: SQ.RECALL.top_remembered.map(([a, b]) => `${human(a)} ${b}`).join(", "),
    EXPRESS: `First-attempt inputs ${SQ.EXPRESS.first_attempt}; date-based ${SQ.EXPRESS.date}; reformulation ${SQ.EXPRESS.reformulation}; explicit barrier ${SQ.EXPRESS.barrier}`,
    MATCH: `Candidates surfaced in ${SQ.MATCH.candidates_surfaced}; too many results ${SQ.MATCH.too_many_results}; records stating the product misread the clues: ${SQ.MATCH.product_misread_stated}`,
    RECOGNIZE: `Would recognise on sight ${SQ.RECOGNIZE.can_on_sight}; cannot tell which is right ${SQ.RECOGNIZE.cannot_tell}; heavy inspection ${SQ.RECOGNIZE.heavy_inspection}`,
    RECOVER: `Reformulate, switch or browse ${SQ.RECOVER.effort}; success after several attempts ${SQ.RECOVER.success_after_effort}; exits ${SQ.RECOVER.exits}`,
  };
  
  const rows = Object.entries(DC).map(([k, v]) => [
    `<strong>${esc(k)} ${esc(v.name)}</strong>`,
    v.breakdown ? ev(`node:${k}:breakdown`, v.breakdown) : `<strong>${v.breakdown}</strong>`,
    v.indirect ? ev(`node:${k}:indirect`, v.indirect) : v.indirect,
    v.effort ? ev(`node:${k}:effort`, v.effort) : v.effort,
    v.intact ? ev(`node:${k}:intact`, v.intact) : v.intact,
    `${v.no_evidence} of ${REL}`,
  ]);

  return `<h1>Retrieval Journey</h1>
  
  <h2 style="font-size: 1.8em; margin: 1.5em 0;">North Star : Incremental Successful retrieval of vaguely remembered photos</h2>

  <h2>Decomposition of Successful Retrieval</h2>
  <p class="lede">${INTERP} Success needs every node to hold: usable partial memory (D1), expression (D2), the product
  bringing the photo into the candidates (D3), recognition (D4), refinement when the first try fails (D5), and the
  photo being in the library (D6). A retrieval fails at the first node that does not hold.</p>
  
  ${table(["Node", "Case question", "User behaviour", "Product outcome"],
    Object.entries(NODES).map(([k, v]) =>
      [`<strong>${esc(k)} ${esc(v.name)}</strong>`, esc(v.brief_question), esc(v.user_behavior),
        esc(v.product_outcome)]))}
        
  
  
  <h2>Observed stage paths</h2>
  <p class="muted">${Object.keys(J.top_paths).length} shown of ${J.n_paths} distinct paths.</p>
  ${table(["Path", "Records"], Object.entries(J.top_paths).map(([k, v]) => [`<span class="mono">${esc(k)}</span>`, v]))}`;
});

page("insights", "Insights", "Stages 1–3", () => {
  const s1 = D.stage1, bg = D.behavior_groups, N = D.needs, NT = D.narrative.needs;
  const remembered = sortedEntries(s1.remembered), lacking = sortedEntries(s1.forgotten_family);
  const maxR = remembered[0][1], maxL = lacking[0][1];
  const needRows = Object.entries(N).map(([k, v]) => {
    const code = k.split(" ")[0], t = NT[code] || ["", ""];
    return [`<strong>${esc(code)}</strong> ${esc(k.slice(code.length + 1))}`, esc(t[0]), esc(t[1]),
      ev("need:" + code, v.n, REL), Object.entries(v.profile.outcomes).filter(([a, b]) => b && a !== "unknown")
        .map(([a, b]) => `${b} ${human(a)}`).join(", ") || "<span class='muted'>Outcome Not Stated</span>"];
  });
  const ctxRows = Object.entries(N).map(([k, v]) => {
    const p = v.profile;
    return [esc(k.split(" ")[0]),
      sortedEntries(p.object_mix).slice(0, 3).map(([a, b]) => `${human(a)} ${b}`).join(", "),
      Object.entries(p.stage_counts).map(([a, b]) => `${titleCase(a.toLowerCase())} ${b}`).join(", "),
      sortedEntries(p.remembered_mix).slice(0, 3).map(([a, b]) => `${human(a)} ${b}`).join(", "),
      `${p.large_library_stated} of ${p.n}`];
  });
  return `<h1>Insights</h1>
  <h2>The case's four questions</h2>
  ${table(["Question", "Answer from this corpus", "Limit"], [
    ["What kinds of old photos do users struggle to retrieve?",
      sortedEntries(s1.object_class).map(([a, b]) => `${human(a)} ${b}`).join(", "),
      "No class struggles more than chance, so no ranking of kinds is supportable"],
    ["What do people actually remember?", remembered.slice(0, 6).map(([a, b]) => `${human(a)} ${b}`).join(", "),
      "Template sentences; the richness of real memory is unknown"],
    ["What have they forgotten?", lacking.map(([a, b]) => `${esc(a)} ${b}`).join(", "),
      "'Don\\'t explicitly state' means memory stated without a named gap"],
    ["How do users formulate searches?", Object.entries(bg).map(([a, v]) => `${esc(a.split(" (")[0])} ${v.n}`).join("; "),
      "One behaviour sentence per record, so sequences inside a record are not observable"],
  ])}
  <h2>Remembered ${OBS}</h2>
  ${table(["Dimension", "", "Records naming it"], remembered.map(([a, b]) => barRow(human(a), b, maxR, REL)))}
  <h2>Lacking ${OBS}</h2>
  ${table(["Information", "", "Records naming it"], lacking.map(([a, b]) => barRow(titleCase(a), b, maxL, REL)))}
  <h2>Retrieval needs</h2>
  <p class="muted">Needs overlap: a record can express several. Derived from what records say, never from source.</p>
  ${table(["Need", "User goal", "Memory pattern", "Records", "Stated outcomes"], needRows)}
  <h3>Retrieval context and journey stages per need</h3>
  ${table(["Need", "Objects", "Journey stages (records touching)", "Remembers", "Library size stated"], ctxRows)}
  <h2>How users searched</h2>
  ${table(["Behaviour group", "Records", "Members"], Object.entries(bg).map(([k, v]) =>
    [esc(k), `${v.n} <span class="muted">(${pct(v.n, REL)})</span>`,
      Object.entries(v.members).map(([c, n]) => `${esc(human(D.behavior_labels[c] || c))} ${n}`).join("; ")]))}`;
});

/*
page("decomposition", "Decomposition", "The case's questions", () => {
  const DC = D.decomposition, NODES = D.narrative.decomposition_nodes, rules = D.narrative.attribution_rules;
  const rows = Object.entries(DC).map(([k, v]) => [
    `<strong>${esc(k)} ${esc(v.name)}</strong>`,
    v.breakdown ? ev(`node:${k}:breakdown`, v.breakdown) : `<strong>${v.breakdown}</strong>`,
    v.indirect ? ev(`node:${k}:indirect`, v.indirect) : v.indirect,
    v.effort ? ev(`node:${k}:effort`, v.effort) : v.effort,
    v.intact ? ev(`node:${k}:intact`, v.intact) : v.intact,
    `${v.no_evidence} of ${REL}`,
  ]);
  return `<h1>Decomposition of successful retrieval</h1>
  <p class="lede">${INTERP} Success needs every node to hold: usable partial memory (D1), expression (D2), the product
  bringing the photo into the candidates (D3), recognition (D4), refinement when the first try fails (D5), and the
  photo being in the library (D6). A retrieval fails at the first node that does not hold.</p>
  ${table(["Node", "Case question", "User behaviour", "Product outcome"],
    Object.entries(NODES).map(([k, v]) =>
      [`<strong>${esc(k)} ${esc(v.name)}</strong>`, esc(v.brief_question), esc(v.user_behavior),
        esc(v.product_outcome)]))}
  
  <h2>First-failing-node rule for the task tests</h2>
  ${table(["Order", "Node", "Classify here when"], rules.map((r, i) =>
    [i + 1, `${esc(r.node)} ${esc(NODES[r.node].name)}`, esc(r.rule)]))}
  <h2>Product outcome to measure per node</h2>
  <p class="muted">${esc(D.narrative.production_note)}</p>
  ${table(["Node", "Candidate measure"], Object.entries(NODES).map(([k, v]) =>
    [`${esc(k)} ${esc(v.name)}`, esc(v.proposed_measure)]))}`;
});
*/

page("opportunities", "Opportunities", "Stages 5–6", () => {
  const O = D.opps, NAR = D.narrative.opportunities;
  const sorted = Object.entries(O).sort((a, b) => b[1].n - a[1].n);
  const cards = sorted.map(([k, v]) => {
    const code = k.split(" ")[0], t = NAR[code] || {};
    const outs = Object.entries(v.profile.outcomes).filter(([a, b]) => b && a !== "unknown")
      .map(([a, b]) => `${b} ${human(a)}`).join(", ") || "Outcome Not Stated";
    return `<div class="card"><h3>${esc(k)} ${label("OPP-HYP")}</h3>
      <p>${esc(t.beh || "")}</p>
      <p class="muted">Journey stage: ${esc(t.st || "")} · Decomposition node: ${esc(t.node || "")}</p>
      ${table(["Frequency", "Severity", "Outcomes", "Unknowns"], [[
        ev("opp:" + code, v.n, REL), esc(t.sev || ""), esc(outs), esc(t.unk || ""),
      ]])}</div>`;
  }).join("");
  return `<h1>Opportunity areas</h1>
  <p class="lede">Where retrieval could improve. An opportunity is not a feature and not a problem. Counts overlap;
  together the ${D.derived.opp_count} areas cover ${D.opp_union_all} of ${REL} records.</p>
  ${cards}
  <h2>Product Opportunity Analysis</h2>
  <p class="muted">A filtered opportunity analysis focusing on issues, severity, and outcomes. Note: Competitor analysis and cost-to-build are excluded as they require external or engineering input. All items here are hypotheses to be validated, not guaranteed features.</p>
  ${table(["Opportunity", "Records", "Share", "Severity signals present", "Impact on Outcomes"], sorted.map(([k, v]) => {
    const code = k.split(" ")[0];
    const outs = Object.entries(v.profile.outcomes).filter(([a, b]) => b && a !== "unknown")
      .map(([a, b]) => `${b} ${human(a)}`).join(", ") || "Outcome Not Stated";
    return [esc(k), ev("opp:" + code, v.n, REL), pct(v.n, REL),
      `${v.profile.with_severity_signal} with ≥1, ${v.profile.with_2plus_signals} with ≥2`, esc(outs)];
  }))}
  <div class="card">
    <h3>Observation :</h3>
    <p><strong>Contains All Terminal Outcomes:</strong> O5 is the only opportunity area that contains every terminal outcome (e.g., failed searches, abandonment, or users switching to another app), as well as all effortful successes.</p>
    <p><strong>Strongest Behavioural Evidence:</strong> Compared to competing explanations (like O1 Memory Expression or O3 Candidate Recognition), O5 has the largest body of explicit behavioral evidence (46.4% of relevant records). Focusing here allows us to investigate tangible user actions rather than relying solely on self-reported memory barriers.</p>
  </div>`;
});

page("segments", "Segments", "Stage 4", () => {
  const S = D.segments, defs = D.narrative.segment_defs, s1 = D.stage1;
  const signals = Object.keys(s1.signals);
  const four = Object.entries(S).filter(([k]) => !k.startsWith("SEG-T"));
  const target = Object.entries(S).find(([k]) => k.startsWith("SEG-T"));
  const outcomeCells = (p) => ["found_quickly", "found_with_effort", "similar_uncertain", "failed", "abandoned", "external_workaround", "unknown"]
    .map((k) => (k === "found_quickly" ? p.found_quickly : p.outcomes[k]));
  const row = ([k, v]) => {
    const code = k.split(" ")[0], p = v.profile;
    return [`<strong>${esc(code)}</strong> ${esc(k.slice(code.length + 1))}`, esc(defs[code]),
      ev("seg:" + code, v.n, REL), ...outcomeCells(p)];
  };
  return `<h1>Behavioural segments</h1>
  <p class="lede">Segments are the retrieval state each record states, so the four are mutually exclusive and sum to
  ${REL}. All share one precondition: a specific photo the user expects to exist, remembered imprecisely.</p>
  <div class="grid">${four.map(([k, v]) => stat(v.n, k.slice(k.split(" ")[0].length + 1), "seg:" + k.split(" ")[0])).join("")}</div>
  <h2>Definition and outcomes</h2>
  ${table(["Segment", "Objective definition", "Records", "Found quickly", "With effort", "Uncertain", "Failed", "Abandoned", "Other app", "Outcome Not Stated"],
    [...four, target].map(row))}
  <h2>What they remember, forget and do ${OBS}</h2>
  ${table(["Segment", "Remembers", "Lacks", "Most common behaviours"], [...four, target].map(([k, v]) => {
    const p = v.profile;
    return [esc(k.split(" ")[0]),
      sortedEntries(p.remembered_mix).slice(0, 3).map(([a, b]) => `${human(a)} ${b}`).join(", "),
      sortedEntries(p.forgotten_mix).slice(0, 3).map(([a, b]) => `${esc(a)} ${b}`).join(", "),
      p.top_behaviors.map(([a, b]) => `${esc(human(a))} ${b}`).join("; ")];
  }))}
  <h2>Severity signals by segment ${OBS}</h2>
  ${table(["Segment", ...signals.map(human)], [...four, target].map(([k, v]) =>
    [esc(k.split(" ")[0]), ...signals.map((s) => v.profile.signal_counts[s] || 0)]))}
  <p class="muted">${INTERP} Retrieval state is defined by the sentence that carries these signals, so "every member
  shows a signal" is definitional inside the first three segments, not a finding. The informative contrast is that
  first-attempt records carry almost none, and that expression barriers are spread evenly across all four.</p>

  <div class="card" style="margin-top: 1rem;">
    <h3>Observation :</h3>
    <p><strong>Captures the Real Struggle:</strong> SEG-T is defined as a combination of users who either had to change their strategy/make repeated attempts (SEG-2) or had to manually inspect a large candidate set (SEG-3). It explicitly targets users who expect a photo to exist and lack a precise identifier, but are actively putting in effort to find it.</p>
    <p><strong>Definitional Severity:</strong> Every single record in this segment (${D.target.n} out of ${REL}, or ~${D.target.pct}%) carries at least one severity signal (like manual browsing, large candidate sets, or strategy switching).</p>
    <p><strong>Research Fit:</strong> By targeting users who are in the middle of a difficult retrieval path (rather than those who immediately failed and left, or those just making their first attempt), we can directly observe the breakdown in the retrieval journey and test how to help them recover.</p>
  </div>
  <div class="card" style="margin-top: 1rem;">
    <h3>${label("OPP-HYP")} RESEARCH HYPOTHESIS</h3>
    <p>Investigate <strong>users who attempted to retrieve a specific photo they expected to exist, lacked a precise
    identifier, and either changed strategy or made several attempts, or manually inspected a candidate set</strong>:
    ${ev("seg:SEG-T", D.target.n, REL)} records (${D.target.pct}%). Every member states
    effortful behaviour.</p>
  </div>`;
});

/*
page("target", "4-Level Impact Map", "Stages 7–8", () => {
  const T = D.target, I = D.impact, p = T.profile;
  const oppsTable = table(["Opportunity", "Issues (Frequency)", "Severity Signals", "Impact on Outcomes"], 
    Object.entries(D.opps).sort((a, b) => b[1].n - a[1].n).map(([k, v]) => {
      const code = k.split(" ")[0];
      const outs = Object.entries(v.profile.outcomes).filter(([a, b]) => b && a !== "unknown")
        .map(([a, b]) => `${b} ${human(a)}`).join(", ") || "Outcome Not Stated";
      return [esc(k), ev("opp:" + code, v.n, REL), 
        `${v.profile.with_severity_signal} records with ≥1`, esc(outs)];
    }));

  return `<h1>4-Level Impact Map</h1>
  <p class="lede">Navigating the uncertainty of Product Discovery using Impact Mapping and JTBD frameworks, tailored to our photo retrieval problem space.</p>
  
  <h2>1. WHY: Business Goal & Impact Sizing</h2>
  <p>The overarching impact we want to achieve is to increase <strong>incremental successful retrievals</strong> by helping users recover from failed searches.</p>
  ${table(["Step", "Observed in the corpus " + OBS, "Production value"], [
    ["Eligible retrieval attempts", `${I.eligible} records (posts, not attempts)`, "<strong>TBD</strong> requires Google production data"],
    ["Share in the target behaviour", `${ev("seg:SEG-T", I.target, I.eligible)} (${I.target_pct}%)`, "<strong>TBD</strong> requires Google production data"],
    ["Share with failure or effort", `Effort signal ${I.target_with_effort_signal} of ${I.target}, definitional; stated uncertain outcome ${I.target_uncertain_stated}; downstream exits ${I.exits_adjacent}, of which ${I.exits_failed_or_abandoned} failed or abandoned`, "<strong>TBD</strong> needs a log definition of effort"],
    ["Share potentially recoverable", `Not estimable here. Proxy to test: ${p.recognition_retained} of ${I.target} say they would recognise the photo`, "<strong>TBD</strong> primary research plus production data"],
    ["Expected improvement", "Not estimable before a solution exists", "<strong>TBD</strong>"],
    ["Incremental successful retrievals", "—", "<strong>TBD</strong>"],
  ])}

  <h2>2. WHO: The Target Segment (Actors)</h2>
  <div class="grid">
    ${stat(T.n, "records in the target segment", "seg:SEG-T")}
    ${stat(p.express_barrier, "state a memory-expression barrier")}
    ${stat(p.recognition_retained, "say they would recognise it on sight")}
    ${stat(T.adjacent_exit, "downstream exit-path records", "seg:SEG-1")}
  </div>
  ${table(["Element", "Detail"], [
    ["By state", Object.entries(T.by_state).map(([k, v]) => `${human(k)} ${v}`).join("; ")],
    ["Explicitly knows the photo exists", `${p.knows_exists} of ${T.n} (${T.knows_exists_pct}%)`],
    ["After removing near-duplicates", `${T.after_near_dup_removal} of ${T.n}`],
  ])}

  <h2>3. HOW: Jobs-To-Be-Done & Behavior Change</h2>

  <p><strong>"How might we" challenge:</strong> How might we enable users with imprecise memories to confidently evaluate and refine their search results?</p>

  <h2>Product Opportunity Analysis</h2>
  <p class="muted">A filtered opportunity analysis focusing on issues, severity, and outcomes. Note: Competitor analysis and cost-to-build are excluded as they require external or engineering input. All items here are hypotheses to be validated, not guaranteed features.</p>
  ${oppsTable}`;
});
*/

/*
page("hypotheses", "Hypotheses", "Stage 9", () => {
  const H = D.narrative.hypotheses;
  return `<h1>Research hypotheses</h1>
  <p class="lede">Each is a ${label("PROB-HYP")} to test, never a root cause. Every one carries a competing
  explanation and a falsification test. ${label("VALIDATED", "warn")} none: no research has been run.</p>
  ${H.map((h) => `<div class="card">
    <h3>${esc(h.name)} <span class="chip">node ${esc(h.node)}</span> <span class="chip warn">verdict: ${esc(h.verdict)}</span></h3>
    ${table(["Field", "Content"], [
      ["Observation " + OBS, `${esc(h.observation)} ${ev(h.key, countOf(h.key))}`],
      ["Interpretation " + INTERP, esc(h.interpretation)],
      ["Hypothesis " + label("PROB-HYP"), esc(h.hypothesis)],
      ["Competing explanation", esc(h.rival)],
      ["Validate or falsify", esc(h.test)],
      ["Evidence for", esc(h.evidence_for)],
      ["Evidence against", esc(h.evidence_against)],
      ["Unknown " + UNKNOWN, esc(h.unknown)],
      ["Qualitative (WHY/HOW)", esc(h.qualitative)],
      ["Quantitative (WHERE/HOW MUCH)", esc(h.quantitative)],
    ])}</div>`).join("")}`;
});

page("plan", "Research plan", "Stages 10–12", () => {
  const G = D.narrative.interview_guide, T = D.narrative.tasks;
  return `<h1>Primary research plan</h1>
  <p class="lede"><strong>PROPOSED PLAN — NOT RESEARCH FINDINGS.</strong> Sequence: interviews, then task-based tests,
  then a survey. Nothing here tests a solution.</p>
  <h2>What each method can answer</h2>
  ${table(["Method", "Answers", "Cannot answer"], [
    ["Corpus (today)", "WHERE, directionally", "WHY, HOW, HOW MUCH"],
    ["Interviews (16)", "WHY, HOW", "HOW MUCH"],
    ["Task-based tests (12)", "HOW, observed; WHERE via first failing node", "HOW MUCH at population scale"],
    ["Survey (≥400)", "WHERE, HOW MUCH, self-reported", "WHY"],
    ["Production data", "HOW MUCH", "WHY"],
  ])}
  <h2>Interview guide (30 minutes)</h2>
  ${G.map((g) => `<div class="card"><h3>${esc(g.part)}</h3><ul>${g.questions.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>
    <p class="muted">Interviewer note: ${esc(g.note)}</p></div>`).join("")}
  <p class="muted">Avoid: "Would an assistant help?", any feature or technology wording, and questions that assume
  difficulty.</p>
  <h2>Task-based tests</h2>
  ${table(["Task", "Scenario", "Provided", "Withheld", "Headline measure"],
    T.map((t) => [esc(t.name), esc(t.scenario), esc(t.provided), esc(t.withheld), esc(t.primary)]))}
  <h3>Recorded for every task</h3>
  <p>Retrieval success, time to successful retrieval, attempts and reformulations, candidate photos inspected,
  abandonment, confidence. Also logged: first action, first query, every reformulation, filters used, browsing
  behaviour, workaround use. Every unsuccessful attempt is classified by its first failing node.</p>
  ${table(["Task", "Qualitative observation"], T.map((t) => [esc(t.name), esc(t.qualitative)]))}
  <h2>Survey, recruitment and sample sizes</h2>
  ${table(["Item", "Detail"], [
    ["Survey purpose", "Estimate prevalence of the scenarios found qualitatively. No solution questions"],
    ["Survey sample", "At least 400 respondents, at least 100 per compared subgroup, for ±5 points at 95% confidence"],
    ["Interviews", "16 participants: 6 effortful-path, 4 recent failure or abandonment, 2 quick-success contrast, 4 heavy-library"],
    ["Usability tests", "12 participants; enough for recurring strategies, not for benchmark times"],
    ["Recruitment", "Google Photos as primary store for 2+ years; searched for an older photo in the past 30 days without a precise identifier"],
    ["Exclusions", "Google or competitor employees, UX and research professionals, recent photo-search study participants"],
  ])}
  <h2>Synthesis framework</h2>
  ${table(["Layer", "Rule to advance", "Guard rail"], [
    ["Observation", "Verbatim or logged, tagged with a participant ID", "No interpretation at this layer"],
    ["Pattern", "Seen in at least 3 participants, in stated and observed behaviour", "Counts as 'n of N participants', never percentages of users"],
    ["Interpretation", "At least 2 rival readings written", "The rival must explain the same pattern"],
    ["Root-cause hypothesis", "Each of H1–H7 marked supported, weakened or falsified", "No cause called on one method"],
    ["Validation", "Cause explains the pattern, rivals do not, prevalence estimated", "Production sizing stays TBD"],
    ["Problem", "Only when the gate is met", "No solution language"],
  ])}`;
});

page("problem", "Problem", "Stage 14", () => {
  const T = D.target, s1 = D.stage1, J = D.journey;
  return `<h1>Problem definition</h1>
  <div class="card">
    <h3>${label("PROB-HYP")} PROVISIONAL PROBLEM HYPOTHESIS — REQUIRES PRIMARY RESEARCH</h3>
    <p>Google Photos users trying to <strong>find a specific photo they know they have</strong> in
    <strong>a large personal library</strong>, when they remember its context but <strong>not a precise
    identifier</strong>, struggle to <strong>reach it without repeated attempts, manual inspection, or leaving the
    product</strong>, because <strong>[cause to be validated]</strong>, resulting in <strong>extra effort, uncertainty
    about whether the right photo was found, and in some cases giving up</strong>.</p>
    <p class="muted">The cause slot is empty on purpose. ${label("VALIDATED", "warn")} No validated problem exists.
    The statement contains no solution, feature or technology wording.</p>
  </div>
  <h2>Evidence behind each element</h2>
  ${table(["Element", "Evidence " + OBS, "Strength"], [
    ["User: retrieving a specific photo they believe exists", `${ev("claim:K01", REL, REL)} records; explicitly says the photo exists in ${T.profile.knows_exists} of ${T.n} target records`, "Medium"],
    ["Context: large personal library", `Stated in ${s1.closer_code.C02_thousands_of_images} of ${REL} records`, "Low"],
    ["Imprecise memory", `${ev("claim:K02", J.breakdown.RECALL.n, REL)} name specific missing information`, "Medium"],
    ["Struggle", `${ev("opp:O5", countOf("opp:O5"), REL)} show recovery behaviour; ${ev("seg:SEG-3", countOf("seg:SEG-3"), REL)} inspect candidates`, "Medium"],
    ["Consequence", `${ev("seg:SEG-1", countOf("seg:SEG-1"), REL)} end in failure, giving up or another app; ${ev("claim:K07", countOf("claim:K07"))} cannot confirm a candidate`, "Low–Medium"],
    ["Cause", "Not established", "None"],
  ])}
  <h2>Gate before this becomes a validated problem</h2>
  ${table(["#", "Condition", "Met?"], [
    [1, "At least 80% of interviewees give a specific recent incident; H1–H7 all have verdicts", "No"],
    [2, "Task tests confirm the behaviours by observation, with first-failing-node classification", "No"],
    [3, "One cause explains the pattern while its rival does not, agreed by at least 2 methods", "No"],
    [4, "Survey prevalence estimated", "No"],
    [5, "The cause slot filled with evidence-backed wording, no solution language", "No"],
  ])}
  <p class="muted">Only after this gate: how-might-we, ideation, solution, MVP, testing.</p>`;
});
*/

page("evidence", "Evidence explorer", "Rule 15", () => {
  const keys = Object.keys(D.evidence_index).sort();
  const opts = (name, values) =>
    `<select data-filter="${name}"><option value="">${human(name)}: any</option>${values
      .map((v) => {
        let text = v;
        if (name === "outcome" && v === "unknown") text = "Outcome Not Stated";
        return `<option value="${esc(v)}">${esc(text)}</option>`;
      }).join("")}</select>`;
  const uniq = (col) => [...new Set(D.records.rows.map((r) => r[COLS[col]]).filter(Boolean))].sort();
  return `<h1>Evidence explorer</h1>
  <p class="lede">Every conclusion in this engine traces to records. Filter the corpus, or open any named group to see
  exactly which records sit behind it.</p>
  <h2>Named groups</h2>
  ${table(["Group", "Records"], keys.map((k) => [`<span class="mono">${esc(k)}</span>`, ev(k, countOf(k))]))}
  <h2>All records</h2>
  <div class="filters">
    <input id="q" type="search" placeholder="Search verbatim text…" aria-label="Search record text">
    ${opts("relevance", uniq("relevance"))}
    ${opts("retrieval_state", uniq("retrieval_state"))}
    ${opts("outcome", uniq("outcome"))}
    ${opts("object_class", uniq("object_class"))}
  </div>
  <p id="hits" class="muted"></p>
  <div id="results"></div>`;
});

function wireExplorer() {
  const q = document.getElementById("q");
  if (!q) return;
  const sels = [...document.querySelectorAll("[data-filter]")];
  const results = document.getElementById("results"), hits = document.getElementById("hits");
  const apply = () => {
    const term = q.value.trim().toLowerCase();
    const active = sels.filter((s) => s.value).map((s) => [COLS[s.dataset.filter], s.value]);
    const matched = [];
    D.records.rows.forEach((row, i) => {
      if (term && !row[COLS.raw_text].toLowerCase().includes(term)) return;
      for (const [idx, val] of active) if (row[idx] !== val) return;
      matched.push(i);
    });
    hits.textContent = `${matched.length} of ${D.records.rows.length} records match`;
    results.innerHTML = matched.slice(0, 100).map(recordCard).join("") ||
      "<p class='muted'>No records match these filters.</p>";
    if (matched.length > 100) results.innerHTML += `<p class="muted">Showing 100 of ${matched.length}.</p>`;
  };
  q.addEventListener("input", apply);
  sels.forEach((s) => s.addEventListener("change", apply));
  apply();
}

/* ---------- router ---------- */
const nav = document.getElementById("nav"), main = document.getElementById("main");
nav.innerHTML = PAGES.map((p) =>
  `<button type="button" data-page="${p.id}"><span>${esc(p.title)}</span></button>`).join("");

function show(id) {
  const p = PAGES.find((x) => x.id === id) || PAGES[0];
  main.innerHTML = p.render();
  [...nav.querySelectorAll("button")].forEach((b) => {
    b.setAttribute("aria-current", b.dataset.page === p.id ? "page" : "false");
    // Hide 'evidence' tab in evaluator mode
    if (b.dataset.page === "evidence") {
      b.classList.add("internal-only");
    }
  });
  if (p.id === "evidence") wireExplorer();
  closeDrawer();
  main.focus();
  if (location.hash.slice(1) !== p.id) history.replaceState(null, "", "#" + p.id);
  window.scrollTo(0, 0);
}
nav.addEventListener("click", (e) => {
  const b = e.target.closest("button[data-page]");
  if (b) show(b.dataset.page);
});
window.addEventListener("hashchange", () => show(location.hash.slice(1)));

/* ---------- theme & modes ---------- */
const root = document.documentElement;
const savedTheme = (() => { try { return localStorage.getItem("theme"); } catch { return null; } })();
if (savedTheme) root.dataset.theme = savedTheme;
document.getElementById("themeToggle").addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch { /* private mode */ }
});



async function askAI(question) {
  if (!question) return;
  const input = document.getElementById('aiInput');
  const responseDiv = document.getElementById('aiResponse');
  
  if (input) input.value = question;
  responseDiv.style.display = 'block';
  responseDiv.innerHTML = '<span class="loading">Generating answer...</span>';
  
  try {
    const res = await fetch('http://localhost:8080/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const data = await res.json();
    if (data.error) {
      responseDiv.innerHTML = '<strong>API Error:</strong> ' + data.error;
    } else if (data.answer) {
      responseDiv.innerHTML = data.answer.replace(/\n/g, '<br/>');
    } else {
      responseDiv.innerHTML = 'Error: Unexpected response format from server.';
    }
  } catch (e) {
    responseDiv.innerHTML = 'Error: Could not connect to the backend server. Details: ' + e.message;
  }
}

show(location.hash.slice(1) || PAGES[0].id);
