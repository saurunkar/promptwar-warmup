"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Send, Zap, ChevronRight, BrainCircuit, BookOpen, Target, Award, Loader2, Settings, BarChart3, TrendingUp, Clock, CheckCircle2, XCircle, Flame, GraduationCap } from 'lucide-react';

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

interface SessionStats {
  questionsAsked: number;
  quizzesTaken: number;
  correctAnswers: number;
  totalAnswers: number;
  topicsExplored: string[];
  sessionStart: number;
  responseTimesMs: number[];
}

export default function Home() {
  const [userId] = useState("user-001");
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "👋 Welcome to Aegis! I'm your AI learning companion powered by Google Gemini.\n\nI adapt to your pace and style. Try:\n• \"Explain Neural Networks\"\n• \"Teach me Calculus\"\n• \"What is Machine Learning?\"\n\nLet's begin your learning journey!", type: 'welcome' }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [activeState, setActiveState] = useState("idle");
  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [quiz, setQuiz] = useState<QuizQuestion[] | null>(null);
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizConcept, setQuizConcept] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [stats, setStats] = useState<SessionStats>({
    questionsAsked: 0, quizzesTaken: 0, correctAnswers: 0, totalAnswers: 0,
    topicsExplored: [], sessionStart: Date.now(), responseTimesMs: [],
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => { fetchProfile(); }, []);

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
      console.log("Profile fetch (backend starting):", e);
    }
  };

  const handleSend = async () => {
    if (!query.trim() || isLoading) return;
    const userMsg = query;
    setQuery("");
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);
    const startTime = Date.now();

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, query: userMsg }),
      });

      const elapsed = Date.now() - startTime;

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'assistant', content: data.content,
          type: data.type, suggested_actions: data.suggested_actions,
        }]);
        setActiveState(data.state || "idle");
        setCurrentTopic(data.topic);
        if (data.knowledge) {
          setProfile((prev: any) => prev ? { ...prev, knowledge_graph: data.knowledge } : prev);
        }
        // Update stats
        setStats(prev => ({
          ...prev,
          questionsAsked: prev.questionsAsked + 1,
          topicsExplored: data.topic && !prev.topicsExplored.includes(data.topic)
            ? [...prev.topicsExplored, data.topic] : prev.topicsExplored,
          responseTimesMs: [...prev.responseTimesMs, elapsed],
        }));
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
        setStats(prev => ({ ...prev, quizzesTaken: prev.quizzesTaken + 1 }));
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `📝 Quiz: "${data.concept}" • ${data.difficulty} difficulty • ${data.total_questions} questions`,
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
          user_id: userId, concept: quizConcept,
          question: q.question, user_answer: answer, correct_answer: q.correct_answer,
        }),
      });

      if (res.ok) {
        const fb = await res.json();
        const icon = fb.is_correct ? '✅' : '❌';
        setMessages(prev => [...prev,
          { role: 'user', content: answer },
          { role: 'assistant', content: `${icon} ${fb.explanation}`, type: 'feedback' },
        ]);

        setStats(prev => ({
          ...prev,
          totalAnswers: prev.totalAnswers + 1,
          correctAnswers: fb.is_correct ? prev.correctAnswers + 1 : prev.correctAnswers,
        }));

        if (fb.updated_knowledge) {
          setProfile((prev: any) => prev ? { ...prev, knowledge_graph: fb.updated_knowledge, weak_areas: fb.weak_areas } : prev);
        }

        if (quizIndex < quiz.length - 1) {
          setQuizIndex(quizIndex + 1);
        } else {
          setQuiz(null);
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: '🎉 Quiz complete! Your knowledge graph has been updated.',
            type: 'quiz_end',
            suggested_actions: ['Continue Learning', 'New Topic', 'Take Another Quiz'],
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
    if (action === 'Start Quiz' || action === 'Take a Quiz' || action === 'Take Another Quiz') {
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
    } catch (e) { console.error("Failed to update prefs:", e); }
  };

  const knowledgeEntries = profile?.knowledge_graph ? Object.entries(profile.knowledge_graph) : [];
  const totalMastery = knowledgeEntries.length > 0
    ? Math.round((knowledgeEntries.reduce((sum: number, [, v]: any) => sum + v, 0) / knowledgeEntries.length) * 100)
    : 0;
  const accuracy = stats.totalAnswers > 0 ? Math.round((stats.correctAnswers / stats.totalAnswers) * 100) : 0;
  const avgResponseTime = stats.responseTimesMs.length > 0
    ? (stats.responseTimesMs.reduce((a, b) => a + b, 0) / stats.responseTimesMs.length / 1000).toFixed(1)
    : "0.0";
  const sessionMinutes = Math.round((Date.now() - stats.sessionStart) / 60000);

  return (
    <main className="container">
      <div className="layout-grid-3col">

        {/* ═══ LEFT SIDEBAR — Knowledge ═══ */}
        <div className="glass-card fade-in sidebar">
          <div className="logo-section">
            <div className="logo-icon"><Zap size={18} color="white" /></div>
            <h1 className="gradient-text" style={{ fontSize: '1.3rem' }}>Aegis AI</h1>
            <button className="icon-btn" onClick={() => setShowSettings(!showSettings)} style={{ marginLeft: 'auto' }}>
              <Settings size={14} />
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
                const s = (document.getElementById('pref-style') as HTMLSelectElement).value;
                const p = (document.getElementById('pref-pace') as HTMLSelectElement).value;
                handleUpdatePreferences(s, p);
              }}>Save</button>
            </div>
          )}

          <div className="section">
            <h3 className="section-title">Mastery</h3>
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
                <p className="empty-text">Start learning to build your graph!</p>
              )}
            </div>
          </div>

          {profile?.weak_areas && profile.weak_areas.length > 0 && (
            <div className="section">
              <h3 className="section-title">Focus Areas</h3>
              <div className="weak-areas">
                {profile.weak_areas.map((a: string) => <span key={a} className="weak-tag">{a}</span>)}
              </div>
            </div>
          )}

          <div className="learning-status" style={{ marginTop: 'auto' }}>
            <div className={`status-pill ${activeState}`}>
              <BrainCircuit size={13} />
              <span>{activeState.replace('_', ' ')}</span>
            </div>
            {currentTopic && <p className="current-topic">📚 {currentTopic}</p>}
          </div>
        </div>

        {/* ═══ CENTER — Chat ═══ */}
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
                          <button key={j} className="chip" onClick={() => handleAction(action)}>{action}</button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {quiz && quiz[quizIndex] && (
                <div className="message assistant">
                  <div className="message-bubble quiz-bubble">
                    <p className="quiz-question">Q{quizIndex + 1}/{quiz.length}: {quiz[quizIndex].question}</p>
                    <div className="quiz-options">
                      {quiz[quizIndex].options.map((opt, i) => (
                        <button key={i} className="quiz-option" onClick={() => handleQuizAnswer(opt)} disabled={isLoading}>
                          <span className="opt-letter">{String.fromCharCode(65 + i)}</span>{opt}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {isLoading && (
                <div className="message assistant">
                  <div className="message-bubble loading-bubble">
                    <Loader2 size={16} className="spinner" /><span>Aegis is thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="input-area glass-card fade-in">
            <input className="input" placeholder="Ask me anything..." value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={isLoading} />
            <button className="btn" onClick={handleSend} disabled={isLoading}>
              {isLoading ? <Loader2 size={16} className="spinner" /> : <Send size={16} />}
              <span>Send</span>
            </button>
          </div>
        </div>

        {/* ═══ RIGHT SIDEBAR — KPIs ═══ */}
        <div className="glass-card fade-in kpi-sidebar">
          <h3 className="section-title">Learning Metrics</h3>

          <div className="kpi-grid">
            <KpiCard icon={<Target size={16} />} label="Accuracy" value={`${accuracy}%`}
              color={accuracy >= 70 ? 'var(--success)' : accuracy >= 40 ? 'var(--warning)' : 'var(--accent)'} />
            <KpiCard icon={<Flame size={16} />} label="Questions" value={`${stats.questionsAsked}`} color="var(--primary)" />
            <KpiCard icon={<GraduationCap size={16} />} label="Quizzes" value={`${stats.quizzesTaken}`} color="#8b5cf6" />
            <KpiCard icon={<Clock size={16} />} label="Avg Response" value={`${avgResponseTime}s`} color="#06b6d4" />
          </div>

          <div className="kpi-divider"></div>

          <h3 className="section-title">Session</h3>
          <div className="session-stats">
            <div className="stat-row">
              <span className="stat-label"><Clock size={12} /> Duration</span>
              <span className="stat-value">{sessionMinutes} min</span>
            </div>
            <div className="stat-row">
              <span className="stat-label"><BookOpen size={12} /> Topics</span>
              <span className="stat-value">{stats.topicsExplored.length}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label"><CheckCircle2 size={12} /> Correct</span>
              <span className="stat-value correct">{stats.correctAnswers}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label"><XCircle size={12} /> Incorrect</span>
              <span className="stat-value incorrect">{stats.totalAnswers - stats.correctAnswers}</span>
            </div>
          </div>

          <div className="kpi-divider"></div>

          <h3 className="section-title">Pace Indicator</h3>
          <PaceIndicator pace={profile?.pace || 'medium'} avgTime={parseFloat(avgResponseTime)} />

          <div className="kpi-divider"></div>

          <h3 className="section-title">Understanding</h3>
          <UnderstandingMeter mastery={totalMastery} accuracy={accuracy} questionsAsked={stats.questionsAsked} />

          {stats.topicsExplored.length > 0 && (
            <>
              <div className="kpi-divider"></div>
              <h3 className="section-title">Topics Explored</h3>
              <div className="topics-list">
                {stats.topicsExplored.map((t, i) => (
                  <span key={i} className="topic-tag">{t}</span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

/* ═══ Components ═══ */

function RadialGraph({ progress, label }: { progress: number; label: string }) {
  const r = 50, c = 2 * Math.PI * r, o = c - (progress / 100) * c;
  return (
    <div className="radial-graph">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle className="bg" cx="60" cy="60" r={r} />
        <circle className="progress" cx="60" cy="60" r={r} style={{ strokeDasharray: c, strokeDashoffset: o }} />
        <text x="60" y="55" className="percent">{progress}%</text>
        <text x="60" y="73" className="label">{label}</text>
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

function KpiCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="kpi-card">
      <div className="kpi-icon" style={{ color }}>{icon}</div>
      <div className="kpi-info">
        <span className="kpi-value" style={{ color }}>{value}</span>
        <span className="kpi-label">{label}</span>
      </div>
    </div>
  );
}

function PaceIndicator({ pace, avgTime }: { pace: string; avgTime: number }) {
  const paceMap: Record<string, { label: string; color: string; width: string }> = {
    slow: { label: 'Relaxed', color: '#06b6d4', width: '33%' },
    medium: { label: 'Balanced', color: '#f59e0b', width: '66%' },
    fast: { label: 'Intensive', color: '#f43f5e', width: '100%' },
  };
  const p = paceMap[pace] || paceMap.medium;
  return (
    <div className="pace-indicator">
      <div className="pace-header">
        <span className="pace-label">{p.label}</span>
        <TrendingUp size={14} style={{ color: p.color }} />
      </div>
      <div className="pace-track">
        <div className="pace-fill" style={{ width: p.width, backgroundColor: p.color }} />
      </div>
      <p className="pace-hint">Avg response: {avgTime}s</p>
    </div>
  );
}

function UnderstandingMeter({ mastery, accuracy, questionsAsked }: { mastery: number; accuracy: number; questionsAsked: number }) {
  const understanding = questionsAsked > 0 ? Math.round((mastery * 0.6 + accuracy * 0.4)) : 0;
  const level = understanding >= 80 ? 'Expert' : understanding >= 60 ? 'Proficient' : understanding >= 30 ? 'Learning' : 'Beginner';
  const color = understanding >= 80 ? '#10b981' : understanding >= 60 ? '#f59e0b' : understanding >= 30 ? '#6366f1' : '#64748b';
  return (
    <div className="understanding-meter">
      <div className="understanding-header">
        <span className="understanding-level" style={{ color }}>{level}</span>
        <span className="understanding-score">{understanding}%</span>
      </div>
      <div className="understanding-track">
        <div className="understanding-fill" style={{ width: `${understanding}%`, backgroundColor: color }} />
      </div>
      <div className="understanding-breakdown">
        <span>Mastery: {mastery}%</span>
        <span>Accuracy: {accuracy}%</span>
      </div>
    </div>
  );
}
