"use client";

import React, { useState } from 'react';
import '../styles/globals.css';
import { Send, BookOpen, Target, BarChart2, Award, Zap } from 'lucide-react';

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your Intelligent Learning Assistant. What would you like to master today?' }
  ]);

  const handleSend = () => {
    if (!query.trim()) return;
    setMessages([...messages, { role: 'user', content: query }]);
    // Simulate assistant response
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `I've analyzed your query about "${query}". Let's dive in. First, I'll explain the core concepts...` 
      }]);
    }, 1000);
    setQuery("");
  };

  return (
    <main className="container">
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '2rem', height: 'calc(100vh - 4rem)' }}>
        {/* Sidebar - Knowledge Graph & Stats */}
        <div className="glass-card fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ padding: '8px', background: 'var(--primary)', borderRadius: '10px' }}>
              <Zap size={20} color="white" />
            </div>
            <h2 className="gradient-text" style={{ fontSize: '1.25rem' }}>Aegis Learning</h2>
          </div>

          <div style={{ marginTop: '1rem' }}>
            <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Current Mastery</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              < MasteryItem label="Neural Networks" progress={75} />
              < MasteryItem label="Calculus" progress={45} />
              < MasteryItem label="Python Logic" progress={90} />
            </div>
          </div>

          <div style={{ marginTop: 'auto' }}>
            <div className="glass-card" style={{ padding: '1rem', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8rem' }}>Daily Goal</span>
                <span style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>80%</span>
              </div>
              <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }}>
                <div style={{ height: '100%', width: '80%', background: 'var(--primary)', borderRadius: '3px' }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content - Agent Interaction */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="glass-card fade-in" style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '2.5rem' }}>
            {messages.map((m, i) => (
              <div key={i} style={{ 
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                background: m.role === 'user' ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                padding: '1.25rem',
                borderRadius: m.role === 'user' ? '20px 20px 0 20px' : '20px 20px 20px 0',
                border: m.role === 'user' ? 'none' : '1px solid var(--glass-border)',
                lineHeight: '1.6'
              }}>
                {m.content}
              </div>
            ))}
          </div>

          <div className="glass-card fade-in" style={{ padding: '1rem', display: 'flex', gap: '1rem' }}>
            <input 
              className="input" 
              placeholder="Ask anything... (e.g. Explain Quantum Computing at a slow pace)" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="btn" onClick={handleSend}>
              <Send size={18} />
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

function MasteryItem({ label, progress }: { label: string, progress: number }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
        <span>{label}</span>
        <span>{progress}%</span>
      </div>
      <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px' }}>
        <div style={{ height: '100%', width: `${progress}%`, background: 'var(--primary)', borderRadius: '2px' }}></div>
      </div>
    </div>
  );
}
