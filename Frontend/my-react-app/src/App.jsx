import { useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [pdfFile, setPdfFile] = useState(null);
  const [messages, setMessages] = useState([]); // Stores user queries and chatbot responses

  const handleSendMessage = async () => {
    if (message.trim()) {
      const userMessage = { type: "user", text: message };

      try {
        const res = await fetch("http://127.0.0.1:5000/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query: message }),
        });

        if (!res.ok) {
          throw new Error("Failed to fetch response");
        }

        const data = await res.json();
        const botResponse = { type: "bot", text: data.response };

        // Update messages state with user query and bot response
        setMessages((prevMessages) => [...prevMessages, userMessage, botResponse]);
      } catch (error) {
        console.error("Error sending message:", error);
      }

      setMessage(""); // Clear input field after sending message
    }
  };

  return (
    <div>
      <h1>Research Assistance</h1>
      {/* Message display section */}
      <div className="messages-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.type}`}>
            {msg.type === "user" ? "🧑‍💬" : "🤖"} {msg.text}
          </div>
        ))}
      </div>

      {/* Chat input section */}
      <div className="chat-container">
        <div className="chat-box">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Message React"
            className="chat-input"
          />

          <button onClick={handleSendMessage} className="send-button">
            <span className="send-icon">↑</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
