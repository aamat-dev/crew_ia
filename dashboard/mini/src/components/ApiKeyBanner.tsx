import type { JSX } from 'react';
import { FormEvent, useState } from 'react';
import { useApiKey } from '../state/ApiKeyContext';
import { DEMO_API_KEY } from '../config/env';

export const ApiKeyBanner = (): JSX.Element => {
  const { setApiKey, useEnvKey, setUseEnvKey } = useApiKey();
  const [input, setInput] = useState('');

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setApiKey(input.trim());
    setInput('');
  };

  const envKeyDefined = Boolean(DEMO_API_KEY);

  return (
    <div>
      <form onSubmit={onSubmit}>
        <input
          data-testid="apiKeyInput"
          type="password"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={useEnvKey}
        />
        <button data-testid="useButton" type="submit" disabled={useEnvKey}>
          Utiliser
        </button>
        <label>
          <input
            data-testid="useEnvToggle"
            type="checkbox"
            checked={useEnvKey}
            onChange={(e) => setUseEnvKey(e.target.checked)}
          />
          Utiliser la clé .env (démo)
        </label>
      </form>
      {useEnvKey && envKeyDefined && (
        <span data-testid="envActiveBadge">Clé de démo (.env) active</span>
      )}
      {useEnvKey && !envKeyDefined && (
        <span data-testid="envActiveBadge">Clé de démo (.env) non définie</span>
      )}
    </div>
  );
};

export default ApiKeyBanner;
