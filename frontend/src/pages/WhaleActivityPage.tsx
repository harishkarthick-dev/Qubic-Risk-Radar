import { useState } from 'react'
import { useWhaleActivity } from '../api/hooks/useMetrics'
import { formatDistanceToNow } from 'date-fns'
import { TrendingUp, ExternalLink } from 'lucide-react'

export default function WhaleActivityPage() {
    const [hours, setHours] = useState(24)
    const [minAmount, setMinAmount] = useState(1000000)

    const { data, isLoading } = useWhaleActivity(hours, minAmount)

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Whale Activity</h1>
                <p className="text-gray-600 mt-1">Track large token transfers on the Qubic network</p>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="flex items-center space-x-4">
                    <TrendingUp className="h-5 w-5 text-gray-400" />

                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                            Time Window
                        </label>
                        <select
                            value={hours}
                            onChange={(e) => setHours(Number(e.target.value))}
                            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="1">Last Hour</option>
                            <option value="6">Last 6 Hours</option>
                            <option value="24">Last 24 Hours</option>
                            <option value="168">Last Week</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                            Minimum Amount
                        </label>
                        <select
                            value={minAmount}
                            onChange={(e) => setMinAmount(Number(e.target.value))}
                            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                            <option value="500000">500K QUBIC</option>
                            <option value="1000000">1M QUBIC</option>
                            <option value="5000000">5M QUBIC</option>
                            <option value="10000000">10M QUBIC</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Whale Transfers Table */}
            <div className="card">
                <h2 className="text-lg font-semibold mb-4">
                    Large Transfers ({data?.total_count || 0})
                </h2>

                {isLoading ? (
                    <div className="text-center py-8 text-gray-500">Loading whale activity...</div>
                ) : data && data.transfers.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead>
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">From</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">To</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contract</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tx</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {data.transfers.map((transfer) => (
                                    <tr key={transfer.id} className="hover:bg-gray-50">
                                        <td className="px-4 py-3 text-sm text-gray-500">
                                            {formatDistanceToNow(new Date(transfer.timestamp), { addSuffix: true })}
                                        </td>
                                        <td className="px-4 py-3 text-sm font-mono text-gray-900">
                                            {transfer.from_address.slice(0, 10)}...
                                        </td>
                                        <td className="px-4 py-3 text-sm font-mono text-gray-900">
                                            {transfer.to_address.slice(0, 10)}...
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            <span className="font-semibold text-critical-600">
                                                {Number(transfer.amount).toLocaleString()} {transfer.token_symbol}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-600">
                                            {transfer.contract || 'N/A'}
                                        </td>
                                        <td className="px-4 py-3 text-sm">
                                            {transfer.tx_hash && (
                                                <a
                                                    href={`https://explorer.qubic.org/network/tx/${transfer.tx_hash}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-primary-600 hover:text-primary-700"
                                                >
                                                    <ExternalLink className="h-4 w-4" />
                                                </a>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        No whale transfers found in selected time window
                    </div>
                )}
            </div>
        </div>
    )
}
