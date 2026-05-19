---
name: seo-demand-research
description: Research overseas SEO demand and low-competition keyword opportunities for AI tools, SaaS, niche websites, or content/product ideas. Use when the user asks to 找词, 挖需求, 判断关键词值不值得做, research keywords, analyze search intent, inspect SERPs, compare competitors, use Ahrefs/Semrush/Similarweb/Google Trends, or produce an executable SEO/product SOP before building a site.
---

# SEO Demand Research

Use this skill to turn a rough market idea into a prioritized keyword/opportunity list, competitor analysis, and execution SOP for an overseas SEO-led product site.

## Operating Principles

- Verify current data with live tools when keyword metrics, SERPs, competitors, prices, domains, or trends matter.
- Treat keyword tools as estimates, not truth. Cross-check Ahrefs/Semrush/SERP/Similarweb/Google Trends before ranking opportunities.
- Prefer long-tail, intent-clear, buildable keywords over broad vanity keywords.
- Do not call a keyword “easy” only because KD is low; inspect the actual Google top results.
- Reject opportunities where the top results are old, high-authority, product-strong, backlink-heavy, and directly satisfy intent.
- Favor opportunities where searchers want an action/tool/result, not just information.
- Produce decisions with evidence, not vibes.

## Default Automation Behavior

If the user says only “找词”, “挖需求”, “继续调研”, or gives a rough niche:

1. Treat the task as **Full research** unless time/tool access is limited.
2. Generate seed clusters first.
3. Browse current SERPs for the most promising candidates.
4. Use keyword tools if available or if the user explicitly asks.
5. Score and reject weak candidates.
6. Return a ranked shortlist and one recommended next action.

If the user asks “能不能做” or challenges a previous recommendation:

1. Re-check the live SERP first.
2. Compare against Ahrefs/Semrush/SiteData/Similarweb if available.
3. Explain whether the prior decision was wrong, uncertain, or still valid.
4. Update the score and recommendation.

## Workflow

Choose one of three modes based on the user's request:

- **Quick scan**: 10-20 keywords, SERP spot checks, one recommended wedge.
- **Full research**: keyword clusters, Ahrefs/Semrush/Similarweb/Trends, competitor testing, ranked report.
- **Build handoff**: full research plus MVP scope, pricing hypothesis, SEO page map, and developer-ready SOP.

1. **Clarify the seed**
   - Identify niche, target country/language, monetization model, user pain, and product type.
   - If the user already has a project or domain, read its context first.

2. **Generate seed keyword clusters**
   - Create 5-10 keyword clusters from pain, input format, output format, user role, platform, comparison, and workflow.
   - Example dimensions: `pdf`, `notes`, `youtube transcript`, `anki`, `quizlet`, `students`, `exam`, `generator`, `converter`, `maker`.

3. **Collect current evidence**
   - Use Google SERP for each serious candidate.
   - Use Ahrefs keyword difficulty/backlinks when available.
   - Use Semrush for volume, KD, CPC, related terms, and intent.
   - Use Similarweb/SiteData-like overlays for competitor traffic and domain age.
   - Use Google Trends for new/rising terms or seasonality.

4. **Judge the real SERP**
   - Record top 5-10 results, domain strength, age, traffic, page type, backlink/domain count, and whether the result is a real tool.
   - Identify ads, AI overviews, snippets, videos, marketplaces, Reddit/Quora, Chrome extensions, and app stores.
   - Note whether a new focused tool can realistically beat or flank the SERP.

5. **Score opportunities**
   - Use `references/keyword-scorecard.md`.
   - Require both quantitative and qualitative judgment.
   - Mark each candidate as `Build now`, `Content support`, `Watch`, or `Reject`.

6. **Inspect competitors**
   - Use the competitor product manually when practical.
   - Capture onboarding, input limits, pricing, output quality, export formats, speed, UX, trust signals, SEO pages, and monetization.
   - Extract gaps that a new product can exploit.

7. **Produce outputs**
   - Keyword shortlist with evidence.
   - Competitor map.
   - Recommended wedge.
   - MVP scope.
   - SEO page plan.
   - Risks and next validation tasks.
   - Use `references/output-templates.md`.

## When Using Browser Tools

- If the user asks to use their local browser, prefer that browser for logged-in SEO tools and product inspection.
- If using Tabbit/Chrome with existing sessions, avoid changing account settings, buying domains, submitting payments, or mutating production configs unless the user explicitly asks.
- For Ahrefs free keyword difficulty, record KD, backlink estimate, visible SERP rows, DR/UR/backlinks/domains/traffic/keywords if shown.
- For Semrush, record country, volume, KD, CPC, intent, trend, related keywords, and date.
- For Similarweb, record approximate traffic, top channels, geography, and competitor overlap if available.

## Required References

Load only what is needed:

- `references/research-sop.md`: detailed end-to-end research process.
- `references/keyword-scorecard.md`: scoring rubric, reject rules, and priority labels.
- `references/tool-playbook.md`: Ahrefs/Semrush/Similarweb/Google/Trends usage notes.
- `references/output-templates.md`: report, SOP, and keyword table templates.
- `references/case-study-pdf-flashcards.md`: prior PDF flashcard project lessons; load when researching AI flashcard, PDF, study, Anki, Quizlet, or education-tool niches.

## Quality Bar

Before finalizing, check:

- Did current data come from live tools when needed?
- Did the SERP inspection contradict keyword-tool metrics?
- Are the top competitors actually beatable?
- Is the MVP small enough to build but useful enough to convert?
- Is the monetization path explicit?
- Are next actions concrete enough for Codex to execute in a later development session?

## Default User-Facing Output

Unless the user asks for another format, answer in Chinese with concise Markdown. Put the recommendation first, then evidence tables, then next actions.
