import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import AuthLayout from '../../components/AuthLayout';
import ThemeToggle from '../../components/ThemeToggle';
import { login as apiLogin } from '../../services/api';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await apiLogin(email, password);
      setSuccess(true);
      login({ email: data.email, name: data.name });
      setTimeout(() => navigate('/chat'), 800);
    } catch (err) {
      setError(err.message || 'Invalid email or password');
      console.error('Login error:', err);
      setTimeout(() => setError(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <ThemeToggle className="fixed" />
      
      <div className="auth-box">
        <div className="auth-header">
          <div className="logo">⚖️</div>
          <h1>Estasher <span className="arabic">استشير</span></h1>
          <p>مساعدك الموثوق في قانون العمل المصري</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <div className="input-wrapper">
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required 
                placeholder="your@email.com"
              />
              <span className="input-icon">📧</span>
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="input-wrapper">
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
                placeholder="••••••••"
              />
              <span className="input-icon">🔒</span>
            </div>
          </div>

          <button 
            type="submit" 
            className={`btn-primary ${loading ? 'loading' : ''} ${success ? 'success' : ''}`}
            disabled={loading}
          >
            {success ? '✓ Welcome Counsel!' : loading ? '' : 'Login'}
          </button>
        </form>

        <div className="auth-footer">
          Don't have an account? <Link to="/signup">Sign up</Link>
        </div>
      </div>
    </AuthLayout>
  );
};

export default Login;
