import React from 'react';
import { render, screen } from '@testing-library/react';
import ChatCanvas from '../src/components/ChatCanvas';

test('shows model badge per message', () => {
  const msgs = [{ text: 'hi', model: 'gpt-4' }];
  render(<ChatCanvas messages={msgs} />);
  expect(screen.getByTestId('model-badge').textContent).toContain('gpt-4');
});
