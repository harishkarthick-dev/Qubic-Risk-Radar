import React, { useEffect, useState } from 'react';
import { BarChart3, PieChart, TrendingUp, Download } from 'lucide-react';
import { apiClient } from '../api/client';
import type { AnalyticsOverview, Report } from '../types';
import './Analytics.css';

export default function Analytics() {
    const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [overviewData, reportsData] = await Promise.all([
                apiClient.getAnalyticsOverview(),
                apiClient.getReports({ limit: 10 })
            ]);
            setOverview(overviewData);
            setReports(reportsData);
        } catch (error) {
            console.error('Failed to load analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateReport = async () => {
        try {
            await apiClient.generateReport({
                scope: 'all',
                time_range_days: 7,
                report_type: 'detailed'
            });
            await loadData();
            alert('Report generated successfully!');
        } catch (error) {
            console.error('Failed to generate report:', error);
            alert('Failed to generate report');
        }
    };

    if (loading) {
        return <div className="loading-container"><div className="spinner"></div></div>;
    }

    return (
        <div className="analytics-page">
            <div className="page-header">
                <div>
                    <h1>Analytics Dashboard</h1>
                    <p className="subtitle">Insights and trends from your security data</p>
                </div>
                <button className="primary-btn" onClick={handleGenerateReport}>
                    <Download size={20} /> Generate Report
                </button>
            </div>

            {/* Overview Stats */}
            <div className="analytics-grid">
                <div className="analytics-card">
                    <div className="card-header">
                        <BarChart3 size={24} color="#3b82f6" />
                        <h3>Total Detections</h3>
                    </div>
                    <div className="card-value">{overview?.total_detections || 0}</div>
                    <div className="card-footer">
                        <span>This week: {overview?.detections_this_week || 0}</span>
                    </div>
                </div>

                <div className="analytics-card">
                    <div className="card-header">
                        <TrendingUp size={24} color="#10b981" />
                        <h3>Today's Activity</h3>
                    </div>
                    <div className="card-value">{overview?.detections_today || 0}</div>
                    <div className="card-footer">
                        <span>Last 24 hours</span>
                    </div>
                </div>

                <div className="analytics-card">
                    <div className="card-header">
                        <PieChart size={24} color="#f59e0b" />
                        <h3>Categories</h3>
                    </div>
                    <div className="card-value">
                        {Object.keys(overview?.by_category || {}).length}
                    </div>
                    <div className="card-footer">
                        <span>Unique threat types</span>
                    </div>
                </div>
            </div>

            {/* Severity Breakdown */}
            <div className="chart-section">
                <h2>Severity Distribution</h2>
                <div className="severity-bars">
                    {Object.entries(overview?.by_severity || {}).map(([severity, count]) => {
                        const colors: Record<string, string> = {
                            CRITICAL: '#dc2626',
                            HIGH: '#f59e0b',
                            MEDIUM: '#3b82f6',
                            LOW: '#10b981',
                            INFO: '#6b7280'
                        };
                        const total = overview?.total_detections || 1;
                        const percentage = ((count as number) / total) * 100;

                        return (
                            <div key={severity} className="severity-bar-item">
                                <div className="severity-bar-header">
                                    <span className="severity-label">{severity}</span>
                                    <span className="severity-count">{count}</span>
                                </div>
                                <div className="severity-bar-track">
                                    <div
                                        className="severity-bar-fill"
                                        style={{
                                            width: `${percentage}%`,
                                            backgroundColor: colors[severity]
                                        }}
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Recent Reports */}
            <div className="reports-section">
                <h2>Recent Reports</h2>
                {reports.length === 0 ? (
                    <div className="empty-state">
                        <p>No reports yet</p>
                        <button className="primary-btn" onClick={handleGenerateReport}>
                            Generate Your First Report
                        </button>
                    </div>
                ) : (
                    <div className="reports-list">
                        {reports.map((report) => (
                            <div key={report.id} className="report-item">
                                <div className="report-header">
                                    <h4>{report.scope.toUpperCase()} Report</h4>
                                    <span className="report-type">{report.report_type}</span>
                                </div>
                                <div className="report-stats">
                                    <span>Total: {report.total_detections}</span>
                                    <span className="critical">Critical: {report.critical_count}</span>
                                    <span className="high">High: {report.high_count}</span>
                                </div>
                                <p className="report-summary">{report.executive_summary}</p>
                                <div className="report-footer">
                                    <span className="timestamp">
                                        {new Date(report.generated_at).toLocaleString()}
                                    </span>
                                    <span className="risk-badge">{report.risk_assessment}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
