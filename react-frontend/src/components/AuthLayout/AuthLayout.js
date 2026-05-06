import { useMemo } from 'react';
import './AuthLayout.css';

const LEGAL_SYMBOLS = ['⚖️', '📜', '🏛️', '⚖', '§'];

const AuthLayout = ({ children }) => {
  const particles = useMemo(() => (
    Array.from({ length: 15 }, (_, i) => {
      const isSymbol = i % 4 === 0;
      const size = Math.random() * 4 + 2;
      return {
        id: i,
        isSymbol,
        symbol: isSymbol
          ? LEGAL_SYMBOLS[Math.floor(Math.random() * LEGAL_SYMBOLS.length)]
          : null,
        style: {
          left: `${Math.random() * 100}%`,
          animationDelay: `${Math.random() * 20}s`,
          animationDuration: `${Math.random() * 10 + 15}s`,
          ...(isSymbol
            ? { fontSize: `${Math.random() * 15 + 10}px` }
            : { width: `${size}px`, height: `${size}px` }),
        },
      };
    })
  ), []);

  return (
    <div className="auth-page">
      <div className="background"></div>
      <div className="particles">
        {particles.map(p => (
          <div
            key={p.id}
            className={`particle${p.isSymbol ? ' legal-symbol' : ''}`}
            style={p.style}
          >
            {p.symbol}
          </div>
        ))}
      </div>
      <div className="auth-container">
        {children}
      </div>
    </div>
  );
};

export default AuthLayout;
