import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Key, Download, LogOut, FileText, Calendar, AlertCircle } from 'lucide-react';
import { adminApi } from '../services/api';

function AdminLeads({ onLogout }) {
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleDownload = async () => {
    if (!fromDate || !toDate) {
      setError('Please select both from and to dates');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const fromDateTime = new Date(fromDate).toISOString();
      const toDateTime = new Date(toDate + 'T23:59:59').toISOString();

      const response = await adminApi.getLeadsByDate(fromDateTime, toDateTime);
      
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads_${fromDate}_${toDate}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSuccess('Leads downloaded successfully!');
    } catch (err) {
      if (err.response?.status === 404) {
        setError('No leads found in the specified date range');
      } else {
        setError('Failed to download leads');
      }
    } finally {
      setLoading(false);
    }
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
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-gray-300 rounded-lg hover:bg-slate-600 transition"
          >
            <Key className="w-4 h-4" />
            Device Keys
          </Link>
          <Link
            to="/admin/leads"
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg"
          >
            <FileText className="w-4 h-4" />
            Download Leads
          </Link>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Download Fresh Leads by Date</h2>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                From Date
              </label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                To Date
              </label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition"
              />
            </div>
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {success && (
            <div className="mb-4 flex items-center gap-2 text-green-600 bg-green-50 p-3 rounded-lg">
              <Download className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm">{success}</span>
            </div>
          )}

          <button
            onClick={handleDownload}
            disabled={loading || !fromDate || !toDate}
            className="w-full flex items-center justify-center gap-2 bg-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-purple-700 focus:ring-4 focus:ring-purple-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            <Download className="w-5 h-5" />
            {loading ? 'Downloading...' : 'Download Leads'}
          </button>

          <p className="mt-4 text-sm text-gray-500 text-center">
            Downloads all fresh leads collected within the selected date range as a TXT file.
          </p>
        </div>
      </div>
    </div>
  );
}

export default AdminLeads;
