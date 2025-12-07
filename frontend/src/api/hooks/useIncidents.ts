import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { Incident, IncidentDetail } from '../../types'

interface IncidentsListResponse {
    incidents: Incident[]
    total: number
    page: number
    page_size: number
}

interface IncidentsFilters {
    severity?: string
    status?: string
    protocol?: string
    type?: string
    hours?: number
    page?: number
    page_size?: number
}

export function useIncidents(filters: IncidentsFilters = {}) {
    return useQuery({
        queryKey: ['incidents', filters],
        queryFn: async () => {
            const params = new URLSearchParams()
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined) {
                    params.append(key, String(value))
                }
            })

            const { data } = await apiClient.get<IncidentsListResponse>(
                `/incidents?${params.toString()}`
            )
            return data
        },
        refetchInterval: 30000, // Refetch every 30 seconds
    })
}

export function useIncidentDetail(incidentId: string | undefined) {
    return useQuery({
        queryKey: ['incident', incidentId],
        queryFn: async () => {
            if (!incidentId) throw new Error('Incident ID is required')
            const { data } = await apiClient.get<IncidentDetail>(`/incidents/${incidentId}`)
            return data
        },
        enabled: !!incidentId,
        refetchInterval: 10000, // Refetch every 10 seconds
    })
}

export function useUpdateIncident() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async ({ id, status }: { id: string; status: string }) => {
            const { data } = await apiClient.patch<Incident>(`/incidents/${id}`, { status })
            return data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['incidents'] })
            queryClient.invalidateQueries({ queryKey: ['incident'] })
        },
    })
}

export function useIncidentStats(hours: number = 24) {
    return useQuery({
        queryKey: ['incident-stats', hours],
        queryFn: async () => {
            const { data } = await apiClient.get(`/incidents/stats/summary?hours=${hours}`)
            return data
        },
        refetchInterval: 60000, // Refetch every minute
    })
}
