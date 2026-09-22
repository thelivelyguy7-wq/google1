import re

with open('site/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

journey_regex = r'page\("journey",.*?^\}\);'

new_journey_page = """page("journey", "Journey & KPI Tree", "Stage 2", () => {
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

  return `<h1>Retrieval Journey & KPIs</h1>
  
  <h2>KPI Tree: Drivers of Successful Retrieval</h2>
  <p class="lede">A breakdown of the metrics that ladder up to our primary impact goal.</p>
  <div class="card">
    <ul style="line-height: 1.8; list-style-type: none; padding-left: 0;">
      <li><strong>🎯 Incremental Successful Retrievals</strong>
        <ul style="list-style-type: none;">
          <li>↳ <strong>Total Retrieval Attempts</strong> (Volume)</li>
          <li>↳ <strong>Overall Success Rate</strong> (Quality)
            <ul style="list-style-type: none;">
              <li>↳ First-Attempt Success Rate</li>
              <li>↳ Recovery Success Rate (from failed first attempt)
                <ul style="list-style-type: none;">
                  <li>↳ Recovery Attempt Rate</li>
                  <li>↳ Success Rate of Recovery Attempts
                    <ul style="list-style-type: none;">
                      <li>↳ Success via Query Reformulation</li>
                      <li>↳ Success via Manual Browsing</li>
                    </ul>
                  </li>
                </ul>
              </li>
            </ul>
          </li>
        </ul>
      </li>
    </ul>
  </div>

  <h2>Decomposition of Successful Retrieval</h2>
  <p class="lede">${INTERP} Success needs every node to hold: usable partial memory (D1), expression (D2), the product
  bringing the photo into the candidates (D3), recognition (D4), refinement when the first try fails (D5), and the
  photo being in the library (D6). A retrieval fails at the first node that does not hold.</p>
  
  ${table(["Node", "Case question", "User behaviour", "Product outcome", "Opportunity"],
    Object.entries(NODES).map(([k, v]) =>
      [`<strong>${esc(k)} ${esc(v.name)}</strong>`, esc(v.brief_question), esc(v.user_behavior),
        esc(v.product_outcome), esc(v.opportunity)]))}
        
  <h2>Evidence per node ${OBS}</h2>
  <p class="muted">Breakdown = the record states a difficulty here. Indirect = consistent with failure here but not
  attributable. Effort = extra work here. Intact = the step worked or the capability is retained.</p>
  ${table(["Node", "Breakdown", "Indirect", "Effort", "Intact", "No evidence"], rows)}
  
  <div class="card">
    <h3>Where the greatest opportunity lies</h3>
    <p>The evidence supports investigating <strong>D2 Express</strong> (${ev("node:D2:breakdown", DC.D2.breakdown)}),
    <strong>D4 Evaluate</strong> (${DC.D4.breakdown_or_effort} with breakdown or effort evidence) and
    <strong>D5 Refine</strong> (${DC.D5.breakdown_or_effort}).</p>
    <p><strong>D3 has ${DC.D3.breakdown} records</strong> stating the product misread the clues, and
    ${ev("node:D3:indirect", DC.D3.indirect)} showing indirect signs only. ${UNKNOWN} That question is unanswerable
    from this corpus, which is not the same as the answer being no.</p>
  </div>
  
  <h2>Observed stage paths</h2>
  <p class="muted">${Object.keys(J.top_paths).length} shown of ${J.n_paths} distinct paths.</p>
  ${table(["Path", "Records"], Object.entries(J.top_paths).map(([k, v]) => [`<span class="mono">${esc(k)}</span>`, v]))}`;
});"""

new_text = re.sub(journey_regex, new_journey_page, text, flags=re.MULTILINE|re.DOTALL)

with open('site/app.js', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Updated journey page successfully")
