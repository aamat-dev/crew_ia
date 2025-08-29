import { describe, it, expect } from 'vitest';
import { parseLinkHeader } from '../api/links';

describe('parseLinkHeader', () => {
  it('prev only', () => {
    const { prev, next } = parseLinkHeader('</runs?page=1>; rel="prev"');
    expect(prev).toBeInstanceOf(URL);
    expect(prev?.searchParams.get('page')).toBe('1');
    expect(next).toBeUndefined();
  });

  it('next only', () => {
    const { prev, next } = parseLinkHeader('</runs?page=2>; rel="next"');
    expect(next).toBeInstanceOf(URL);
    expect(next?.searchParams.get('page')).toBe('2');
    expect(prev).toBeUndefined();
  });

  it('prev and next', () => {
    const { prev, next } = parseLinkHeader(
      '</runs?page=1>; rel="prev", </runs?page=3>; rel="next"',
    );
    expect(prev).toBeInstanceOf(URL);
    expect(next).toBeInstanceOf(URL);
  });

  it('no links', () => {
    const { prev, next } = parseLinkHeader('');
    expect(prev).toBeUndefined();
    expect(next).toBeUndefined();
  });

  it('preserves query params', () => {
    const { next } = parseLinkHeader(
      '</runs?page=2&status=running>; rel="next"',
    );
    expect(next?.searchParams.get('status')).toBe('running');
  });
});
