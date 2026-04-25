%%javascript
import {
  addPrescriptionEntry,
  addSearchEntry,
  addPageViewEntry,
} from './historyManager';


// --- 1. After OCR / prescription scan ---------------------------
//
//  Find the function in your code that handles image upload and
//  calls your OCR service. Add the marked lines after the API call.

async function handlePrescriptionUpload(imageFile) {

  // YOUR EXISTING CODE — calling your OCR/ML backend
  const result = await yourOcrService.analyze(imageFile);

  // ✅ ADD THIS — saves the result to history automatically
  addPrescriptionEntry({
    imageFileName: imageFile.name,
    // imageDataUrl: await fileToBase64(imageFile),  // optional thumbnail
    medicines:    result.medicines,       // string[]
    doctorName:   result.doctorName,
    hospitalName: result.hospitalName,
    patientName:  result.patientName,
    diagnosis:    result.diagnosis,
    instructions: result.dosageNotes,
    rawText:      result.fullOcrText,
    confidence:   result.confidencePercent,  // number 0–100
  });

  // YOUR EXISTING CODE — render results
  displayResults(result);
}

// Helper: convert File to base64 if you want image thumbnails in history
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}


// --- 2. When user submits a drug search ---------------------------

async function handleDrugSearch(queryString) {

  // YOUR EXISTING CODE — call your search API
  const results = await yourSearchApi.query(queryString);

  // ✅ ADD THIS
  addSearchEntry({
    query:       queryString,
    category:    autoDetectCategory(queryString),
    resultCount: results.length,
    topResults:  results.slice(0, 3).map(r => ({
      title:   r.name,
      snippet: r.description?.slice(0, 100),
      url:     r.url,
    })),
  });

  displaySearchResults(results);
}

// Auto-detect what kind of query the user made
function autoDetectCategory(query) {
  if (/interact/i.test(query))             return 'interaction';
  if (/dose|dosage|mg|tablet/i.test(query)) return 'dosage';
  if (/side.?effect|adverse/i.test(query)) return 'side-effects';
  if (/generic|brand|substitute/i.test(query)) return 'drug-info';
  return 'general';
}


// --- 3. When user opens a drug detail page ------------------------

// Add this inside your drug detail page component's useEffect
// (React) or DOMContentLoaded handler (vanilla JS)

// React:
useEffect(() => {
  addPageViewEntry({
    drugName: drug.name,
    pageUrl:  window.location.href,
    category: drug.therapeuticClass,
  });
}, [drug.name]);

// Vanilla JS:
document.addEventListener('DOMContentLoaded', () => {
  const drugName = document.querySelector('[data-drug-name]')?.dataset.drugName;
  if (drugName) {
    addPageViewEntry({
      drugName,
      pageUrl:  window.location.href,
      category: document.querySelector('[data-drug-category]')?.dataset.drugCategory,
    });
  }
});


// --- 4. Add the History link to your navbar -----------------------

// HTML navbar — add this link wherever your nav links are:
// <a href="/history">📋 History</a>

// React Router v6:
import { Link } from 'react-router-dom';
// <Link to="/history">📋 History</Link>


// --- 5. Add the route --------------------------------------------

// React Router v6 — in your App.jsx routes:
import HistoryPage from './HistoryPage';

// Inside <Routes>:
// <Route path="/history" element={<HistoryPage />} />

// Next.js App Router — create app/history/page.jsx:
// 'use client';
// import HistoryPage from '@/components/HistoryPage';
// export default function HistoryRoute() { return <HistoryPage />; }

// Next.js Pages Router — create pages/history.jsx:
// import dynamic from 'next/dynamic';
// const HistoryPage = dynamic(() => import('../components/HistoryPage'), { ssr: false });
// export default function HistoryRoute() { return <HistoryPage />; }


// --- 6. Vanilla JS — no React? ------------------------------------
//
//  The historyManager.js functions work in any JS environment.
//  Build your own UI and read history like this:

import { getHistory, getStats } from './historyManager';

function renderHistoryPage() {
  const stats   = getStats();
  const history = getHistory({ type: 'all', limit: 50 });

  document.getElementById('total-count').textContent = stats.total;

  const list = document.getElementById('history-list');
  list.innerHTML = history.map(entry => `
    <div class="history-item ${entry.type}">
      <div class="item-icon">${entry.type === 'prescription' ? '💊' : '🔍'}</div>
      <div class="item-body">
        <strong>${entry.title}</strong>
        <small>${new Date(entry.timestamp).toLocaleString()}</small>
        ${entry.type === 'prescription'
          ? `<p>${entry.medicines?.join(', ') ?? ''}</p>`
          : `<p>Query: ${entry.query} · ${entry.resultCount} results</p>`
        }
      </div>
    </div>
  `).join('');
}