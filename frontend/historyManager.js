// historyManager.js — stores prescription & chat history in localStorage

const STORAGE_KEY = 'medez_history';
const MAX_ENTRIES = 100;

function getHistory({ type = 'all', limit = 50 } = {}) {
  const raw = localStorage.getItem(STORAGE_KEY);
  let entries = raw ? JSON.parse(raw) : [];
  if (type !== 'all') entries = entries.filter(e => e.type === type);
  return entries.slice(0, limit);
}

function _save(entries) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_ENTRIES)));
}

function addPrescriptionEntry({ medicines = [], doctorName, date, confidence, rawText, imageFileName } = {}) {
  const entries = getHistory();
  entries.unshift({
    id: Date.now(),
    type: 'prescription',
    timestamp: new Date().toISOString(),
    title: imageFileName || 'Prescription Scan',
    medicines: medicines.map(m => m.brand_name).filter(Boolean),
    doctorName: doctorName || null,
    date: date || null,
    confidence: confidence || null,
    rawText: rawText || null,
  });
  _save(entries);
}

function addSearchEntry({ query, resultCount = 0 } = {}) {
  const entries = getHistory();
  entries.unshift({
    id: Date.now(),
    type: 'search',
    timestamp: new Date().toISOString(),
    title: query,
    query,
    resultCount,
  });
  _save(entries);
}

function addChatEntry({ message, reply } = {}) {
  const entries = getHistory();
  entries.unshift({
    id: Date.now(),
    type: 'chat',
    timestamp: new Date().toISOString(),
    title: message.slice(0, 60),
    message,
    reply,
  });
  _save(entries);
}

function getStats() {
  const all = getHistory();
  return {
    total: all.length,
    prescriptions: all.filter(e => e.type === 'prescription').length,
    chats: all.filter(e => e.type === 'chat').length,
    searches: all.filter(e => e.type === 'search').length,
  };
}

function clearHistory() {
  localStorage.removeItem(STORAGE_KEY);
}