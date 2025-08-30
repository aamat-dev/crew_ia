import { copyFile } from 'fs/promises';
import { resolve } from 'path';

const distDir = resolve('dist');
const src = resolve(distDir, 'index.html');
const dest = resolve(distDir, '404.html');

async function main() {
  try {
    await copyFile(src, dest);
    console.log('404.html created');
  } catch (error) {
    console.error('Unable to create 404.html', error);
    process.exit(1);
  }
}

main();
