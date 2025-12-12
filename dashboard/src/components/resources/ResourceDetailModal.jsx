import React from 'react';
import api from '../../services/api.js';
import { Card, CardHeader, CardContent } from '../ui/Card.jsx';
import { Button } from '../ui/Button.jsx';
import { Badge } from '../ui/Badge.jsx';
import { TagInput } from '../ui/TagInput.jsx';

const COMMON_ACTIONS = [
  's3:DeleteBucket',
  's3:PutBucketAcl',
  's3:PutBucketPolicy',
  's3:DeleteObject',
  'iam:DeleteUser',
  'iam:AttachUserPolicy',
  'iam:PutUserPolicy',
  'ec2:TerminateInstances',
  'ec2:ModifyInstanceAttribute',
  'rds:DeleteDBInstance',
  'kms:DisableKey',
  'cloudtrail:StopLogging',
];

const normalizeCriticality = (value) => {
  const v = (value || '').toString().trim().toUpperCase();
  return v || 'STANDARD';
};

const toApiCriticality = (value) => normalizeCriticality(value).toLowerCase();

const criticalityClasses = (level) => {
  const v = normalizeCriticality(level);
  if (v === 'CRITICAL') {
    return 'bg-error-container text-[var(--md-sys-color-on-error-container)]';
  }
  if (v === 'LOW') {
    return 'bg-tertiary-container text-[var(--md-sys-color-on-tertiary-container)]';
  }
  return 'bg-surface-variant text-[var(--md-sys-color-on-surface-variant)]';
};

const typeToBadgeVariant = (typeValue) => {
  const t = (typeValue || '').toString().toLowerCase();
  if (t.includes('s3')) return 'info';
  if (t.includes('ec2')) return 'warning';
  if (t.includes('rds') || t.includes('db')) return 'success';
  if (t.includes('iam') || t.includes('auth')) return 'default';
  return 'default';
};

const getResourceId = (row) => row?.resource_id || row?.uuid || row?.arn || row?.resource_arn;

const getRegion = (row) => 'eu-north-1';
const getAccountId = (row) => row?.cloud_account_id || '';
const getArn = (row) => row?.arn || row?.resource_arn || row?.resourceArn || '';
const getName = (row) => row?.name || row?.resource_name || row?.title || getResourceId(row) || 'Resource';
const getType = (row) => row?.type || row?.service || row?.kind || '—';

