import type { JSX, ReactNode } from 'react';
import ApiKeyBanner from '../components/ApiKeyBanner';
import ConfigPanel from '../components/ConfigPanel';

export const AppLayout = ({
  children,
}: {
  children: ReactNode;
}): JSX.Element => (
  <div>
    <header>
      <h1>Mini Dashboard (read-only) — Fil G</h1>
    </header>
    <ConfigPanel />
    <ApiKeyBanner />
    <main>{children}</main>
  </div>
);

export default AppLayout;
