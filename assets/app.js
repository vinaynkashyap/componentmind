const PRESETS = {
  pricing: `<section aria-label="Pricing tiers">
  <h2>Simple transparent pricing</h2>
  <div class="pricing-grid">
    <article class="plan">
      <h3>Starter</h3>
      <p>$0 per month forever for indie developers.</p>
      <img src="/badge.svg" alt="Starter plan icon" width="48" height="48" loading="lazy" />
      <button type="button">Start Free</button>
    </article>
  </div>
</section>`,
  noisy: `<div class="hero">
  <div class="title">Welcome to Our App</div>
  <img src="/hero-banner.png" />
  <div onclick="signup()">Click Here</div>
  <a href="/docs">Read more</a>
  <input type="email" placeholder="Email" />
</div>`,
  datatable: `<section aria-labelledby="cmp-heading">
  <h2 id="cmp-heading">Framework Comparison</h2>
  <table>
    <caption>Component audit speed and Core Web Vitals impact</caption>
    <thead>
      <tr><th scope="col">Tool</th><th scope="col">MCP Native</th><th scope="col">CI Overhead</th></tr>
    </thead>
    <tbody>
      <tr><td>ComponentMind</td><td>Yes</td><td>&lt; 2s</td></tr>
    </tbody>
  </table>
</section>`
};

function auditComponent(code) {
  const findings = [];
  let score = 100;

  const hasSemantic = /<(section|article|main|header|nav|footer|table|aside|figure)\b/i.test(code);
  if (hasSemantic) {
    findings.push({ status: "pass", label: "Semantic Landmarks", detail: "Uses semantic HTML5 container elements for crawler and screen-reader clarity." });
  } else {
    score -= 18;
    findings.push({ status: "fail", label: "Div Soup Detected", detail: "Wrap primary UI blocks in <section>, <article>, or <main> instead of bare <div> tags." });
  }

  const hasHeading = /<h[1-6]\b/i.test(code);
  if (hasHeading) {
    findings.push({ status: "pass", label: "Heading Hierarchy", detail: "Explicit heading tag present for SEO/GEO outline extraction." });
  } else {
    score -= 15;
    findings.push({ status: "fail", label: "Missing Heading Tag", detail: "Replace styled <div> titles with semantic <h1>–<h3> elements." });
  }

  const imgs = [...code.matchAll(/<img\b[^>]*>/gi)];
  if (imgs.length > 0) {
    const missingAlt = imgs.some(m => !/\balt\s*=/i.test(m[0]));
    const missingDims = imgs.some(m => !(/\bwidth\s*=/i.test(m[0]) && /\bheight\s*=/i.test(m[0])));
    if (missingAlt) {
      score -= 18;
      findings.push({ status: "fail", label: "Image Missing Alt Text", detail: "Add descriptive alt attributes to all <img> elements for WCAG & image search." });
    } else {
      findings.push({ status: "pass", label: "Image Alt Attributes", detail: "All detected <img> elements include descriptive alt text." });
    }
    if (missingDims) {
      score -= 12;
      findings.push({ status: "warn", label: "CLS Layout Shift Risk", detail: "Specify explicit width and height attributes on <img> tags to protect Core Web Vitals CLS." });
    } else {
      findings.push({ status: "pass", label: "CLS Safe Dimensions", detail: "Explicit image dimensions prevent Cumulative Layout Shift." });
    }
  }

  const clickableDiv = /<div\b[^>]*onClick=/i.test(code);
  if (clickableDiv) {
    score -= 16;
    findings.push({ status: "fail", label: "Non-Accessible Click Handler", detail: "Replace <div onclick=...> with a native <button type=\"button\"> for keyboard accessibility." });
  }

  const unlabeledInput = /<input\b(?![^>]*(aria-label|aria-labelledby))[^>]*>/i.test(code) && !/<label\b/i.test(code);
  if (unlabeledInput) {
    score -= 12;
    findings.push({ status: "warn", label: "Unlabeled Form Control", detail: "Pair <input> with a visible <label> or aria-label instead of relying solely on placeholder text." });
  }

  const genericLink = /<a\b[^>]*>\s*(click here|read more|learn more)\s*<\/a>/i.test(code);
  if (genericLink) {
    score -= 9;
    findings.push({ status: "warn", label: "Weak Anchor Text", detail: "Replace generic link text ('Read more') with descriptive anchor text to pass topical PageRank." });
  }

  const hasTable = /<table\b/i.test(code);
  if (hasTable) {
    findings.push({ status: "pass", label: "GEO / AI Overview Ready", detail: "Structured HTML <table> with headers is directly parseable by Google AI Overviews and LLM search engines." });
  }

  score = Math.max(0, Math.min(100, score));
  return { score, findings };
}

function initSandbox() {
  const input = document.getElementById("component-code");
  const scoreEl = document.getElementById("audit-score");
  const listEl = document.getElementById("audit-results");
  const runBtn = document.getElementById("run-audit-btn");
  const presetBtns = document.querySelectorAll("[data-preset]");

  if (!input || !scoreEl || !listEl) return;

  function render() {
    const { score, findings } = auditComponent(input.value);
    scoreEl.textContent = `${score}/100`;
    scoreEl.className = "score-pill" + (score < 60 ? " bad" : score < 85 ? " warn" : "");
    listEl.innerHTML = findings.map(f => {
      const tagClass = f.status === "pass" ? "tag-pass" : f.status === "warn" ? "tag-warn" : "tag-fail";
      return `<li class="audit-item"><span class="tag ${tagClass}">${f.status}</span><strong>${f.label}:</strong> ${f.detail}</li>`;
    }).join("");
  }

  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      presetBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      input.value = PRESETS[btn.dataset.preset] || PRESETS.pricing;
      render();
    });
  });

  if (runBtn) runBtn.addEventListener("click", render);
  input.addEventListener("input", render);
  input.value = PRESETS.noisy;
  render();
}

document.addEventListener("DOMContentLoaded", initSandbox);
