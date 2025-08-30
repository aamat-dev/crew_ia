import type { JSX, FormEvent } from 'react';
import { useState } from 'react';

export default function ConfigPanel(): JSX.Element {
  const [url, setUrl] = useState<string>(
    localStorage.getItem('apiBaseUrl') || '',
  );
  const [message, setMessage] = useState('');

  const isValidUrl = (value: string): boolean => /^https?:\/\//.test(value);

  const onSave = (e: FormEvent): void => {
    e.preventDefault();
    const trimmed = url.trim();
    if (!isValidUrl(trimmed)) {
      setMessage('URL invalide');
      setTimeout(() => setMessage(''), 2000);
      return;
    }
    localStorage.setItem('apiBaseUrl', trimmed);
    setMessage('Enregistré');
    setTimeout(() => setMessage(''), 2000);
  };

  return (
    <form onSubmit={onSave}>
      <label>
        API URL
        <input
          data-testid="apiUrlInput"
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      </label>
      <button type="submit">Enregistrer</button>
      {message && <p data-testid="apiUrlMessage">{message}</p>}
    </form>
  );
}
