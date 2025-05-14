import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [ping, setPing] = useState('');

  useEffect(() => {
    fetch('/api/ping')
      .then(res => res.json())
      .then(data => setPing(data.message))
      .catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-4">Dashboard</h1>
      {ping && (
        <p className="mb-4">Backend says: <span className="font-mono">{ping}</span></p>
      )}
      <Link
        to="/quiz"
        className="inline-block px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Start Quiz
      </Link>
    </div>
  );
}
