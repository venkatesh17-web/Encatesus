/**
 * Encatesus AI Chat - Modern ChatGPT-like Frontend Application
 * Pure Vanilla JavaScript (ES6+) with Tailwind CSS, Marked.js & Highlight.js
 */

(function () {
  'use strict';

  // --- Constants & Config ---
  const STORAGE_KEYS = {
    CONVERSATIONS: 'gemini_chat_conversations_v1',
    SETTINGS: 'gemini_chat_settings_v1',
    CURRENT_ID: 'gemini_chat_current_id_v1'
  };

  const DEFAULT_SETTINGS = {
    apiKey: '',
    selectedModel: 'gemini-3.5-flash-lite',
    systemPrompt: '',
    temperature: 0.7
  };

  const MODEL_NAMES = {
    'gemini-3.5-flash-lite': 'Gemini 3.5 Flash Lite',
    'gemini-flash-lite-latest': 'Gemini Flash Lite (Latest)',
    'gemini-3.8-flash': 'Gemini 3.8 Flash',
    'gemini-3.5-flash': 'Gemini 3.5 Flash'
  };

  // --- Application State ---
  const state = {
    conversations: [],
    currentConversationId: null,
    isStreaming: false,
    abortController: null,
    settings: { ...DEFAULT_SETTINGS },
    searchQuery: '',
    userScrolledUp: false,
    confirmAction: null
  };

  // --- DOM Elements Cache ---
  const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarBackdrop: document.getElementById('sidebar-backdrop'),
    sidebarToggleBtn: document.getElementById('sidebar-toggle-btn'),
    closeSidebarBtn: document.getElementById('close-sidebar-btn'),
    newChatBtn: document.getElementById('new-chat-btn'),
    quickNewChatBtn: document.getElementById('quick-new-chat-btn'),
    searchInput: document.getElementById('search-input'),
    clearSearchBtn: document.getElementById('clear-search-btn'),
    conversationsContainer: document.getElementById('conversations-container'),
    clearAllBtn: document.getElementById('clear-all-btn'),
    settingsBtn: document.getElementById('settings-btn'),
    headerSettingsBtn: document.getElementById('header-settings-btn'),
    apiStatusDot: document.getElementById('api-status-dot'),
    
    // Header
    currentChatTitle: document.getElementById('current-chat-title'),
    headerModelDropdownBtn: document.getElementById('header-model-dropdown-btn'),
    headerModelName: document.getElementById('header-model-name'),
    headerModelMenu: document.getElementById('header-model-menu'),
    modelOptions: document.querySelectorAll('.model-option'),

    // Main Chat
    chatMessagesContainer: document.getElementById('chat-messages-container'),
    welcomeState: document.getElementById('welcome-state'),
    messagesList: document.getElementById('messages-list'),
    starterCards: document.querySelectorAll('.starter-prompt-card'),

    // Input Bar
    chatForm: document.getElementById('chat-form'),
    promptInput: document.getElementById('prompt-input'),
    sendBtn: document.getElementById('send-btn'),
    sendIcon: document.getElementById('send-icon'),
    stopIcon: document.getElementById('stop-icon'),

    // Settings Modal
    settingsModal: document.getElementById('settings-modal'),
    closeSettingsModalBtn: document.getElementById('close-settings-modal-btn'),
    cancelSettingsBtn: document.getElementById('cancel-settings-btn'),
    saveSettingsBtn: document.getElementById('save-settings-btn'),
    apiKeyInput: document.getElementById('api-key-input'),
    toggleKeyVisibilityBtn: document.getElementById('toggle-key-visibility-btn'),
    defaultModelSelect: document.getElementById('default-model-select'),
    systemPromptInput: document.getElementById('system-prompt-input'),
    tempSlider: document.getElementById('temp-slider'),
    tempValue: document.getElementById('temp-value'),
    apiKeyHelpLink: document.getElementById('api-key-help-link'),

    // Confirmation Modal
    confirmModal: document.getElementById('confirm-modal'),
    confirmModalTitle: document.getElementById('confirm-modal-title'),
    confirmModalDesc: document.getElementById('confirm-modal-desc'),
    confirmCancelBtn: document.getElementById('confirm-cancel-btn'),
    confirmActionBtn: document.getElementById('confirm-action-btn'),

    // Toast
    toastContainer: document.getElementById('toast-container')
  };

  // --- Initialize Application ---
  function init() {
    loadSettings();
    loadConversations();
    configureMarked();
    setupEventListeners();
    updateUIForCurrentState();
    refreshIcons();
  }

  // --- Configure Marked.js with Highlight.js ---
  function configureMarked() {
    const renderer = new marked.Renderer();

    // Custom code block renderer with language badge and copy button
    renderer.code = function ({ text, lang }) {
      const language = (lang && hljs.getLanguage(lang)) ? lang : 'plaintext';
      let highlightedCode = '';
      try {
        if (lang && hljs.getLanguage(lang)) {
          highlightedCode = hljs.highlight(text, { language }).value;
        } else {
          highlightedCode = hljs.highlightAuto(text).value;
        }
      } catch (e) {
        highlightedCode = escapeHtml(text);
      }

      const displayLang = lang || 'code';
      const encodedCode = encodeURIComponent(text);

      return `
        <div class="code-block-wrapper my-3 rounded-xl overflow-hidden border border-dark-700 bg-dark-950">
          <div class="code-block-header flex items-center justify-between px-3.5 py-1.5 bg-dark-800 border-b border-dark-700 text-xs text-slate-400 font-mono">
            <span class="font-semibold text-slate-300 text-[11px] uppercase tracking-wider">${escapeHtml(displayLang)}</span>
            <button class="copy-code-btn flex items-center space-x-1.5 px-2 py-1 rounded hover:bg-dark-700 text-slate-400 hover:text-slate-200 transition text-[11px]" data-code="${encodedCode}">
              <i data-lucide="copy" class="w-3.5 h-3.5"></i>
              <span>Copy</span>
            </button>
          </div>
          <pre class="p-3.5 overflow-x-auto text-xs sm:text-sm leading-relaxed"><code class="hljs language-${escapeHtml(language)}">${highlightedCode}</code></pre>
        </div>
      `;
    };

    // Custom link renderer (open in new tab safely)
    renderer.link = function ({ href, title, text }) {
      const titleAttr = title ? ` title="${escapeHtml(title)}"` : '';
      return `<a href="${escapeHtml(href)}"${titleAttr} target="_blank" rel="noopener noreferrer" class="text-indigo-400 hover:text-indigo-300 underline underline-offset-2">${text}</a>`;
    };

    // Custom table renderer
    renderer.table = function ({ header, rows }) {
      return `
        <div class="overflow-x-auto my-3 rounded-lg border border-dark-700">
          <table class="min-w-full text-xs text-left text-slate-300">
            <thead class="bg-dark-800 text-slate-200 font-semibold border-b border-dark-700">
              ${header}
            </thead>
            <tbody class="divide-y divide-dark-700/60 bg-dark-850/40">
              ${rows}
            </tbody>
          </table>
        </div>
      `;
    };

    marked.setOptions({
      renderer: renderer,
      breaks: true,
      gfm: true
    });
  }

  // --- Local Storage & Settings ---
  function loadSettings() {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      if (stored) {
        state.settings = { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      }
    } catch (e) {
      console.warn('Failed to parse settings from localStorage:', e);
    }
    updateApiStatusIndicator();
    updateModelSelectorUI();
  }

  function saveSettings() {
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(state.settings));
      updateApiStatusIndicator();
      updateModelSelectorUI();
      showToast('Settings saved successfully', 'success');
    } catch (e) {
      showToast('Failed to save settings to localStorage', 'error');
    }
  }

  function updateApiStatusIndicator() {
    if (state.settings.apiKey && state.settings.apiKey.trim().length > 5) {
      elements.apiStatusDot.className = 'w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-emerald-400/20';
      elements.apiStatusDot.title = 'Custom API Key active';
    } else {
      elements.apiStatusDot.className = 'w-2 h-2 rounded-full bg-amber-400';
      elements.apiStatusDot.title = 'No custom API key set (using backend default)';
    }
  }

  function updateModelSelectorUI() {
    const currentModel = state.settings.selectedModel || 'gemini-2.5-flash';
    const displayName = MODEL_NAMES[currentModel] || currentModel;
    elements.headerModelName.textContent = displayName;

    elements.modelOptions.forEach(opt => {
      const isSelected = opt.getAttribute('data-model') === currentModel;
      const checkIcon = opt.querySelector('.check-icon');
      if (isSelected) {
        opt.classList.add('bg-dark-750', 'text-indigo-300');
        if (checkIcon) checkIcon.classList.remove('hidden');
      } else {
        opt.classList.remove('bg-dark-750', 'text-indigo-300');
        if (checkIcon) checkIcon.classList.add('hidden');
      }
    });
  }

  // --- Conversations Management ---
  function loadConversations() {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.CONVERSATIONS);
      if (stored) {
        state.conversations = JSON.parse(stored);
      }
      const lastId = localStorage.getItem(STORAGE_KEYS.CURRENT_ID);
      if (lastId && state.conversations.some(c => c.id === lastId)) {
        state.currentConversationId = lastId;
      } else if (state.conversations.length > 0) {
        state.currentConversationId = state.conversations[0].id;
      } else {
        state.currentConversationId = null;
      }
    } catch (e) {
      console.warn('Failed to load conversations:', e);
      state.conversations = [];
    }
    renderConversationsList();
    renderActiveConversation();
  }

  function saveConversations() {
    try {
      localStorage.setItem(STORAGE_KEYS.CONVERSATIONS, JSON.stringify(state.conversations));
      if (state.currentConversationId) {
        localStorage.setItem(STORAGE_KEYS.CURRENT_ID, state.currentConversationId);
      } else {
        localStorage.removeItem(STORAGE_KEYS.CURRENT_ID);
      }
    } catch (e) {
      console.error('Failed to save conversations:', e);
    }
  }

  function createNewConversation(initialUserMessage = null) {
    if (state.isStreaming) {
      abortStreaming();
    }

    const newId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
    const newConv = {
      id: newId,
      title: initialUserMessage ? generateTitleFromMessage(initialUserMessage) : 'New Conversation',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      model: state.settings.selectedModel,
      messages: []
    };

    state.conversations.unshift(newConv);
    state.currentConversationId = newId;
    saveConversations();
    renderConversationsList();
    renderActiveConversation();

    // Close mobile sidebar if open
    closeMobileSidebar();

    // Focus input
    elements.promptInput.focus();
    return newConv;
  }

  function generateTitleFromMessage(message) {
    const clean = message.trim().replace(/^[^a-zA-Z0-9]+/, '');
    if (clean.length <= 32) return clean || 'New Chat';
    return clean.slice(0, 32).trim() + '...';
  }

  function getCurrentConversation() {
    return state.conversations.find(c => c.id === state.currentConversationId);
  }

  function deleteConversation(id, event) {
    if (event) event.stopPropagation();
    openConfirmModal(
      'Delete Conversation',
      'Are you sure you want to delete this conversation? This action cannot be undone.',
      () => {
        state.conversations = state.conversations.filter(c => c.id !== id);
        if (state.currentConversationId === id) {
          state.currentConversationId = state.conversations.length > 0 ? state.conversations[0].id : null;
        }
        saveConversations();
        renderConversationsList();
        renderActiveConversation();
        showToast('Conversation deleted', 'info');
      }
    );
  }

  function renameConversation(id, currentTitle, event) {
    if (event) event.stopPropagation();
    const newTitle = prompt('Enter new conversation title:', currentTitle);
    if (newTitle && newTitle.trim() && newTitle.trim() !== currentTitle) {
      const conv = state.conversations.find(c => c.id === id);
      if (conv) {
        conv.title = newTitle.trim();
        conv.updatedAt = Date.now();
        saveConversations();
        renderConversationsList();
        if (state.currentConversationId === id) {
          elements.currentChatTitle.textContent = conv.title;
        }
        showToast('Conversation renamed', 'success');
      }
    }
  }

  function clearAllConversations() {
    if (state.conversations.length === 0) {
      showToast('No conversations to clear', 'info');
      return;
    }
    openConfirmModal(
      'Clear All Conversations',
      'Are you sure you want to delete all conversations from history? This cannot be undone.',
      () => {
        if (state.isStreaming) abortStreaming();
        state.conversations = [];
        state.currentConversationId = null;
        saveConversations();
        renderConversationsList();
        renderActiveConversation();
        showToast('All conversations cleared', 'info');
      }
    );
  }

  // --- Grouping Conversations by Date ---
  function groupConversationsByDate(convs) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterday = today - 86400000;
    const sevenDaysAgo = today - 86400000 * 7;
    const thirtyDaysAgo = today - 86400000 * 30;

    const groups = {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      Older: []
    };

    convs.forEach(c => {
      const time = c.updatedAt || c.createdAt || Date.now();
      if (time >= today) {
        groups['Today'].push(c);
      } else if (time >= yesterday) {
        groups['Yesterday'].push(c);
      } else if (time >= sevenDaysAgo) {
        groups['Previous 7 Days'].push(c);
      } else if (time >= thirtyDaysAgo) {
        groups['Previous 30 Days'].push(c);
      } else {
        groups['Older'].push(c);
      }
    });

    return groups;
  }

  // --- Render Conversation Sidebar ---
  function renderConversationsList() {
    const query = state.searchQuery.toLowerCase().trim();
    let filtered = state.conversations;

    if (query) {
      filtered = state.conversations.filter(c => {
        const titleMatch = c.title.toLowerCase().includes(query);
        const messageMatch = c.messages && c.messages.some(m => m.content.toLowerCase().includes(query));
        return titleMatch || messageMatch;
      });
    }

    elements.conversationsContainer.innerHTML = '';

    if (filtered.length === 0) {
      elements.conversationsContainer.innerHTML = `
        <div class="text-center py-8 px-4 text-xs text-slate-500">
          <i data-lucide="message-square-dashed" class="w-6 h-6 mx-auto mb-2 opacity-50"></i>
          ${query ? 'No matching conversations' : 'No conversations yet'}
        </div>
      `;
      refreshIcons();
      return;
    }

    const groups = groupConversationsByDate(filtered);

    Object.entries(groups).forEach(([groupName, items]) => {
      if (items.length === 0) return;

      const groupHeader = document.createElement('div');
      groupHeader.className = 'text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-2 pt-3 pb-1';
      groupHeader.textContent = groupName;
      elements.conversationsContainer.appendChild(groupHeader);

      const itemsList = document.createElement('div');
      itemsList.className = 'space-y-0.5';

      items.forEach(conv => {
        const isActive = conv.id === state.currentConversationId;
        const itemEl = document.createElement('div');
        itemEl.className = `conversation-item group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition select-none ${
          isActive
            ? 'bg-dark-750 text-white font-medium border border-dark-700/80 shadow-sm'
            : 'text-slate-400 hover:text-slate-200 hover:bg-dark-800/60'
        }`;

        itemEl.innerHTML = `
          <div class="flex items-center space-x-2.5 min-w-0 flex-1">
            <i data-lucide="${isActive ? 'message-square' : 'message-square'}" class="w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}"></i>
            <span class="truncate chat-title">${escapeHtml(conv.title)}</span>
          </div>
          <div class="item-actions flex items-center space-x-1 pl-2">
            <button class="rename-btn p-1 hover:text-white rounded hover:bg-dark-700/70 text-slate-400 transition" title="Rename">
              <i data-lucide="edit-3" class="w-3 h-3"></i>
            </button>
            <button class="delete-btn p-1 hover:text-red-400 rounded hover:bg-dark-700/70 text-slate-400 transition" title="Delete">
              <i data-lucide="trash" class="w-3 h-3"></i>
            </button>
          </div>
        `;

        // Switch to conversation on click
        itemEl.addEventListener('click', (e) => {
          if (e.target.closest('.rename-btn') || e.target.closest('.delete-btn')) return;
          if (state.currentConversationId !== conv.id) {
            if (state.isStreaming) abortStreaming();
            state.currentConversationId = conv.id;
            saveConversations();
            renderConversationsList();
            renderActiveConversation();
            closeMobileSidebar();
          }
        });

        // Rename listener
        const renameBtn = itemEl.querySelector('.rename-btn');
        renameBtn.addEventListener('click', (e) => renameConversation(conv.id, conv.title, e));

        // Delete listener
        const deleteBtn = itemEl.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', (e) => deleteConversation(conv.id, e));

        itemsList.appendChild(itemEl);
      });

      elements.conversationsContainer.appendChild(itemsList);
    });

    refreshIcons();
  }

  // --- Render Active Conversation in Main View ---
  function renderActiveConversation() {
    const currentConv = getCurrentConversation();

    if (!currentConv || !currentConv.messages || currentConv.messages.length === 0) {
      elements.welcomeState.classList.remove('hidden');
      elements.messagesList.classList.add('hidden');
      elements.currentChatTitle.textContent = 'New Conversation';
      elements.messagesList.innerHTML = '';
      return;
    }

    elements.welcomeState.classList.add('hidden');
    elements.messagesList.classList.remove('hidden');
    elements.currentChatTitle.textContent = currentConv.title;

    elements.messagesList.innerHTML = '';

    currentConv.messages.forEach((msg, index) => {
      const messageRow = createMessageElement(msg, index);
      elements.messagesList.appendChild(messageRow);
    });

    scrollToBottom();
    refreshIcons();
    attachCodeCopyListeners();
  }

  // --- Create DOM Element for a Single Message ---
  function createMessageElement(message, index) {
    const isUser = message.role === 'user';
    const row = document.createElement('div');
    row.className = `flex gap-3 sm:gap-4 p-4 rounded-2xl transition duration-150 ${
      isUser ? 'bg-dark-850 border border-dark-750/70 ml-auto max-w-2xl' : 'bg-dark-800/60 border border-dark-700/50 mr-auto w-full'
    }`;
    row.dataset.messageIndex = index;

    if (isUser) {
      row.innerHTML = `
        <div class="flex items-start justify-between w-full gap-3">
          <div class="text-sm text-slate-100 whitespace-pre-wrap flex-1 leading-relaxed">${escapeHtml(message.content)}</div>
          <div class="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center flex-shrink-0 text-white shadow-md shadow-indigo-600/30">
            <i data-lucide="user" class="w-4 h-4"></i>
          </div>
        </div>
      `;
    } else {
      const formattedHtml = marked.parse(message.content || '');
      const modelLabel = message.model ? MODEL_NAMES[message.model] || message.model : MODEL_NAMES[state.settings.selectedModel];

      row.innerHTML = `
        <div class="w-7 h-7 rounded-lg gemini-gradient-bg flex items-center justify-center flex-shrink-0 text-white shadow-md shadow-indigo-500/25 mt-0.5">
          <i data-lucide="sparkles" class="w-4 h-4"></i>
        </div>
        <div class="flex-1 min-w-0 space-y-2">
          <div class="flex items-center justify-between text-[11px] text-slate-400">
            <span class="font-medium text-indigo-300 flex items-center gap-1.5">
              ${modelLabel}
            </span>
            <div class="flex items-center space-x-1 message-actions">
              <button class="copy-response-btn p-1.5 hover:text-white rounded hover:bg-dark-700 text-slate-400 transition" title="Copy full response" data-content="${encodeURIComponent(message.content || '')}">
                <i data-lucide="copy" class="w-3.5 h-3.5"></i>
              </button>
            </div>
          </div>
          <div class="markdown-body message-content">
            ${formattedHtml}
          </div>
        </div>
      `;

      // Copy response button handler
      const copyBtn = row.querySelector('.copy-response-btn');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          const rawText = decodeURIComponent(copyBtn.getAttribute('data-content'));
          copyToClipboard(rawText);
          showToast('Response copied to clipboard', 'success');
        });
      }
    }

    return row;
  }

  // --- Real-time Streaming & Chat Submission ---
  async function handleFormSubmit(e) {
    if (e) e.preventDefault();
    if (state.isStreaming) return;

    const userText = elements.promptInput.value.trim();
    if (!userText) return;

    // Reset textarea height and clear input
    elements.promptInput.value = '';
    adjustTextareaHeight();

    // Ensure we have an active conversation
    let conv = getCurrentConversation();
    if (!conv) {
      conv = createNewConversation(userText);
    } else if (conv.messages.length === 0) {
      conv.title = generateTitleFromMessage(userText);
      elements.currentChatTitle.textContent = conv.title;
    }

    // Append user message
    const userMessage = {
      role: 'user',
      content: userText,
      timestamp: Date.now()
    };
    conv.messages.push(userMessage);
    conv.updatedAt = Date.now();
    saveConversations();
    renderConversationsList();

    // Hide welcome state and append user bubble
    elements.welcomeState.classList.add('hidden');
    elements.messagesList.classList.remove('hidden');
    
    const userRow = createMessageElement(userMessage, conv.messages.length - 1);
    elements.messagesList.appendChild(userRow);

    // Create placeholder assistant message row with streaming cursor
    const assistantIndex = conv.messages.length;
    const assistantMessage = {
      role: 'assistant',
      content: '',
      model: state.settings.selectedModel,
      timestamp: Date.now()
    };
    conv.messages.push(assistantMessage);

    const assistantRow = document.createElement('div');
    assistantRow.className = 'flex gap-3 sm:gap-4 p-4 rounded-2xl bg-dark-800/60 border border-dark-700/50 mr-auto w-full';
    assistantRow.dataset.messageIndex = assistantIndex;
    assistantRow.innerHTML = `
      <div class="w-7 h-7 rounded-lg gemini-gradient-bg flex items-center justify-center flex-shrink-0 text-white shadow-md shadow-indigo-500/25 mt-0.5">
        <i data-lucide="sparkles" class="w-4 h-4"></i>
      </div>
      <div class="flex-1 min-w-0 space-y-2">
        <div class="flex items-center justify-between text-[11px] text-slate-400">
          <span class="font-medium text-indigo-300 flex items-center gap-1.5">
            ${MODEL_NAMES[state.settings.selectedModel] || state.settings.selectedModel}
          </span>
          <div class="flex items-center space-x-1">
            <span class="text-[10px] text-indigo-400 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>
              Generating...
            </span>
          </div>
        </div>
        <div class="markdown-body message-content streaming-cursor">
          <div class="flex items-center space-x-1 py-1 text-slate-400 text-xs">
            <span class="w-2 h-2 rounded-full bg-indigo-400 dot-1"></span>
            <span class="w-2 h-2 rounded-full bg-indigo-400 dot-2"></span>
            <span class="w-2 h-2 rounded-full bg-indigo-400 dot-3"></span>
          </div>
        </div>
      </div>
    `;

    elements.messagesList.appendChild(assistantRow);
    refreshIcons();
    scrollToBottom(true);

    // Set streaming UI state
    setStreamingState(true);

    const contentDiv = assistantRow.querySelector('.message-content');
    let fullResponseText = '';

    try {
      state.abortController = new AbortController();

      // Build payload
      const payload = {
        conversationId: conv.id,
        message: userText,
        model: state.settings.selectedModel,
        apiKey: state.settings.apiKey || undefined,
        systemPrompt: state.settings.systemPrompt || undefined,
        temperature: parseFloat(state.settings.temperature) || 0.7,
        messages: conv.messages.slice(0, -1) // Send context without empty placeholder
      };

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream, application/json, text/plain'
        },
        body: JSON.stringify(payload),
        signal: state.abortController.signal
      });

      if (!response.ok) {
        let errMessage = `Error ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData.detail || errData.error || errData.message) {
            errMessage = errData.detail || errData.error || errData.message;
          }
        } catch (_) {}
        throw new Error(errMessage);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Check for SSE format lines
        if (buffer.includes('\n')) {
          const lines = buffer.split('\n');
          buffer = lines.pop(); // Keep incomplete tail

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith(':')) continue;

            if (trimmed.startsWith('data:')) {
              const dataContent = trimmed.slice(5).trim();
              if (dataContent === '[DONE]') {
                break;
              }
              try {
                const parsed = JSON.parse(dataContent);
                const textChunk = parsed.chunk || parsed.text || parsed.content || parsed.delta || '';
                if (textChunk) {
                  fullResponseText += textChunk;
                  updateStreamingContent(contentDiv, fullResponseText);
                }
              } catch (_) {
                // If not JSON, treat raw payload as string chunk
                if (dataContent) {
                  fullResponseText += dataContent;
                  updateStreamingContent(contentDiv, fullResponseText);
                }
              }
            } else {
              // Direct stream chunk without data prefix
              fullResponseText += trimmed;
              updateStreamingContent(contentDiv, fullResponseText);
            }
          }
        } else if (buffer.length > 50) {
          // Plain text streaming fallback without newlines
          fullResponseText += buffer;
          buffer = '';
          updateStreamingContent(contentDiv, fullResponseText);
        }
      }

      // Flush remainder
      if (buffer.trim()) {
        const trimmed = buffer.trim();
        if (trimmed.startsWith('data:')) {
          const dataContent = trimmed.slice(5).trim();
          if (dataContent !== '[DONE]') {
            try {
              const parsed = JSON.parse(dataContent);
              fullResponseText += parsed.chunk || parsed.text || parsed.content || parsed.delta || '';
            } catch (_) {
              fullResponseText += dataContent;
            }
          }
        } else {
          fullResponseText += trimmed;
        }
      }

    } catch (err) {
      if (err.name === 'AbortError') {
        fullResponseText += '\n\n*(Generation stopped by user)*';
      } else {
        console.error('Chat stream error:', err);
        showToast(err.message || 'Error generating response', 'error');
        fullResponseText = `⚠️ **Error:** ${err.message || 'Unable to connect to the Gemini API backend. Please check your backend server status or verify your API key in Settings.'}`;
      }
    } finally {
      // Finalize assistant message
      setStreamingState(false);
      state.abortController = null;

      // Clean up cursor and render final markdown
      contentDiv.classList.remove('streaming-cursor');
      contentDiv.innerHTML = marked.parse(fullResponseText || 'No response received.');
      
      // Update data model
      assistantMessage.content = fullResponseText;
      conv.updatedAt = Date.now();
      saveConversations();

      // Replace header status with copy button
      const actionsContainer = assistantRow.querySelector('.message-actions') || assistantRow.querySelector('.space-y-2 > div:first-child');
      if (actionsContainer) {
        actionsContainer.innerHTML = `
          <span class="font-medium text-indigo-300 flex items-center gap-1.5">
            ${MODEL_NAMES[state.settings.selectedModel] || state.settings.selectedModel}
          </span>
          <div class="flex items-center space-x-1">
            <button class="copy-response-btn p-1.5 hover:text-white rounded hover:bg-dark-700 text-slate-400 transition" title="Copy full response" data-content="${encodeURIComponent(fullResponseText)}">
              <i data-lucide="copy" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        `;
        const copyBtn = actionsContainer.querySelector('.copy-response-btn');
        if (copyBtn) {
          copyBtn.addEventListener('click', () => {
            copyToClipboard(fullResponseText);
            showToast('Response copied to clipboard', 'success');
          });
        }
      }

      refreshIcons();
      attachCodeCopyListeners();
      scrollToBottom();
    }
  }

  function updateStreamingContent(element, markdownText) {
    if (!element) return;
    element.innerHTML = marked.parse(markdownText);
    attachCodeCopyListeners();
    if (!state.userScrolledUp) {
      scrollToBottom();
    }
  }

  function setStreamingState(isStreaming) {
    state.isStreaming = isStreaming;
    if (isStreaming) {
      elements.sendIcon.classList.add('hidden');
      elements.stopIcon.classList.remove('hidden');
      elements.sendBtn.classList.remove('bg-indigo-600', 'hover:bg-indigo-500');
      elements.sendBtn.classList.add('bg-red-600', 'hover:bg-red-500');
      elements.sendBtn.title = 'Stop generating (Escape)';
      elements.sendBtn.disabled = false;
    } else {
      elements.sendIcon.classList.remove('hidden');
      elements.stopIcon.classList.add('hidden');
      elements.sendBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-500');
      elements.sendBtn.classList.remove('bg-red-600', 'hover:bg-red-500');
      elements.sendBtn.title = 'Send message (Enter)';
    }
  }

  function abortStreaming() {
    if (state.abortController) {
      state.abortController.abort();
    }
  }

  // --- Auto-Scrolling Helpers ---
  function scrollToBottom(force = false) {
    if (!elements.chatMessagesContainer) return;
    if (force || !state.userScrolledUp) {
      elements.chatMessagesContainer.scrollTop = elements.chatMessagesContainer.scrollHeight;
    }
  }

  function handleContainerScroll() {
    const el = elements.chatMessagesContainer;
    const threshold = 60;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    state.userScrolledUp = !atBottom;
  }

  // --- Textarea Dynamic Auto-Height ---
  function adjustTextareaHeight() {
    const input = elements.promptInput;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 200) + 'px';
  }

  // --- Copy to Clipboard & Code Block Listeners ---
  function attachCodeCopyListeners() {
    document.querySelectorAll('.copy-code-btn').forEach(btn => {
      // Prevent attaching multiple times
      if (btn.dataset.listenerAttached) return;
      btn.dataset.listenerAttached = 'true';

      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const encoded = btn.getAttribute('data-code');
        const codeText = decodeURIComponent(encoded || '');

        await copyToClipboard(codeText);

        const span = btn.querySelector('span');
        const icon = btn.querySelector('i');
        const originalText = span ? span.textContent : 'Copy';

        if (span) span.textContent = 'Copied!';
        btn.classList.add('text-emerald-400', 'copied');

        showToast('Code copied to clipboard', 'info');

        setTimeout(() => {
          if (span) span.textContent = originalText;
          btn.classList.remove('text-emerald-400', 'copied');
        }, 2000);
      });
    });
  }

  async function copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-999999px';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand('copy');
        textarea.remove();
      }
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  }

  // --- Toast Notifications ---
  function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconName = 'info';
    if (type === 'success') iconName = 'check-circle-2';
    if (type === 'error') iconName = 'alert-circle';

    toast.innerHTML = `
      <i data-lucide="${iconName}" class="w-4 h-4 flex-shrink-0 ${type === 'success' ? 'text-emerald-400' : type === 'error' ? 'text-red-400' : 'text-indigo-400'}"></i>
      <span class="flex-1">${escapeHtml(message)}</span>
    `;

    elements.toastContainer.appendChild(toast);
    refreshIcons();

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.2s ease-out';
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }

  // --- Modal Management ---
  function openSettingsModal() {
    elements.apiKeyInput.value = state.settings.apiKey || '';
    elements.defaultModelSelect.value = state.settings.selectedModel || 'gemini-2.5-flash';
    elements.systemPromptInput.value = state.settings.systemPrompt || '';
    elements.tempSlider.value = state.settings.temperature || 0.7;
    elements.tempValue.textContent = state.settings.temperature || 0.7;

    elements.settingsModal.classList.add('active');
  }

  function closeSettingsModal() {
    elements.settingsModal.classList.remove('active');
  }

  function openConfirmModal(title, description, onConfirm) {
    elements.confirmModalTitle.textContent = title;
    elements.confirmModalDesc.textContent = description;
    state.confirmAction = onConfirm;
    elements.confirmModal.classList.add('active');
  }

  function closeConfirmModal() {
    elements.confirmModal.classList.remove('active');
    state.confirmAction = null;
  }

  // --- Mobile Sidebar Controls ---
  function toggleMobileSidebar() {
    const isOpen = elements.sidebar.classList.contains('translate-x-0');
    if (isOpen) {
      closeMobileSidebar();
    } else {
      openMobileSidebar();
    }
  }

  function openMobileSidebar() {
    elements.sidebar.classList.remove('-translate-x-full');
    elements.sidebar.classList.add('translate-x-0');
    elements.sidebarBackdrop.classList.add('active');
  }

  function closeMobileSidebar() {
    elements.sidebar.classList.add('-translate-x-full');
    elements.sidebar.classList.remove('translate-x-0');
    elements.sidebarBackdrop.classList.remove('active');
  }

  // --- Helper Utilities ---
  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function refreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  // --- Event Listeners Setup ---
  function setupEventListeners() {
    // Form submission & Send / Stop Button
    elements.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      if (state.isStreaming) {
        abortStreaming();
      } else {
        handleFormSubmit();
      }
    });

    // Textarea input handling (Auto-resize & Enter to send)
    elements.promptInput.addEventListener('input', adjustTextareaHeight);
    elements.promptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (state.isStreaming) {
          abortStreaming();
        } else {
          handleFormSubmit();
        }
      }
    });

    // New Chat buttons
    elements.newChatBtn.addEventListener('click', () => createNewConversation());
    elements.quickNewChatBtn.addEventListener('click', () => createNewConversation());

    // Starter Prompt Cards
    elements.starterCards.forEach(card => {
      card.addEventListener('click', () => {
        const promptText = card.getAttribute('data-prompt');
        if (promptText) {
          elements.promptInput.value = promptText;
          handleFormSubmit();
        }
      });
    });

    // Sidebar Search
    elements.searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value;
      if (state.searchQuery) {
        elements.clearSearchBtn.classList.remove('hidden');
      } else {
        elements.clearSearchBtn.classList.add('hidden');
      }
      renderConversationsList();
    });

    elements.clearSearchBtn.addEventListener('click', () => {
      elements.searchInput.value = '';
      state.searchQuery = '';
      elements.clearSearchBtn.classList.add('hidden');
      renderConversationsList();
      elements.searchInput.focus();
    });

    // Clear All Conversations
    elements.clearAllBtn.addEventListener('click', clearAllConversations);

    // Sidebar Mobile Toggle
    elements.sidebarToggleBtn.addEventListener('click', toggleMobileSidebar);
    elements.closeSidebarBtn.addEventListener('click', closeMobileSidebar);
    elements.sidebarBackdrop.addEventListener('click', closeMobileSidebar);

    // Header Model Dropdown
    elements.headerModelDropdownBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      elements.headerModelMenu.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
      if (!elements.headerModelMenu.contains(e.target) && !elements.headerModelDropdownBtn.contains(e.target)) {
        elements.headerModelMenu.classList.add('hidden');
      }
    });

    elements.modelOptions.forEach(opt => {
      opt.addEventListener('click', () => {
        const model = opt.getAttribute('data-model');
        if (model) {
          state.settings.selectedModel = model;
          saveSettings();
          elements.headerModelMenu.classList.add('hidden');
        }
      });
    });

    // Settings Modal
    elements.settingsBtn.addEventListener('click', openSettingsModal);
    elements.headerSettingsBtn.addEventListener('click', openSettingsModal);
    elements.closeSettingsModalBtn.addEventListener('click', closeSettingsModal);
    elements.cancelSettingsBtn.addEventListener('click', closeSettingsModal);

    elements.apiKeyHelpLink.addEventListener('click', () => {
      window.open('https://aistudio.google.com/app/apikey', '_blank');
    });

    elements.toggleKeyVisibilityBtn.addEventListener('click', () => {
      const isPassword = elements.apiKeyInput.type === 'password';
      elements.apiKeyInput.type = isPassword ? 'text' : 'password';
      const icon = elements.toggleKeyVisibilityBtn.querySelector('i');
      if (icon) {
        icon.setAttribute('data-lucide', isPassword ? 'eye-off' : 'eye');
        refreshIcons();
      }
    });

    elements.tempSlider.addEventListener('input', (e) => {
      elements.tempValue.textContent = e.target.value;
    });

    elements.saveSettingsBtn.addEventListener('click', () => {
      state.settings.apiKey = elements.apiKeyInput.value.trim();
      state.settings.selectedModel = elements.defaultModelSelect.value;
      state.settings.systemPrompt = elements.systemPromptInput.value.trim();
      state.settings.temperature = parseFloat(elements.tempSlider.value) || 0.7;
      saveSettings();
      closeSettingsModal();
    });

    // Confirmation Modal
    elements.confirmCancelBtn.addEventListener('click', closeConfirmModal);
    elements.confirmActionBtn.addEventListener('click', () => {
      if (typeof state.confirmAction === 'function') {
        state.confirmAction();
      }
      closeConfirmModal();
    });

    // Chat Container Scroll Detection
    elements.chatMessagesContainer.addEventListener('scroll', handleContainerScroll);

    // Global Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      // Ctrl+N for new chat
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        createNewConversation();
      }
      // Ctrl+K for search
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        elements.searchInput.focus();
      }
      // Escape closes modals or stops streaming
      if (e.key === 'Escape') {
        if (elements.settingsModal.classList.contains('active')) {
          closeSettingsModal();
        } else if (elements.confirmModal.classList.contains('active')) {
          closeConfirmModal();
        } else if (state.isStreaming) {
          abortStreaming();
        }
      }
    });
  }

  function updateUIForCurrentState() {
    updateApiStatusIndicator();
    updateModelSelectorUI();
  }

  // Run on DOM Ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
