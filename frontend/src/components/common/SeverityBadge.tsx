import type { Incident } from '../../types'
import { clsx } from 'clsx'

interface SeverityBadgeProps {
    severity: Incident['severity']
    className?: string
}

export default function SeverityBadge({ severity, className }: SeverityBadgeProps) {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'

    const severityClasses = {
        CRITICAL: 'bg-critical-100 text-critical-700',
        WARNING: 'bg-warning-100 text-warning-700',
        INFO: 'bg-info-100 text-info-700',
    }

    return (
        <span className={clsx(baseClasses, severityClasses[severity], className)}>
            {severity}
        </span>
    )
}
