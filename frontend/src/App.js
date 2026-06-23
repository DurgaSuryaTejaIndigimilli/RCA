import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FiSend, FiUpload, FiActivity, FiAlertCircle, FiCheckCircle, FiClock, FiCpu, FiMessageSquare, FiTrendingUp, FiFileText, FiRefreshCw, FiHome, FiBarChart2, FiBook, FiSettings, FiZap, FiGithub, FiExternalLink, FiTrash2, FiDownload } from 'react-icons/fi';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisContext, setAnalysisContext] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState('chat');
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [stats, setStats] = useState({ totalAnalyses: 0, avgMttr: 0, issuesResolved: 0 });
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Welcome message
  useEffect(() => {
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `# 👋 Welcome to AI Root Cause Analyzer

I'm your **AI-powered incident analysis assistant**, specialized in diagnosing issues in distributed systems, microservices, and IoT infrastructure.

## 🚀 What I Can Do

- 🔍 **Analyze logs** from any source (ELK, Splunk, Kafka, raw text)
- 🎯 **Detect anomalies** using ML + rule-based engines
- 🔗 **Correlate events** across services to find causal chains
- 📊 **Generate RCA reports** with confidence scores
- 🛠️ **Recommend fixes** with prioritized action steps
- 💬 **Interactive Q&A** about your incident
- 📚 **Match historical incidents** from your knowledge base

## ⚡ Quick Start Options

1. **📂 Upload logs** — Paste or upload your system logs
2. **🎬 Run demo** — Try a pre-built incident scenario
3. **💬 Ask me** — Chat about debugging, best practices, or any tech question

Ready to start? Try clicking **"Run Demo Analysis"** in the sidebar, or paste your logs below!`,
      timestamp: new Date().toISOString(),
      isWelcome: true
    }]);
  }, []);

  // ==================== API Calls ====================

  const analyzeLogs = async (logs, query = null) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/analyze`, {
        logs,
        query
      });
      return response.data;
    } catch (error) {
      console.error('Analysis error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const sendChatMessage = async (message, context = null) => {
    try {
      const response = await axios.post(`${API_BASE}/api/chat`, {
        message,
        context
      });
      return response.data;
    } catch (error) {
      console.error('Chat error:', error);
      throw error;
    }
  };

  const runDemo = async () => {
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: '🎬 Run a demo analysis with a sample incident',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await axios.get(`${API_BASE}/api/demo`);
      const data = response.data;

      setAnalysisContext(data);
      setFeedbackGiven(false);
      setStats(prev => ({
        ...prev,
        totalAnalyses: prev.totalAnalyses + 1,
        issuesResolved: prev.issuesResolved + 1
      }));

      // Add to history
      setAnalysisHistory(prev => [{
        id: data.analysis_id,
        timestamp: data.timestamp,
        summary: data.summary,
        severity: data.summary?.severity || 0
      }, ...prev].slice(0, 10));

      // Build comprehensive response
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: formatAnalysisResponse(data),
        timestamp: new Date().toISOString(),
        analysisData: data,
        isAnalysis: true
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ **Error running demo**: ${error.message}\n\nPlease make sure the backend is running on port 8000.`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');

    // Check if input contains logs (multi-line or long)
    if (currentInput.includes('\n') || currentInput.length > 500) {
      // Treat as log analysis
      setIsLoading(true);
      try {
        const data = await analyzeLogs(currentInput);
        setAnalysisContext(data);
        setFeedbackGiven(false);
        setStats(prev => ({ ...prev, totalAnalyses: prev.totalAnalyses + 1 }));

        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: formatAnalysisResponse(data),
          timestamp: new Date().toISOString(),
          analysisData: data,
          isAnalysis: true
        };
        setMessages(prev => [...prev, assistantMessage]);
      } catch (error) {
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `❌ **Analysis failed**: ${error.message}\n\nPlease check:\n- Backend is running on port 8000\n- Log format is valid\n- Network connection is stable`,
          timestamp: new Date().toISOString(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    } else {
      // Regular chat
      setIsLoading(true);
      try {
        const response = await sendChatMessage(currentInput, analysisContext?.summary);
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          timestamp: response.timestamp
        };
        setMessages(prev => [...prev, assistantMessage]);
      } catch (error) {
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `❌ **Chat error**: ${error.message}`,
          timestamp: new Date().toISOString(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      const content = e.target.result;
      setInput(content);
      // Auto-submit
      setTimeout(() => handleSend(), 100);
    };
    reader.readAsText(file);
  };

  const submitFeedback = async (rating) => {
    if (!analysisContext?.analysis_id) return;

    try {
      await axios.post(`${API_BASE}/api/feedback`, {
        analysis_id: analysisContext.analysis_id,
        rating,
        rca_accurate: rating >= 4,
        fix_helpful: rating >= 4
      });
      setFeedbackGiven(true);

      const confirmMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `✅ **Thank you for your feedback!** Your rating of ${rating}/5 helps us improve the AI model. This will be used in future training cycles to enhance accuracy.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, confirmMessage]);
    } catch (error) {
      console.error('Feedback error:', error);
    }
  };

  const formatAnalysisResponse = (data) => {
    let content = '';

    // Summary
    if (data.summary) {
      const severityLevel = data.summary.severity > 0.8 ? '🔴 CRITICAL' :
                           data.summary.severity > 0.6 ? '🟠 HIGH' :
                           data.summary.severity > 0.4 ? '🟡 MEDIUM' : '🟢 LOW';
      content += `## 📊 Analysis Summary\n\n`;
      content += `| Metric | Value |\n|--------|-------|\n`;
      content += `| **Logs Analyzed** | ${data.summary.total_logs_analyzed} |\n`;
      content += `| **Anomalies Detected** | ${data.summary.anomalies_detected} |\n`;
      content += `| **Incident Chains** | ${data.summary.incident_chains} |\n`;
      content += `| **Severity Score** | ${(data.summary.severity * 100).toFixed(0)}% ${severityLevel} |\n`;
      content += `| **Services Affected** | ${data.summary.services_affected.join(', ')} |\n\n`;
    }

    // RCA Report
    if (data.rca_report) {
      content += `---\n\n${data.rca_report}\n\n---\n\n`;
    }

    // Fix Recommendations
    if (data.fix_recommendations) {
      content += `${data.fix_recommendations}\n\n---\n\n`;
    }

    // Historical Matches
    if (data.similar_historical_incidents && data.similar_historical_incidents.length > 0) {
      content += `## 📚 Similar Historical Incidents\n\n`;
      data.similar_historical_incidents.forEach((inc, i) => {
        content += `### ${i + 1}. ${inc.title}\n`;
        content += `- **ID**: \`${inc.incident_id}\`\n`;
        content += `- **Date**: ${inc.date}\n`;
        content += `- **Similarity**: ${(inc.similarity_score * 100).toFixed(0)}%\n`;
        content += `- **Resolution Time**: ${inc.resolution_time_minutes} minutes\n`;
        content += `- **Resolution**: ${inc.resolution}\n\n`;
      });
    }

    return content;
  };

  const clearChat = () => {
    setMessages([{
      id: 'welcome-new',
      role: 'assistant',
      content: `# 🔄 Chat Cleared

Ready for a new analysis! How can I help you?`,
      timestamp: new Date().toISOString()
    }]);
    setAnalysisContext(null);
    setFeedbackGiven(false);
  };

  return (
    <div className="app">
      {/* Animated Background */}
      <div className="bg-animation">
        <div className="bg-gradient-1"></div>
        <div className="bg-gradient-2"></div>
        <div className="bg-gradient-3"></div>
      </div>

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <div className="logo-container">
            <div className="logo-icon">
              <FiCpu />
            </div>
            <div className="logo-text">
              <div className="logo-title">RCA Analyzer</div>
              <div className="logo-subtitle">AI-Powered</div>
            </div>
          </div>
          <button className="icon-btn" onClick={() => setSidebarOpen(false)} title="Close sidebar">
            <FiActivity />
          </button>
        </div>

        <div className="sidebar-section">
          <div className="section-label">QUICK ACTIONS</div>
          <button className="sidebar-btn primary" onClick={runDemo} disabled={isLoading}>
            <FiZap /> Run Demo Analysis
          </button>
          <button className="sidebar-btn" onClick={() => fileInputRef.current?.click()} disabled={isLoading}>
            <FiUpload /> Upload Logs
            <input
              ref={fileInputRef}
              type="file"
              accept=".log,.txt"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </button>
          <button className="sidebar-btn" onClick={clearChat}>
            <FiTrash2 /> Clear Chat
          </button>
        </div>

        <div className="sidebar-section">
          <div className="section-label">STATISTICS</div>
          <div className="stat-card">
            <div className="stat-icon"><FiActivity /></div>
            <div className="stat-info">
              <div className="stat-value">{stats.totalAnalyses}</div>
              <div className="stat-label">Total Analyses</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon success"><FiCheckCircle /></div>
            <div className="stat-info">
              <div className="stat-value">{stats.issuesResolved}</div>
              <div className="stat-label">Issues Resolved</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon warning"><FiClock /></div>
            <div className="stat-info">
              <div className="stat-value">~45m</div>
              <div className="stat-label">Avg Resolution</div>
            </div>
          </div>
        </div>

        {analysisHistory.length > 0 && (
          <div className="sidebar-section">
            <div className="section-label">RECENT ANALYSES</div>
            <div className="history-list">
              {analysisHistory.map((item) => (
                <div key={item.id} className="history-item">
                  <FiFileText className="history-icon" />
                  <div className="history-content">
                    <div className="history-id">{item.id.substring(0, 18)}...</div>
                    <div className="history-meta">
                      {new Date(item.timestamp).toLocaleTimeString()} · 
                      <span className={`severity-badge ${item.severity > 0.7 ? 'high' : item.severity > 0.4 ? 'medium' : 'low'}`}>
                        {item.severity > 0.7 ? 'High' : item.severity > 0.4 ? 'Med' : 'Low'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <div className="footer-text">
            <div className="footer-title">Harris IoT Ideathon 2026</div>
            <div className="footer-subtitle">Theme: AI-Driven Automation</div>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-content">
        <header className="top-bar">
          <div className="top-bar-left">
            {!sidebarOpen && (
              <button className="icon-btn" onClick={() => setSidebarOpen(true)}>
                <FiActivity />
              </button>
            )}
            <div className="chat-title">
              <div className="title-main">Incident Analysis Chat</div>
              <div className="title-sub">
                <span className="status-dot"></span>
                AI Engine Online · {isLoading ? 'Analyzing...' : 'Ready'}
              </div>
            </div>
          </div>
          <div className="top-bar-right">
            <div className="badge">
              <FiCpu /> GPT-4 Ready
            </div>
            <div className="badge success">
              <FiCheckCircle /> System Healthy
            </div>
          </div>
        </header>

        <div className="messages-container">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onFeedback={submitFeedback}
              feedbackGiven={feedbackGiven}
            />
          ))}

          {isLoading && (
            <div className="message-row assistant">
              <div className="avatar assistant-avatar">
                <FiCpu />
              </div>
              <div className="message-bubble assistant loading">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
                <div className="loading-text">Analyzing logs and generating RCA report...</div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <button
              className="input-action-btn"
              onClick={() => fileInputRef.current?.click()}
              title="Upload log file"
            >
              <FiUpload />
            </button>
            <textarea
              className="message-input"
              placeholder="Paste logs here, or ask me anything about incident analysis..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              rows={1}
              disabled={isLoading}
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              title="Send message"
            >
              {isLoading ? <FiRefreshCw className="spinning" /> : <FiSend />}
            </button>
          </div>
          <div className="input-hint">
            <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line · Paste logs for auto-analysis
          </div>
        </div>
      </main>
    </div>
  );
}

// ==================== Message Bubble Component ====================

function MessageBubble({ message, onFeedback, feedbackGiven }) {
  const isUser = message.role === 'user';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
  };

  return (
    <div className={`message-row ${message.role} animate-fade-in`}>
      <div className={`avatar ${isUser ? 'user-avatar' : 'assistant-avatar'}`}>
        {isUser ? '👤' : <FiCpu />}
      </div>
      <div className="message-content-wrapper">
        <div className="message-meta">
          <span className="message-author">{isUser ? 'You' : 'AI Assistant'}</span>
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <div className={`message-bubble ${message.role} ${message.isError ? 'error' : ''}`}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              }
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        <div className="message-actions">
          <button className="action-btn" onClick={copyToClipboard} title="Copy">
            <FiDownload /> Copy
          </button>
          {message.isAnalysis && !isUser && !feedbackGiven && (
            <div className="feedback-group">
              <span className="feedback-label">Rate this analysis:</span>
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  className="rating-btn"
                  onClick={() => onFeedback(rating)}
                  title={`Rate ${rating}/5`}
                >
                  ⭐
                </button>
              ))}
            </div>
          )}
          {feedbackGiven && message.isAnalysis && (
            <span className="feedback-thanks">✅ Feedback submitted</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;