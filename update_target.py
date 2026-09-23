import re

with open('site/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to replace the entire `page("target", ...)` block with the new content.
target_regex = r'page\("target",.*?^\}\);'

new_target_page = """page("target", "Target segment and impact sizing", "Stages 7–8", () => {
  const T = D.target, I = D.impact, p = T.profile;
  const oppsTable = table(["Opportunity", "Issues (Frequency)", "Severity Signals", "Impact on Outcomes"], 
    Object.entries(D.opps).sort((a, b) => b[1].n - a[1].n).map(([k, v]) => {
      const code = k.split(" ")[0];
      const outs = Object.entries(v.profile.outcomes).filter(([a, b]) => b && a !== "unknown")
        .map(([a, b]) => `${b} ${human(a)}`).join(", ") || "Outcome Not Stated";
      return [esc(k), ev("opp:" + code, v.n, REL), 
        `${v.profile.with_severity_signal} records with ≥1`, esc(outs)];
    }));

  return `<h1>Target segment and impact sizing</h1>
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
  <div class="card">
    <h3>${label("OPP-HYP")} TARGET SEGMENT HYPOTHESIS</h3>
    <p>Investigate <strong>users who attempted to retrieve a specific photo they expected to exist, lacked a precise
    identifier, and either changed strategy or made several attempts, or manually inspected a candidate set</strong>:
    ${ev("seg:SEG-T", T.n, REL)} records (${T.pct}%). Every member states
    effortful behaviour.</p>
  </div>
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
  <div class="card">
    <h3>Jobs-to-be-Done (JTBD)</h3>
    <p><strong>When I</strong> am looking for a specific photo I know I have from the past...</p>
    <p><strong>But</strong> I lack a precise identifier like the exact date, location, or album...</p>
    <p><strong>Help me</strong> quickly narrow down my large library and recover from a failed search without endless manual scrolling.</p>
  </div>
  <p><strong>"How might we" challenge:</strong> How might we enable users with imprecise memories to confidently evaluate and refine their search results?</p>

  <h2>4. WHAT: Product Opportunity Analysis</h2>
  <p class="muted">A filtered opportunity analysis focusing on issues, severity, and outcomes. Note: Competitor analysis and cost-to-build are excluded as they require external or engineering input. All items here are hypotheses to be validated, not guaranteed features.</p>
  ${oppsTable}`;
});"""

new_text = re.sub(target_regex, new_target_page, text, flags=re.MULTILINE|re.DOTALL)

with open('site/app.js', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Updated target page successfully")
