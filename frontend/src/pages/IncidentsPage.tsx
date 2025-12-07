import { useState } from 'react'
import { useIncidents } from '../api/hooks/useIncidents'
import IncidentCard from '../components/incidents/IncidentCard'
import { Filter } from 'lucide-react'

export default function IncidentsPage() {
    const [severity, setSeverity] = useState<string>('')
    const [status, setStatus] = useState<string>('')
    const [page, setPage] = useState(1)

    const { data, isLoading, error } = useIncidents({
        severity: severity || undefined,
        status: status || undefined,
        page,
        page_size: 20,
    })

    const totalPages = data ? Math.ceil(data.total / data.page_size) : 0

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Incidents</h1>
                <p className="text-gray-600 mt-1">Monitor and manage blockchain security incidents</p>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="flex items-center space-x-4">
                    <Filter className="h-5 w-5 text-gray-400" />

                    <select
                        value={severity}
                        onChange={(e) => setSeverity(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                        <option value="">All Severities</option>
                        <option value="CRITICAL">Critical</option>
                        <option value="WARNING">Warning</option>
                        <option value="INFO">Info</option>
                    </select>

                    <select
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                        <option value="">All Statuses</option>
                        <option value="open">Open</option>
                        <option value="acknowledged">Acknowledged</option>
                        <option value="resolved">Resolved</option>
                    </select>

                    {(severity || status) && (
                        <button
                            onClick={() => {
                                setSeverity('')
                                setStatus('')
                                setPage(1)
                            }}
                            className="text-sm text-gray-600 hover:text-gray-900"
                        >
                            Clear filters
                        </button>
                    )}
                </div>
            </div>

            {/* Incidents List */}
            {isLoading ? (
                <div className="text-center py-12 text-gray-500">Loading incidents...</div>
            ) : error ? (
                <div className="text-center py-12 text-red-600">Error loading incidents</div>
            ) : data && data.incidents.length > 0 ? (
                <>
                    <div className="space-y-4">
                        {data.incidents.map((incident) => (
                            <IncidentCard key={incident.id} incident={incident} />
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex justify-center items-center space-x-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                            >
                                Previous
                            </button>

                            <span className="text-sm text-gray-600">
                                Page {page} of {totalPages}
                            </span>

                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            ) : (
                <div className="text-center py-12 text-gray-500">
                    No incidents found
                </div>
            )}
        </div>
    )
}
