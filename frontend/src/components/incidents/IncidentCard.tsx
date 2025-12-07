import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import type { Incident } from '../../types'
import SeverityBadge from '../common/SeverityBadge'
import StatusBadge from '../common/StatusBadge'
import { ExternalLink } from 'lucide-react'

interface IncidentCardProps {
    incident: Incident
}

export default function IncidentCard({ incident }: IncidentCardProps) {
    const metadata = incident.metadata_json || {}

    return (
        <Link
            to={`/incidents/${incident.id}`}
            className="block card hover:shadow-md transition-shadow"
        >
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                    <SeverityBadge severity={incident.severity} />
                    <StatusBadge status={incident.status} />
                </div>
                <span className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(incident.first_seen_at), { addSuffix: true })}
                </span>
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {incident.title}
            </h3>

            {incident.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {incident.description}
                </p>
            )}

            <div className="flex flex-wrap gap-3 text-sm">
                {incident.type && (
                    <div className="flex items-center text-gray-700">
                        <span className="font-medium">Type:</span>
                        <span className="ml-1">{incident.type}</span>
                    </div>
                )}

                {incident.protocol && (
                    <div className="flex items-center text-gray-700">
                        <span className="font-medium">Protocol:</span>
                        <span className="ml-1">{incident.protocol}</span>
                    </div>
                )}

                {metadata.amount && metadata.token && (
                    <div className="flex items-center text-gray-700">
                        <span className="font-medium">Amount:</span>
                        <span className="ml-1">
                            {Number(metadata.amount).toLocaleString()} {metadata.token}
                        </span>
                    </div>
                )}
            </div>

            {metadata.tx_hash && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center text-xs text-primary-600">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View Transaction
                    </div>
                </div>
            )}
        </Link>
    )
}
