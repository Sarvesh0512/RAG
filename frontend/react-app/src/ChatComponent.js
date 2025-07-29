import React, { useState } from 'react';

// Define the backend API URL.
// Make sure this matches where your FastAPI server is running.
const API_URL = 'http://localhost:8000';

function ChatComponent() {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!question.trim()) return;

        setIsLoading(true);
        setError(null);
        setAnswer('');

        try {
            const response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                // Handle HTTP errors from the backend
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setAnswer(data.answer);

        } catch (err) {
            setError(err.message);
            console.error("Failed to fetch chat response:", err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <h1>Asset Management Chatbot</h1>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a question..."
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Thinking...' : 'Send'}
                </button>
            </form>

            {error && <div style={{ color: 'red' }}>Error: {error}</div>}

            {answer && <p><strong>Answer:</strong> {answer}</p>}
        </div>
    );
}

export default ChatComponent;