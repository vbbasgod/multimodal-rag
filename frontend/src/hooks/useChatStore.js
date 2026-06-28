import { useState, useCallback, useRef } from "react";

// Simple in-memory store (swap for Zustand/Redux in prod)
let globalState = {
  conversations: [],
  activeId: null,
  messages: {}, // { conversationId: Message[] }
};
const listeners = new Set();

function setState(updater) {
  globalState = typeof updater === "function" ? updater(globalState) : { ...globalState, ...updater };
  listeners.forEach((fn) => fn(globalState));
}

function genId() {
  return Math.random().toString(36).slice(2, 10);
}

export function useChatStore() {
  const [, forceUpdate] = useState(0);

  // Subscribe to global state changes
  const listenerRef = useRef(null);
  if (!listenerRef.current) {
    listenerRef.current = () => forceUpdate((n) => n + 1);
    listeners.add(listenerRef.current);
  }

  // Cleanup
  const cleanupRef = useRef(false);
  if (!cleanupRef.current) {
    cleanupRef.current = true;
    // In a real app, useEffect would handle cleanup
  }

  const createConversation = useCallback(() => {
    const id = genId();
    setState((s) => ({
      ...s,
      conversations: [{ id, title: "New conversation", createdAt: new Date().toISOString() }, ...s.conversations],
      activeId: id,
      messages: { ...s.messages, [id]: [] },
    }));
    return id;
  }, []);

  const setActiveId = useCallback((id) => {
    setState((s) => ({ ...s, activeId: id }));
  }, []);

  const getMessages = useCallback((conversationId) => {
    return globalState.messages[conversationId] || [];
  }, []);

  const addMessage = useCallback((conversationId, message) => {
    setState((s) => {
      const existing = s.messages[conversationId] || [];
      const updated = [...existing, message];

      // Update conversation title from first user message
      const convs = s.conversations.map((c) => {
        if (c.id === conversationId && c.title === "New conversation" && message.role === "user") {
          return { ...c, title: message.content.slice(0, 40) + (message.content.length > 40 ? "…" : "") };
        }
        return c;
      });

      return {
        ...s,
        messages: { ...s.messages, [conversationId]: updated },
        conversations: convs,
      };
    });
  }, []);

  const updateMessage = useCallback((conversationId, messageId, updates) => {
    setState((s) => {
      const messages = (s.messages[conversationId] || []).map((m) =>
        m.id === messageId ? { ...m, ...updates } : m
      );
      return { ...s, messages: { ...s.messages, [conversationId]: messages } };
    });
  }, []);

  // Auto-create first conversation
  if (globalState.conversations.length === 0 && globalState.activeId === null) {
    const id = genId();
    globalState = {
      conversations: [{ id, title: "New conversation", createdAt: new Date().toISOString() }],
      activeId: id,
      messages: { [id]: [] },
    };
  }

  return {
    conversations: globalState.conversations,
    activeId: globalState.activeId,
    createConversation,
    setActiveId,
    getMessages,
    addMessage,
    updateMessage,
  };
}
