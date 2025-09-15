#!/usr/bin/env node
import { execFile } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { setTimeout as delay } from 'node:timers/promises';

const URL = process.env.URL || 'http://localhost:3000';
const OUT = process.env.LH_OUT || 'lighthouse-report.json';
const MIN = Number(process.env.LH_MIN || '0.9');

async function waitForServer(url, timeoutMs = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const ok = await fetch(url).then(r => r.ok).catch(() => false);
    if (ok) return true;
    await delay(1000);
  }
  throw new Error(`Server not ready at ${url}`);
}

function runLighthouse(url, out) {
  return new Promise((resolve, reject) => {
    const args = [
      url,
      '--quiet',
      '--chrome-flags=--headless=new',
      '--only-categories=accessibility,performance,best-practices',
      '--output=json',
      `--output-path=${out}`,
      '--preset=desktop',
    ];
    const cmd = process.env.LIGHTHOUSE_BIN || 'lighthouse';
    const child = execFile(cmd, args, { encoding: 'utf8' }, (err, stdout, stderr) => {
      if (err) return reject(err);
      resolve({ stdout, stderr });
    });
    child.stdout?.pipe(process.stdout);
    child.stderr?.pipe(process.stderr);
  });
}

try {
  await waitForServer(URL);
  await runLighthouse(URL, OUT);
  const report = JSON.parse(readFileSync(OUT, 'utf8'));
  const acc = report.categories.accessibility.score;
  const perf = report.categories.performance.score;
  const bp = report.categories['best-practices'].score;
  const msg = `Lighthouse scores — A11y: ${(acc*100).toFixed(0)}, Perf: ${(perf*100).toFixed(0)}, BP: ${(bp*100).toFixed(0)}`;
  console.log(msg);
  writeFileSync('lh-summary.md', `# Lighthouse (Cockpit)\n\n${msg}\n`);
  if (acc < MIN || perf < MIN || bp < MIN) {
    console.error('One or more categories below threshold: ', MIN*100);
    process.exit(1);
  }
} catch (e) {
  console.error('[lighthouse:ci] Failed:', e?.message || e);
  process.exit(1);
}

