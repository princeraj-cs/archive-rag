import { useSyncExternalStore } from "react";

const STORAGE_KEY = "archive-qa-chats";
const listeners = new Set();

function createId() {
  return globalThis.crypto?.randomUUID?.() || `chat-${Date.now()}`;
}

function createEmptyChat() {
  const now = Date.now();
  return {
    id: createId(),
    title: "New conversation",
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
}

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (saved?.chats?.length) return saved;
  } catch {
    // Use a fresh local store when saved data is unavailable or malformed.
  }

  const chat = createEmptyChat();
  return { chats: [chat], activeChatId: chat.id };
}

let state = loadState();

function emit() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  listeners.forEach((listener) => listener());
}

function titleFromMessages(messages) {
  const firstQuestion = messages.find((message) => message.role === "user");
  if (!firstQuestion) return "New conversation";
  const title = firstQuestion.content.replace(/\s+/g, " ").trim();
  return title.length > 48 ? `${title.slice(0, 48)}...` : title;
}

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getSnapshot() {
  return state;
}

export function useChatStore() {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

export function createChat() {
  const chat = createEmptyChat();
  state = {
    ...state,
    chats: [chat, ...state.chats],
    activeChatId: chat.id,
  };
  emit();
}

export function selectChat(chatId) {
  if (!state.chats.some((chat) => chat.id === chatId)) return;
  state = { ...state, activeChatId: chatId };
  emit();
}

export function updateChatMessages(chatId, messages) {
  state = {
    ...state,
    chats: state.chats.map((chat) =>
      chat.id === chatId
        ? {
            ...chat,
            messages,
            title: titleFromMessages(messages),
            updatedAt: Date.now(),
          }
        : chat,
    ),
  };
  emit();
}

export function deleteChat(chatId) {
  const remaining = state.chats.filter((chat) => chat.id !== chatId);
  if (remaining.length === 0) {
    const chat = createEmptyChat();
    state = { chats: [chat], activeChatId: chat.id };
  } else {
    state = {
      chats: remaining,
      activeChatId:
        state.activeChatId === chatId ? remaining[0].id : state.activeChatId,
    };
  }
  emit();
}
