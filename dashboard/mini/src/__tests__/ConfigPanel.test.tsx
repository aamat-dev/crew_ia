import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import ConfigPanel from '../components/ConfigPanel';

describe('ConfigPanel', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("enregistre l'URL saisie", () => {
    render(<ConfigPanel />);
    const input = screen.getByTestId('apiUrlInput');
    fireEvent.change(input, { target: { value: 'https://example.com' } });
    fireEvent.click(screen.getByText('Enregistrer'));
    expect(localStorage.getItem('apiBaseUrl')).toBe('https://example.com');
    expect(screen.getByTestId('apiUrlMessage')).toHaveTextContent('Enregistré');
  });
});
