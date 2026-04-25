"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Send, Zap, ChevronRight, BrainCircuit, BookOpen, Target, Award, Loader2, Settings, BarChart3 } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: string;
  suggested_actions?: string[];
}

interface QuizQuestion {
  question: string;
  options: string[];
  correct_answer: string;
  explanation?: string;
}

export default function Home() {
  const [userId] = useState("user-001");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Welcome to Aegis! I'm your AI learning companion. What topic would you like to explore today? Try asking me to explain Neural Networks, Calculus, or any subject.", type: 'welcome' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [activeState, setActiveState] = useState("idle");
  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [quiz, setQuiz] = useState<QuizQuestion[] | null>(null);
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizConcept, setQuizConcept] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load profile on mount
  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${API_URL}/profile/${userId}`);
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setActiveState(data.current_state || "idle");
        setCurrentTopic(data.current_topic);
      }
    } catch (e) {
      console.log("Profile fetch failed (backend may be starting):", e);
    }
  };

  const handleSend = async () => {
    if (!query.trim() || isLoading) return;
    const userMsg = query;
    setQuery("");
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, query: userMsg }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.content,
          type: data.type,
          suggested_actions: data.suggested_actions,
        }]);
        setActiveState(data.state || "idle");
        setCurrentTopic(data.topic);
        if (data.knowledge) {
          setProfile((prev: any) => ({ ...prev, knowledge_graph: data.knowledge }));
        }
      } else {
        setMessages(prev => [...prev, { role: 'system', content: 'Server error. Please try again.' }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'system', content: 'Unable to reach the server. Is the backend running?' }]);
    }
    setIsLoading(false);
  };

  const handleStartQuiz = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, concept: currentTopic }),
      });
      if (res.ok) {
        const data = await res.json();
        setQuiz(data.questions);
        setQuizIndex(0);
        setQuizConcept(data.concept);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `📝 Quiz on "${data.concept}" (${data.difficulty} difficulty) — ${data.total_questions} questions. Let's go!`,
          type: 'quiz_start',
        }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'system', content: 'Failed to generate quiz.' }]);
    }
    setIsLoading(false);
  };

  const handleQuizAnswer = async (answer: string) => {
    if (!quiz) return;
    const q = quiz[quizIndex];
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          concept: quizConcept,
          question: q.question,
          user_answer: answer,
          correct_answer: q.correct_answer,
        }),
      });

      if (res.ok) {
        const fb = await res.json();
        const icon = fb.is_correct ? '✅' : '❌';
        setMessages(prev => [...prev,
          { role: 'user', content: answer },
          { role: 'assistant', content: `${icon} ${fb.explanation}`, type: 'feedback' },
        ]);

        if (fb.updated_knowledge) {
          setProfile((prev: any) => ({ ...prev, knowledge_graph: fb.updated_knowledge, weak_areas: fb.weak_areas }));
        }

        if (quizIndex < quiz.length - 1) {
          setQuizIndex(quizIndex + 1);
        } else {
          setQuiz(null);
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: '🎉 Quiz complete! Your knowledge graph has been updated. Keep learning or try another topic!',
            type: 'quiz_end',
            suggested_actions: ['Continue Learning', 'New Topic', 'View Progress'],
          }]);
          fetchProfile();
        }
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'system', content: 'Failed to submit answer.' }]);
    }
    setIsLoading(false);
  };

  const handleAction = (action: string) => {
    if (action === 'Start Quiz' || action === 'Take a Quiz') {
      handleStartQuiz();
    } else {
      setQuery(action);
    }
  };

  const handleUpdatePreferences = async (style: string, pace: string) => {
    try {
      await fetch(`${API_URL}/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, learning_style: style, pace: pace }),
      });
      fetchProfile();
      setShowSettings(false);
    } catch (e) {
      console.error("Failed to update preferences:", e);
    }
  };

  const knowledgeEntries = profile?.knowledge_graph ? Object.entries(profile.knowledge_graph) : [];
  const totalMastery = knowledgeEntries.length > 0
    ? Math.round((knowledgeEntries.reduce((sum: number, [, v]: any) => sum + v, 0) / knowledgeEntries.length) * 100)
    : 0;

  return (
    <main className="container">
      <div className="layout-grid">
        {/* ─── Sidebar ─── */}
        <div className="glass-card fade-in sidebar">
          <div className="logo-section">
            <div className="logo-icon"><Zap size={20} color="white" /></div>
            <h1 className="gradient-text" style={{ fontSize: '1.4rem' }}>Aegis AI</h1>
            <button className="icon-btn" onClick={() => setShowSettings(!showSettings)} style={{ marginLeft: 'auto' }}>
              <Settings size={16} />
            </button>
          </div>

          {showSettings && (
            <div className="settings-panel fade-in">
              <h3 className="section-title">Preferences</h3>
              <div className="pref-group">
                <label>Style</label>
                <select defaultValue={profile?.learning_style || 'mixed'} id="pref-style">
                  <option value="visual">Visual</option>
                  <option value="textual">Textual</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>
              <div className="pref-group">
                <label>Pace</label>
                <select defaultValue={profile?.pace || 'medium'} id="pref-pace">
                  <option value="slow">Slow</option>
                  <option value="medium">Medium</option>
                  <option value="fast">Fast</option>
                </select>
              </div>
              <button className="btn btn-sm" onClick={() => {
                const style = (document.getElementById('pref-style') as HTMLSelectElement).value;
                const pace = (document.getElementById('pref-pace') as HTMLSelectElement).value;
                handleUpdatePreferences(style, pace);
              }}>Save</button>
            </div>
          )}

          <div className="section">
            <h3 className="section-title">Mastery Overview</h3>
            <div className="radial-graph-container">
              <RadialGraph progress={totalMastery} label="Overall" />
            </div>
          </div>

          <div className="section">
            <h3 className="section-title">Knowledge Graph</h3>
            <div className="concept-list">
              {knowledgeEntries.length > 0 ? knowledgeEntries.map(([concept, score]: any) => (
                <ConceptBar key={concept} label={concept} score={score} />
              )) : (
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Start learning to build your graph!</p>
              )}
            </div>
          </div>

          {profile?.weak_areas && profile.weak_areas.length > 0 && (
            <div className="section">
              <h3 className="section-title">Focus Areas</h3>
              <div className="weak-areas">
                {profile.weak_areas.map((area: string) => (
                  <span key={area} className="weak-tag">{area}</span>
                ))}
              </div>
            </div>
          )}

          <div className="learning-status" style={{ marginTop: 'auto' }}>
            <div className={`status-pill ${activeState}`}>
              <BrainCircuit size={14} />
              <span>{activeState.replace('_', ' ')}</span>
            </div>
            {currentTopic && <p className="current-topic">Topic: {currentTopic}</p>}
          </div>
        </div>

        {/* ─── Main Content ─── */}
        <div className="main-content">
          <div className="chat-window glass-card fade-in">
            <div className="messages-container">
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.role}`}>
                  <div className={`message-bubble ${m.type || ''}`}>
                    <p>{m.content}</p>
                    {m.suggested_actions && (
                      <div className="action-chips">
                        {m.suggested_actions.map((action, j) => (
                          <button key={j} className="chip" onClick={() => handleAction(action)}>
                            {action}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Active Quiz Question */}
              {quiz && quiz[quizIndex] && (
                <div className="message assistant">
                  <div className="message-bubble quiz-bubble">
                    <p className="quiz-question">Q{quizIndex + 1}: {quiz[quizIndex].question}</p>
                    <div className="quiz-options">
                      {quiz[quizIndex].options.map((opt, i) => (
                        <button key={i} className="quiz-option" onClick={() => handleQuizAnswer(opt)} disabled={isLoading}>
                          <span className="opt-letter">{String.fromCharCode(65 + i)}</span>
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {isLoading && (
                <div className="message assistant">
                  <div className="message-bubble loading-bubble">
                    <Loader2 size={18} className="spinner" />
                    <span>Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="input-area glass-card fade-in">
            <input
              className="input"
              placeholder="Ask anything... (e.g., Explain Neural Networks)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={isLoading}
            />
            <button className="btn" onClick={handleSend} disabled={isLoading}>
              {isLoading ? <Loader2 size={18} className="spinner" /> : <Send size={18} />}
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

/* ─── Components ─── */

function RadialGraph({ progress, label }: { progress: number; label: string }) {
  const radius = 55;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="radial-graph">
      <svg width="130" height="130" viewBox="0 0 130 130">
        <circle className="bg" cx="65" cy="65" r={radius} />
        <circle className="progress" cx="65" cy="65" r={radius}
          style={{ strokeDasharray: circumference, strokeDashoffset: offset }} />
        <text x="65" y="60" className="percent">{progress}%</text>
        <text x="65" y="80" className="label">{label}</text>
      </svg>
    </div>
  );
}

function ConceptBar({ label, score }: { label: string; score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#f43f5e';
  return (
    <div className="concept-bar">
      <div className="concept-bar-header">
        <span className="concept-bar-label">{label}</span>
        <span className="concept-bar-pct">{pct}%</span>
      </div>
      <div className="concept-bar-track">
        <div className="concept-bar-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}
