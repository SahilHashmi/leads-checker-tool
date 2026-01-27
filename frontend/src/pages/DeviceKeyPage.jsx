import { useState } from 'react';
import { Key, AlertCircle, CheckCircle } from 'lucide-react';
import { authApi } from '../services/api';

function DeviceKeyPage({ onSuccess }) {
  const [deviceKey, setDeviceKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authApi.verifyKey(deviceKey);
      
      if (response.data.valid) {
        localStorage.setItem('deviceKey', deviceKey);
        localStorage.setItem('deviceKeyValid', 'true');
        onSuccess();
      } else {
        setError(response.data.message || 'Invalid device key');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to verify device key');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <Key className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Leads Checker Tool</h1>
          <p className="text-gray-500 mt-2">Enter your device key to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="deviceKey" className="block text-sm font-medium text-gray-700 mb-2">
              Device Key
            </label>
            <input
              type="text"
              id="deviceKey"
              value={deviceKey}
              onChange={(e) => setDeviceKey(e.target.value)}
              placeholder="Enter your device key"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              required
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !deviceKey.trim()}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? 'Verifying...' : 'Verify & Continue'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default DeviceKeyPage;
