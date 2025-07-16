import React, { useEffect, useState } from 'react';

export default function ModelSelector({ onChange }) {
  const [models, setModels] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/models-config');
        const data = await res.json();
        setModels(data.models || []);
      } catch (e) {
        console.error('Failed to load models', e);
      }
    }
    load();
  }, []);

  return (
    <select onChange={e => onChange(e.target.value)} data-testid="model-select">
      <option value="">Choose model</option>
      {models.map(m => (
        <option key={m} value={m}>{m}</option>
      ))}
    </select>
  );
}
