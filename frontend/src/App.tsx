import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

// Pages
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import Dashboard from './pages/Dashboard';
import Detections from './pages/Detections';
import WebhooksManagement from './pages/WebhooksManagement';
import Analytics from './pages/Analytics';

function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <div className="app">
                    <Routes>
                        {/* Public routes */}
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/signup" element={<SignupPage />} />

                        {/* Protected routes */}
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/detections" element={<Detections />} />
                        <Route path="/webhooks" element={<WebhooksManagement />} />
                        <Route path="/analytics" element={<Analytics />} />
                    </Routes>
                </div>
            </AuthProvider>
        </BrowserRouter>
    );
}

export default App;
