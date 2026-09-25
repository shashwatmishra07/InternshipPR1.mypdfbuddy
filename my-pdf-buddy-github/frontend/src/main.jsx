import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertCircle, ArrowUp, Bot, Check, FileText, Loader2, MessageCircle, Paperclip,
  Plus, Sparkles, Trash2, UploadCloud, User, X
} from "lucide-react";
import "./styles.css";

const API = "http://127.0.0.1:8000";
const starters = ["Give me a quick summary", "What are the key takeaways?", "Find the most important dates"];

function formatBytes(bytes) {
  if (!bytes) return "0 KB";
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [chatting, setChatting] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [notice, setNotice] = useState(null);
  const [erasing, setErasing] = useState(false);
  const inputRef = useRef(null);

  const loadDocuments = useCallback(async () => {
    try {
      const response = await fetch(`${API}/api/documents`);
      if (!response.ok) return;
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch { /* API may not be running yet; the upload action explains this clearly. */ }
  }, []);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(null), 6500);
    return () => clearTimeout(timer);
  }, [notice]);

  const chooseFile = (file) => {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setNotice({ type: "error", text: "Please choose a PDF file." }); return;
    }
    setSelectedFile(file);
  };

  const upload = async () => {
    if (!selectedFile || uploading) return;
    setUploading(true); setNotice(null);
    const form = new FormData();
    form.append("file", selectedFile);
    try {
      const response = await fetch(`${API}/api/documents`, { method: "POST", body: form });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Could not upload this PDF.");
      setDocuments((current) => [{ filename: data.filename, chunks: data.chunks }, ...current.filter((d) => d.filename !== data.filename)]);
      setSelectedFile(null);
      setNotice({ type: "success", text: data.message || "Your PDF is ready to chat with." });
    } catch (error) {
      setNotice({ type: "error", text: error.message.includes("fetch") ? "Could not connect to the API. Start uvicorn on port 8000 and try again." : error.message });
    } finally { setUploading(false); }
  };

  const sendMessage = async (text = question) => {
    const value = text.trim();
    if (!value || chatting) return;
    setQuestion(""); setMessages((current) => [...current, { role: "user", text: value }]);
    setChatting(true); setNotice(null);
    try {
      const response = await fetch(`${API}/api/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: value, top_k: 5 })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "The assistant could not answer.");
      setMessages((current) => [...current, { role: "assistant", text: data.answer || "I couldn't find an answer.", sources: data.sources || [] }]);
    } catch (error) {
      setNotice({ type: "error", text: error.message.includes("fetch") ? "Could not connect to the API. Make sure the backend is running." : error.message });
    } finally { setChatting(false); }
  };

  const eraseAllData = async () => {
    if (erasing || !window.confirm("Erase all uploaded PDFs and chat history? This cannot be undone.")) return;
    setErasing(true);
    setNotice(null);
    try {
      const response = await fetch(`${API}/api/documents`, { method: "DELETE" });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Could not erase the uploaded data.");
      setDocuments([]);
      setMessages([]);
      setSelectedFile(null);
      setNotice({ type: "success", text: data.message || "All uploaded data has been erased." });
    } catch (error) {
      setNotice({ type: "error", text: error.message.includes("fetch") ? "Could not connect to the API." : error.message });
    } finally {
      setErasing(false);
    }
  };

  const onDrop = (event) => {
    event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]);
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark"><FileText size={20} strokeWidth={2.6} /></div><span>My PDF <b>Buddy</b></span></div>
        <div className="topbar-right"><span className="status-dot" /> <span>Local workspace</span></div>
      </header>
      <main className="layout">
        <aside className="sidebar">
          <div className="sidebar-heading"><div><span className="eyebrow">WORKSPACE</span><h2>Documents <span>{documents.length}</span></h2></div><button className="icon-btn" onClick={() => inputRef.current?.click()} aria-label="Add document"><Plus size={19} /></button></div>
          <div className={`dropzone ${dragging ? "is-dragging" : ""}`} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop} onClick={() => inputRef.current?.click()}>
            <input ref={inputRef} type="file" accept="application/pdf,.pdf" hidden onChange={(e) => chooseFile(e.target.files?.[0])} />
            <div className="upload-icon"><UploadCloud size={22} /></div>
            <strong>Drop a PDF here</strong><span>or <u>browse files</u></span><small>PDF only · up to 50 MB</small>
          </div>
          {selectedFile && <div className="file-preview"><div className="pdf-icon"><FileText size={16} /></div><div className="file-info"><b>{selectedFile.name}</b><span>{formatBytes(selectedFile.size)} · Ready to upload</span></div><button onClick={() => setSelectedFile(null)} aria-label="Remove file"><X size={15} /></button><button className="upload-button" onClick={upload} disabled={uploading}>{uploading ? <Loader2 className="spin" size={15} /> : <UploadCloud size={15} />}{uploading ? "Uploading" : "Upload"}</button></div>}
          <div className="doc-list">{documents.length ? documents.map((doc, index) => <div className="doc-item" key={`${doc.filename}-${index}`}><div className="doc-icon"><FileText size={16} /></div><div><b title={doc.filename}>{doc.filename}</b><span>{doc.chunks ? `${doc.chunks} chunks` : "Indexed document"}</span></div><Check className="doc-check" size={15} /></div>) : <div className="empty-docs"><FileText size={19} /><span>Your uploaded PDFs<br />will appear here.</span></div>}</div>
          <div className="sidebar-actions">
            <button className="erase-button" onClick={eraseAllData} disabled={erasing}>
              <Trash2 size={15} /> {erasing ? "Erasing..." : "Erase all data"}
            </button>
            <div className="sidebar-tip"><Sparkles size={16} /><span><b>Tip</b><br />Ask specific questions for more accurate answers.</span></div>
          </div>
        </aside>
        <section className="chat-panel">
          <div className="chat-header"><div><span className="eyebrow">YOUR AI READING COMPANION</span><h1>Ask anything about your PDFs</h1><p>Upload a document, then start a conversation with your personal research assistant.</p></div></div>
          <div className="conversation">
            {messages.length === 0 && <div className="welcome"><div className="welcome-orb"><Bot size={29} /></div><h2>What would you like to explore?</h2><p>I’ll read your documents and give you clear, cited answers. Try one of these to get started.</p><div className="starter-grid">{starters.map((starter) => <button key={starter} onClick={() => sendMessage(starter)}><MessageCircle size={16} />{starter}<ArrowUp size={14} /></button>)}</div></div>}
            {messages.map((message, index) => <div className={`message-row ${message.role}`} key={`${message.role}-${index}`}><div className="message-avatar">{message.role === "assistant" ? <Bot size={16} /> : <User size={16} />}</div><div className="message-content"><span className="message-author">{message.role === "assistant" ? "PDF Buddy" : "You"}</span><div className="bubble">{message.text}</div>{message.sources?.length > 0 && <div className="sources"><span className="source-label">SOURCES</span>{message.sources.map((source, sourceIndex) => <span className="source-chip" key={`${source.source}-${sourceIndex}`}><FileText size={12} />{source.source}{source.page ? ` · p. ${source.page}` : ""}</span>)}</div>}</div></div>)}
            {chatting && <div className="message-row assistant"><div className="message-avatar"><Bot size={16} /></div><div className="message-content"><span className="message-author">PDF Buddy</span><div className="bubble typing"><i /><i /><i /></div></div></div>}
          </div>
          <div className="composer-wrap"><div className="composer"><button className="attach-btn" onClick={() => inputRef.current?.click()} aria-label="Attach PDF"><Paperclip size={19} /></button><input value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendMessage()} placeholder={documents.length ? "Ask a question about your documents..." : "Upload a PDF to start asking questions..."} /><button className="send-btn" onClick={() => sendMessage()} disabled={!question.trim() || chatting} aria-label="Send message"><ArrowUp size={19} /></button></div><span className="composer-hint">Answers are generated from your indexed documents <span>·</span> <b>Enter</b> to send</span></div>
        </section>
      </main>
      {notice && <div className={`notice ${notice.type}`}><div>{notice.type === "success" ? <Check size={17} /> : <AlertCircle size={17} />}</div><span>{notice.text}</span><button onClick={() => setNotice(null)}><X size={15} /></button></div>}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
