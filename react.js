const processSchema = async () => {
    if (!inputFile || !query.trim()) {
      setError('Please provide both a schema file and a query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', inputFile);
      formData.append('query', query);
      formData.append('output_format', outputFormat);
      formData.append('threshold', threshold);

      const response = await fetch('/api/process-schema', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        setResult(data.result);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Error processing schema: ' + err.message);
    } finally {
      setLoading(false);
    }
};