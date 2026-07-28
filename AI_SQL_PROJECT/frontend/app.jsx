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

  return (
    <div className="app-container">
      <header>
        <h1>AI SQL Assistant</h1>
        <p className="info-text">Chat with your database in plain English</p>
      </header>

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
          className="primary" 
          onClick={() => handleQuery(input)}
          disabled={loading || !input.trim() || confirmModal !== null}
        >
          Run
        </button>
      </div>

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
