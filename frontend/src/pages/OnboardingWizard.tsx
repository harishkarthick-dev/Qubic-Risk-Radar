import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, AlertCircle, Loader2, Copy, CheckCircle } from 'lucide-react'
import { apiClient } from '../api/client'

interface OnboardingStatus {
    completed: boolean
    current_step: number
    webhook_configured: boolean
    webhook_test_received: boolean
    notifications_configured: boolean
    discord_verified: boolean
    telegram_verified: boolean
}

export default function OnboardingWizard() {
    const navigate = useNavigate()
    const [currentStep, setCurrentStep] = useState(1)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    // Step 1: Webhook Setup
    const [alertId, setAlertId] = useState('')
    const [webhookUrl, setWebhookUrl] = useState('')
    const [webhookSecret, setWebhookSecret] = useState('')
    const [webhookConfigured, setWebhookConfigured] = useState(false)

    // Step 2: Test Polling
    const [testReceived, setTestReceived] = useState(false)
    const [polling, setPolling] = useState(false)

    // Step 3: Notifications
    const [discordId, setDiscordId] = useState('')
    const [telegramId, setTelegramId] = useState('')
    const [emailEnabled, setEmailEnabled] = useState(true)
    const [discordVerified, setDiscordVerified] = useState(false)
    const [telegramVerified, setTelegramVerified] = useState(false)
    const [discordLoading, setDiscordLoading] = useState(false)
    const [telegramLoading, setTelegramLoading] = useState(false)

    // Load onboarding status
    useEffect(() => {
        loadStatus()
    }, [])

    const loadStatus = async () => {
        try {
            const { data } = await apiClient.get<OnboardingStatus>('/onboarding/status')

            if (data.completed) {
                navigate('/dashboard')
                return
            }

            setCurrentStep(data.current_step)
            setWebhookConfigured(data.webhook_configured)
            setTestReceived(data.webhook_test_received)
            setDiscordVerified(data.discord_verified)
            setTelegramVerified(data.telegram_verified)

            if (data.webhook_configured && data.current_step === 1) {
                setCurrentStep(2)
            }
        } catch (err: any) {
            console.error('Failed to load status:', err)
        }
    }

    // Step 1: Create Webhook Config
    const handleCreateWebhook = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const { data } = await apiClient.post('/onboarding/webhook', {
                alert_id: alertId,
                description: 'Onboarding webhook'
            })

            setWebhookUrl(data.webhook_url)
            setWebhookSecret(data.webhook_secret)
            setWebhookConfigured(true)
            setCurrentStep(2)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to create webhook')
        } finally {
            setLoading(false)
        }
    }

    // Step 2: Poll for Test Webhook
    useEffect(() => {
        if (currentStep === 2 && webhookConfigured && !testReceived) {
            setPolling(true)
            const interval = setInterval(async () => {
                try {
                    const { data } = await apiClient.get('/onboarding/test-status')
                    if (data.received) {
                        setTestReceived(true)
                        setPolling(false)
                        setCurrentStep(3)
                        clearInterval(interval)
                    }
                } catch (err) {
                    console.error('Polling error:', err)
                }
            }, 3000) // Poll every 3 seconds

            return () => clearInterval(interval)
        }
    }, [currentStep, webhookConfigured, testReceived])

    // Step 3: Verify Discord
    const handleVerifyDiscord = async () => {
        setError('')
        setDiscordLoading(true)

        try {
            const { data } = await apiClient.post('/onboarding/verify-discord', {
                discord_user_id: discordId
            })

            if (data.success) {
                setDiscordVerified(true)
            } else {
                setError(data.error || 'Discord verification failed')
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to verify Discord')
        } finally {
            setDiscordLoading(false)
        }
    }

    // Step 3: Verify Telegram
    const handleVerifyTelegram = async () => {
        setError('')
        setTelegramLoading(true)

        try {
            const { data } = await apiClient.post('/onboarding/verify-telegram', {
                telegram_chat_id: telegramId
            })

            if (data.success) {
                setTelegramVerified(true)
            } else {
                setError(data.error || 'Telegram verification failed')
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to verify Telegram')
        } finally {
            setTelegramLoading(false)
        }
    }

    // Complete Onboarding
    const handleComplete = async () => {
        if (!discordVerified && !telegramVerified) {
            setError('Please verify at least one notification channel (Discord or Telegram)')
            return
        }

        setError('')
        setLoading(true)

        try {
            await apiClient.post('/onboarding/complete', {
                email_notifications_enabled: emailEnabled
            })

            // Success! Redirect to dashboard
            setTimeout(() => {
                navigate('/dashboard')
            }, 2000)
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to complete onboarding')
            setLoading(false)
        }
    }

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text)
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full">
                {/* Progress Steps */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        {[1, 2, 3].map((step) => (
                            <div key={step} className="flex items-center flex-1">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${currentStep > step ? 'bg-green-500 border-green-500 text-white' :
                                        currentStep === step ? 'bg-blue-500 border-blue-500 text-white' :
                                            'bg-white border-gray-300 text-gray-400'
                                    }`}>
                                    {currentStep > step ? <Check size={20} /> : step}
                                </div>
                                {step < 3 && (
                                    <div className={`flex-1 h-1 mx-2 ${currentStep > step ? 'bg-green-500' : 'bg-gray-300'
                                        }`} />
                                )}
                            </div>
                        ))}
                    </div>
                    <div className="flex justify-between mt-2 text-sm">
                        <span className={currentStep >= 1 ? 'text-gray-900 font-medium' : 'text-gray-500'}>
                            Webhook Setup
                        </span>
                        <span className={currentStep >= 2 ? 'text-gray-900 font-medium' : 'text-gray-500'}>
                            Test Webhook
                        </span>
                        <span className={currentStep >= 3 ? 'text-gray-900 font-medium' : 'text-gray-500'}>
                            Notifications
                        </span>
                    </div>
                </div>

                {/* Content Card */}
                <div className="bg-white rounded-lg shadow-lg p-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        {currentStep === 1 && 'Setup Your Webhook'}
                        {currentStep === 2 && 'Test Your Webhook'}
                        {currentStep === 3 && 'Configure Notifications'}
                    </h1>
                    <p className="text-gray-600 mb-6">
                        {currentStep === 1 && 'Connect your EasyConnect alert to start receiving notifications'}
                        {currentStep === 2 && 'Send a test notification from EasyConnect to verify the connection'}
                        {currentStep === 3 && 'Choose how you want to receive alerts'}
                    </p>

                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                            <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
                            <p className="text-red-700 text-sm">{error}</p>
                        </div>
                    )}

                    {/* Step 1: Webhook Setup */}
                    {currentStep === 1 && !webhookConfigured && (
                        <form onSubmit={handleCreateWebhook}>
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    EasyConnect Alert ID
                                </label>
                                <input
                                    type="text"
                                    value={alertId}
                                    onChange={(e) => setAlertId(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="Enter your alert ID from EasyConnect"
                                    required
                                />
                                <p className="mt-2 text-sm text-gray-500">
                                    Find this in your EasyConnect dashboard under alert settings
                                </p>
                            </div>

                            <button
                                type="submit"
                                disabled={loading || !alertId}
                                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="animate-spin" size={20} />
                                        Creating Webhook...
                                    </>
                                ) : (
                                    'Create Webhook Configuration'
                                )}
                            </button>
                        </form>
                    )}

                    {/* Step 1: Webhook Created - Show URL */}
                    {currentStep === 1 && webhookConfigured && (
                        <div className="space-y-4">
                            <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
                                <CheckCircle className="text-green-500" size={24} />
                                <p className="text-green-800 font-medium">Webhook configured successfully!</p>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Webhook URL
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={webhookUrl}
                                        readOnly
                                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                                    />
                                    <button
                                        onClick={() => copyToClipboard(webhookUrl)}
                                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg"
                                    >
                                        <Copy size={20} />
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Webhook Secret
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={webhookSecret}
                                        readOnly
                                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                                    />
                                    <button
                                        onClick={() => copyToClipboard(webhookSecret)}
                                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg"
                                    >
                                        <Copy size={20} />
                                    </button>
                                </div>
                            </div>

                            <button
                                onClick={() => setCurrentStep(2)}
                                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700"
                            >
                                Next: Test Webhook
                            </button>
                        </div>
                    )}

                    {/* Step 2: Waiting for Test */}
                    {currentStep === 2 && !testReceived && (
                        <div className="text-center py-8">
                            <Loader2 className="animate-spin mx-auto mb-4 text-blue-500" size={48} />
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                Waiting for test notification...
                            </h3>
                            <p className="text-gray-600 mb-4">
                                Send a test notification from your EasyConnect dashboard
                            </p>
                            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-left">
                                <h4 className="font-medium text-blue-900 mb-2">Instructions:</h4>
                                <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
                                    <li>Go to your EasyConnect dashboard</li>
                                    <li>Find your alert configuration</li>
                                    <li>Click "Send Test Notification"</li>
                                    <li>We'll automatically detect it here</li>
                                </ol>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Test Received */}
                    {currentStep === 2 && testReceived && (
                        <div className="text-center py-8">
                            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Check className="text-green-600" size={32} />
                            </div>
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                Test notification received!
                            </h3>
                            <p className="text-gray-600 mb-6">
                                Your webhook is working correctly
                            </p>
                            <button
                                onClick={() => setCurrentStep(3)}
                                className="bg-blue-600 text-white py-3 px-8 rounded-lg font-medium hover:bg-blue-700"
                            >
                                Continue to Notifications
                            </button>
                        </div>
                    )}

                    {/* Step 3: Configure Notifications */}
                    {currentStep === 3 && (
                        <div className="space-y-6">
                            {/* Discord */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Discord User ID (Optional)
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={discordId}
                                        onChange={(e) => setDiscordId(e.target.value)}
                                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        placeholder="Your Discord User ID"
                                        disabled={discordVerified}
                                    />
                                    <button
                                        onClick={handleVerifyDiscord}
                                        disabled={!discordId || discordVerified || discordLoading}
                                        className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        {discordLoading ? (
                                            <Loader2 className="animate-spin" size={20} />
                                        ) : discordVerified ? (
                                            <><Check size={20} /> Verified</>
                                        ) : (
                                            'Verify'
                                        )}
                                    </button>
                                </div>
                                <p className="mt-1 text-xs text-gray-500">
                                    <a href="#" className="text-blue-600 hover:underline">How to find your Discord ID</a>
                                </p>
                            </div>

                            {/* Telegram */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Telegram Chat ID (Optional)
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={telegramId}
                                        onChange={(e) => setTelegramId(e.target.value)}
                                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                        placeholder="Your Telegram Chat ID"
                                        disabled={telegramVerified}
                                    />
                                    <button
                                        onClick={handleVerifyTelegram}
                                        disabled={!telegramId || telegramVerified || telegramLoading}
                                        className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        {telegramLoading ? (
                                            <Loader2 className="animate-spin" size={20} />
                                        ) : telegramVerified ? (
                                            <><Check size={20} /> Verified</>
                                        ) : (
                                            'Verify'
                                        )}
                                    </button>
                                </div>
                                <p className="mt-1 text-xs text-gray-500">
                                    Start chat with @YourBotName to get your chat ID
                                </p>
                            </div>

                            {/* Email */}
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div>
                                    <p className="font-medium text-gray-900">Email Notifications</p>
                                    <p className="text-sm text-gray-600">Receive alerts via email</p>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={emailEnabled}
                                        onChange={(e) => setEmailEnabled(e.target.checked)}
                                        className="sr-only peer"
                                    />
                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                            </div>

                            {/* Validation Message */}
                            {!discordVerified && !telegramVerified && (
                                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                    <p className="text-sm text-yellow-800">
                                        <strong>Note:</strong> Please verify at least one notification channel (Discord or Telegram) to continue.
                                    </p>
                                </div>
                            )}

                            {/* Complete Button */}
                            <button
                                onClick={handleComplete}
                                disabled={loading || (!discordVerified && !telegramVerified)}
                                className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="animate-spin" size={20} />
                                        Completing Setup...
                                    </>
                                ) : (
                                    '🎉 Complete Setup'
                                )}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
