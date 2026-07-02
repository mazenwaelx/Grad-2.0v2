import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import AuthLayout from '../../components/AuthLayout';
import ThemeToggle from '../../components/ThemeToggle';
import { register as apiRegister } from '../../services/api';
import estasheerLogo from '../../assets/images/estasheer-logo.png';
import './Signup.css';

const Signup = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({ level: '', width: 0 });
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const checkPasswordStrength = (pwd) => {
    let strength = 0;
    if (pwd.length >= 6) strength++;
    if (pwd.length >= 10) strength++;
    if (/[A-Z]/.test(pwd)) strength++;
    if (/[0-9]/.test(pwd)) strength++;
    if (/[^A-Za-z0-9]/.test(pwd)) strength++;

    if (pwd.length === 0) {
      return { level: '', width: 0 };
    } else if (strength <= 2) {
      return { level: 'weak', width: 33 };
    } else if (strength <= 4) {
      return { level: 'medium', width: 66 };
    } else {
      return { level: 'strong', width: 100 };
    }
  };

  const handlePasswordChange = (e) => {
    const pwd = e.target.value;
    setPassword(pwd);
    setPasswordStrength(checkPasswordStrength(pwd));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (password !== confirmPassword) {
      setError('❌ Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const data = await apiRegister(email, name, password);
      setSuccess('✓ Account created successfully! Redirecting...');
      login({ email: data.email, name: data.name });
      setTimeout(() => navigate('/chat'), 1500);
    } catch (err) {
      setError('❌ ' + (err.message || 'Registration failed'));
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <ThemeToggle className="fixed" />
      
      <div className="auth-box">
        <div className="auth-header">
          <div className="logo">
            <img src={estasheerLogo} alt="Estasheer Logo" />
          </div>
          <h1>Estasheer <span className="arabic">استشير</span></h1>
          <p>إنشاء حساب جديد</p>
        </div>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>الاسم الكامل</label>
            <div className="input-wrapper">
              <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                required 
                placeholder="أحمد محمد"
              />
              <span className="input-icon">👤</span>
            </div>
          </div>

          <div className="form-group">
            <label>البريد الإلكتروني</label>
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
            <label>كلمة المرور</label>
            <div className="input-wrapper">
              <input 
                type="password" 
                value={password}
                onChange={handlePasswordChange}
                required 
                minLength={6}
                placeholder="••••••••"
              />
              <span className="input-icon">🔒</span>
            </div>
            <div className={`password-strength ${password ? 'visible' : ''}`}>
              <div 
                className={`password-strength-bar ${passwordStrength.level}`}
                style={{ width: `${passwordStrength.width}%` }}
              ></div>
            </div>
          </div>

          <div className="form-group">
            <label>تأكيد كلمة المرور</label>
            <div className="input-wrapper">
              <input 
                type="password" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required 
                minLength={6}
                placeholder="••••••••"
              />
              <span className="input-icon">🔐</span>
            </div>
          </div>

          <button 
            type="submit" 
            className={`btn-primary ${loading ? 'loading' : ''} ${success ? 'success' : ''}`}
            disabled={loading}
          >
            {success ? '✓ تم بنجاح!' : loading ? '' : 'إنشاء حساب'}
          </button>
        </form>

        <div className="auth-footer">
          لديك حساب بالفعل؟ <Link to="/login">تسجيل الدخول</Link>
        </div>
      </div>
    </AuthLayout>
  );
};

export default Signup;
