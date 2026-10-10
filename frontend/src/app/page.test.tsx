import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import Page from './page';

test('renders the main heading', () => {
  render(<Page />);
  expect(screen.getByRole('heading', { level: 1 })).toBeDefined();
});
