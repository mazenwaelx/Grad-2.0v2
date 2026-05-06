# Estasher React Frontend

This is the React version of the Estasher (استشير) Egyptian Labor Law Assistant frontend.

## Features

- **Login/Signup**: User authentication with animated forms
- **Chat Interface**: Real-time chat with the AI legal assistant
- **File Upload**: Support for PDF, DOCX, and Excel files
- **Dark/Light Theme**: Toggle between themes with persistent preference
- **Reply to Messages**: Reply to specific messages in the chat
- **Copy Messages**: Easily copy any message content
- **Chat Management**: Create, rename, and delete chats

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API server running at `http://localhost:8000`

### Installation

1. Navigate to the react-frontend directory:
   ```bash
   cd react-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
react-frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── AuthLayout/         # Shared auth page layout with particles
│   │   └── ThemeToggle/        # Theme toggle button component
│   ├── context/
│   │   ├── AuthContext.js      # Authentication state management
│   │   └── ThemeContext.js     # Theme state management
│   ├── pages/
│   │   ├── Login/              # Login page
│   │   ├── Signup/             # Signup page
│   │   └── Chat/               # Main chat page
│   │       └── components/     # Chat-specific components
│   │           ├── Sidebar     # Chat list sidebar
│   │           ├── MessageList # Messages container
│   │           ├── Message     # Individual message
│   │           ├── TypingIndicator
│   │           ├── InputArea   # Message input with file upload
│   │           └── EmptyState  # Welcome screen with suggestions
│   ├── services/
│   │   └── api.js              # API service functions
│   ├── styles/
│   │   └── global.css          # Global styles and animations
│   ├── App.js                  # Main app with routing
│   └── index.js                # App entry point
└── package.json
```

## API Proxy

The development server is configured to proxy API requests to `http://localhost:8000`. Make sure your backend server is running before testing the frontend.

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder. You can serve it with any static file server or integrate it with your backend.

## Animations

The app preserves all the beautiful animations from the original HTML version:
- Floating particles on auth pages
- Scale-in logo animation
- Message slide-in effects
- Typing indicator dots
- Theme toggle rotation
- Button hover effects
- And more!
