import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Key, Plus, Copy, Check, XCircle, LogOut, FileText, Trash2 } from 'lucide-react';
import { adminApi } from '../services/api';

function AdminKeys({ onLogout }) {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      const response = await adminApi.getKeys();
      setKeys(response.data);
    } catch (err) {
      setError('Failed to load device keys');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateKey = async () => {
    setGenerating(true);
    setError('');

    try {
      const response = await adminApi.generateKey();
      setKeys([response.data, ...keys]);
    } catch (err) {
      setError('Failed to generate key');
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleStatus = async (keyId, currentStatus) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    
    try {
      await adminApi.updateKey(keyId, newStatus);
      setKeys(keys.map(k => 
        k.id === keyId ? { ...k, status: newStatus } : k
      ));
    } catch (err) {
      setError('Failed to update key status');
    }
  };

  const handleDeleteKey = async (keyId) => {
    if (!confirm('Are you sure you want to delete this key?')) return;

    try {
      await adminApi.deleteKey(keyId);
      setKeys(keys.filter(k => k.id !== keyId));
    } catch (err) {
      setError('Failed to delete key');
    }
  };

  const handleCopyKey = (key) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 pt-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
            <p className="text-gray-400">Manage device keys and leads</p>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>

        {/* Navigation */}
        <div className="flex gap-4 mb-6">
          <Link
            to="/admin/keys"
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg"
          >
            <Key className="w-4 h-4" />
            Device Keys
          </Link>
          <Link
            to="/admin/leads"
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-gray-300 rounded-lg hover:bg-slate-600 transition"
          >
            <FileText className="w-4 h-4" />
            Download Leads
          </Link>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Device Keys</h2>
            <button
              onClick={handleGenerateKey}
              disabled={generating}
              className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 transition"
            >
              <Plus className="w-4 h-4" />
              {generating ? 'Generating...' : 'Generate New Key'}
            </button>
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
              <XCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : keys.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No device keys yet. Generate one to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Key</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Created</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {keys.map((key) => (
                    <tr key={key.id} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono">
                            {key.key.substring(0, 8)}...{key.key.substring(key.key.length - 4)}
                          </code>
                          <button
                            onClick={() => handleCopyKey(key.key)}
                            className="text-gray-400 hover:text-gray-600 transition"
                            title="Copy full key"
                          >
                            {copiedKey === key.key ? (
                              <Check className="w-4 h-4 text-green-500" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            key.status === 'active'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {key.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">
                        {formatDate(key.created_at)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleToggleStatus(key.id, key.status)}
                            className={`px-3 py-1 rounded text-sm font-medium transition ${
                              key.status === 'active'
                                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                : 'bg-green-100 text-green-700 hover:bg-green-200'
                            }`}
                          >
                            {key.status === 'active' ? 'Disable' : 'Enable'}
                          </button>
                          <button
                            onClick={() => handleDeleteKey(key.id)}
                            className="p-1 text-gray-400 hover:text-red-600 transition"
                            title="Delete key"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AdminKeys;
