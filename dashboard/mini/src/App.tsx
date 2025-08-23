import type { JSX } from 'react';
import ApiKeyBanner from './components/ApiKeyBanner';
import { ApiKeyProvider } from './state/ApiKeyContext';

export const App = (): JSX.Element => (
  <ApiKeyProvider>
    <div>
      <ApiKeyBanner />
      <h1>Mini Dashboard (read-only) — Fil G</h1>
    </div>
  </ApiKeyProvider>
);

export default App;
