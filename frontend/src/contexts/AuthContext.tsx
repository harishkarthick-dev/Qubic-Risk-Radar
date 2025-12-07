import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient } from '../api/client'

interface User {
    id: string
    email: string
    full_name: string
    is_verified: boolean
    onboarding_completed: boolean
}

interface AuthContextType {
    user: User | null
    isAuthenticated: boolean
    loading: boolean
    login: (email: string, password: string) => Promise<void>
    signup: (email: string, password: string, fullName: string) => Promise<{ message: string }>
    logout: () => void
    refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)

    // Load user from token on mount
    useEffect(() => {
        const token = localStorage.getItem('access_token')
        if (token) {
            refreshUser()
        } else {
            setLoading(false)
        }
    }, [])

    const refreshUser = async () => {
        try {
            const { data } = await apiClient.get('/auth/me')
            setUser(data)
        } catch (error) {
            localStorage.removeItem('access_token')
            setUser(null)
        } finally {
            setLoading(false)
        }
    }

    const login = async (email: string, password: string) => {
        // Use FormData for OAuth2 format
        const formData = new FormData()
        formData.append('username', email) // OAuth2 uses "username" field
        formData.append('password', password)

        const { data } = await apiClient.post('/auth/login', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })

        localStorage.setItem('access_token', data.access_token)
        setUser(data.user)
    }

    const signup = async (email: string, password: string, fullName: string) => {
        const { data } = await apiClient.post('/auth/signup', {
            email,
            password,
            full_name: fullName
        })
        return data
    }

    const logout = () => {
        localStorage.removeItem('access_token')
        setUser(null)
        window.location.href = '/login'
    }

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated: !!user,
            loading,
            login,
            signup,
            logout,
            refreshUser
        }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within AuthProvider')
    }
    return context
}
