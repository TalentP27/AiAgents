import React, { useState } from 'react';

const ProcurementAgent: React.FC = () => {
  const [productList, setProductList] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [csvAvailable, setCsvAvailable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setCsvAvailable(false);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('product_list', productList);
      formData.append('location', location);
      const res = await fetch('http://localhost:8000/procure', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to fetch results');
      const data = await res.json();
      setResult(data.markdown);
      setCsvAvailable(data.csv_available);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    window.open('http://localhost:8000/csv', '_blank');
  };

  return (
    <div className="max-w-2xl mx-auto py-12 px-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Procurement Agent</h1>
      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-4">
        <div>
          <label className="block font-medium mb-1">Product List (comma separated)</label>
          <textarea
            className="w-full border rounded p-2 min-h-[60px]"
            value={productList}
            onChange={e => setProductList(e.target.value)}
            placeholder="e.g. Office Chairs, MacBooks, Whiteboards"
            required
          />
        </div>
        <div>
          <label className="block font-medium mb-1">Location (city, country)</label>
          <input
            className="w-full border rounded p-2"
            value={location}
            onChange={e => setLocation(e.target.value)}
            placeholder="e.g. Madrid, Spain"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Find Vendors'}
        </button>
      </form>
      {error && <div className="mt-4 text-red-600 text-center">{error}</div>}
      {result && (
        <div className="mt-8 bg-gray-50 p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-2">Results</h2>
          <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: result.replace(/\n/g, '<br/>') }} />
          {csvAvailable && (
            <button
              onClick={handleDownload}
              className="mt-4 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
            >
              Download CSV
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ProcurementAgent; 