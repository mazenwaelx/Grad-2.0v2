import { Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import Chat from './pages/Chat';
import { useEffect } from 'react';

// Auto-login wrapper that checks URL params
const AutoLoginWrapper = ({ children }) => {
  const { currentUser, login } = useAuth();
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    // Check if user info is in URL parameters (coming from website)
    const userEmail = searchParams.get('userEmail');
    const userName = searchParams.get('userName');
    
    if (userEmail && userName) {
      // Auto-login the user only if not already logged in or different user
      if (!currentUser || currentUser.email !== userEmail) {
        console.log('Auto-logging in user:', userEmail);
        login({
          email: userEmail,
          name: userName
        });
      }
    } else if (!currentUser) {
      // If no user and no URL params, create a guest user
      console.log('Creating guest user');
      login({
        email: 'guest@estasheer.com',
        name: 'Guest User'
      });
    }
  }, [searchParams]); // Remove currentUser and login from dependencies to prevent loops
  
  // Show loading while setting up authentication
  if (!currentUser) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: '#0a0e27',
        color: '#d4af37',
        fontSize: '20px',
        fontFamily: 'sans-serif'
      }}>
        Loading AI Chat...
      </div>
    );
  }
  
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={
        <AutoLoginWrapper>
          <Chat />
        </AutoLoginWrapper>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <AppRoutes />
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
