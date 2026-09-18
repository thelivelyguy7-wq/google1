import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Screenshots are build artefacts: keep them out of the repo unless UI_CHECK_OUT says otherwise.
OUT = Path(os.environ.get("UI_CHECK_OUT") or (Path(os.environ.get("TEMP", "/tmp")) / "discovery-ui-shots"))
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8931/"
VIEWS = ["overview", "journey", "memory", "search", "scenarios", "segments", "opportunities",
         "opportunities/approximate_time_anchoring", "research", "explore", "review"]
errors, checks = [], []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    for theme in ["light", "dark"]:
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=theme)
        page = ctx.new_page()
        page.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        for v in VIEWS:
            page.goto(BASE + "#/" + v)
            page.wait_for_selector("main .page-head, main .notice", timeout=15000)
            page.wait_for_timeout(700)
            broken = page.locator("main >> text=This view couldn't be drawn").count()
            check(f"{theme}:{v} renders", broken == 0)
            page.screenshot(path=str(OUT / f"{theme}-{v.replace('/', '_')}.png"), full_page=True)
        ctx.close()

    # Interactions (light, desktop)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.goto(BASE + "#/memory"); page.wait_for_selector(".bar[data-drill]")
    page.locator(".bar[data-drill]").first.click()
    page.wait_for_selector("#drawer.open .result", timeout=15000)
    n = page.locator("#drawer .result").count()
    check("drill opens evidence drawer with results", n > 0, f"{n} results")
    check("results contain highlights", page.locator("#drawer mark[data-k]").count() > 0)
    page.screenshot(path=str(OUT / "i-drill.png"))
    page.locator("#drawer .result").first.click()
    page.wait_for_selector("#drawer .kv", timeout=15000)
    check("record inspector opens (back button)", page.locator("[data-action=drawer-back]").count() == 1)
    page.locator("[data-challenge]").nth(4).click()
    check("challenge form shows", page.locator(".challenge:not([hidden]) select").count() == 1)
    page.screenshot(path=str(OUT / "i-inspector.png"))
    page.locator("[data-action=drawer-back]").click(); page.wait_for_timeout(400)
    check("back returns to evidence list", page.locator("#drawer .result").count() > 0)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    check("escape closes drawer", "open" not in (page.locator("#drawer").get_attribute("class") or ""))

    page.keyboard.press("Control+k")
    page.wait_for_selector("#palette:not([hidden])")
    page.fill("#paletteInput", "What do users commonly forget?")
    page.screenshot(path=str(OUT / "i-palette.png"))
    page.keyboard.press("Enter")
    page.wait_for_selector(".answer .bars, .answer .result", timeout=20000)
    check("palette ask lands on explore with answer", "#/explore" in page.url)
    page.locator("[data-ask]").first.click()
    page.wait_for_selector(".answer:nth-child(1) .result", timeout=20000)
    check("suggested question returns evidence", page.locator(".answer").first.locator(".result").count() > 0)
    page.select_option("select[data-facet=forgotten]", "exact_date_unknown")
    page.wait_for_selector("#searchResults .result", timeout=20000)
    check("facet search returns results", page.locator("#searchResults .result").count() > 0)
    page.screenshot(path=str(OUT / "i-explore.png"), full_page=True)

    page.goto(BASE + "#/segments"); page.wait_for_selector("tr[data-segment]")
    page.locator("th[data-sort]").nth(2).click(); page.wait_for_timeout(200)
    check("sort toggles arrow", page.locator("th .arr").count() == 1)
    page.locator("tr[data-segment]").first.click()
    page.wait_for_selector("#drawer.open .kpi", timeout=10000)
    check("segment drawer opens", True)
    page.keyboard.press("Escape")
    page.goto(BASE + "#/overview"); page.wait_for_selector(".stage")
    page.locator(".stage").nth(3).click(); page.wait_for_selector("#drawer.open .kpi", timeout=10000)
    check("stage drawer opens", True)
    page.keyboard.press("Escape")
    page.goto(BASE + "#/opportunities"); page.wait_for_selector("g.map-dot")
    page.locator("g.map-dot").first.click(); page.wait_for_timeout(500)
    check("map bubble navigates to detail", "#/opportunities/" in page.url)
    page.goto(BASE + "#/review"); page.wait_for_selector("[data-reviewtab]")
    page.locator("[data-reviewtab=log]").click(); page.wait_for_timeout(200)
    check("review tabs switch", page.locator("[data-reviewtab=log].on").count() == 1)

    # Part 2: the metric decomposition leads the opportunities page and drills into evidence
    page.goto(BASE + "#/opportunities"); page.wait_for_selector("table.data tr[data-drill]")
    rows = page.locator("table.data tr[data-drill]").count()
    check("decomposition table lists the stages the metric is lost at", rows >= 5, f"{rows} stages")
    check("decomposition headroom is labelled INTERPRETATION", page.locator("text=INTERPRETATION").count() > 0)
    page.locator("table.data tr[data-drill]").first.click()
    page.wait_for_selector("#drawer.open .result", timeout=15000)
    check("stage row drills into the attempts behind it", page.locator("#drawer .result").count() > 0)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)

    # Segments: four behavioural segments (primary) and three secondary lenses
    page.goto(BASE + "#/segments"); page.wait_for_selector(".seg-card")
    names = page.locator(".seg-card .seg-name").all_inner_texts()
    check("the four behavioural segments are shown, in order of effort",
          names[:4] == ["Direct Retrieval", "Contextual Retrieval", "Candidate-Heavy Retrieval", "Recovery Retrieval"],
          " > ".join(names[:4]))
    check("the partition bar places every attempt once", page.locator("text=shares add up to 100%").count() == 1
          and page.locator(".segbar.tall span").count() >= 4)
    check("segments can be taken into research", page.locator("[data-pick-segment]").count() > 0,
          f"{page.locator('[data-pick-segment]').count()} selectable")
    overflow = max(page.evaluate("(() => [...document.querySelectorAll('.table-wrap')].map(t => t.scrollWidth - t.clientWidth))()") or [0])
    check("segment tables fit without clipping", overflow <= 1, f"overflow {overflow}px")
    check("placement rules and precedence are stated", page.locator("text=How attempts are placed").count() == 1
          and page.locator("text=Precedence.").count() == 1)
    check("behaviours that the precedence rule does not place are still shown",
          page.locator("table.heat.cooc:not(.lens) td.self").count() == 4)
    check("attempts outside the four are shown with their reasons", page.locator("text=Outside the four").count() >= 1)
    for lens, label in [("memory_state", "Memory state"), ("complexity", "Retrieval complexity"), ("outcome_effort", "Retrieval outcome / effort")]:
        page.locator(f"[data-seglens={lens}]").click(); page.wait_for_timeout(350)
        rows = page.locator("table.lens tbody tr").count()
        check(f"secondary lens '{label}' cuts across the four segments", rows == 5, f"{rows} rows incl. all attempts")
    page.locator("[data-seglens=memory_state]").click(); page.wait_for_timeout(300)
    check("find rates by memory state carry the post-length caveat", page.locator("text=Read as composition, not cause").count() == 1)
    page.locator("table.lens td.clickable").first.click(); page.wait_for_selector("#drawer.open .result", timeout=15000)
    check("a lens cell drills into the attempts behind it", page.locator("#drawer .result").count() > 0
          and page.locator("#drawer .chip:has-text('Memory state')").count() == 1)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    page.locator(".seg-share").nth(2).click(); page.wait_for_selector("#drawer.open .kpi .v", timeout=15000)
    seg_n = page.locator("#drawer .kpi .v").first.inner_text()
    check("a segment's share opens exactly its attempts", seg_n.strip() == page.locator(".seg-card").nth(2).locator(".seg-share .small").inner_text().split("/")[0].strip(),
          f"{seg_n} matches")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    page.locator(".seg-card [data-segment]").nth(3).click(); page.wait_for_selector("#drawer.open .kpi", timeout=10000)
    check("segment drawer explains how it would be researched",
          page.locator("#drawer >> text=Taking this segment into research").count() == 1
          and page.locator("#drawer >> text=In their words").count() == 1)
    check("segment drawer carries a screener", page.locator("#drawer ol.guide li").count() >= 5,
          f"{page.locator('#drawer ol.guide li').count()} screener questions")
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    page.goto(BASE + "#/research"); page.wait_for_selector("[data-researchtab]")
    page.locator("[data-researchtab=method]").click(); page.wait_for_timeout(300)
    check("method tab explains the methodology", page.locator("text=Alternatives considered").count() == 1
          and page.locator("text=Threats to validity").count() == 1)
    check("method tab renders without empty cards", page.locator("main .card").count() >= 5, f"{page.locator('main .card').count()} cards")
    check("method tab says what each part of the session buys",
          page.locator("text=What each part of the session buys").count() == 1)
    # The adaptation card is segment-dependent: with no target chosen it must say so and offer the way there.
    adapted = page.locator("text=Adapted for the target segment").count()
    check("method tab states its segment adaptation, or that there is none",
          adapted == 1 or page.locator("text=Not yet adapted to a segment").count() == 1,
          "adapted" if adapted else "no target segment chosen")

    # Part 4: the problem definition and how it was arrived at
    page.locator("[data-researchtab=problem]").click(); page.wait_for_timeout(300)
    steps = page.locator(".chain-step").count()
    check("problem definition shows the chain from metric to problem", steps == 5, f"{steps} steps")
    check("problem definition rules out the generic framing",
          page.locator("text=What this problem is not").count() == 1)
    check("problem definition is marked a draft", page.locator("text=DRAFT").count() > 0)
    page.screenshot(path=str(OUT / "i-problem.png"), full_page=True)
    page.locator("[data-researchtab=plan]").click(); page.wait_for_timeout(300)
    check("research tabs return to the plan", page.locator("[data-researchtab=plan].on").count() == 1)
    ctx.close()

    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(f"pageerror(mobile): {e}"))
    for v in ["overview", "opportunities", "opportunities/approximate_time_anchoring", "research", "segments", "explore"]:
        page.goto(BASE + "#/" + v); page.wait_for_selector("main .page-head"); page.wait_for_timeout(600)
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        check(f"mobile {v} no horizontal overflow", overflow <= 1, f"overflow {overflow}px")
        page.screenshot(path=str(OUT / f"m-{v.replace('/', '_')}.png"), full_page=True)
    page.locator("#menuBtn").click(); page.wait_for_timeout(300)
    check("mobile menu opens", "open" in (page.locator("#sidebar").get_attribute("class") or ""))
    page.screenshot(path=str(OUT / "m-menu.png"))
    browser.close()

for name, ok, detail in checks:
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))
print("ERRORS:", json.dumps(sorted(set(errors)), indent=1))

