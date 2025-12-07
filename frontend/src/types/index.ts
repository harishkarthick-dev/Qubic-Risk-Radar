// Common types
export interface Detection {
    id: string;
    severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
    summary: string;
    anomaly_score: number;
    confidence: number;
    primary_category: string;
    sub_categories?: string[];
    scope: string;
    detailed_analysis?: string;
    detected_patterns?: string[];
    risk_factors?: string[];
    recommendations?: string[];
    created_at: string;
}

export interface Incident {
    id: string;
    title: string;
    severity: string;
    category: string;
    status: 'open' | 'investigating' | 'resolved' | 'closed';
    created_at: string;
    resolved_at?: string;
}

export interface RoutingRule {
    id: string;
    severity: string;
    discord_channel_id?: string;
    telegram_chat_id?: string;
    email_enabled: boolean;
    webhook_url?: string;
    notification_format: string;
    priority: number;
    enabled: boolean;
}

export interface Webhook {
    id: string;
    name: string;
    description?: string;
    alert_id: string;
    webhook_url: string;
    tags: string[];
    webhook_priority: number;
    is_primary: boolean;
    enabled: boolean;
    total_events: number;
    last_event_at?: string;
    created_at: string;
}

export interface Report {
    id: string;
    scope: string;
    report_type: string;
    time_range_start: string;
    time_range_end: string;
    total_detections: number;
    critical_count: number;
    high_count: number;
    executive_summary?: string;
    risk_assessment?: string;
    generated_at: string;
}

export interface AnalyticsOverview {
    total_detections: number;
    detections_today: number;
    detections_this_week: number;
    by_severity: Record<string, number>;
    by_category: Record<string, number>;
    trend_7days: Array<{ date: string; count: number }>;
}
