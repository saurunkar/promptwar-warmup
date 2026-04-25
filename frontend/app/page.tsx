"use client";

import React, { useState, useEffect } from 'react';
import '../styles/globals.css';
import { Send, BookOpen, Target, BarChart2, Award, Zap, ChevronRight, BrainCircuit } from 'lucide-react';

export default function Home() {
  const [query, setQuery] = useState("");
  const [activeState, setActiveState] = useState("INTRODUCTION");
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Welcome back! Ready to explore something new? Try 'Explain Neural Networks' to start your journey." }
  ]);

  const handleSend = () => {
    if (!query.trim()) return;
    setMessages([...messages, { role: 'user', content: query }]);
    
    // Simulate complex orchestration
    setTimeout(() => {
      let response = "";
      if (query.toLowerCase().includes("neural")) {
        setActiveState("DEEP_DIVE");
        response = "Great choice. Neural Networks are the backbone of modern AI. Let's move from the basics into a technical deep dive. We'll look at neurons, layers, and how they learn...";
      } else {
        response = "I've analyzed your query. Based on your mixed learning style, here is a tailored explanation...";
      }
      setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    }, 1000);
    setQuery("");
  };

  return (
    <main className="container">
      <div className="layout-grid">
        {/* Sidebar - Advanced Mastery View */}
        <div className="glass-card fade-in sidebar">
          <div className="logo-section">
            <div className="logo-icon"><Zap size={20} color="white" /></div>
            <h2 className="gradient-text">Aegis AI</h2>
          </div>

          <div className="section">
            <h3 className="section-title">Knowledge Nexus</h3>
            <div className="radial-graph-container">
              <RadialGraph progress={65} label="Total Mastery" />
            </div>
          </div>

          <div className="section">
            <h3 className="section-title">Concept Clusters</h3>
            <div className="concept-list">
              <ConceptItem label="Deep Learning" level="Expert" color="#6366f1" />
              <ConceptItem label="Mathematics" level="Intermediate" color="#f43f5e" />
              <ConceptItem label="System Design" level="Beginner" color="#10b981" />
            </div>
          </div>

          <div className="learning-status">
            <div className={`status-pill ${activeState.toLowerCase()}`}>
              <BrainCircuit size={14} />
              <span>{activeState}</span>
            </div>
          </div>
        </div>

        {/* Main Content - Chat & Interaction */}
        <div className="main-content">
          <div className="chat-window glass-card fade-in">
            <div className="messages-container">
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.role}`}>
                  <div className="message-bubble">{m.content}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="input-area glass-card fade-in">
            <input 
              className="input" 
              placeholder="Start a new topic or ask a follow-up..." 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="btn" onClick={handleSend}>
              <Send size={18} />
              <span>Analyze</span>
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

function RadialGraph({ progress, label }: { progress: number, label: string }) {
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="radial-graph">
      <svg width="140" height="140">
        <circle className="bg" cx="70" cy="70" r={radius} />
        <circle 
          className="progress" 
          cx="70" cy="70" r={radius} 
          style={{ strokeDasharray: circumference, strokeDashoffset: offset }}
        />
        <text x="70" y="70" className="percent">{progress}%</text>
        <text x="70" y="90" className="label">{label}</text>
      </svg>
    </div>
  );
}

function ConceptItem({ label, level, color }: { label: string, level: string, color: string }) {
  return (
    <div className="concept-item">
      <div className="dot" style={{ backgroundColor: color }}></div>
      <div className="details">
        <span className="name">{label}</span>
        <span className="level">{level}</span>
      </div>
      <ChevronRight size={14} className="icon" />
    </div>
  );
}
