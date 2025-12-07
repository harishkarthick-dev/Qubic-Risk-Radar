import axios, { AxiosInstance } from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Add auth token interceptor
        this.client.interceptors.request.use((config) => {
            const token = localStorage.getItem('access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });
    }

    // Detections API
    async getDetections(params?: {
        page?: number;
        page_size?: number;
        severity?: string;
        category?: string;
        scope?: string;
        min_anomaly_score?: number;
        days?: number;
    }) {
        const response = await this.client.get('/api/detections', { params });
        return response.data;
    }

    async getDetection(id: string) {
        const response = await this.client.get(`/api/detections/${id}`);
        return response.data;
    }

    async getDetectionStats() {
        const response = await this.client.get('/api/detections/stats');
        return response.data;
    }

    async submitDetectionFeedback(id: string, feedback: { is_accurate: boolean; feedback_text?: string }) {
        const response = await this.client.post(`/api/detections/${id}/feedback`, feedback);
        return response.data;
    }

    // Incidents API
    async getIncidents(params?: { status?: string; limit?: number }) {
        const response = await this.client.get('/api/detections/incidents', { params });
        return response.data;
    }

    async updateIncident(id: string, data: any) {
        const response = await this.client.put(`/api/detections/incidents/${id}`, data);
        return response.data;
    }

    async resolveIncident(id: string, resolution: string) {
        const response = await this.client.post(`/api/detections/incidents/${id}/resolve`, { resolution });
        return response.data;
    }

    // Routing Rules API
    async getRoutingRules() {
        const response = await this.client.get('/api/routing-rules');
        return response.data;
    }

    async createRoutingRule(rule: any) {
        const response = await this.client.post('/api/routing-rules', rule);
        return response.data;
    }

    async updateRoutingRule(id: string, rule: any) {
        const response = await this.client.put(`/api/routing-rules/${id}`, rule);
        return response.data;
    }

    async deleteRoutingRule(id: string) {
        const response = await this.client.delete(`/api/routing-rules/${id}`);
        return response.data;
    }

    async initDefaultRoutingRules() {
        const response = await this.client.post('/api/routing-rules/init-defaults');
        return response.data;
    }

    // Notification Logs API
    async getNotificationLogs(params?: { limit?: number; offset?: number; channel?: string; status?: string }) {
        const response = await this.client.get('/api/notifications/logs', { params });
        return response.data;
    }

    async getNotificationStats() {
        const response = await this.client.get('/api/notifications/stats');
        return response.data;
    }

    // Webhooks Management API
    async getWebhooks(tag?: string) {
        const response = await this.client.get('/api/webhooks', { params: { tag } });
        return response.data;
    }

    async getWebhook(id: string) {
        const response = await this.client.get(`/api/webhooks/${id}`);
        return response.data;
    }

    async createWebhook(webhook: any) {
        const response = await this.client.post('/api/webhooks', webhook);
        return response.data;
    }

    async updateWebhook(id: string, webhook: any) {
        const response = await this.client.put(`/api/webhooks/${id}`, webhook);
        return response.data;
    }

    async deleteWebhook(id: string) {
        const response = await this.client.delete(`/api/webhooks/${id}`);
        return response.data;
    }

    async regenerateWebhookSecret(id: string) {
        const response = await this.client.post(`/api/webhooks/${id}/regenerate-secret`);
        return response.data;
    }

    async getWebhookTags() {
        const response = await this.client.get('/api/webhooks/tags/list');
        return response.data;
    }

    async getWebhookStats() {
        const response = await this.client.get('/api/webhooks/stats/overview');
        return response.data;
    }

    // Analytics API
    async generateReport(data: { scope?: string; time_range_days?: number; report_type?: string }) {
        const response = await this.client.post('/api/analytics/reports/generate', data);
        return response.data;
    }

    async getReports(params?: { scope?: string; limit?: number }) {
        const response = await this.client.get('/api/analytics/reports', { params });
        return response.data;
    }

    async getReport(id: string) {
        const response = await this.client.get(`/api/analytics/reports/${id}`);
        return response.data;
    }

    async getAnalyticsOverview() {
        const response = await this.client.get('/api/analytics/overview');
        return response.data;
    }

    async getSeverityStats(days: number = 7) {
        const response = await this.client.get('/api/analytics/stats/severity', { params: { days } });
        return response.data;
    }

    async getCategoryStats(days: number = 7, limit: number = 10) {
        const response = await this.client.get('/api/analytics/stats/categories', { params: { days, limit } });
        return response.data;
    }

    async getTimelineTrend(days: number = 30) {
        const response = await this.client.get('/api/analytics/trends/timeline', { params: { days } });
        return response.data;
    }
}

export const apiClient = new ApiClient();
export default apiClient;
