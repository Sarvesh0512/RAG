import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Define the backend API URL.
const API_URL = 'http://localhost:8000';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;

if (recognition) {
  recognition.continuous = false;
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);

  // Function to scroll to the bottom of the message list
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch initial chat history when the component mounts.
  // NOTE: This is commented out because the `/chats/` endpoint is not yet
  // implemented in the backend.
  // useEffect(() => {
  //   const fetchChatHistory = async () => {
  //     try {
  //       const response = await fetch(`${API_URL}/chats/`);
  //       if (!response.ok) {
  //         throw new Error('Failed to fetch chat history');
  //       }
  //       const chatLogs = await response.json();
  //       // Transform the logs into the format the UI expects
  //       const formattedMessages = chatLogs.flatMap(log => [
  //         { text: log.user_query, sender: 'user' },
  //         { text: log.bot_response, sender: 'bot' },
  //       ]);
  //       setMessages(formattedMessages);
  //     } catch (error) {
  //       console.error("Error fetching chat history:", error);
  //       setMessages([{ text: 'Failed to load chat history.', sender: 'bot' }]);
  //     }
  //   };
  //   fetchChatHistory();
  // }, []);

  // Effect to handle speech recognition events
  useEffect(() => {
    if (!recognition) return;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setUserInput(transcript);
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    return () => {
      recognition.stop();
    };
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const query = userInput.trim();
    if (!query) return;

    const userMessage = { text: query, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setUserInput("");
    setIsLoading(true);

    try {
      // Use the correct API URL, endpoint, and payload structure
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      // Use the correct key ('answer') from the backend response
      const botResponse = await response.json();
      const newBotMessage = { text: botResponse.answer, sender: 'bot' };
      setMessages(prev => [...prev, newBotMessage]);

    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = { text: 'Sorry, something went wrong. Please try again.', sender: 'bot' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleListening = () => {
    if (!recognition) {
      alert("Sorry, your browser doesn't support voice recognition.");
      return;
    }
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
    setIsListening(!isListening);
  };

  return (
    <div className="chat-app">
      <div className="chat-header">
        <h2>RAG Chatbot</h2>
        <p>Your AI Assistant</p>
      </div>
      <div className="message-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message-container ${msg.sender}`}>
            <div className="avatar">
              {msg.sender === 'user' ? '🧑' : '🤖'}
            </div>
            <div className={`message ${msg.sender}`}>
              {msg.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-container bot">
            <div className="avatar">🤖</div>
            <div className="message bot loading-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          className="chat-input"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="Type a message or use the microphone..."
          disabled={isLoading}
        />
        {recognition && (
          <button
            type="button"
            onClick={handleToggleListening}
            className={`mic-button ${isListening ? 'listening' : ''}`}
            disabled={isLoading}
            title="Use voice input"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
          </button>
        )}
        <button
          type="submit"
          className="send-button"
          disabled={isLoading || !userInput.trim()}
          title="Send message"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </form>
    </div>
  );
}

export default App;