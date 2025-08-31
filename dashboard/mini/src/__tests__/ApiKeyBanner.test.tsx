import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { ApiKeyProvider } from '../state/ApiKeyContext';
import ApiKeyBanner from '../components/ApiKeyBanner';
import ApiKeyInput from '../components/ApiKeyInput';

describe('ApiKeyBanner', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubEnv('VITE_API_KEY', '');
    vi.stubEnv('VITE_DEMO_API_KEY', '');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("affiche l'alerte puis la cache après enregistrement", () => {
    render(
      <ApiKeyProvider>
        <ApiKeyInput />
        <ApiKeyBanner />
      </ApiKeyProvider>,
    );

    expect(screen.getByRole('alert')).toHaveTextContent('API Key requise');

    fireEvent.change(screen.getByLabelText('api-key'), {
      target: { value: 'abc' },
    });
    fireEvent.click(screen.getByText('Enregistrer'));

    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('ne montre pas la bannière si une clé .env est définie', () => {
    vi.stubEnv('VITE_API_KEY', 'env-key');
    render(
      <ApiKeyProvider>
        <ApiKeyBanner />
      </ApiKeyProvider>,
    );
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
