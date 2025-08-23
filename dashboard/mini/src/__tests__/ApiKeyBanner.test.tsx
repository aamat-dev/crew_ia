import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { ApiKeyProvider, useApiKey } from '../state/ApiKeyContext';
import ApiKeyBanner from '../components/ApiKeyBanner';

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <ApiKeyProvider>{children}</ApiKeyProvider>
);

const Display = () => {
  const { apiKey } = useApiKey();
  return <div data-testid="currentKey">{apiKey}</div>;
};

describe('ApiKeyBanner', () => {
  it('rendu initial', () => {
    render(
      <Wrapper>
        <ApiKeyBanner />
      </Wrapper>
    );
    const input = screen.getByTestId('apiKeyInput') as HTMLInputElement;
    const toggle = screen.getByTestId('useEnvToggle') as HTMLInputElement;
    expect(input.value).toBe('');
    expect(input.disabled).toBe(false);
    expect(toggle.checked).toBe(false);
    expect(screen.getByTestId('useButton')).toBeInTheDocument();
  });

  it("saisie et utilisation d'une clé", () => {
    render(
      <Wrapper>
        <ApiKeyBanner />
        <Display />
      </Wrapper>
    );
    const input = screen.getByTestId('apiKeyInput') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'secret' } });
    fireEvent.click(screen.getByTestId('useButton'));
    expect(screen.getByTestId('currentKey').textContent).toBe('secret');
  });

  it('toggle clé .env active', () => {
    render(
      <Wrapper>
        <ApiKeyBanner />
      </Wrapper>
    );
    const input = screen.getByTestId('apiKeyInput') as HTMLInputElement;
    const toggle = screen.getByTestId('useEnvToggle') as HTMLInputElement;
    fireEvent.click(toggle);
    expect(toggle.checked).toBe(true);
    expect(input.disabled).toBe(true);
    expect(screen.getByTestId('envActiveBadge').textContent).toContain('active');
  });

  it('toggle désactivé rend le champ éditable', () => {
    render(
      <Wrapper>
        <ApiKeyBanner />
      </Wrapper>
    );
    const input = screen.getByTestId('apiKeyInput') as HTMLInputElement;
    const toggle = screen.getByTestId('useEnvToggle') as HTMLInputElement;
    fireEvent.click(toggle);
    fireEvent.click(toggle);
    expect(toggle.checked).toBe(false);
    expect(input.disabled).toBe(false);
  });

  it('pas de persistance après remount', () => {
    const view = render(
      <Wrapper>
        <ApiKeyBanner />
        <Display />
      </Wrapper>
    );
    const input = screen.getByTestId('apiKeyInput') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'temp' } });
    fireEvent.click(screen.getByTestId('useButton'));
    expect(screen.getByTestId('currentKey').textContent).toBe('temp');
    view.unmount();
    render(
      <Wrapper>
        <ApiKeyBanner />
        <Display />
      </Wrapper>
    );
    expect(screen.getByTestId('currentKey').textContent).toBe('');
  });
});
