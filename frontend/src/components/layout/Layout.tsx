import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Activity, Home, AlertTriangle, Webhook, BarChart3 } from 'lucide-react'

interface LayoutProps {
    children: React.ReactNode
}

const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/detections', label: 'Detections', icon: AlertTriangle },
    { path: '/webhooks', label: 'Webhooks', icon: Webhook },
    { path: '/analytics', label: 'Analytics', icon: BarChart3 },
]

export const Layout: React.FC<LayoutProps> = ({ children }) => {
    const location = useLocation()

    return (
        <div className="min-h-screen flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center">
                            <Activity className="h-8 w-8 text-primary-600" />
                            <span className="ml-2 text-xl font-bold text-gray-900">
                                Qubic Risk Radar
                            </span>
                        </div>

                        <nav className="flex space-x-4">
                            {navItems.map((item) => {
                                const Icon = item.icon
                                const isActive = location.pathname === item.path

                                return (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive
                                            ? 'bg-primary-100 text-primary-700'
                                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                                            }`}
                                    >
                                        <Icon className="h-4 w-4 mr-2" />
                                        {item.label}
                                    </Link>
                                )
                            })}
                        </nav>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 bg-gray-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {children}
                </div>
            </main>

            {/* Footer */}
            <footer className="bg-white border-t border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <p className="text-center text-sm text-gray-500">
                        &copy; 2025 Qubic Risk Radar - Production-grade blockchain monitoring and alerting
                    </p>
                </div>
            </footer>
        </div>
    )
}
