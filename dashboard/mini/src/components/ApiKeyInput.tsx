import type { JSX } from 'react';
import { useState, useEffect } from 'react';
import { useApiKey } from '../state/ApiKeyContext';

export default function ApiKeyInput(): JSX.Element {
  const { apiKey, setApiKey } = useApiKey();
  const [value, setValue] = useState(apiKey);

  useEffect(() => {
    setValue(apiKey);
  }, [apiKey]);

  return (
    <div>
      <input
        type="password"
        aria-label="api-key"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <button onClick={() => setApiKey(value)}>Enregistrer</button>
      {apiKey && <button onClick={() => setApiKey('')}>Effacer</button>}
    </div>
  );
}
