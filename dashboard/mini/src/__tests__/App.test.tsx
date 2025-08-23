import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App', () => {
  it('affiche le titre', () => {
    render(<App />);
    expect(
      screen.getByText('Mini Dashboard (read-only) — Fil G'),
    ).toBeInTheDocument();
  });
});
