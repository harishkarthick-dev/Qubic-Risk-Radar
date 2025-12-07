import type { Incident } from '../../types'
import { clsx } from 'clsx'

interface StatusBadgeProps {
    status: Incident['status']
    className?: string
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'

    const statusClasses = {
        open: 'bg-red-100 text-red-700',
        acknowledged: 'bg-yellow-100 text-yellow-700',
        resolved: 'bg-green-100 text-green-700',
    }

    return (
        <span className={clsx(baseClasses, statusClasses[status], className)}>
            {status.toUpperCase()}
        </span>
    )
}
