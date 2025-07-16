import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ModelSelector from '../src/components/ModelSelector';

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({ json: () => Promise.resolve({ models: ['a', 'b'] }) })
  );
});

afterEach(() => {
  jest.resetAllMocks();
});

test('loads models and renders options', async () => {
  render(<ModelSelector onChange={() => {}} />);
  await waitFor(() => screen.getByTestId('model-select'));
  expect(screen.getAllByRole('option').length).toBe(3); // including placeholder
});
