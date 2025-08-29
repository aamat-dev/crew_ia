import type { JSX } from 'react';
import { FormEvent, useState } from 'react';
import { getApiBaseUrl, setApiBaseUrl, DEFAULT_API_BASE_URL } from '../config/env';
import { pingApi } from '../api/ping';

export const ConfigPanel = (): JSX.Element => {
  const [input, setInput] = useState<string>(getApiBaseUrl());
  const [message, setMessage] = useState<string>('');

  const isValidUrl = (url: string): boolean => /^https?:\/\//.test(url);

  const onSave = (e: FormEvent) => {
    e.preventDefault();
    if (!isValidUrl(input)) {
      setMessage('URL invalide');
      return;
    }
    setApiBaseUrl(input);
    setMessage('Enregistré');
  };

  const onTest = async (): Promise<void> => {
    if (!isValidUrl(input)) {
      setMessage('URL invalide');
      return;
    }
    setMessage('Test...');
    const res = await pingApi(input);
    if (res.ok) {
      setMessage('Connexion OK');
    } else if (res.status === 401 || res.status === 403) {
      setMessage('Clé API requise — à renseigner dans la bannière');
    } else {
      setMessage('Échec de connexion');
    }
  };

  const onReset = (): void => {
    setInput(DEFAULT_API_BASE_URL);
    setApiBaseUrl(DEFAULT_API_BASE_URL);
    setMessage('Réinitialisé');
  };

  return (
    <div>
      <form onSubmit={onSave}>
        <label>
          API URL
          <input
            data-testid="apiUrlInput"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </label>
        <button type="submit">Enregistrer</button>
        <button type="button" onClick={onTest}>
          Tester
        </button>
        <button type="button" onClick={onReset}>
          Réinitialiser
        </button>
      </form>
      {message && <p data-testid="apiUrlMessage">{message}</p>}
    </div>
  );
};

export default ConfigPanel;
