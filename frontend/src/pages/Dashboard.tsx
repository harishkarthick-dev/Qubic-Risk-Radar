import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, TrendingUp, Shield } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Detection, AnalyticsOverview } from '../types';
import './Dashboard.css';

export default function Dashboard() {
    const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
    const [recentDetections, setRecentDetections] = useState<Detection[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [overviewData, detectionsData] = await Promise.all([
                apiClient.getAnalyticsOverview(),
                apiClient.getDetections({ page: 1, page_size: 5 })
            ]);
            setOverview(overviewData);
            setRecentDetections(detectionsData.detections || []);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading dashboard...</p>
            </div>
        );
    }

    const getSeverityColor = (severity: string) => {
        const colors: Record<string, string> = {
            CRITICAL: '#dc2626',
            HIGH: '#f59e0b',
            MEDIUM: '#3b82f6',
            LOW: '#10b981',
            INFO: '#6b7280'
        };
        return colors[severity] || '#6b7280';
    };

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <h1>Dashboard</h1>
                <p className="subtitle">Blockchain Security Overview</p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#eff6ff' }}>
                        <Activity color="#3b82f6" size={24} />
                    </div>
                    <div className="stat-content">
                        <p className="stat-label">Total Detections</p>
                        <p className="stat-value">{overview?.total_detections || 0}</p>
                        <p className="stat-change positive">This week: {overview?.detections_this_week || 0}</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#fef2f2' }}>
                        <AlertTriangle color="#dc2626" size={24} />
                    </div>
                    <div className="stat-content">
                        <p className="stat-label">Critical Alerts</p>
                        <p className="stat-value">{overview?.by_severity?.CRITICAL || 0}</p>
                        <p className="stat-change">Requires immediate attention</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#fef3c7' }}>
                        <TrendingUp color="#f59e0b" size={24} />
                    </div>
                    <div className="stat-content">
                        <p className="stat-label">High Priority</p>
                        <p className="stat-value">{overview?.by_severity?.HIGH || 0}</p>
                        <p className="stat-change">Review recommended</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ backgroundColor: '#f0fdf4' }}>
                        <Shield color="#10b981" size={24} />
                    </div>
                    <div className="stat-content">
                        <p className="stat-label">Today's Activity</p>
                        <p className="stat-value">{overview?.detections_today || 0}</p>
                        <p className="stat-change">Last 24 hours</p>
                    </div>
                </div>
            </div>

            {/* Recent Detections */}
            <div className="dashboard-section">
                <div className="section-header">
                    <h2>Recent Detections</h2>
                    <Link to="/detections" className="view-all-link">View All →</Link>
                </div>

                <div className="detections-list">
                    {recentDetections.length === 0 ? (
                        <div className="empty-state">
                            <Shield size={48} color="#9ca3af" />
                            <p>No detections yet</p>
                            <p className="empty-subtitle">Your system is being monitored</p>
                        </div>
                    ) : (
                        recentDetections.map((detection) => (
                            <div key={detection.id} className="detection-card">
                                <div className="detection-header">
                                    <span
                                        className="severity-badge"
                                        style={{ backgroundColor: getSeverityColor(detection.severity) }}
                                    >
                                        {detection.severity}
                                    </span>
                                    <span className="category-badge">{detection.primary_category}</span>
                                    <span className="anomaly-score">
                                        Score: {Math.round(detection.anomaly_score * 100)}%
                                    </span>
                                </div>
                                <p className="detection-summary">{detection.summary}</p>
                                <div className="detection-footer">
                                    <span className="timestamp">
                                        {new Date(detection.created_at).toLocaleString()}
                                    </span>
                                    <Link to={`/detections`} className="details-link">
                                        View Details →
                                    </Link>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
                <h3>Quick Actions</h3>
                <div className="actions-grid">
                    <Link to="/webhooks" className="action-card">
                        <div className="action-icon">🔗</div>
                        <div className="action-content">
                            <h4>Manage Webhooks</h4>
                            <p>Configure monitoring endpoints</p>
                        </div>
                    </Link>

                    <Link to="/settings/notifications" className="action-card">
                        <div className="action-icon">🔔</div>
                        <div className="action-content">
                            <h4>Notification Settings</h4>
                            <p>Customize alert routing</p>
                        </div>
                    </Link>

                    <Link to="/analytics" className="action-card">
                        <div className="action-icon">📊</div>
                        <div className="action-content">
                            <h4>View Analytics</h4>
                            <p>Generate detailed reports</p>
                        </div>
                    </Link>
                </div>
            </div>
        </div>
    );
}
