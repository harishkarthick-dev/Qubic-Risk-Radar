import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { NetworkHealth, IncidentStats } from '../../types'

export function useNetworkHealth(hours: number = 1) {
    return useQuery({
        queryKey: ['network-health', hours],
        queryFn: async () => {
            const { data } = await apiClient.get<NetworkHealth>(`/metrics/network?hours=${hours}`)
            return data
        },
        refetchInterval: 15000, // Refetch every 15 seconds
    })
}

export function useIncidentTimeSeries(hours: number = 24, severity?: string) {
    return useQuery({
        queryKey: ['incident-timeseries', hours, severity],
        queryFn: async () => {
            const params = new URLSearchParams({ hours: String(hours) })
            if (severity) params.append('severity', severity)

            const { data } = await apiClient.get(`/metrics/incidents/timeseries?${params.toString()}`)
            return data
        },
        refetchInterval: 60000,
    })
}

export function useWhaleActivity(hours: number = 24, minAmount: number = 1000000) {
    return useQuery({
        queryKey: ['whale-activity', hours, minAmount],
        queryFn: async () => {
            const { data } = await apiClient.get(
                `/metrics/whale-activity?hours=${hours}&min_amount=${minAmount}`
            )
            return data
        },
        refetchInterval: 30000,
    })
}

export function useProtocolActivity(hours: number = 24) {
    return useQuery({
        queryKey: ['protocol-activity', hours],
        queryFn: async () => {
            const { data } = await apiClient.get(`/metrics/protocols/activity?hours=${hours}`)
            return data
        },
        refetchInterval: 60000,
    })
}
