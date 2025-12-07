import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { apiClient } from '../api/client'
import { CheckCircle, XCircle, Loader } from 'lucide-react'

export default function VerifyEmailPage() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
    const [message, setMessage] = useState('')

    useEffect(() => {
        const verifyEmail = async () => {
            const token = searchParams.get('token')

            if (!token) {
                setStatus('error')
                setMessage('Invalid verification link')
                return
            }

            try {
                const { data } = await apiClient.get(`/auth/verify-email?token=${token}`)
                setStatus('success')
                setMessage(data.message)

                // Redirect to login after 3 seconds
                setTimeout(() => {
                    navigate('/login')
                }, 3000)
            } catch (error: any) {
                setStatus('error')
                setMessage(error.response?.data?.detail || 'Failed to verify email')
            }
        }

        verifyEmail()
    }, [searchParams, navigate])

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                    <div className="text-center">
                        {status === 'loading' && (
                            <>
                                <Loader className="mx-auto h-12 w-12 text-primary-600 animate-spin" />
                                <h2 className="mt-4 text-2xl font-bold text-gray-900">Verifying your email...</h2>
                            </>
                        )}

                        {status === 'success' && (
                            <>
                                <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
                                <h2 className="mt-4 text-2xl font-bold text-gray-900">Email verified!</h2>
                                <p className="mt-2 text-sm text-gray-600">{message}</p>
                                <p className="mt-4 text-sm text-gray-600">
                                    Your Pro trial has been activated. Redirecting to login...
                                </p>
                            </>
                        )}

                        {status === 'error' && (
                            <>
                                <XCircle className="mx-auto h-12 w-12 text-red-500" />
                                <h2 className="mt-4 text-2xl font-bold text-gray-900">Verification failed</h2>
                                <p className="mt-2 text-sm text-gray-600">{message}</p>
                                <div className="mt-6">
                                    <button
                                        onClick={() => navigate('/login')}
                                        className="btn-primary"
                                    >
                                        Go to Login
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
