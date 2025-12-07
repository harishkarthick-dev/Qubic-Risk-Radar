import React, { useEffect, useState } from 'react';
import { Plus, Tag, Trash2, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import type { Webhook } from '../types';
import './WebhooksManagement.css';

export default function WebhooksManagement() {
    const [webhooks, setWebhooks] = useState<Webhook[]>([]);
    const [loading, setLoading] = useState(true);
    const [showEditor, setShowEditor] = useState(false);
    const [editingWebhook, setEditingWebhook] = useState<Webhook | null>(null);

    useEffect(() => {
        loadWebhooks();
    }, []);

    const loadWebhooks = async () => {
        try {
            const data = await apiClient.getWebhooks();
            setWebhooks(data);
        } catch (error) {
            console.error('Failed to load webhooks:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this webhook?')) return;

        try {
            await apiClient.deleteWebhook(id);
            await loadWebhooks();
        } catch (error) {
            console.error('Failed to delete webhook:', error);
        }
    };

    const handleRegenerateSecret = async (id: string) => {
        if (!confirm('This will invalidate the current webhook secret. Continue?')) return;

        try {
            const result = await apiClient.regenerateWebhookSecret(id);
            alert(`New secret: ${result.new_secret}`);
            await loadWebhooks();
        } catch (error) {
            console.error('Failed to regenerate secret:', error);
        }
    };

    if (loading) {
        return <div className="loading-container"><div className="spinner"></div></div>;
    }

    return (
        <div className="webhooks-page">
            <div className="page-header">
                <div>
                    <h1>Webhooks Management</h1>
                    <p className="subtitle">Configure and manage your monitoring endpoints</p>
                </div>
                <button className="primary-btn" onClick={() => setShowEditor(true)}>
                    <Plus size={20} /> New Webhook
                </button>
            </div>

            {webhooks.length === 0 ? (
                <div className="empty-state">
                    <p>No webhooks configured</p>
                    <button className="primary-btn" onClick={() => setShowEditor(true)}>
                        Create Your First Webhook
                    </button>
                </div>
            ) : (
                <div className="webhooks-grid">
                    {webhooks.map((webhook) => (
                        <div key={webhook.id} className="webhook-card">
                            {webhook.is_primary && <div className="primary-badge">⭐ Primary</div>}

                            <div className="webhook-header">
                                <h3>{webhook.name}</h3>
                                <span className="priority-badge">Priority: {webhook.webhook_priority}</span>
                            </div>

                            {webhook.description && (
                                <p className="webhook-description">{webhook.description}</p>
                            )}

                            <div className="webhook-details">
                                <div className="detail-row">
                                    <span className="label">Alert ID:</span>
                                    <code>{webhook.alert_id}</code>
                                </div>
                                <div className="detail-row">
                                    <span className="label">Events:</span>
                                    <span>{webhook.total_events}</span>
                                </div>
                            </div>

                            {webhook.tags && webhook.tags.length > 0 && (
                                <div className="tags">
                                    {webhook.tags.map((tag, idx) => (
                                        <span key={idx} className="tag">
                                            <Tag size={12} /> {tag}
                                        </span>
                                    ))}
                                </div>
                            )}

                            <div className="webhook-actions">
                                <button onClick={() => { setEditingWebhook(webhook); setShowEditor(true); }}>
                                    Edit
                                </button>
                                <button onClick={() => handleRegenerateSecret(webhook.id)}>
                                    <RefreshCw size={16} /> Secret
                                </button>
                                <button className="danger" onClick={() => handleDelete(webhook.id)}>
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {showEditor && (
                <WebhookEditorModal
                    webhook={editingWebhook}
                    onClose={() => { setShowEditor(false); setEditingWebhook(null); }}
                    onSave={async () => { await loadWebhooks(); setShowEditor(false); setEditingWebhook(null); }}
                />
            )}
        </div>
    );
}

function WebhookEditorModal({ webhook, onClose, onSave }: any) {
    const [formData, setFormData] = useState({
        name: webhook?.name || '',
        description: webhook?.description || '',
        alert_id: webhook?.alert_id || '',
        tags: webhook?.tags || [],
        webhook_priority: webhook?.webhook_priority || 50,
        is_primary: webhook?.is_primary || false
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (webhook) {
                await apiClient.updateWebhook(webhook.id, formData);
            } else {
                await apiClient.createWebhook(formData);
            }
            await onSave();
        } catch (error) {
            console.error('Failed to save webhook:', error);
            alert('Failed to save webhook');
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h2>{webhook ? 'Edit Webhook' : 'New Webhook'}</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Name *</label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Description</label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            rows={3}
                        />
                    </div>

                    <div className="form-group">
                        <label>Alert ID *</label>
                        <input
                            type="text"
                            value={formData.alert_id}
                            onChange={(e) => setFormData({ ...formData, alert_id: e.target.value })}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Priority (0-100)</label>
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={formData.webhook_priority}
                            onChange={(e) => setFormData({ ...formData, webhook_priority: parseInt(e.target.value) })}
                        />
                        <span className="range-value">{formData.webhook_priority}</span>
                    </div>

                    <div className="form-group checkbox">
                        <label>
                            <input
                                type="checkbox"
                                checked={formData.is_primary}
                                onChange={(e) => setFormData({ ...formData, is_primary: e.target.checked })}
                            />
                            Mark as primary webhook
                        </label>
                    </div>

                    <div className="form-actions">
                        <button type="button" onClick={onClose}>Cancel</button>
                        <button type="submit" className="primary-btn">Save</button>
                    </div>
                </form>
            </div>
        </div>
    );
}
