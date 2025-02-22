import React, { useState } from 'react';
import { AlertCircle, Upload, FileDown, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const SchemaProcessor = () => {
  const [inputFile, setInputFile] = useState(null);
  const [query, setQuery] = useState('');
  const [outputFormat, setOutputFormat] = useState('json');
  const [threshold, setThreshold] = useState(0.1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setInputFile(file);
      setError(null);
    }
  };

  const processSchema = async () => {
    if (!inputFile || !query.trim()) {
      setError('Please provide both a schema file and a query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Here we would integrate with the Python backend
      // For now, we'll simulate processing
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simulated result
      const mockResult = {
        orders: {
          columns: [
            { name: 'order_id', type: 'integer', description: 'Unique order identifier' },
            { name: 'user_id', type: 'integer', description: 'Reference to users table' }
          ],
          relevance_score: 0.85
        },
        users: {
          columns: [
            { name: 'user_id', type: 'integer', description: 'Unique user identifier' },
            { name: 'username', type: 'string', description: "User's display name" }
          ],
          relevance_score: 0.65
        }
      };

      setResult(mockResult);
    } catch (err) {
      setError('Error processing schema: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadResult = () => {
    if (!result) return;

    const content = outputFormat === 'json' 
      ? JSON.stringify(result, null, 2)
      : "# YAML output would be here";

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `processed_schema.${outputFormat}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Schema Processor</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Upload Schema File</label>
              <div className="border-2 border-dashed rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept=".json,.yaml,.yml"
                  onChange={handleFileChange}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="flex flex-col items-center gap-2">
                    <Upload className="h-8 w-8 text-gray-400" />
                    <span className="text-sm text-gray-600">
                      {inputFile ? inputFile.name : 'Drop your schema file here or click to browse'}
                    </span>
                  </div>
                </label>
              </div>
            </div>

            {/* Query Input */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Query</label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your query (e.g., 'find user orders')"
                className="w-full p-2 border rounded"
              />
            </div>

            {/* Output Format */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Output Format</label>
              <Select value={outputFormat} onValueChange={setOutputFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="yaml">YAML</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Threshold Slider */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Relevance Threshold: {threshold}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Process Button */}
            <Button 
              onClick={processSchema} 
              disabled={loading || !inputFile || !query.trim()}
              className="w-full"
            >
              {loading ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Process Schema
            </Button>

            {/* Error Display */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results Display */}
        {result && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Results</CardTitle>
              <Button onClick={downloadResult} variant="outline" size="sm">
                <FileDown className="mr-2 h-4 w-4" />
                Download
              </Button>
            </CardHeader>
            <CardContent>
              <pre className="bg-gray-100 p-4 rounded-lg overflow-auto max-h-96">
                {outputFormat === 'json' 
                  ? JSON.stringify(result, null, 2)
                  : "# YAML output would be here"}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default SchemaProcessor;