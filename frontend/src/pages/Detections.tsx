import React, { useEffect, useState } from 'react';
import { Search, Filter, ChevronDown } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Detection } from '../types';
import './Detections.css';

export default function Detections() {
    const [detections, setDetections] = useState<Detection[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [filters, setFilters] = useState({
        severity: '',
        category: '',
        days: 7
    });

    useEffect(() => {
        loadDetections();
    }, [page, filters]);

    const loadDetections = async () => {
        try {
            setLoading(true);
            const data = await apiClient.getDetections({
                page,
                page_size: 20,
                ...filters
            });
            setDetections(data.detections || []);
            setTotalPages(data.total_pages || 1);
        } catch (error) {
            console.error('Failed to load detections:', error);
        } finally {
            setLoading(false);
        }
    };

    const severityColors: Record<string, string> = {
        CRITICAL: '#dc2626',
        HIGH: '#f59e0b',
        MEDIUM: '#3b82f6',
        LOW: '#10b981',
        INFO: '#6b7280'
    };

    return (
        <div className="detections-page">
            <div className="page-header">
                <div>
                    <h1>AI Detections</h1>
                    <p className="subtitle">Browse and analyze security detections</p>
                </div>
            </div>

            {/* Filters */}
            <div className="filters-bar">
                <div className="filter-group">
                    <label>Severity</label>
                    <select
                        value={filters.severity}
                        onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                    >
                        <option value="">All Severities</option>
                        <option value="CRITICAL">Critical</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                        <option value="INFO">Info</option>
                    </select>
                </div>

                <div className="filter-group">
                    <label>Time Range</label>
                    <select
                        value={filters.days}
                        onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
                    >
                        <option value={1}>Last 24 hours</option>
                        <option value={7}>Last 7 days</option>
                        <option value={30}>Last 30 days</option>
                        <option value={90}>Last 90 days</option>
                    </select>
                </div>

                <button className="refresh-btn" onClick={loadDetections}>
                    Refresh
                </button>
            </div>

            {/* Detections List */}
            {loading ? (
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Loading detections...</p>
                </div>
            ) : detections.length === 0 ? (
                <div className="empty-state">
                    <p>No detections found</p>
                    <p className="empty-subtitle">Try adjusting your filters</p>
                </div>
            ) : (
                <>
                    <div className="detections-grid">
                        {detections.map((detection) => (
                            <div key={detection.id} className="detection-item">
                                <div className="detection-item-header">
                                    <span
                                        className="severity-badge"
                                        style={{ backgroundColor: severityColors[detection.severity] }}
                                    >
                                        {detection.severity}
                                    </span>
                                    <span className="confidence-badge">
                                        Confidence: {Math.round(detection.confidence * 100)}%
                                    </span>
                                </div>

                                <div className="detection-item-body">
                                    <div className="category">{detection.primary_category}</div>
                                    <p className="summary">{detection.summary}</p>

                                    {detection.detected_patterns && detection.detected_patterns.length > 0 && (
                                        <div className="patterns">
                                            <strong>Patterns:</strong>
                                            <div className="pattern-tags">
                                                {detection.detected_patterns.slice(0, 3).map((pattern, idx) => (
                                                    <span key={idx} className="pattern-tag">{pattern}</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {detection.recommendations && detection.recommendations.length > 0 && (
                                        <div className="recommendations">
                                            <strong>Recommendations:</strong>
                                            <ul>
                                                {detection.recommendations.slice(0, 2).map((rec, idx) => (
                                                    <li key={idx}>{rec}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>

                                <div className="detection-item-footer">
                                    <span className="timestamp">
                                        {new Date(detection.created_at).toLocaleString()}
                                    </span>
                                    <span className="anomaly-score">
                                        Anomaly: {Math.round(detection.anomaly_score * 100)}%
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="pagination">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                            >
                                Previous
                            </button>
                            <span>Page {page} of {totalPages}</span>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
