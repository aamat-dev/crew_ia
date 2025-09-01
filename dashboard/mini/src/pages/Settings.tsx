import type { JSX, FormEvent } from 'react';
import { useState } from 'react';
import { useSettings } from '../store/settings';

export default function Settings(): JSX.Element {
  const [settings, save] = useSettings();
  const [apiUrl, setApiUrl] = useState(settings.apiUrl);
  const [apiKey, setApiKey] = useState(settings.apiKey);
  const [reveal, setReveal] = useState(false);

  const onSubmit = (e: FormEvent): void => {
    e.preventDefault();
    save({ apiUrl: apiUrl.trim(), apiKey: apiKey.trim() });
  };

  return (
    <form onSubmit={onSubmit}>
      <div>
        <label>
          API URL
          <input
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
          />
        </label>
      </div>
      <div>
        <label>
          API Key
          <input
            type={reveal ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </label>
        <button type="button" onClick={() => setReveal((v) => !v)}>
          {reveal ? 'Masquer' : 'Afficher'}
        </button>
      </div>
      <button type="submit">Enregistrer</button>
    </form>
  );
}
