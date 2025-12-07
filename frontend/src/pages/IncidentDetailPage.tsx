import { useParams } from 'react-router-dom'
import { useIncidentDetail, useUpdateIncident } from '../api/hooks/useIncidents'
import { formatDistanceToNow, format } from 'date-fns'
import SeverityBadge from '../components/common/SeverityBadge'
import StatusBadge from '../components/common/StatusBadge'
import { ExternalLink, Check, Eye } from 'lucide-react'

export default function IncidentDetailPage() {
    const { id } = useParams<{ id: string }>()
    const { data: incident, isLoading, error } = useIncidentDetail(id)
    const updateMutation = useUpdateIncident()

    const handleStatusUpdate = async (newStatus: string) => {
        if (!id) return
        await updateMutation.mutateAsync({ id, status: newStatus })
    }

    if (isLoading) {
        return <div className="text-center py-12">Loading incident details...</div>
    }

    if (error || !incident) {
        return <div className="text-center py-12 text-red-600">Incident not found</div>
    }

    const metadata = incident.metadata_json || {}

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="card">
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        <SeverityBadge severity={incident.severity} />
                        <StatusBadge status={incident.status} />
                    </div>

                    <span className="text-sm text-gray-500">
                        {formatDistanceToNow(new Date(incident.first_seen_at), { addSuffix: true })}
                    </span>
                </div>

                <h1 className="text-2xl font-bold text-gray-900 mb-2">{incident.title}</h1>

                {incident.description && (
                    <p className="text-gray-700 mb-4">{incident.description}</p>
                )}

                {/* Actions */}
                {incident.status === 'open' && (
                    <div className="flex space-x-2">
                        <button
                            onClick={() => handleStatusUpdate('acknowledged')}
                            disabled={updateMutation.isPending}
                            className="btn-secondary flex items-center"
                        >
                            <Eye className="h-4 w-4 mr-2" />
                            Acknowledge
                        </button>
                        <button
                            onClick={() => handleStatusUpdate('resolved')}
                            disabled={updateMutation.isPending}
                            className="btn-primary flex items-center"
                        >
                            <Check className="h-4 w-4 mr-2" />
                            Resolve
                        </button>
                    </div>
                )}

                {incident.status === 'acknowledged' && (
                    <button
                        onClick={() => handleStatusUpdate('resolved')}
                        disabled={updateMutation.isPending}
                        className="btn-primary flex items-center"
                    >
                        <Check className="h-4 w-4 mr-2" />
                        Mark Resolved
                    </button>
                )}
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="card">
                    <h2 className="text-lg font-semibold mb-4">Incident Details</h2>
                    <dl className="space-y-3">
                        <div>
                            <dt className="text-sm font-medium text-gray-600">Type</dt>
                            <dd className="text-sm text-gray-900">{incident.type}</dd>
                        </div>

                        {incident.protocol && (
                            <div>
                                <dt className="text-sm font-medium text-gray-600">Protocol</dt>
                                <dd className="text-sm text-gray-900">{incident.protocol}</dd>
                            </div>
                        )}

                        {metadata.amount && metadata.token && (
                            <div>
                                <dt className="text-sm font-medium text-gray-600">Amount</dt>
                                <dd className="text-sm text-gray-900">
                                    {Number(metadata.amount).toLocaleString()} {metadata.token}
                                </dd>
                            </div>
                        )}

                        <div>
                            <dt className="text-sm font-medium text-gray-600">First Seen</dt>
                            <dd className="text-sm text-gray-900">
                                {format(new Date(incident.first_seen_at), 'PPpp')}
                            </dd>
                        </div>

                        <div>
                            <dt className="text-sm font-medium text-gray-600">Last Seen</dt>
                            <dd className="text-sm text-gray-900">
                                {format(new Date(incident.last_seen_at), 'PPpp')}
                            </dd>
                        </div>
                    </dl>
                </div>

                <div className="card">
                    <h2 className="text-lg font-semibold mb-4">Blockchain Data</h2>
                    <dl className="space-y-3">
                        {incident.contract_address && (
                            <div>
                                <dt className="text-sm font-medium text-gray-600">Contract</dt>
                                <dd className="text-sm font-mono text-gray-900 break-all">
                                    {incident.contract_address}
                                </dd>
                            </div>
                        )}

                        {incident.primary_wallet && (
                            <div>
                                <dt className="text-sm font-medium text-gray-600">Primary Wallet</dt>
                                <dd className="text-sm font-mono text-gray-900 break-all">
                                    {incident.primary_wallet}
                                </dd>
                            </div>
                        )}

                        {metadata.tx_hash && (
                            <div>
                                <dt className="text-sm font-medium text-gray-600">Transaction</dt>
                                <dd className="text-sm">
                                    <a
                                        href={`https://explorer.qubic.org/network/tx/${metadata.tx_hash}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary-600 hover:text-primary-700 flex items-center"
                                    >
                                        <span className="font-mono mr-2">{metadata.tx_hash.slice(0, 16)}...</span>
                                        <ExternalLink className="h-4 w-4" />
                                    </a>
                                </dd>
                            </div>
                        )}
                    </dl>
                </div>
            </div>

            {/* Related Events */}
            {incident.related_events && incident.related_events.length > 0 && (
                <div className="card">
                    <h2 className="text-lg font-semibold mb-4">Related Events</h2>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead>
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Event</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">From</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">To</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {incident.related_events.map((event) => (
                                    <tr key={event.id}>
                                        <td className="px-4 py-3 text-sm text-gray-900">{event.event_name}</td>
                                        <td className="px-4 py-3 text-sm font-mono text-gray-600">
                                            {event.from_address.slice(0, 8)}...
                                        </td>
                                        <td className="px-4 py-3 text-sm font-mono text-gray-600">
                                            {event.to_address.slice(0, 8)}...
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-900">
                                            {event.amount ? `${Number(event.amount).toLocaleString()} ${event.token_symbol}` : '-'}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-500">
                                            {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
