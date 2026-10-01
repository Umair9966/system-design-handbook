
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
      secTitle.innerHTML = `<span>${secData.title}</span> <span class="sec-count">${secData.items.length}</span>`;
      
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

    breadcrumb.textContent = `${doc.sectionTitle}  /  ${doc.title}`;
    readingTime.textContent = `⏱ ${doc.readingTime} min read`;
    document.title = `${doc.title} | System Design Handbook`;

    // Process markdown and handle Mermaid blocks
    let rawMd = doc.content;
    
    // Replace ```mermaid code blocks with <div class="mermaid">...</div>
    const mermaidRegex = /\\`\\`\\`mermaid\s*([\s\S]*?)\\`\\`\\`/g;
    const mermaidPlaceholders = [];
    rawMd = rawMd.replace(mermaidRegex, (match, code) => {
      const idx = mermaidPlaceholders.length;
      mermaidPlaceholders.push(code.trim());
      return `<!--MERMAID_${idx}-->`;
    });

    let renderedHtml = marked.parse(rawMd);

    // Restore Mermaid placeholders
    mermaidPlaceholders.forEach((code, idx) => {
      renderedHtml = renderedHtml.replace(
        `<!--MERMAID_${idx}-->`,
        `<div class="mermaid">${code}</div>`
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
      a.textContent = h.textContent.replace(/^\d+\.\s*/, '');
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
      let snippet = m.content.replace(/#+/g, '').replace(/\*+/g, '').slice(0, 140);
      const matchIdx = m.content.toLowerCase().indexOf(query);
      if (matchIdx > -1) {
        snippet = '...' + m.content.slice(Math.max(0, matchIdx - 40), matchIdx + 80) + '...';
      }

      item.innerHTML = `
        <div class="search-result-title">${m.title} <span style="font-size:0.75rem;color:var(--text-muted);">(${m.sectionTitle})</span></div>
        <div class="search-result-snippet">${snippet}</div>
      `;
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
