import {
  BookOpen,
  Check,
  CloudUpload,
  FileText,
  FileUp,
  MessageCircle,
  MessageSquarePlus,
  Trash2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { deleteSource, getSources, uploadDoc } from "./api/client";
import ChatWindow from "./components/ChatWindow";
import {
  createChat,
  deleteChat,
  selectChat,
  updateChatMessages,
  useChatStore,
} from "./store/chatStore";
import "./styles.css";

export default function App() {
  const { chats, activeChatId } = useChatStore();
  const fileInput = useRef(null);
  const [status, setStatus] = useState("Ready for documents");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [failedFile, setFailedFile] = useState(null);
  const [sources, setSources] = useState([]);
  const [selectedSourceIds, setSelectedSourceIds] = useState([]);
  const activeChat = chats.find((chat) => chat.id === activeChatId) || chats[0];

  useEffect(() => {
    getSources()
      .then(({ sources: loadedSources }) => {
        setSources(loadedSources);
        setSelectedSourceIds(loadedSources.map((source) => source.id));
        if (loadedSources.length)
          setStatus(`${loadedSources.length} document(s) indexed`);
      })
      .catch(() => {
        // An empty index is a normal first-run state.
      });
  }, []);

  async function handleFile(file) {
    if (!file) return;
    setUploading(true);
    setFailedFile(null);
    setUploadProgress(0);
    setStatus(`Indexing ${file.name}...`);
    try {
      const result = await uploadDoc(file, setUploadProgress);
      setSources((current) => [...current, result]);
      setSelectedSourceIds((current) => [...current, result.id]);
      setStatus(`${file.name} is indexed`);
    } catch (error) {
      setFailedFile(file);
      setStatus(error.message);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function handleDeleteDocument(documentId) {
    try {
      await deleteSource(documentId);
      setSources((current) =>
        current.filter((source) => source.id !== documentId),
      );
      setSelectedSourceIds((current) =>
        current.filter((id) => id !== documentId),
      );
      setStatus("Document removed");
    } catch (error) {
      setStatus(error.message);
    }
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragActive(false);
    handleFile(event.dataTransfer.files?.[0]);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/">
          <BookOpen size={19} /> ARCHIVE / Q&A
        </a>
        <div className="connection">
          <span className="status-dot" /> LOCAL WORKSPACE
        </div>
      </header>
      <div className="layout">
        <aside className="sidebar">
          <div className="eyebrow">Notebook desk</div>
          <h1>Answers with a paper trail.</h1>
          <p className="intro">
            A quiet interface for asking questions of the documents that matter.
          </p>
          {sources.length ? (
            <div className="document-actions">
              <button
                className="add-document-row"
                onClick={() => fileInput.current?.click()}
                disabled={uploading}
              >
                <FileUp size={15} />
                <span>
                  {uploading
                    ? `Indexing ${uploadProgress}%`
                    : "Replace document"}
                </span>
              </button>
              {failedFile && (
                <button
                  className="retry-button"
                  onClick={() => handleFile(failedFile)}
                >
                  Retry upload
                </button>
              )}
            </div>
          ) : (
            <div
              className={`upload-box ${dragActive ? "is-dragging" : ""}`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
            >
              <div className="upload-icon">
                <CloudUpload size={21} />
              </div>
              <div>
                <strong>Bring in a document</strong>
                <span>PDF or TXT, one at a time</span>
              </div>
              <button
                className="upload-button"
                onClick={() => fileInput.current?.click()}
                disabled={uploading}
              >
                <FileUp size={16} />{" "}
                {uploading ? `${uploadProgress}%` : "Upload"}
              </button>
              {uploading && (
                <div className="upload-progress">
                  <span style={{ width: `${uploadProgress}%` }} />
                </div>
              )}
              {failedFile && (
                <button
                  className="retry-button"
                  onClick={() => handleFile(failedFile)}
                >
                  Retry upload
                </button>
              )}
            </div>
          )}
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.txt"
            onChange={(event) => handleFile(event.target.files?.[0])}
            hidden
          />
          <div className="status-line">
            {status.includes("indexed") ? (
              <Check size={15} />
            ) : (
              <span className="status-ring" />
            )}
            <span>{status}</span>
          </div>
          {sources.map((source) => (
            <div className="document-card" key={source.id}>
              <input
                type="checkbox"
                checked={selectedSourceIds.includes(source.id)}
                onChange={() =>
                  setSelectedSourceIds((current) =>
                    current.includes(source.id)
                      ? current.filter((id) => id !== source.id)
                      : [...current, source.id],
                  )
                }
                aria-label={`Include ${source.filename}`}
              />
              <FileText size={16} />
              <div>
                <strong>{source.filename}</strong>
                <span>
                  {source.page_count} page{source.page_count === 1 ? "" : "s"}
                </span>
              </div>
              <button
                onClick={() => handleDeleteDocument(source.id)}
                title="Remove document"
                aria-label={`Remove ${source.filename}`}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          <div className="chat-history">
            <div className="history-heading">
              <span>Previous chats</span>
              <button
                className="new-chat-button"
                onClick={createChat}
                title="New chat"
                aria-label="New chat"
              >
                <MessageSquarePlus size={16} />
              </button>
            </div>
            <div className="chat-list">
              {chats.map((chat) => (
                <div
                  className={`chat-list-item ${chat.id === activeChatId ? "is-active" : ""}`}
                  key={chat.id}
                  onClick={() => selectChat(chat.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ")
                      selectChat(chat.id);
                  }}
                >
                  <MessageCircle size={14} />
                  <span>{chat.title}</span>
                  <button
                    className="delete-chat-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      deleteChat(chat.id);
                    }}
                    title="Delete chat"
                    aria-label={`Delete ${chat.title}`}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="sidebar-note">
            Answers are constrained to retrieved document context. Sources stay
            attached so you can verify the trail.
          </div>
        </aside>
        <ChatWindow
          key={activeChat.id}
          chat={activeChat}
          onMessagesChange={(messages) =>
            updateChatMessages(activeChat.id, messages)
          }
          enabledDocumentIds={selectedSourceIds}
        />
      </div>
    </main>
  );
}
