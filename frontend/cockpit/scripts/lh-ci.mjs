import { spawn } from 'node:child_process';
import { readFile, mkdir } from 'node:fs/promises';
import net from 'node:net';

function getPort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.on('error', reject);
    server.listen(0, () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

function run(cmd, args, options = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, { stdio: 'inherit', ...options });
    proc.on('error', reject);
    proc.on('close', code => {
      if (code === 0) resolve();
      else reject(new Error(`${cmd} exited with code ${code}`));
    });
  });
}

async function main() {
  const port = await getPort();
  await run('npx', ['next', 'build']);
  const server = spawn('npx', ['next', 'start', '-p', String(port)], { stdio: 'inherit' });
  await new Promise(res => setTimeout(res, 5000));

  try {
    await mkdir('.lighthouse', { recursive: true });
    await run('npx', [
      'lighthouse',
      `http://localhost:${port}/dashboard`,
      '--output=json',
      '--output-path=./.lighthouse/report.json',
      '--quiet',
      '--chrome-flags=--headless'
    ]);
    const report = JSON.parse(await readFile('./.lighthouse/report.json', 'utf8'));
    const score = report.categories.accessibility.score;
    console.log(`Accessibility score: ${score}`);
    if (score < 0.9) {
      throw new Error(`Accessibility score ${score} is below 0.90`);
    }
  } finally {
    server.kill('SIGINT');
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
