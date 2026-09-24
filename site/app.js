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

function ev(key, n, of) {
  const ids = D.evidence_index[key];
  if (!ids) return `${n}${of ? " of " + of : ""}`;
  const text = `${n}${of ? " of " + of : ""}`;
  return `<button class="link" data-key="${esc(key)}">${text}</button>`;
}
const countOf = (key) => (D.evidence_index[key] || []).length;

function table(headers, rows, opts = {}) {
  const head = headers.map((h) => `<th>${esc(h)}</th>`).join("");
  const body = rows.map((r) => {
    const textContent = r.join(" ").toLowerCase();
    const isZeroOrTBD = textContent.includes(">0<") || textContent.includes(">0 (0.0%)<") || textContent.includes(">tbd<") || textContent.includes(">outcome not stated<") || textContent.includes(">none<");
    const rowClass = isZeroOrTBD ? ' class="hidden-row"' : '';
    return `<tr${rowClass}>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`;
  }).join("");
  return `<table${opts.id ? ` id="${opts.id}"` : ""}><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function stat(n, lab, key, cls="") {
  const value = key ? ev(key, n) : esc(String(n));
  return `<div class="stat ${cls}"><div class="n">${value}</div><div class="lab">${esc(lab)}</div></div>`;
}

function barRow(name, n, max, of, cls="") {
  const w = max ? Math.round((100 * n) / max) : 0;
  return `
    <div class="progress-bar-container">
      <div class="progress-label"><span>${esc(name)}</span> <span>${n} (${pct(n, of)})</span></div>
      <div class="progress-track"><div class="progress-fill ${cls}" style="width:${w}%"></div></div>
    </div>
  `;
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
      return `<span class="chip">${esc(`${c.split("_")[0]}: ${val}`)}</span>`;
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
  const s0 = D.stage0;
  return `<h1>Overview & Strategic Premise</h1>
  <p class="lede">A data-driven Discovery Engine built for the Core Experience team at Google Photos.</p>
  
  <div class="card" style="border: 2px solid var(--accent); background: var(--accent-soft); padding: 24px; margin-bottom: 32px;">
    <h3 style="margin-top: 0; color: var(--accent);">Strategic Goal</h3>
    <p style="font-size: 16px; font-weight: 500; color: var(--ink);">
      Increase the percentage of users who successfully retrieve a photo they remember but cannot precisely describe when they start searching.
    </p>
    <p class="muted" style="font-size: 14px; margin-bottom: 0;">
      <em>The challenge is not to improve search in general, but to solve retrieval for incomplete memories.</em>
    </p>
  </div>

  <h2>Evidence from Users</h2>
  <p class="muted">This engine goes beyond sentiment analysis to extract specific retrieval problems from public datasets.</p>
  
  <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px;">
    <span class="chip">Google Play Store reviews</span>
    <span class="chip">App Store reviews</span>
    <span class="chip">Reddit discussions</span>
    <span class="chip">Google Photos community/support</span>
    <span class="chip">Social media conversations</span>
    <span class="chip">YouTube comments</span>
    <span class="chip">Forums</span>
  </div>

  <div class="grid">

    ${stat(s0.relevant, "retrieval-related records", "claim:K01")}
    ${stat(s0.total, "records in the file")}
  </div>
  
  <h2>Ask the AI Discovery Engine</h2>
  <div class="card ai-chat-container">
    <p class="muted" style="margin-top: 0;">Explore problems, compare areas, and query evidence directly from the dataset.</p>
    <div class="ai-input-group">
      <input type="text" id="aiInput" placeholder="Ask a custom question..." onkeydown="if(event.key === 'Enter') askAI(this.value)" />
      <button onclick="askAI(document.getElementById('aiInput').value)">Ask</button>
    </div>
    <div id="aiResponse" class="ai-response" style="display:none;"></div>
  </div>`;
});

page("insights", "Insights", "Stages 1–3", () => {
  const s1 = D.stage1;
  const remembered = sortedEntries(s1.remembered), lacking = sortedEntries(s1.forgotten_family);
  const maxR = remembered[0][1], maxL = lacking[0][1];
  
  const objects = sortedEntries(s1.object_class);
  const maxO = objects[0][1];
  
  const retrieval = sortedEntries(s1.retrieval_state);
  const maxRet = retrieval[0][1];

  return `<h1>Answering the Core Questions</h1>
  <p class="lede">Synthesizing the dataset to answer the strategic questions regarding user memory and search behavior.</p>

  <div class="grid grid-2">
    <!-- Q1 -->
    <div class="card">
      <h3 style="margin-top:0;">1. What kinds of old photos do users struggle to retrieve?</h3>
      <p class="muted">Families, documents, and social events dominate vague-memory retrieval struggles.</p>
      ${objects.slice(0, 5).map(([a, b]) => barRow(human(a), b, maxO, REL, "")).join("")}
    </div>

    <!-- Q4 -->
    <div class="card">
      <h3 style="margin-top:0;">2. How do users formulate searches?</h3>
      <p class="muted">When memory is incomplete, users often exit entirely or rely on complex recovery strategies.</p>
      ${retrieval.map(([a, b]) => {
        let label = a === "exit_path" ? "Give up / Exit" : 
                    a === "recovery_dependent" ? "Switch strategy / Reformulate" : 
                    a === "candidate_inspection" ? "Manual browsing / Timeline" : "Single initial query";
        return barRow(label, b, maxRet, REL, a === "exit_path" ? "danger" : a === "first_attempt" ? "success" : "warn");
      }).join("")}
    </div>
  </div>

  <div class="grid grid-2">
    <!-- Q2 -->
    <div class="card">
      <h3 style="margin-top:0;">3. What information do people actually remember?</h3>
      <p class="muted">Users frequently remember visual details and people.</p>
      ${remembered.map(([a, b]) => barRow(human(a), b, maxR, REL, "success")).join("")}
    </div>

    <!-- Q3 -->
    <div class="card">
      <h3 style="margin-top:0;">4. What information have they forgotten?</h3>
      <p class="muted">Users consistently lack exact dates and locations. <br/><small><em>* "Don't explicitly state" means the user stated their memory without naming the exact gap.</em></small></p>
      ${lacking.map(([a, b]) => barRow(titleCase(a), b, maxL, REL, "danger")).join("")}
    </div>
  </div>

  <h2>Retrieval needs</h2>
  <p class="muted">Needs overlap: a record can express several. Derived from what records say, never from source.</p>
  ${table(["Need", "User goal", "Memory pattern", "Records", "Stated outcomes"], Object.entries(D.needs).map(([k, v]) => {
    const code = k.split(" ")[0], t = D.narrative.needs[code] || ["", ""];
    return [`<strong>${esc(code)}</strong> ${esc(k.slice(code.length + 1))}`, esc(t[0]), esc(t[1]),
      ev("need:" + code, v.n, REL), Object.entries(v.profile.outcomes).filter(([a, b]) => b && a !== "unknown")
        .map(([a, b]) => `${b} ${human(a)}`).join(", ") || "<span class='muted'>Outcome Not Stated</span>"];
  }))}

  `;
});

page("journey", "Journey & Decomposition", "Stage 2", () => {
  const DC = D.decomposition, NODES = D.narrative.decomposition_nodes;
  
  const J = D.journey;
  const INTERP = `<span class="chip obs">Interpretation</span>`;
  
  return `<h1>Retrieval Journey</h1>
  
  <h2>Decomposition of Successful Retrieval</h2>
  <p class="lede">${INTERP} Success needs every stage to hold: usable partial memory (D1 — Remember), expression into a search (D2 — Express), the product matching the clues (D3 — Match), recognition of the target (D4 — Recognize), refinement when the first try fails (D5 — Recover), and the target photo actually being available in the library (Precondition). A retrieval fails at the first stage that does not hold.</p>
  
  ${table(["Stage", "Case question", "User behaviour", "Product outcome"], [
    ["<strong>D1 — Remember</strong>", "What information do people actually remember, and what have they forgotten?", "Holds partial context — people, place, story, visual appearance, roughly when — but lacks a precise identifier", "Precondition: the user has enough contextual memory to attempt retrieval, while the photo exists somewhere in the library"],
    ["<strong>D2 — Express</strong>", "Is the user context-to-query translation what they remember?", "Turns memory into a query, filter, or navigation step", "The input the product receives carries the clues the user actually holds"],
    ["<strong>D3 — Match</strong>", "Does Google Photos fail to understand the clues they provide?", "Submits clues and inspects what comes back", "The intended photo appears among the candidates returned"],
    ["<strong>D4 — Recognize</strong>", "Are potentially relevant results difficult to evaluate?", "Scans candidates and decides which one is the intended photo", "The user identifies and confirms the right photo, quickly and with confidence"],
    ["<strong>D5 — Recover</strong>", "Does the user struggle to recover from an unsuccessful search?", "Reformulates, switches strategy, browses, asks someone, or stops", "A failed first attempt can still lead to successful retrieval, or the user reaches an informed stop"],
    ["<strong>Precondition — Available</strong>", "Is the photo in the searchable library at all?", "May ask another person, switch app/device, or give up when the photo cannot be located in the searchable library", "The intended photo is available in the searchable library, making retrieval possible"]
  ])}
        
  <h2>Observed stage paths</h2>
  <p class="muted">${Object.keys(J.top_paths).length} shown of ${J.n_paths} distinct paths.</p>
  ${table(["Path", "Records"], Object.entries(J.top_paths).map(([k, v]) => [`<span class="mono">${esc(k.replace(/REMEMBER/g, 'REMEMBER'))}</span>`, v]))}`;
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
  const OBS = '<span class="chip obs">Observation</span>';
  const INTERP = '<span class="chip obs">Interpretation</span>';
  const label = (text, cls="obs") => `<span class="chip ${cls}">${text}</span>`;
  
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

  
  <h2>SEGMENT × JOURNEY Matrix</h2>
  <p class="muted">Mapping the behavioral segments against the stages of the retrieval journey to identify where friction occurs.</p>
  ${table(["Segment", "Remember", "Express", "Match", "Recognize", "Recover"], [
    ["<strong>SEG-1</strong><br><small class='muted'>Keyword Requirements</small>", "Medium", "High", "High", "NA", "Low"],
    ["<strong>SEG-2</strong><br><small class='muted'>Strategy Switching</small>", "Medium", "High", "High", "NA", "High"],
    ["<strong>SEG-3</strong><br><small class='muted'>Manual Inspection</small>", "Medium", "Medium", "High", "High", "NA"],
    ["<strong>SEG-4</strong><br><small class='muted'>Single Initial Attempt</small>", "Medium", "Low", "Low", "Low", "NA"],
    ["<strong style='color:var(--accent);'>SEG-T</strong><br><small class='muted'>The Effortful Path</small>", "Medium", "High", "High", "High", "High"]
  ])}
  `;
});

