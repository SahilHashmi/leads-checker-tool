import { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Download, LogOut, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';
import { leadsApi } from '../services/api';

function UploadPage({ onLogout }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.txt')) {
        setError('Please select a .txt file');
        return;
      }
      setFile(selectedFile);
      setError('');
      setTaskId(null);
      setTaskStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      const response = await leadsApi.upload(file);
      setTaskId(response.data.task_id);
      startPolling(response.data.task_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const startPolling = (id) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    const poll = async () => {
      try {
        const response = await leadsApi.getTaskStatus(id);
        setTaskStatus(response.data);

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          clearInterval(pollIntervalRef.current);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    poll();
    pollIntervalRef.current = setInterval(poll, 2000);
  };

  const handleDownload = async () => {
    if (!taskId) return;

    try {
      const response = await leadsApi.downloadResult(taskId);
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fresh_leads_${taskId}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to download results');
    }
  };

  const handleReset = () => {
    setFile(null);
    setTaskId(null);
    setTaskStatus(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 pt-4">
          <h1 className="text-2xl font-bold text-white">Leads Checker Tool</h1>
          <button
            onClick={onLogout}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* Upload Section */}
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Leads File</h2>
            
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt"
                onChange={handleFileChange}
                className="hidden"
              />
              
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText className="w-8 h-8 text-blue-600" />
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Click to upload or drag and drop</p>
                  <p className="text-sm text-gray-400 mt-1">TXT file with one email per line</p>
                </>
              )}
            </div>

            {error && (
              <div className="mt-4 flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                <XCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleUpload}
                disabled={!file || uploading || taskStatus?.status === 'processing'}
                className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Process Leads
                  </>
                )}
              </button>

              {(taskId || file) && (
                <button
                  onClick={handleReset}
                  className="px-4 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                >
                  <RefreshCw className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>

          {/* Progress Section */}
          {taskStatus && (
            <div className="border-t pt-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Processing Status</h2>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>{taskStatus.message}</span>
                  <span>{taskStatus.progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-500 ${
                      taskStatus.status === 'completed'
                        ? 'bg-green-500'
                        : taskStatus.status === 'failed'
                        ? 'bg-red-500'
                        : 'bg-blue-600'
                    }`}
                    style={{ width: `${taskStatus.progress}%` }}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-gray-900">{taskStatus.total_emails}</p>
                  <p className="text-sm text-gray-500">Total Emails</p>
                </div>
                <div className="bg-red-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-red-600">{taskStatus.leaked_count}</p>
                  <p className="text-sm text-gray-500">Leaked</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-green-600">{taskStatus.fresh_count}</p>
                  <p className="text-sm text-gray-500">Fresh</p>
                </div>
              </div>

              {/* Download Button */}
              {taskStatus.status === 'completed' && taskStatus.fresh_count > 0 && (
                <button
                  onClick={handleDownload}
                  className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 focus:ring-4 focus:ring-green-200 transition flex items-center justify-center gap-2"
                >
                  <Download className="w-5 h-5" />
                  Download Fresh Leads ({taskStatus.fresh_count})
                </button>
              )}

              {taskStatus.status === 'completed' && taskStatus.fresh_count === 0 && (
                <div className="flex items-center justify-center gap-2 text-yellow-600 bg-yellow-50 p-4 rounded-lg">
                  <XCircle className="w-5 h-5" />
                  <span>No fresh leads found. All emails were already leaked.</span>
                </div>
              )}

              {taskStatus.status === 'failed' && (
                <div className="flex items-center justify-center gap-2 text-red-600 bg-red-50 p-4 rounded-lg">
                  <XCircle className="w-5 h-5" />
                  <span>Processing failed. Please try again.</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
