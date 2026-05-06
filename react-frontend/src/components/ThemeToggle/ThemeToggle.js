import React from 'react';
import { useTheme } from '../../context/ThemeContext';
import './ThemeToggle.css';

const ThemeToggle = ({ className = '' }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div 
      className={`theme-toggle ${className}`}
      onClick={toggleTheme}
      title="Toggle Theme"
    >
      <span className="theme-icon">
        {theme === 'dark' ? '🌙' : '☀️'}
      </span>
    </div>
  );
};

export default ThemeToggle;