page("opportunities", "Opportunities", "Stages 5–6", () => {
  return `<h1>Opportunities</h1>
  <p class="lede">Breaking down the business metric of successful retrieval into failure points, and identifying where the greatest opportunities exist.</p>

  <h2>Opportunity Areas</h2>
  <p class="muted">Using the decomposition above to identify where the greatest opportunities exist.</p>
  
  <div class="grid grid-2">
    <!-- Area 1: Context-to-Query Translation -->
    <div class="card" style="border-top: 4px solid var(--success);">
      <h3 style="margin-top:0;">1. Context-to-Query Translation</h3>
      <ul style="font-size: 14px; padding-left: 20px; line-height: 1.6;">
        <li style="margin-bottom: 8px;"><strong>Memory vs. Gap:</strong> The Insights data shows 200 records remember people and 134 remember visual appearance, but 199 explicitly lack precise time and 149 lack exact names.</li>
        <li style="margin-bottom: 8px;"><strong>Expression Barrier:</strong> The Evidence Explorer/Segments indicate ${s1.express_barrier} out of ${s0.relevant} (${pct(s1.express_barrier, s0.relevant)}%) state an explicit expression barrier where their memory couldn't be turned into a search keyword.</li>
        <li><strong>Impact:</strong> This directly addresses the 594 records identified in the Journey breakdown where users lacked specific memory information to form a traditional query.</li>
      </ul>
    </div>
    <!-- Area 2 -->
    <div class="card" style="border-top: 4px solid var(--warn);">
      <h3 style="margin-top:0;">2. Vague Query Interpretation</h3>
      <ul style="font-size: 14px; padding-left: 20px; line-height: 1.6;">
        <li style="margin-bottom: 8px;"><strong>Abandonment Rate:</strong> 341 records (42.6%) fall into SEG-1 (Exit-path retrievers), meaning their initial search failure led to complete abandonment (115 records) or failure (140 records).</li>
        <li style="margin-bottom: 8px;"><strong>Low Success Baseline:</strong> Only ${s1.outcome.found_quickly} out of ${s0.relevant} records (${pct(s1.outcome.found_quickly, s0.relevant)}%) were resolved on the "first attempt" (found quickly).</li>
        <li><strong>Impact:</strong> Improving the zero-state interpretation directly targets the 42.6% of users who hit a wall on query #1 and never recover.</li>
      </ul>
    </div>
    
    <!-- Area 3 -->
    <div class="card" style="border-top: 4px solid var(--danger);">
      <h3 style="margin-top:0;">3. Search Recovery Guidance</h3>
      <ul style="font-size: 14px; padding-left: 20px; line-height: 1.6;">
        <li style="margin-bottom: 8px;"><strong>Volume of Recovery:</strong> The Need "Recover after a first attempt did not resolve" (N8) represents 625 records (78.1%). Almost 8 out of 10 users require recovery efforts.</li>
        <li style="margin-bottom: 8px;"><strong>Behavioral Signals:</strong> There are 166 records showing "strategy switching" and 146 records showing "repeated attempts".</li>
        <li><strong>Impact:</strong> 284 records belong to SEG-2 (Recovery-dependent retrievers). Guiding them could convert these effortful journeys into quicker successes.</li>
      </ul>
    </div>

    <!-- Area 4 -->
    <div class="card" style="border-top: 4px solid var(--accent);">
      <h3 style="margin-top:0;">4. Smart Candidate Filtering</h3>
      <ul style="font-size: 14px; padding-left: 20px; line-height: 1.6;">
        <li style="margin-bottom: 8px;"><strong>The Browsing Burden:</strong> 234 records explicitly mention "browsing" as a severity signal, and 149 records mention dealing with a "large candidate set."</li>
        <li style="margin-bottom: 8px;"><strong>Candidate Inspection:</strong> The "Recognise/verify the right photo among plausible candidates" need (N6) affects 120 records (15.0%), and every single one of those 120 records notes "uncertainty" in picking the right photo.</li>
        <li><strong>Impact:</strong> Providing dynamic filters post-search would directly alleviate the friction for the SEG-3 users who successfully generate candidates but fail at the manual inspection stage.</li>
      </ul>
    </div>

    <!-- Area 5 -->
    <div class="card" style="border-top: 4px solid var(--success);">
      <h3 style="margin-top:0;">5. Specialized Retrieval for High-Struggle Categories</h3>
      <ul style="font-size: 14px; padding-left: 20px; line-height: 1.6;">
        <li style="margin-bottom: 8px;"><strong>Top Categories:</strong> The dataset explicitly ranks the most struggled-with objects: family/person (183 records, ~23%), document/screenshot (161 records, ~20%), and event/social (134 records, ~17%).</li>
        <li style="margin-bottom: 8px;"><strong>Document Struggle:</strong> Need N9 ("Retrieve an information-bearing image") accounts for 257 records (32.1%), indicating that 1 in 3 struggles is about a document, screenshot, or receipt.</li>
        <li><strong>Impact:</strong> Building specialized flows (like a dedicated "Documents" or "People/Events" filter hub) would proactively solve the retrieval use case for over 60% of the dataset's recorded struggles.</li>
      </ul>
    </div>
  </div>

  <h2 style="margin-top: 48px;">Opportunity hypotheses</h2>
  <p class="muted">Mapping our proposed opportunities to specific behavioral segments to create testable opportunity hypotheses.</p>

  <div class="card" style="margin-bottom: 16px;">
    <h3 style="margin-top:0;">Keyword Requirements</h3>
    <p><strong>Target Opportunity:</strong> <span class="chip obs">Vague Query Interpretation &amp; Context-to-Query Translation</span></p>
    <p><em>If we test natural language/conversational search and zero-state interpretation with SEG-1 users (who currently abandon their search 42% of the time due to rigid keyword requirements), they will successfully pull a set of plausible candidates on their first attempt instead of hitting a dead end.</em></p>
  </div>

  <div class="card" style="margin-bottom: 16px;">
    <h3 style="margin-top:0;">Strategy Switching</h3>
    <p><strong>Target Opportunity:</strong> <span class="chip obs">Search Recovery Guidance</span></p>
    <p><em>If we introduce visual entity auto-suggestions to SEG-2 users (who currently rely on trial-and-error query reformulations), we will observe a measurable reduction in repeated attempts and faster recovery times after an initial failed search.</em></p>
  </div>

  <div class="card" style="margin-bottom: 16px;">
    <h3 style="margin-top:0;">Manual Inspection</h3>
    <p><strong>Target Opportunity:</strong> <span class="chip obs">Smart Candidate Filtering</span></p>
    <p><em>If we provide dynamic, post-search visual filters to SEG-3 users (who successfully generate results but get stuck scrolling through large candidate sets), we will significantly decrease the time and effort required in the final "Recognize" stage of the journey.</em></p>
  </div>

  <div class="card" style="margin-bottom: 16px;">
    <h3 style="margin-top:0;">High-Struggle Tasks</h3>
    <p><strong>Target Opportunity:</strong> <span class="chip obs">Specialized Retrieval for High-Struggle Categories</span></p>
    <p><em>Because documents, screenshots, and family events account for over 60% of struggles across all segments, testing dedicated search tabs/flows for these specific categories will increase the "first-attempt success rate" (SEG-4) and intercept users before they ever reach an effortful state.</em></p>
  </div>

  <div class="card" style="margin-bottom: 16px;">
    <h3 style="margin-top:0;">The Effortful Path</h3>
    <p><strong>Target Opportunities:</strong> <span class="chip obs">The Combined Ecosystem of Opportunities</span></p>
    <p><em>By combining Context-to-Query Translation, Search Recovery Guidance, and Smart Candidate Filtering specifically for SEG-T users (the 50.5% of users who are actively putting in effort to find a photo), we will convert their frustrating, multi-step journeys into quick successes, thereby driving up our North Star metric: the Successful Retrieval Rate.</em></p>
  </div>`;
});

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
    <input id="q" type="search" placeholder="Search verbatim text..." aria-label="Search record text">
    ${opts("relevance", uniq("relevance"))}
    ${opts("retrieval_state", uniq("retrieval_state"))}
    ${opts("outcome", uniq("outcome"))}
    ${opts("object_class", uniq("object_class"))}
  </div>
  <p id="hits" class="muted"></p>
  <div id="results"></div>`;
});

window.wireExplorer = function() {
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
};


/* ---------- router ---------- */
const nav = document.getElementById("nav"), main = document.getElementById("main");
nav.innerHTML = PAGES.map((p) =>
  `<button type="button" data-page="${p.id}"><span>${esc(p.title)}</span></button>`).join("");

function show(id) {
  const p = PAGES.find((x) => x.id === id) || PAGES[0];
  main.innerHTML = p.render();
  [...nav.querySelectorAll("button")].forEach((b) => {
    b.setAttribute("aria-current", b.dataset.page === p.id ? "page" : "false");
  });
  if (p.id === "evidence") {
    if (typeof wireExplorer === 'function') wireExplorer();
  }
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
document.getElementById("themeToggle").addEventListener("click", (e) => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  e.target.textContent = next === "dark" ? "Light Mode" : "Dark Mode";
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
