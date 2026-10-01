const fs = require('fs');
const path = require('path');

const rootDir = __dirname;
const distDir = path.join(rootDir, 'dist');

// Ensure dist directory exists
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

// Helper to format title from filename or frontmatter
function extractTitle(content, fallback) {
  const match = content.match(/^#\s+(.+)$/m);
  if (match) return match[1].trim();
  return fallback.replace(/^\d+-/, '').replace(/-/g, ' ').replace(/\.md$/, '')
    .split(' ')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

// Section formatting
const sectionTitles = {
  '00-core': 'Getting Started',
  '01-fundamentals': '01. Fundamentals',
  '02-networking': '02. Networking',
  '03-load-balancing-and-proxies': '03. Load Balancing & Proxies',
  '04-caching': '04. Caching & Eviction',
  '05-databases': '05. Databases & Storage',
  '06-data-partitioning-and-replication': '06. Partitioning & Replication',
  '07-distributed-systems-theory': '07. Distributed Systems Theory',
  '08-messaging-and-streaming': '08. Messaging & Streaming',
  '09-api-design': '09. API Design & Security',
  '10-architecture-patterns': '10. Architecture Patterns',
  '11-reliability-and-resilience': '11. Reliability & Resilience',
  '12-security': '12. Security & Compliance',
  '13-observability': '13. Observability & SRE',
  '14-cloud-and-devops': '14. Cloud & DevOps',
  '15-storage-and-search': '15. Storage & Search',
  '16-real-time-systems': '16. Real-Time Systems',
  '17-low-level-design': '17. Low-Level Design (LLD)',
  '18-data-and-ml-systems': '18. Data & ML Systems',
  '19-case-studies': '19. Real-World Case Studies (35)',
  '20-estimation-and-interview-framework': '20. Estimation & Interview Guide',
  'exercises': 'Exercises & Solutions',
  'resources': 'Resources & Cheatsheets'
};

const allDocs = [];

// 1. Process root guides
const rootFiles = ['README.md', 'ROADMAP.md', 'CONTRIBUTING.md'];
rootFiles.forEach(rf => {
  const p = path.join(rootDir, rf);
  if (fs.existsSync(p)) {
    const content = fs.readFileSync(p, 'utf-8');
    allDocs.push({
      id: rf.toLowerCase().replace(/\.md$/, ''),
      section: '00-core',
      sectionTitle: 'Getting Started',
      title: extractTitle(content, rf),
      path: rf,
      content: content,
      readingTime: Math.ceil(content.split(/\s+/).length / 200)
    });
  }
});

// 2. Process docs/ folder
const docsDir = path.join(rootDir, 'docs');
if (fs.existsSync(docsDir)) {
  const entries = fs.readdirSync(docsDir);
  entries.forEach(entry => {
    const fullPath = path.join(docsDir, entry);
    if (fs.statSync(fullPath).isDirectory()) {
      const sectionKey = entry;
      const secTitle = sectionTitles[sectionKey] || entry.replace(/^\d+-/, '').replace(/-/g, ' ');
      const files = fs.readdirSync(fullPath).filter(f => f.endswith ? f.endswith('.md') : f.endsWith('.md')).sort();
      files.forEach(f => {
        const fp = path.join(fullPath, f);
        const content = fs.readFileSync(fp, 'utf-8');
        const relPath = path.join('docs', entry, f).replace(/\\/g, '/');
        allDocs.push({
          id: relPath.replace(/\.md$/, '').replace(/\//g, '_'),
          section: sectionKey,
          sectionTitle: secTitle,
          title: extractTitle(content, f),
          path: relPath,
          content: content,
          readingTime: Math.ceil(content.split(/\s+/).length / 200)
        });
      });
    } else if (entry.endsWith('.md')) {
      const content = fs.readFileSync(fullPath, 'utf-8');
      const relPath = path.join('docs', entry).replace(/\\/g, '/');
      allDocs.push({
        id: relPath.replace(/\.md$/, '').replace(/\//g, '_'),
        section: '00-core',
        sectionTitle: 'Getting Started',
        title: extractTitle(content, entry),
        path: relPath,
        content: content,
        readingTime: Math.ceil(content.split(/\s+/).length / 200)
      });
    }
  });
}

// 3. Process exercises/ folder
const exercisesDir = path.join(rootDir, 'exercises');
if (fs.existsSync(exercisesDir)) {
  const files = fs.readdirSync(exercisesDir).filter(f => f.endsWith('.md')).sort();
  files.forEach(f => {
    const fp = path.join(exercisesDir, f);
    const content = fs.readFileSync(fp, 'utf-8');
    const relPath = path.join('exercises', f).replace(/\\/g, '/');
    allDocs.push({
      id: relPath.replace(/\.md$/, '').replace(/\//g, '_'),
      section: 'exercises',
      sectionTitle: 'Exercises & Solutions',
      title: extractTitle(content, f),
      path: relPath,
      content: content,
      readingTime: Math.ceil(content.split(/\s+/).length / 200)
    });
  });
}

// 4. Process resources/ folder
const resourcesDir = path.join(rootDir, 'resources');
if (fs.existsSync(resourcesDir)) {
  const files = fs.readdirSync(resourcesDir).filter(f => f.endsWith('.md')).sort();
  files.forEach(f => {
    const fp = path.join(resourcesDir, f);
    const content = fs.readFileSync(fp, 'utf-8');
    const relPath = path.join('resources', f).replace(/\\/g, '/');
    allDocs.push({
      id: relPath.replace(/\.md$/, '').replace(/\//g, '_'),
      section: 'resources',
      sectionTitle: 'Resources & Cheatsheets',
      title: extractTitle(content, f),
      path: relPath,
      content: content,
      readingTime: Math.ceil(content.split(/\s+/).length / 200)
    });
  });
}

console.log(`Indexed ${allDocs.length} total documentation pages.`);

// Write out docs-data.js
const docsDataContent = `window.HANDBOOK_DOCS = ${JSON.stringify(allDocs, null, 2)};`;
fs.writeFileSync(path.join(distDir, 'docs-data.js'), docsDataContent, 'utf-8');
console.log('Generated dist/docs-data.js');

// HTML shell
const indexHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>System Design Handbook | Production-Grade Guide</title>
  <meta name="description" content="Comprehensive open-source handbook covering system design from fundamentals to 35 complete real-world case studies with Mermaid diagrams and code.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <link rel="stylesheet" href="style.css">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body class="dark-theme">
  <div id="reading-progress" class="reading-progress"></div>
  
  <!-- Header Navigation -->
  <header class="navbar">
    <div class="nav-left">
      <button id="toggle-sidebar" class="btn-icon" aria-label="Toggle Navigation">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
      </button>
      <a href="#readme" class="brand">
        <span class="brand-icon">⚡</span>
        <span class="brand-title">System Design <span class="gradient-text">Handbook</span></span>
      </a>
    </div>
    
    <div class="nav-center">
      <div class="search-trigger" id="search-trigger">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <span>Search handbook (200+ topics & case studies)...</span>
        <kbd>Ctrl K</kbd>
      </div>
    </div>

    <div class="nav-right">
      <button id="theme-toggle" class="btn-icon" aria-label="Toggle Theme">
        <svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
      </button>
      <a href="https://github.com" target="_blank" rel="noopener" class="btn-icon" aria-label="GitHub Repository">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
      </a>
    </div>
  </header>

  <!-- App Layout -->
  <div class="layout-container">
    <!-- Sidebar Navigation -->
    <aside id="sidebar" class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-label">HANDBOOK DIRECTORY</span>
      </div>
      <nav id="nav-tree" class="nav-tree"></nav>
    </aside>

    <!-- Main Content Area -->
    <main class="content-wrapper">
      <div class="content-inner">
        <div class="doc-meta-header">
          <div id="breadcrumb" class="breadcrumb"></div>
          <div id="reading-time" class="reading-badge"></div>
        </div>
        <article id="doc-content" class="markdown-body">
          <div class="loading-state">Loading handbook documentation...</div>
        </article>
        
        <!-- Bottom Pagination -->
        <footer class="doc-footer">
          <a id="prev-doc" class="footer-nav-btn prev" href="#">
            <span class="nav-direction">← Previous</span>
            <span class="nav-label">Title</span>
          </a>
          <a id="next-doc" class="footer-nav-btn next" href="#">
            <span class="nav-direction">Next →</span>
            <span class="nav-label">Title</span>
          </a>
        </footer>
      </div>
    </main>

    <!-- Table of Contents Aside -->
    <aside class="toc-sidebar">
      <div class="toc-title">ON THIS PAGE</div>
      <nav id="page-toc" class="page-toc"></nav>
    </aside>
  </div>

  <!-- Search Modal -->
  <div id="search-modal" class="search-modal hidden">
    <div class="search-modal-backdrop" id="modal-backdrop"></div>
    <div class="search-modal-card">
      <div class="search-input-wrapper">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" id="search-input" placeholder="Type a concept, technology (Kafka, Redis, Raft) or case study..." autocomplete="off">
        <kbd id="modal-esc">ESC</kbd>
      </div>
      <div id="search-results" class="search-results"></div>
    </div>
  </div>

  <script src="docs-data.js"></script>
  <script src="app.js"></script>
</body>
</html>
`;

fs.writeFileSync(path.join(distDir, 'index.html'), indexHtml, 'utf-8');
console.log('Generated dist/index.html');

// Generate CSS
const styleCss = `
:root {
  --bg-primary: #0b0f19;
  --bg-secondary: #111827;
  --bg-surface: #1e293b;
  --border-color: #334155;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent-cyan: #06b6d4;
  --accent-violet: #8b5cf6;
  --accent-gradient: linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%);
  --sidebar-width: 320px;
  --toc-width: 240px;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-heading: 'Outfit', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

body.light-theme {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-surface: #f1f5f9;
  --border-color: #e2e8f0;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-sans);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.7;
  overflow-x: hidden;
}

/* Reading Progress Bar */
.reading-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: var(--accent-gradient);
  z-index: 9999;
  width: 0%;
  transition: width 0.1s;
}

/* Header Navbar */
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  height: 64px;
  background-color: rgba(11, 15, 25, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
}

body.light-theme .navbar {
  background-color: rgba(255, 255, 255, 0.85);
}

.nav-left, .nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--text-primary);
  font-family: var(--font-heading);
  font-size: 1.15rem;
  font-weight: 700;
}

.gradient-text {
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.btn-icon {
  background: none;
  border: 1px solid transparent;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-icon:hover {
  color: var(--text-primary);
  background-color: var(--bg-surface);
  border-color: var(--border-color);
}

/* Search Trigger Bar */
.search-trigger {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  padding: 0.45rem 1rem;
  border-radius: 9999px;
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  width: 440px;
  transition: all 0.2s;
}

.search-trigger:hover {
  border-color: var(--accent-cyan);
  color: var(--text-primary);
}

.search-trigger kbd {
  margin-left: auto;
  font-size: 0.75rem;
  font-family: var(--font-mono);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}

/* App Layout */
.layout-container {
  display: flex;
  max-width: 1720px;
  margin: 0 auto;
  min-height: calc(100vh - 64px);
}

/* Sidebar */
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  height: calc(100vh - 64px);
  position: sticky;
  top: 64px;
  overflow-y: auto;
  padding: 1.25rem 0.75rem;
}

.sidebar-header {
  padding: 0.5rem 0.75rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

.nav-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  font-size: 0.825rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 6px;
  margin-top: 0.5rem;
  transition: all 0.15s;
}

.nav-section-title:hover {
  color: var(--text-primary);
  background-color: var(--bg-surface);
}

.nav-items-group {
  margin-left: 0.5rem;
  padding-left: 0.5rem;
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  margin-top: 0.25rem;
}

.nav-link {
  display: block;
  padding: 0.35rem 0.75rem;
  font-size: 0.825rem;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.15s;
}

.nav-link:hover {
  color: var(--accent-cyan);
  background-color: var(--bg-surface);
}

.nav-link.active {
  color: #ffffff;
  background: var(--accent-gradient);
  font-weight: 600;
}

/* Content Area */
.content-wrapper {
  flex-grow: 1;
  min-width: 0;
  padding: 2.5rem 3.5rem;
}

.content-inner {
  max-width: 880px;
  margin: 0 auto;
}

.doc-meta-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.breadcrumb {
  font-size: 0.875rem;
  color: var(--accent-cyan);
  font-weight: 500;
}

.reading-badge {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--bg-surface);
  padding: 0.25rem 0.6rem;
  border-radius: 9999px;
  border: 1px solid var(--border-color);
}

/* Markdown Body Styles */
.markdown-body h1 {
  font-family: var(--font-heading);
  font-size: 2.25rem;
  margin-bottom: 1.5rem;
  line-height: 1.25;
  color: var(--text-primary);
}

.markdown-body h2 {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  margin-top: 2.25rem;
  margin-bottom: 1rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
}

.markdown-body h3 {
  font-size: 1.2rem;
  margin-top: 1.75rem;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
}

.markdown-body p {
  margin-bottom: 1.25rem;
  color: var(--text-secondary);
}

.markdown-body ul, .markdown-body ol {
  margin-bottom: 1.25rem;
  padding-left: 1.5rem;
  color: var(--text-secondary);
}

.markdown-body li {
  margin-bottom: 0.5rem;
}

.markdown-body strong {
  color: var(--text-primary);
}

.markdown-body blockquote {
  border-left: 4px solid var(--accent-cyan);
  padding: 0.75rem 1.25rem;
  background-color: var(--bg-surface);
  border-radius: 0 8px 8px 0;
  margin-bottom: 1.5rem;
  color: var(--text-secondary);
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-size: 0.9rem;
}

.markdown-body th, .markdown-body td {
  border: 1px solid var(--border-color);
  padding: 0.75rem 1rem;
  text-align: left;
}

.markdown-body th {
  background-color: var(--bg-surface);
  color: var(--text-primary);
  font-weight: 600;
}

.markdown-body tr:nth-child(even) {
  background-color: rgba(255, 255, 255, 0.02);
}

/* Code Blocks */
.markdown-body pre {
  position: relative;
  background-color: #141b2d !important;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.25rem;
  overflow-x: auto;
  margin: 1.5rem 0;
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

.markdown-body code {
  font-family: var(--font-mono);
  font-size: 0.875em;
  background-color: var(--bg-surface);
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  color: var(--accent-cyan);
}

.markdown-body pre code {
  background: none;
  padding: 0;
  color: inherit;
}

.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  color: var(--text-primary);
  border-color: var(--accent-cyan);
}

/* Mermaid Diagrams */
.mermaid {
  background-color: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
  margin: 1.5rem 0;
  display: flex;
  justify-content: center;
  overflow-x: auto;
}

/* Table of Contents Aside */
.toc-sidebar {
  width: var(--toc-width);
  flex-shrink: 0;
  height: calc(100vh - 64px);
  position: sticky;
  top: 64px;
  overflow-y: auto;
  padding: 2.5rem 1rem 1rem;
  font-size: 0.8rem;
}

.toc-title {
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}

.page-toc a {
  display: block;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 0.3rem 0;
  line-height: 1.4;
  transition: color 0.15s;
}

.page-toc a:hover {
  color: var(--accent-cyan);
}

/* Footer Navigation */
.doc-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 3.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-color);
  gap: 1rem;
}

.footer-nav-btn {
  display: flex;
  flex-direction: column;
  padding: 1rem 1.25rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  text-decoration: none;
  min-width: 220px;
  transition: all 0.2s;
}

.footer-nav-btn:hover {
  border-color: var(--accent-cyan);
  background: var(--bg-surface);
}

.footer-nav-btn.next {
  text-align: right;
  margin-left: auto;
}

.nav-direction {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
}

.nav-label {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 600;
  margin-top: 0.25rem;
}

/* Search Modal */
.search-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 2000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 10vh;
}

