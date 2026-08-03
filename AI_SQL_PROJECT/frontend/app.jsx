const { useState, useRef, useEffect } = React;

// In production (served from FastAPI), API is on the same origin.
// In local dev (separate servers), fall back to localhost:8000.
const API_BASE = window.location.port === '5173'
  ? 'http://localhost:8000'
  : '';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [confirmModal, setConfirmModal] = useState(null);
  const [isFileUploaded, setIsFileUploaded] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const endOfMessagesRef = useRef(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleQuery = async (question, confirmed = false, sql = null) => {
    if (!question.trim()) return;
    
    setLoading(true);
    // Add user question to chat if it's not a confirmation
    if (!confirmed) {
      setMessages(prev => [...prev, { type: 'user', text: question }]);
      setInput('');
    }

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, confirmed, sql })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.error || 'Server error');
      }

      if (data.requires_confirmation) {
        setConfirmModal({ question, sql: data.sql, message: data.message });
      } else {
        setConfirmModal(null);
        setMessages(prev => [...prev, { 
          type: 'assistant', 
          sql: data.sql,
          result: data,
          id: Date.now()
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        error: error.message || 'Failed to connect to backend'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const confirmDestructive = () => {
    if (confirmModal) {
      handleQuery(confirmModal.question, true, confirmModal.sql);
    }
  };

  const cancelDestructive = () => {
    setMessages(prev => [...prev, { 
      type: 'assistant', 
      error: 'Query execution cancelled by user.',
      sql: confirmModal.sql
    }]);
    setConfirmModal(null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file) => {
    setSelectedFile(file);
    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setUploadMessage('Uploading and processing file...');
    
    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || data.error || 'Upload failed');
      }
      
      setIsFileUploaded(true);
      setUploadMessage('');
      setMessages([{ type: 'assistant', text: `Success! ${data.message}. You can now start asking questions.` }]);
    } catch (error) {
       setUploadMessage(`Error: ${error.message}`);
       setSelectedFile(null); // Reset on error so they can try again
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFile = () => {
    setIsFileUploaded(false);
    setSelectedFile(null);
    setMessages([]);
    setUploadMessage('');
  };

  return (
    <div className="app-container">
      <header className="page-header">
        <h1 className="animate-title">AI SQL Assistant</h1>
        <p className="info-text animate-tagline">Chat with your database in plain English</p>
      </header>

      {!selectedFile ? (
        <div 
          className={`glass-panel upload-area animate-upload ${isDragging ? 'dragging' : ''}`} 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <h2>Upload Data to Begin</h2>
          <p>Drag & drop or select an Excel/CSV file to fetch data from.</p>
          <input 
            type="file" 
            accept=".csv, .xlsx, .xls" 
            onChange={handleFileSelect} 
            disabled={loading}
            id="file-upload"
            className="hidden-input"
          />
          <label htmlFor="file-upload" className={`button primary custom-file-label ${loading ? 'disabled' : ''}`}>
            Choose File
          </label>
          {uploadMessage && <p className="info-text">{uploadMessage}</p>}
        </div>
      ) : (
        <div className="main-workspace animate-workspace">
          <div className="glass-panel file-preview-card">
            <div className="file-info">
              <span className="file-icon">📄</span>
              <span className="file-name">{selectedFile.name}</span>
              {loading && !isFileUploaded && <span className="upload-status">(Uploading...)</span>}
            </div>
            <button className="remove-file-btn" onClick={handleRemoveFile} title="Remove File" disabled={loading}>
              ✕
            </button>
          </div>
          
          {isFileUploaded && (
            <div className="chat-workspace animate-chat">
              <div className="glass-panel chat-history">
        {messages.map((msg, idx) => (
          <div key={idx} className="message-card">
            {msg.type === 'user' ? (
              <div className="question">Q: {msg.text}</div>
            ) : (
              <AssistantMessage 
                msg={msg} 
                onCorrect={(sql, error) => {
                   // When correcting, we use the last question from the chat history
                   const lastQ = [...messages].reverse().find(m => m.type === 'user')?.text || "Unknown question";
                   // Just do a quick loading state
                   setLoading(true);
                   fetch(`${API_BASE}/correct`, {
                     method: 'POST',
                     headers: { 'Content-Type': 'application/json' },
                     body: JSON.stringify({ question: lastQ, sql, error })
                   }).then(res => res.json()).then(data => {
                      if(data.sql) {
                        // re-run the corrected query
                        handleQuery(lastQ, false, data.sql);
                      } else {
                         setMessages(prev => [...prev, { type: 'assistant', error: 'Could not correct query.'}]);
                         setLoading(false);
                      }
                   }).catch(e => {
                      setMessages(prev => [...prev, { type: 'assistant', error: e.message}]);
                      setLoading(false);
                   });
                }}
              />
            )}
          </div>
        ))}
        {loading && <div className="message-card">Loading...</div>}
        <div ref={endOfMessagesRef} />
      </div>

              <div className="glass-panel input-area">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleQuery(input)}
                  placeholder="e.g. Show the five highest-paid employees..."
                  disabled={loading || confirmModal !== null}
                />
                <button 
                  className={`primary analyze-btn ${!input.trim() || loading || confirmModal !== null ? 'disabled' : 'ready'}`}
                  onClick={() => handleQuery(input)}
                  disabled={loading || !input.trim() || confirmModal !== null}
                >
                  {loading && !uploadMessage ? <span className="spinner"></span> : 'Run'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {confirmModal && (
        <div className="modal-overlay">
          <div className="glass-panel modal">
            <h2>⚠️ Confirmation Required</h2>
            <p>{confirmModal.message}</p>
            <div className="sql-block">{confirmModal.sql}</div>
            <div className="actions">
              <button onClick={cancelDestructive}>Cancel</button>
              <button className="danger" onClick={confirmDestructive}>Run Query</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function AssistantMessage({ msg, onCorrect }) {
  const [activeTab, setActiveTab] = useState(null);
  const [tabData, setTabData] = useState({});
  const [loadingTab, setLoadingTab] = useState(false);

  if (msg.error) {
    return (
      <div>
        {msg.sql && <div className="sql-block">{msg.sql}</div>}
        <div className="error-text">Error: {msg.error}</div>
        {msg.sql && !msg.error.includes('cancelled') && (
          <button className="primary" onClick={() => onCorrect(msg.sql, msg.error)}>
            Auto-Correct Query
          </button>
        )}
      </div>
    );
  }

  const handleAction = async (action) => {
    if (activeTab === action) {
      setActiveTab(null);
      return;
    }
    setActiveTab(action);
    if (tabData[action]) return; // Already fetched

    setLoadingTab(true);
    try {
      const res = await fetch(`${API_BASE}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: msg.sql })
      });
      const data = await res.json();
      setTabData(prev => ({ ...prev, [action]: data.explanation || data.optimization || 'No data returned.' }));
    } catch (e) {
      setTabData(prev => ({ ...prev, [action]: `Error: ${e.message}` }));
    } finally {
      setLoadingTab(false);
    }
  };

  return (
    <div>
      <div className="sql-block">{msg.sql}</div>
      
      {msg.result && !msg.result.success && (
        <div className="error-text">DB Error: {msg.result.error}</div>
      )}

      {msg.result && msg.result.success && msg.result.message && (
        <div className="info-text">{msg.result.message}</div>
      )}

      {msg.result && msg.result.success && msg.result.rows && msg.result.rows.length > 0 && (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                {msg.result.columns.map(col => <th key={col}>{col}</th>)}
              </tr>
            </thead>
            <tbody>
              {msg.result.rows.map((row, i) => (
                <tr key={i}>
                  {msg.result.columns.map(col => <td key={col}>{row[col]}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {msg.result && (!msg.result.success) && msg.sql && (
        <div className="actions">
           <button className="primary" onClick={() => onCorrect(msg.sql, msg.result.error)}>
            Auto-Correct Query
          </button>
        </div>
      )}

      {msg.result && msg.result.success && msg.sql && (
        <div className="actions">
          <button 
            className={activeTab === 'explain' ? 'active' : ''} 
            onClick={() => handleAction('explain')}
          >
            Explain
          </button>
          <button 
            className={activeTab === 'optimize' ? 'active' : ''} 
            onClick={() => handleAction('optimize')}
          >
            Optimize
          </button>
        </div>
      )}

      {activeTab && (
        <div className="tabs">
          <div className="tabs-header">
            <span className="tab-btn active">
              {activeTab === 'explain' ? 'Explanation' : 'Optimization Suggestions'}
            </span>
          </div>
          <div className="tab-content">
            {loadingTab ? 'Loading...' : tabData[activeTab]}
          </div>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
