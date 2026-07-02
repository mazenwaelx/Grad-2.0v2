import { createContext, useContext } from 'react';
import useLocalStorage from '../hooks/useLocalStorage';

const AuthContext = createContext(null);

/**
 * Access the auth context.
 * @returns {{ currentUser: object|null, login: function, logout: function }}
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

/**
 * Provides authentication state backed by localStorage.
 */
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser, removeCurrentUser] =
    useLocalStorage('currentUser', null);

  const login = (user) => setCurrentUser(user);
  
  const logout = () => {
    // Clear user data
    removeCurrentUser();
    
    // Clear message files from localStorage
    localStorage.removeItem('messageFiles');
    
    // Clear any other user-specific data
    console.log('User logged out, localStorage cleared');
  };

  return (
    <AuthContext.Provider value={{ currentUser, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
