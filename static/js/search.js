/**
 * Search functionality for notebase-publish
 * Uses Fuse.js for fuzzy search (loaded from CDN)
 */

class SearchEngine {
    constructor() {
        this.index = null;
        this.fuse = null;
        this.input = null;
        this.resultsContainer = null;
        this.debounceTimer = null;
        this.loading = false;
    }

    async init() {
        this.input = document.getElementById('search-input');
        this.resultsContainer = document.querySelector('.search-results') 
            || document.getElementById('search-results');

        if (!this.input) return;

        // Load Fuse.js from CDN
        await this.loadFuse();
        
        // Load search index
        await this.loadIndex();
        
        // Initialize Fuse
        this.initFuse();
        
        // Bind events
        this.bindEvents();
        
        // If there's a query in URL, search immediately
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');
        if (query) {
            this.input.value = query;
            this.search(query);
        }
    }

    async loadFuse() {
        if (window.Fuse) return;
        
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    async loadIndex() {
        try {
            const response = await fetch('/search.json');
            if (!response.ok) throw new Error('Failed to load search index');
            this.index = await response.json();
            console.log(`Loaded search index: ${this.index.length} documents`);
        } catch (err) {
            console.error('Failed to load search index:', err);
            this.index = [];
        }
    }

    initFuse() {
        if (!this.index.length || !window.Fuse) return;
        
        this.fuse = new window.Fuse(this.index, {
            keys: [
                { name: 'title', weight: 3 },
                { name: 'tags', weight: 2 },
                { name: 'content', weight: 1 }
            ],
            threshold: 0.4,
            includeScore: true,
            includeMatches: true,
            minMatchCharLength: 2,
            ignoreLocation: true,
            findAllMatches: true
        });
    }

    bindEvents() {
        if (!this.input) return;

        // Input with debounce
        this.input.addEventListener('input', (e) => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.search(e.target.value.trim());
            }, 150);
        });

        // Focus on '/' key
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && 
                document.activeElement !== this.input &&
                document.activeElement.tagName !== 'INPUT' &&
                document.activeElement.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.input.focus();
            }
        });

        // Escape to clear
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.input.value = '';
                this.input.blur();
                this.clearResults();
            }
        });

        // Enter to submit (handled by form on search.html)
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = this.input.value.trim();
                if (query) {
                    const form = this.input.closest('form');
                    if (form) {
                        form.submit();
                    } else {
                        window.location.href = `/search.html?q=${encodeURIComponent(query)}`;
                    }
                }
            }
        });
    }

    search(query) {
        if (!query || query.length < 1) {
            this.clearResults();
            return;
        }

        if (!this.fuse) {
            this.renderMessage('Search index not ready...');
            return;
        }

        const results = this.fuse.search(query);
        this.renderResults(results, query);
    }

    renderResults(results, query) {
        if (!this.resultsContainer) return;

        if (!results.length) {
            this.renderMessage(`No results for <strong>"${this.escapeHtml(query)}"</strong>. Try different keywords.`);
            return;
        }

        const html = results.slice(0, 20).map(result => this.renderResultItem(result.item, query)).join('');
        this.resultsContainer.innerHTML = html;
    }

    renderResultItem(item, query) {
        const title = this.highlight(item.title, query);
        const excerpt = this.highlight(this.getExcerpt(item, query), query);
        const tagHtml = item.tags?.slice(0, 5).map(tag => 
            `<span class="tag-tag">#${this.escapeHtml(tag)}</span>`
        ).join('') || '';
        
        const dateHtml = item.created 
            ? `<time datetime="${item.created}">${item.created.slice(0, 10)}</time>` 
            : '';

        return `
            <li class="search-result">
                <h3 class="search-result-title">
                    <a href="${item.url}">${title}</a>
                </h3>
                <p class="search-result-excerpt">${excerpt}</p>
                <div class="search-result-meta">
                    ${tagHtml ? `<span class="tags">${tagHtml}</span>` : ''}
                    ${dateHtml}
                </div>
            </li>
        `;
    }

    getExcerpt(item, query) {
        // Prefer matched content, fallback to stored excerpt
        if (item.matches && item.matches[0]?.indices) {
            const match = item.matches[0];
            const start = Math.max(0, match.indices[0][0] - 100);
            const end = Math.min(item.content.length, match.indices[match.indices.length - 1][1] + 100);
            return item.content.slice(start, end);
        }
        return item.excerpt || item.content.slice(0, 300);
    }

    highlight(text, query) {
        if (!query || !text) return this.escapeHtml(text);
        
        const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 1);
        if (!words.length) return this.escapeHtml(text);
        
        let html = this.escapeHtml(text);
        const regex = new RegExp(`(${words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
        
        return html.replace(regex, '<mark class="search-highlight">$1</mark>');
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    renderMessage(html) {
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = `
                <li class="empty-state">
                    ${html}
                </li>
            `;
        }
    }

    clearResults() {
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = '';
        }
    }
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.searchEngine = new SearchEngine();
    window.searchEngine.init();
});

// Export for manual use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchEngine;
}