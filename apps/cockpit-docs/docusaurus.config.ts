import type { Config } from '@docusaurus/types';
import { classic } from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Oria Docs',
  url: 'https://example.com',
  baseUrl: '/',
  favicon: 'img/favicon.ico',
  staticDirectories: ['static'],
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
        },
        blog: false,
      },
    ],
  ],
};

export default config;
