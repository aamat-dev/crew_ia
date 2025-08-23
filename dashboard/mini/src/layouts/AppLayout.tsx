import type { JSX, ReactNode } from 'react';
import ApiKeyBanner from '../components/ApiKeyBanner';

export const AppLayout = ({
  children,
}: {
  children: ReactNode;
}): JSX.Element => (
  <div>
    <header>
      <h1>Mini Dashboard (read-only) — Fil G</h1>
    </header>
    <ApiKeyBanner />
    <main>{children}</main>
  </div>
);

export default AppLayout;