.search-modal.hidden {
  display: none;
}

.search-modal-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
}

.search-modal-card {
  position: relative;
  z-index: 10;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  width: 90%;
  max-width: 640px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
  overflow: hidden;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  gap: 0.75rem;
}

.search-input-wrapper input {
  flex-grow: 1;
  background: none;
  border: none;
  outline: none;
  font-size: 1.1rem;
  color: var(--text-primary);
  font-family: var(--font-sans);
}

.search-results {
  max-height: 420px;
  overflow-y: auto;
  padding: 0.75rem;
}

.search-result-item {
  display: block;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
  transition: all 0.15s;
}

.search-result-item:hover {
  background: var(--bg-surface);
}

.search-result-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--accent-cyan);
}

.search-result-snippet {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 0.2rem;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Responsive */
@media (max-width: 1100px) {
  .toc-sidebar { display: none; }
  .search-trigger { width: 300px; }
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 64px;
    left: -100%;
    z-index: 1050;
    transition: left 0.3s;
    background: var(--bg-primary);
    width: 85%;
    max-width: 320px;
  }
  .sidebar.open {
    left: 0;
  }
  .content-wrapper {
    padding: 1.5rem;
  }
  .search-trigger {
    width: 200px;
  }
  .search-trigger span {
    display: none;
  }
}
`;

fs.writeFileSync(path.join(distDir, 'style.css'), styleCss, 'utf-8');
console.log('Generated dist/style.css');

// Generate Client-Side Application Engine (app.js)
const appJs = `
document.addEventListener('DOMContentLoaded', () => {
  const docs = window.HANDBOOK_DOCS || [];
  const navTree = document.getElementById('nav-tree');
  const docContent = document.getElementById('doc-content');
  const breadcrumb = document.getElementById('breadcrumb');
  const readingTime = document.getElementById('reading-time');
  const pageToc = document.getElementById('page-toc');
  const prevBtn = document.getElementById('prev-doc');
  const nextBtn = document.getElementById('next-doc');
  const progressBar = document.getElementById('reading-progress');
  const sidebar = document.getElementById('sidebar');
  const toggleSidebarBtn = document.getElementById('toggle-sidebar');
  const searchModal = document.getElementById('search-modal');
  const searchTrigger = document.getElementById('search-trigger');
  const searchInput = document.getElementById('search-input');
  const searchResults = document.getElementById('search-results');
  const modalBackdrop = document.getElementById('modal-backdrop');
  const themeToggle = document.getElementById('theme-toggle');

  // Configure marked with syntax highlighting
  marked.setOptions({
    highlight: function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true
  });

  // Initialize Mermaid
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter, sans-serif'
  });

  // Group docs by section
  const sectionMap = {};
  docs.forEach(doc => {
    if (!sectionMap[doc.section]) {
      sectionMap[doc.section] = {
        title: doc.sectionTitle,
        items: []
      };
    }
    sectionMap[doc.section].items.push(doc);
  });

  // Render Sidebar Tree
  function renderNavTree(activeId) {
    navTree.innerHTML = '';
    for (const [secKey, secData] of Object.entries(sectionMap)) {
      const secGroup = document.createElement('div');
      secGroup.className = 'nav-section';

      const secTitle = document.createElement('div');
      secTitle.className = 'nav-section-title';
      secTitle.innerHTML = \`<span>\${secData.title}</span> <span class="sec-count">\${secData.items.length}</span>\`;
      
      const itemsContainer = document.createElement('div');
      itemsContainer.className = 'nav-items-group';

      secData.items.forEach(doc => {
        const a = document.createElement('a');
        a.href = '#' + doc.id;
        a.className = 'nav-link' + (doc.id === activeId ? ' active' : '');
        a.textContent = doc.title;
        a.title = doc.title;
        a.addEventListener('click', () => {
          if (window.innerWidth <= 768) sidebar.classList.remove('open');
        });
        itemsContainer.appendChild(a);
      });

      secGroup.appendChild(secTitle);
      secGroup.appendChild(itemsContainer);
      navTree.appendChild(secGroup);
    }
  }

  // Load Document by ID
  function loadDoc(docId) {
    const doc = docs.find(d => d.id === docId) || docs[0];
    if (!doc) return;

    window.scrollTo({ top: 0, behavior: 'instant' });
    renderNavTree(doc.id);

    breadcrumb.textContent = \`\${doc.sectionTitle}  /  \${doc.title}\`;
    readingTime.textContent = \`⏱ \${doc.readingTime} min read\`;
    document.title = \`\${doc.title} | System Design Handbook\`;

    // Process markdown and handle Mermaid blocks
    let rawMd = doc.content;
    
    // Replace \`\`\`mermaid code blocks with <div class="mermaid">...</div>
    const mermaidRegex = /\\\\\`\\\\\`\\\\\`mermaid\\s*([\\s\\S]*?)\\\\\`\\\\\`\\\\\`/g;
    const mermaidPlaceholders = [];
    rawMd = rawMd.replace(mermaidRegex, (match, code) => {
      const idx = mermaidPlaceholders.length;
      mermaidPlaceholders.push(code.trim());
      return \`<!--MERMAID_\${idx}-->\`;
    });

    let renderedHtml = marked.parse(rawMd);

    // Restore Mermaid placeholders
    mermaidPlaceholders.forEach((code, idx) => {
      renderedHtml = renderedHtml.replace(
        \`<!--MERMAID_\${idx}-->\`,
        \`<div class="mermaid">\${code}</div>\`
      );
    });

    docContent.innerHTML = renderedHtml;

    // Render Mermaid diagrams
    try {
      mermaid.run({
        nodes: document.querySelectorAll('.mermaid')
      });
    } catch (e) {
      console.warn('Mermaid rendering issue:', e);
    }

    // Add Copy buttons to code snippets
    document.querySelectorAll('pre').forEach(pre => {
      const btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.textContent = 'Copy';
      btn.addEventListener('click', () => {
        const codeText = pre.querySelector('code')?.innerText || pre.innerText;
        navigator.clipboard.writeText(codeText);
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 2000);
      });
      pre.appendChild(btn);
    });

    // Generate In-Page TOC
    buildPageToc();

    // Setup Footer Prev/Next
    const curIndex = docs.findIndex(d => d.id === doc.id);
    if (curIndex > 0) {
      const prevDoc = docs[curIndex - 1];
      prevBtn.style.visibility = 'visible';
      prevBtn.href = '#' + prevDoc.id;
      prevBtn.querySelector('.nav-label').textContent = prevDoc.title;
    } else {
      prevBtn.style.visibility = 'hidden';
    }

    if (curIndex < docs.length - 1) {
      const nextDoc = docs[curIndex + 1];
      nextBtn.style.visibility = 'visible';
      nextBtn.href = '#' + nextDoc.id;
      nextBtn.querySelector('.nav-label').textContent = nextDoc.title;
    } else {
      nextBtn.style.visibility = 'hidden';
    }
  }

  // Build In-Page TOC from h2 headers
  function buildPageToc() {
    pageToc.innerHTML = '';
    const headings = docContent.querySelectorAll('h2');
    headings.forEach((h, index) => {
      const id = 'heading-' + index;
      h.id = id;
      const a = document.createElement('a');
      a.href = '#' + id;
      a.textContent = h.textContent.replace(/^\\d+\\.\\s*/, '');
      a.addEventListener('click', (e) => {
        e.preventDefault();
        h.scrollIntoView({ behavior: 'smooth' });
      });
      pageToc.appendChild(a);
    });
  }

  // Reading Progress Listener
  window.addEventListener('scroll', () => {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0;
    progressBar.style.width = progress + '%';
  });

  // Sidebar toggle
  toggleSidebarBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  // Theme toggle
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
  });
  if (localStorage.getItem('theme') === 'light') {
    document.body.classList.add('light-theme');
  }

  // Search Modal handlers
  function openSearch() {
    searchModal.classList.remove('hidden');
    searchInput.value = '';
    searchInput.focus();
    renderSearchResults('');
  }
  function closeSearch() {
    searchModal.classList.add('hidden');
  }
  searchTrigger.addEventListener('click', openSearch);
  modalBackdrop.addEventListener('click', closeSearch);

  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      openSearch();
    }
    if (e.key === 'Escape') closeSearch();
  });

  searchInput.addEventListener('input', (e) => {
    renderSearchResults(e.target.value.trim().toLowerCase());
  });

  function renderSearchResults(query) {
    searchResults.innerHTML = '';
    if (!query) {
      searchResults.innerHTML = '<div style="padding:1rem;color:var(--text-muted);font-size:0.875rem;">Type to search 200+ topics, algorithms, diagrams, and case studies...</div>';
      return;
    }

    const matches = docs.filter(d => 
      d.title.toLowerCase().includes(query) ||
      d.sectionTitle.toLowerCase().includes(query) ||
      d.content.toLowerCase().includes(query)
    ).slice(0, 15);

    if (matches.length === 0) {
      searchResults.innerHTML = '<div style="padding:1rem;color:var(--text-muted);">No results found.</div>';
      return;
    }

    matches.forEach(m => {
      const item = document.createElement('a');
      item.className = 'search-result-item';
      item.href = '#' + m.id;
      
      // Find snippet
      let snippet = m.content.replace(/#+/g, '').replace(/\\*+/g, '').slice(0, 140);
      const matchIdx = m.content.toLowerCase().indexOf(query);
      if (matchIdx > -1) {
        snippet = '...' + m.content.slice(Math.max(0, matchIdx - 40), matchIdx + 80) + '...';
      }

      item.innerHTML = \`
        <div class="search-result-title">\${m.title} <span style="font-size:0.75rem;color:var(--text-muted);">(\${m.sectionTitle})</span></div>
        <div class="search-result-snippet">\${snippet}</div>
      \`;
      item.addEventListener('click', () => {
        closeSearch();
      });
      searchResults.appendChild(item);
    });
  }

  // Hash change routing
  window.addEventListener('hashchange', () => {
    const rawHash = window.location.hash.slice(1);
    if (!rawHash.startsWith('heading-')) {
      loadDoc(rawHash);
    }
  });

  // Initial load
  const initialHash = window.location.hash.slice(1);
  loadDoc(initialHash || 'readme');
});
`;

fs.writeFileSync(path.join(distDir, 'app.js'), appJs, 'utf-8');
console.log('Generated dist/app.js');

console.log('Build completed successfully! Output ready in dist/');
