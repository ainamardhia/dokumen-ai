<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <div class="container">
        <div class="header-content">
          <div class="header-title">
            <svg class="icon-large" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            <div>
              <h1>Regulatory Document Explorer</h1>
              <p class="subtitle">AI-powered compliance document discovery</p>
            </div>
          </div>
          <div class="header-buttons">
            <button 
              @click="currentView = 'list'" 
              :class="['btn', currentView === 'list' ? 'btn-primary' : 'btn-secondary']"
            >
              All Documents
            </button>
            <button 
              @click="currentView = 'bookmarks'" 
              :class="['btn', currentView === 'bookmarks' ? 'btn-primary' : 'btn-secondary']"
            >
              📚 Bookmarks ({{ bookmarks.length }})
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="container main-content">
      <!-- AI Search Bar -->
      <div class="card search-card">
        <div class="search-header">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
          </svg>
          <h2>AI-Powered Search</h2>
        </div>
        <div class="search-input-group">
          <input
            v-model="searchQuery"
            @keyup.enter="handleAISearch"
            type="text"
            placeholder="Try: 'show me recent SEC filings' or 'find compliance reports'"
            class="search-input"
          />
          <button 
            @click="handleAISearch" 
            :disabled="aiLoading || !searchQuery.trim()"
            class="btn btn-primary"
          >
            <span v-if="aiLoading" class="spinner"></span>
            <span v-else>🔍</span>
            Search
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="card filter-card">
        <div class="filter-group">
          <label class="filter-label">Filter by Agency:</label>
          <select v-model="filterAgency" class="select">
            <option value="all">All Agencies</option>
            <option v-for="agency in agencies" :key="agency" :value="agency">
              {{ agency }}
            </option>
          </select>
          <button @click="clearFilters" class="btn-text">
            Clear Filters
          </button>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="alert alert-error">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        <p>{{ error }}</p>
      </div>

      <!-- Main Content Grid -->
      <div class="content-grid">
        <!-- Document List -->
        <div class="document-list-section">
          <div class="card">
            <h2 class="section-title">
              {{ currentView === 'bookmarks' ? 'Bookmarked Documents' : 'Documents' }}
            </h2>

            <div v-if="loading" class="loading-container">
              <div class="spinner"></div>
            </div>

            <div v-else class="document-list">
              <div v-if="displayedDocuments.length === 0" class="empty-state">
                <p>{{ currentView === 'bookmarks' ? 'No bookmarks yet' : 'No documents found' }}</p>
              </div>

              <div
                v-for="doc in displayedDocuments"
                :key="doc.id"
                @click="selectDocument(doc)"
                :class="['document-item', { 'document-item-selected': selectedDoc?.id === doc.id }]"
              >
                <div class="document-content">
                  <h3 class="document-title">{{ doc.title }}</h3>
                  <div class="document-meta">
                    <span class="meta-item">
                      🏢 {{ doc.agency }}
                    </span>
                    <span class="meta-item">
                      📅 {{ doc.date }}
                    </span>
                    <span class="badge">{{ doc.type }}</span>
                  </div>
                  <p class="document-summary">{{ doc.summary }}</p>
                </div>
                <button
                  @click.stop="toggleBookmark(doc)"
                  :class="['bookmark-btn', { 'bookmark-btn-active': isBookmarked(doc.id) }]"
                >
                  {{ isBookmarked(doc.id) ? '⭐' : '☆' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Document Detail Panel -->
        <div class="document-detail-section">
          <div class="card detail-card">
            <div v-if="selectedDoc">
              <h2 class="section-title">Document Details</h2>
              
              <div class="detail-content">
                <div class="detail-header">
                  <h3>{{ selectedDoc.title }}</h3>
                  <div class="detail-badges">
                    <span class="badge badge-primary">{{ selectedDoc.agency }}</span>
                    <span class="badge">{{ selectedDoc.type }}</span>
                  </div>
                  <p class="detail-date">{{ selectedDoc.date }}</p>
                </div>

                <div class="detail-section">
                  <h4>Summary</h4>
                  <p>{{ selectedDoc.summary }}</p>
                </div>

                <button
                  @click="generateAISummary"
                  :disabled="aiLoading"
                  class="btn btn-ai"
                >
                  <span v-if="aiLoading" class="spinner"></span>
                  <span v-else>✨</span>
                  {{ aiLoading ? 'Generating...' : 'Generate AI Analysis' }}
                </button>

                <div v-if="aiSummary" class="ai-summary">
                  <h4>
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
                    </svg>
                    AI Analysis
                  </h4>
                  <div class="ai-summary-content">{{ aiSummary }}</div>
                </div>
              </div>
            </div>

            <div v-else class="empty-detail">
              <svg class="icon-xl" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              <p>Select a document to view details</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';

export default {
  name: 'App',
  setup() {
    // State
    const documents = ref([]);
    const filteredDocs = ref([]);
    const selectedDoc = ref(null);
    const bookmarks = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const searchQuery = ref('');
    const aiLoading = ref(false);
    const aiSummary = ref(null);
    const filterAgency = ref('all');
    const currentView = ref('list');

    // API base URL
    const API_BASE = 'http://localhost:8000/api';

    // Computed
    const agencies = computed(() => {
      return [...new Set(documents.value.map(d => d.agency))];
    });

    const displayedDocuments = computed(() => {
      if (currentView.value === 'bookmarks') {
        return bookmarks.value;
      }
      return filteredDocs.value;
    });

    // Methods
    const fetchDocuments = async () => {
      loading.value = true;
      error.value = null;

      try {
        console.log('Fetching from:', `${API_BASE}/documents`);
        const response = await axios.get(`${API_BASE}/documents`);
        documents.value = response.data;
        filteredDocs.value = response.data;
      } catch (err) {
        console.error('Detailed error:', err.response || err);
        error.value = 'Unable to fetch documents. Please try again later.';
        console.error('Fetch error:', err);
      } finally {
        loading.value = false;
      }
    };

    const handleAISearch = async () => {
      if (!searchQuery.value.trim()) return;

      aiLoading.value = true;
      error.value = null;

      try {
        const response = await axios.post(`${API_BASE}/search`, {
          query: searchQuery.value,
          documents: documents.value
        });

        filteredDocs.value = response.data.relevantDocs;
        
        if (filteredDocs.value.length === 0) {
          error.value = 'No documents matched your search query.';
        }
      } catch (err) {
        error.value = 'AI search failed. Please try again.';
        console.error('Search error:', err);
      } finally {
        aiLoading.value = false;
      }
    };

    const lastRequestTime = ref(0);

    const generateAISummary = async () => {
      const now = Date.now();
      if (now - lastRequestTime.value < 10000) {
        alert('Please wait 10 seconds between requests');
        return;
      }
      lastRequestTime.value = now;
      
      if (!selectedDoc.value) return;

      aiLoading.value = true;
      aiSummary.value = null;

      try {
        const response = await axios.post(`${API_BASE}/summarize`, {
          document: selectedDoc.value
        });

        aiSummary.value = response.data.summary;
      } catch (err) {
        aiSummary.value = 'Unable to generate AI summary at this time. Please try again later.';
        console.error('Summary error:', err);
      } finally {
        aiLoading.value = false;
      }
    };

    const selectDocument = (doc) => {
      selectedDoc.value = doc;
      aiSummary.value = null;
    };

    const toggleBookmark = (doc) => {
      const index = bookmarks.value.findIndex(b => b.id === doc.id);
      
      if (index > -1) {
        bookmarks.value.splice(index, 1);
      } else {
        bookmarks.value.push(doc);
      }
      
      localStorage.setItem('regulatory_bookmarks', JSON.stringify(bookmarks.value));
    };

    const isBookmarked = (docId) => {
      return bookmarks.value.some(b => b.id === docId);
    };

    const clearFilters = () => {
      searchQuery.value = '';
      filterAgency.value = 'all';
      filteredDocs.value = documents.value;
    };

    // Watch for filter changes
    watch(filterAgency, (newAgency) => {
      if (newAgency === 'all') {
        filteredDocs.value = documents.value;
      } else {
        filteredDocs.value = documents.value.filter(doc => doc.agency === newAgency);
      }
    });

    // Lifecycle
    onMounted(() => {
      // Load bookmarks from localStorage
      const saved = localStorage.getItem('regulatory_bookmarks');
      if (saved) {
        bookmarks.value = JSON.parse(saved);
      }

      // Fetch documents
      fetchDocuments();
    });

    return {
      documents,
      filteredDocs,
      selectedDoc,
      bookmarks,
      loading,
      error,
      searchQuery,
      aiLoading,
      aiSummary,
      filterAgency,
      currentView,
      agencies,
      displayedDocuments,
      fetchDocuments,
      handleAISearch,
      generateAISummary,
      selectDocument,
      toggleBookmark,
      isBookmarked,
      clearFilters
    };
  }
};
</script>

<style>
/* Global Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
  color: #333;
  line-height: 1.6;
}

.app {
  min-height: 100vh;
}

/* Container */
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Header */
.header {
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid #e0e0e0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  flex-wrap: wrap;
  gap: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-title h1 {
  font-size: 28px;
  font-weight: 700;
  color: #2563eb;
}

.subtitle {
  font-size: 14px;
  color: #666;
  margin-top: 2px;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

/* Icons */
.icon {
  width: 20px;
  height: 20px;
  stroke-width: 2;
}

.icon-large {
  width: 40px;
  height: 40px;
  stroke-width: 2;
  color: #2563eb;
}

.icon-xl {
  width: 80px;
  height: 80px;
  stroke-width: 1.5;
  color: #d1d5db;
}

/* Main Content */
.main-content {
  padding: 30px 20px;
}

/* Cards */
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 24px;
  margin-bottom: 24px;
}

/* Search Card */
.search-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.search-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.search-header h2 {
  font-size: 20px;
  font-weight: 600;
}

.search-input-group {
  display: flex;
  gap: 12px;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
}

/* Filter Card */
.filter-card {
  padding: 16px 24px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

.select {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
}

.select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Buttons */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.btn-ai {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px;
  margin-top: 16px;
}

.btn-ai:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-text {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 14px;
  margin-left: auto;
}

.btn-text:hover {
  text-decoration: underline;
}

/* Alerts */
.alert {
  padding: 16px;
  border-radius: 8px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.alert-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

/* Section Titles */
.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 20px;
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Document List */
.document-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.document-item {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.document-item:hover {
  border-color: #93c5fd;
  background: #f9fafb;
}

.document-item-selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.document-content {
  flex: 1;
}

.document-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.document-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 13px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 4px;
}

.badge {
  padding: 4px 10px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
}

.badge-primary {
  background: #dbeafe;
  color: #1e40af;
}

.document-summary {
  font-size: 14px;
  color: #6b7280;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bookmark-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: #f3f4f6;
  color: #9ca3af;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.bookmark-btn:hover {
  background: #e5e7eb;
}

.bookmark-btn-active {
  background: #fef3c7;
  color: #f59e0b;
}

/* Document Detail */
.detail-card {
  position: sticky;
  top: 100px;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
}

.detail-badges {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.detail-date {
  font-size: 14px;
  color: #6b7280;
}

.detail-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 8px;
}

.detail-section p {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
}

.empty-detail {
  text-align: center;
  padding: 80px 20px;
  color: #9ca3af;
}

.empty-detail p {
  margin-top: 16px;
  font-size: 16px;
}

/* AI Summary */
.ai-summary {
  padding: 20px;
  background: linear-gradient(135deg, #f0e7ff 0%, #e9d5ff 100%);
  border: 1px solid #d8b4fe;
  border-radius: 8px;
  margin-top: 16px;
}

.ai-summary h4 {
  font-size: 16px;
  font-weight: 600;
  color: #6b21a8;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-summary-content {
  font-size: 14px;
  color: #4c1d95;
  line-height: 1.7;
  white-space: pre-wrap;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-input-group {
    flex-direction: column;
  }

  .filter-group {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>