#!/usr/bin/env node
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function readJSON(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function toKB(bytes) {
  return bytes / 1024;
}

function format(num, unit='ms') {
  return unit === 'kb' ? `${num.toFixed(1)} KB` : `${Math.round(num)} ms`;
}

async function runLighthouse(url) {
  const { default: lighthouse } = await import('lighthouse');
  const chromeLauncher = await import('chrome-launcher');
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  const options = { logLevel: 'error', output: 'json', port: chrome.port };
  const runnerResult = await lighthouse(url, options);
  await chrome.kill();
  return runnerResult.lhr;
}

function evaluate(lhr, budget) {
  const details = { metrics: {}, transferSize: {}, requests: {}, bundles: [] };
  let pass = true;

  const metricsMap = {
    lcp: lhr.audits['largest-contentful-paint']?.numericValue,
    inp: lhr.audits['interaction-to-next-paint']?.numericValue,
    cls: lhr.audits['cumulative-layout-shift']?.numericValue,
    tti: lhr.audits['interactive']?.numericValue
  };

  for (const [key, value] of Object.entries(metricsMap)) {
    const limit = budget.metrics[key];
    if (limit != null) {
      const ok = value <= limit;
      details.metrics[key] = { value, limit, ok };
      if (!ok) pass = false;
    }
  }

  const items = lhr.audits['total-byte-weight'].details.items;
  let js = 0, css = 0, total = 0;
  for (const it of items) {
    total += it.transferSize;
    if (it.resourceType === 'Script') js += it.transferSize;
    if (it.resourceType === 'Stylesheet') css += it.transferSize;
  }
  const sizeBudget = budget.transferSize;
  const sizeMap = { js: toKB(js), css: toKB(css), total: toKB(total) };
  for (const [key, value] of Object.entries(sizeMap)) {
    const limit = sizeBudget[key];
    const ok = value <= limit;
    details.transferSize[key] = { value, limit, ok };
    if (!ok) pass = false;
  }

  const reqs = lhr.audits['network-requests'].details.items.length;
  const okReq = reqs <= budget.requests;
  details.requests = { value: reqs, limit: budget.requests, ok: okReq };
  if (!okReq) pass = false;

  const topBundles = lhr.audits['network-requests'].details.items
    .sort((a, b) => b.transferSize - a.transferSize)
    .slice(0, 5)
    .map(i => `${i.url} (${format(toKB(i.transferSize), 'kb')})`);
  details.bundles = topBundles;

  return { pass, details };
}

function renderReport(results) {
  let out = '# Rapport budgets de performance\n\n';
  for (const { path, pass, details } of results) {
    out += `## ${path} — ${pass ? '✅' : '❌'}\n`;
    out += `| Métrique | Valeur | Budget | OK |\n|---|---|---|---|\n`;
    for (const [m, info] of Object.entries(details.metrics)) {
      out += `| ${m.toUpperCase()} | ${format(info.value)} | ${format(info.limit)} | ${info.ok ? '✅' : '❌'} |\n`;
    }
    out += `| JS | ${format(details.transferSize.js.value, 'kb')} | ${details.transferSize.js.limit} KB | ${details.transferSize.js.ok ? '✅' : '❌'} |\n`;
    out += `| CSS | ${format(details.transferSize.css.value, 'kb')} | ${details.transferSize.css.limit} KB | ${details.transferSize.css.ok ? '✅' : '❌'} |\n`;
    out += `| Total | ${format(details.transferSize.total.value, 'kb')} | ${details.transferSize.total.limit} KB | ${details.transferSize.total.ok ? '✅' : '❌'} |\n`;
    out += `| Requêtes | ${details.requests.value} | ${details.requests.limit} | ${details.requests.ok ? '✅' : '❌'} |\n`;
    out += '\n### Plus gros bundles\n';
    for (const b of details.bundles) {
      out += `- ${b}\n`;
    }
    out += '\n';
  }
  return out;
}

(async () => {
  const budgetsPath = process.argv[2] || path.join(__dirname, '..', 'perf-budgets.json');
  const base = process.env.PREVIEW_URL || 'http://localhost:3000';
  const budgets = readJSON(budgetsPath);
  const results = [];
  for (const [p, cfg] of Object.entries(budgets)) {
    const url = new URL(p, base).toString();
    const lhr = await runLighthouse(url);
    const evaluation = evaluate(lhr, cfg);
    results.push({ path: p, ...evaluation });
  }
  const report = renderReport(results);
  fs.writeFileSync('lh-budgets-report.md', report);
  console.log(report);
  if (results.some(r => !r.pass)) {
    process.exit(1);
  }
})();
