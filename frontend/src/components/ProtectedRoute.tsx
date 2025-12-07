import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { user, loading } = useAuth()
    const location = useLocation()

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading...</p>
            </div>
        </div>
    }

    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />
    }

    // Redirect to onboarding if not completed (except if already on onboarding page)
    if (!user.onboarding_completed && location.pathname !== '/onboarding') {
        return <Navigate to="/onboarding" replace />
    }

    return <>{children}</>
}
