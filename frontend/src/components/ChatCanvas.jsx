import React from 'react';

export default function ChatCanvas({ messages }) {
  return (
    <ul>
      {messages.map((m, idx) => (
        <li key={idx}>
          <span>{m.text}</span>
          {m.model && <span data-testid="model-badge"> [{m.model}]</span>}
        </li>
      ))}
    </ul>
  );
}
