import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [mode, setMode] = useState('chat')
  const [input, setInput] = useState('')
  const [output, setOutput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [error, setError] = useState('')
  const [apiBaseUrl, setApiBaseUrl] = useState('')

  useEffect(() => {
    const isDev = import.meta.env.MODE === 'development'
    const baseUrl = isDev 
      ? 'http://localhost:8000'
      : import.meta.env.VITE_API_BASE_URL || 'https://vizzy-backend.railway.app'
    setApiBaseUrl(baseUrl)
    
    const id = `session-${Date.now()}`
    setSessionId(id)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    setLoading(true)
    setError('')
    try {
      const response = await axios.post(`${apiBaseUrl}/chat`, {
        message: input,
        mode: mode,
        session_id: sessionId
      })
      
      setOutput(response.data.response || response.data.message || '')
      setInput('')
    } catch (err) {
      console.error('Error:', err)
      setError(err.response?.data?.detail || 'An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Vizzy Chat</h1>
        <p>AI Chat & Image Generation</p>
      </header>

      <div className="mode-toggle">
        <button 
          className={`toggle-btn ${mode === 'chat' ? 'active' : ''}`}
          onClick={() => setMode('chat')}
        >
          💬 Chat
        </button>
        <button 
          className={`toggle-btn ${mode === 'image' ? 'active' : ''}`}
          onClick={() => setMode('image')}
        >
          🎨 Generate Image
        </button>
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={mode === 'chat' ? 'Ask something...' : 'Describe an image...'}
          disabled={loading}
          className="input-field"
        />
        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? 'Processing...' : 'Send'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      {output && (
        <div className="output-container">
          {mode === 'image' ? (
            <img src={output} alt="Generated" className="generated-image" />
          ) : (
            <div className="chat-response">{output}</div>
          )}
        </div>
      )}

      <footer className="app-footer">
        <p>Session ID: {sessionId}</p>
      </footer>
    </div>
  )
}

export default App