export const ResourceDetailModal = ({ resource, onClose, onSave }) => {
  const [criticality, setCriticality] = React.useState('STANDARD');
  const [blockedActions, setBlockedActions] = React.useState([]);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [copied, setCopied] = React.useState(false);
  const [detailsLoading, setDetailsLoading] = React.useState(false);

  React.useEffect(() => {
    if (!resource) return;
    console.log('resource changed', resource);
    const initialCriticality = normalizeCriticality(resource?.criticality || resource?.risk || resource?.severity || 'STANDARD');
    const initialBlocked = Array.isArray(resource?.security_config?.blocked_actions)
      ? resource.security_config.blocked_actions
      : [];
    setCriticality(initialCriticality);
    setBlockedActions(initialBlocked);
    setError('');
    setSaving(false);
    setCopied(false);

    let cancelled = false;
    const fetchDetails = async () => {
      try {
        const rid = getResourceId(resource);
        if (!rid) return;
        setDetailsLoading(true);
        const encodedId = encodeURIComponent(rid);
        const { data } = await api.get(`/resources/${encodedId}`);
        const fetchedCriticality = normalizeCriticality(
          data?.criticality || data?.risk || data?.severity || initialCriticality
        );
        const fetchedBlocked = Array.isArray(data?.security_config?.blocked_actions)
          ? data.security_config.blocked_actions
          : initialBlocked;
        if (!cancelled) {
          setCriticality(fetchedCriticality);
          setBlockedActions(fetchedBlocked);
        }
      } catch (_) {
      } finally {
        if (!cancelled) setDetailsLoading(false);
      }
    };
    fetchDetails();
    return () => {
      cancelled = true;
    };
  }, [resource]);

  if (!resource) return null;

  const id = getResourceId(resource);
  const arn = getArn(resource);
  const region = getRegion(resource);
  const accountId = getAccountId(resource);
  const name = getName(resource);
  const type = getType(resource);

  const handleCopyArn = async () => {
    try {
      if (!arn) return;
      await navigator.clipboard.writeText(arn);
      setCopied(true);
      window.clearTimeout(handleCopyArn._t);
      handleCopyArn._t = window.setTimeout(() => setCopied(false), 1500);
    } catch (_) {
    }
  };

  const handleSave = async () => {
    if (!id) return;
    try {
      setSaving(true);
      setError('');
      const payload = {
        criticality: toApiCriticality(criticality),
        security_config: { blocked_actions: blockedActions },
      };
      const encodedId = encodeURIComponent(id);
      await api.patch(`/resources/${encodedId}`, payload);
      if (typeof onSave === 'function') {
        await onSave();
      }
      if (typeof onClose === 'function') {
        onClose();
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err?.response?.data?.message || 'Failed to update resource configuration.');
    } finally {
      setSaving(false);
    }
  };

  const toggleBlockedAction = (action) => {
    setBlockedActions((prev) => {
      if (prev.includes(action)) {
        return prev.filter((a) => a !== action);
      }
      return [...prev, action];
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-2xl bg-white text-black shadow-xl">
        <CardHeader className="flex items-center justify-between border-b border-outline-variant">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <h3 className="truncate text-lg font-semibold text-surface-foreground">{name}</h3>
              <Badge variant={typeToBadgeVariant(type)}>{type}</Badge>
            </div>
            <div className="mt-1 text-xs text-[var(--md-sys-color-on-surface-variant)] truncate">
              {id}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
            </svg>
          </Button>
        </CardHeader>

        <CardContent className="space-y-5">
          <section>
            <h4 className="mb-3 text-sm font-semibold text-surface-foreground">Metadata</h4>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-outline-variant bg-surface-variant p-3">
                <div className="text-xs">AWS Region</div>
                <div className="mt-1 text-sm font-medium text-surface-foreground">{region || '—'}</div>
              </div>
              <div className="rounded-lg border border-outline-variant bg-surface-variant p-3">
                <div className="text-xs">Account ID</div>
                <div className="mt-1 text-sm font-medium text-surface-foreground">{accountId || '—'}</div>
              </div>
            </div>
          </section>

          <section>
            <h4 className="mb-3 text-sm font-semibold text-surface-foreground">Risk Settings</h4>
            <div className="flex items-center gap-3">
              <label className="text-sm text-[var(--md-sys-color-on-surface-variant)]">Criticality</label>
              <select
                className={[
                  'rounded-md px-3 py-2 text-sm border border-outline-variant',
                  'outline-none focus:ring-2 focus:ring-[var(--md-sys-color-outline-variant)]',
                  criticalityClasses(criticality),
                ].join(' ')}
                value={normalizeCriticality(criticality)}
                onChange={(e) => setCriticality(e.target.value)}
              >
                <option value="LOW">LOW</option>
                <option value="STANDARD">STANDARD</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </section>

          <section>
            <div className="mb-2">
              <h4 className="text-sm font-semibold text-surface-foreground">Block Specific Actions</h4>
              <p className="mt-1 text-xs text-[var(--md-sys-color-on-surface-variant)]">
                Actions listed here will trigger a HIGH severity alert if attempted on this resource, regardless of user permissions.
              </p>
            </div>
            <div className="mb-3">
              <div className="mb-2 text-xs font-medium text-surface-foreground">Common Actions</div>
              <div className="flex flex-wrap gap-2">
                {COMMON_ACTIONS.map((action) => {
                  const selected = blockedActions.includes(action);
                  return (
                    <button
                      key={action}
                      type="button"
                      onClick={() => toggleBlockedAction(action)}
                      className={[
                        'rounded-md border px-3 py-1 text-xs transition-colors',
                        selected
                          ? 'bg-primary-container text-primary-container-foreground border-outline-variant'
                          : 'bg-surface-variant text-[var(--md-sys-color-on-surface-variant)] border-outline-variant hover:bg-[var(--md-sys-color-surface-container-high)]',
                      ].join(' ')}
                      aria-pressed={selected}
                    >
                      {action}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="mb-1 text-xs font-medium text-surface-foreground">Add Custom Action</div>
            <TagInput
              value={blockedActions}
              onChange={setBlockedActions}
              placeholder="e.g., s3:DeleteBucket, iam:DeleteUser (press Enter to add)"
              validationRegex={/^[a-zA-Z0-9:*]+:[a-zA-Z0-9*]+$/}
            />
          </section>

          {error && <div className="text-sm text-error">{error}</div>}

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSave} isLoading={saving}>
              Save Configuration
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResourceDetailModal;


