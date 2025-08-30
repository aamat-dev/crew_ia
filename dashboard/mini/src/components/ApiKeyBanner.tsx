import type { JSX } from 'react';
import { useApiKey } from '../state/ApiKeyContext';

export default function ApiKeyBanner(): JSX.Element | null {
  const { apiKey } = useApiKey();
  if (!apiKey || !apiKey.trim()) {
    return (
      <div role="alert">⚠ API Key requise pour accéder aux données</div>
    );
  }
  return null;
}
