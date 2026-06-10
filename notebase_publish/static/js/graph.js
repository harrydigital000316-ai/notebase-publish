/**
 * Knowledge Graph visualization for notebase-publish
 * Uses Cytoscape.js (loaded from CDN)
 */

class KnowledgeGraph {
    constructor() {
        this.cy = null;
        this.graphData = null;
        this.legendContainer = null;
        this.infoPanel = null;
        this.colorMap = {};
    }

    async init() {
        // Load Cytoscape.js from CDN
        await this.loadCytoscape();
        
        // Load graph data
        await this.loadGraphData();
        
        // Initialize Cytoscape
        this.initCytoscape();
        
        // Build legend
        this.buildLegend();
        
        // Setup events
        this.bindEvents();
    }

    async loadCytoscape() {
        if (window.cytoscape) return;
        
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    async loadGraphData() {
        try {
            const response = await fetch('/graph.json');
            if (!response.ok) throw new Error('Failed to load graph data');
            this.graphData = await response.json();
            console.log(`Loaded graph: ${this.graphData.nodes.length} nodes, ${this.graphData.edges.length} edges`);
        } catch (err) {
            console.error('Failed to load graph data:', err);
            this.graphData = { nodes: [], edges: [] };
        }
        
        // Build color map from tag_colors if available
        try {
            const response = await fetch('/tags.json');
            if (response.ok) {
                const tags = await response.json();
                // We'll use the colors from the graph data itself
            }
        } catch (err) {
            // Ignore
        }
    }

    initCytoscape() {
        const container = document.getElementById('graph-container');
        if (!container || !this.graphData?.nodes?.length) {
            this.renderEmpty();
            return;
        }

        // Prepare elements
        const elements = [
            ...this.graphData.nodes.map(n => ({
                data: {
                    id: n.id,
                    label: n.label,
                    title: n.title,
                    group: n.group,
                    color: n.color,
                    url: n.url
                }
            })),
            ...this.graphData.edges.map(e => ({
                data: {
                    id: `e-${e.from}-${e.to}`,
                    source: e.from,
                    target: e.to
                }
            }))
        ];

        // Initialize Cytoscape
        this.cy = window.cytoscape({
            container,
            elements,
            style: this.getStylesheet(),
            layout: {
                name: 'cose',
                animate: true,
                animationDuration: 1000,
                nodeRepulsion: 400000,
                nodeOverlap: 20,
                idealEdgeLength: 100,
                edgeElasticity: 100,
                nestingFactor: 5,
                gravity: 80,
                numIter: 1000,
                tile: true,
                fit: true,
                padding: 50,
                randomize: false,
                componentSpacing: 100
            },
            minZoom: 0.1,
            maxZoom: 3,
            zoomingEnabled: true,
            userZoomingEnabled: true,
            panningEnabled: true,
            boxSelectionEnabled: true,
            selectionType: 'single' // single selection like click
        });

        // Update stats
        this.updateStats();

        // Fit to view after layout
        this.cy.on('layoutstop', () => {
            this.cy.fit(null, 50);
        });

        // Make globally accessible
        window.cytoscapeGraph = this.cy;
    }

    getStylesheet() {
        return [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'font-size': '11px',
                    'font-family': 'JetBrains Mono, monospace',
                    'font-weight': 500,
                    'color': '#fff',
                    'text-outline-color': '#000',
                    'text-outline-width': 2,
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': 'data(color)',
                    'width': 'mapData(degree, 0, 50, 20, 50)',
                    'height': 'mapData(degree, 0, 50, 20, 50)',
                    'border-width': 2,
                    'border-color': '#fff',
                    'border-opacity': 0.8,
                    'overlay-padding': '6px',
                    'z-index': 1
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': '#666',
                    'target-arrow-shape': 'none',
                    'curve-style': 'haystack',
                    'opacity': 0.4
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#fbbf24',
                    'border-opacity': 1,
                    'z-index': 999,
                    'overlay-padding': '10px',
                    'shadow-color': '#fbbf24',
                    'shadow-blur': 10,
                    'shadow-opacity': 0.5
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'border-width': 4,
                    'border-color': '#22c55e',
                    'border-opacity': 1,
                    'z-index': 999,
                    'overlay-padding': '10px'
                }
            },
            {
                selector: 'node.inactive',
                style: {
                    'opacity': 0.15
                }
            },
            {
                selector: 'edge.inactive',
                style: {
                    'opacity': 0.05
                }
            },
            {
                selector: '.parent',
                style: {
                    'background-opacity': 0.1,
                    'border-width': 1,
                    'border-style': 'dashed',
                    'border-color': '#888'
                }
            }
        ];
    }

    buildLegend() {
        this.legendContainer = document.getElementById('legend-items');
        if (!this.legendContainer) return;

        // Build color map from nodes
        const groups = {};
        this.graphData?.nodes?.forEach(node => {
            const group = node.group || 'untagged';
            if (!groups[group]) {
                groups[group] = node.color || '#888';
            }
        });

        this.colorMap = groups;

        const itemsHtml = Object.entries(groups)
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([group, color]) => `
                <div class="legend-item">
                    <span class="legend-color" style="background: ${color}"></span>
                    <span>#${this.escapeHtml(group)}</span>
                </div>
            `).join('');

        this.legendContainer.innerHTML = itemsHtml || '<span class="legend-item">No tags found</span>';
    }

    updateStats() {
        const nodeCountEl = document.getElementById('node-count');
        const edgeCountEl = document.getElementById('edge-count');
        
        if (nodeCountEl) nodeCountEl.textContent = `${this.cy?.nodes().length || 0} nodes`;
        if (edgeCountEl) edgeCountEl.textContent = `${this.cy?.edges().length || 0} edges`;
    }

    bindEvents() {
        if (!this.cy) return;

        // Node click - show info
        this.cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            this.showNodeInfo(node);
            
            // Highlight connected nodes
            this.highlightConnections(node);
        });

        // Background click - clear selection
        this.cy.on('tap', (evt) => {
            if (evt.target === this.cy) {
                this.clearHighlight();
                this.hideNodeInfo();
            }
        });

        // Hover effects
        this.cy.on('mouseover', 'node', (evt) => {
            evt.target.addClass('highlighted');
        });

        this.cy.on('mouseout', 'node', (evt) => {
            evt.target.removeClass('highlighted');
        });

        // Double click to open note
        this.cy.on('dbltap', 'node', (evt) => {
            const url = evt.target.data('url');
            if (url) {
                window.open(url, '_blank');
            }
        });

        // Keyboard: Escape to clear
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearHighlight();
                this.hideNodeInfo();
            }
        });
    }

    showNodeInfo(node) {
        this.infoPanel = document.getElementById('node-info');
        const titleEl = document.getElementById('info-title');
        const tagsEl = document.getElementById('info-tags');
        const linkEl = document.getElementById('info-link');

        if (!this.infoPanel || !titleEl) return;

        titleEl.textContent = node.data('label') || node.id();
        
        // Build tags
        const group = node.data('group');
        if (tagsEl) {
            if (group && group !== 'untagged') {
                tagsEl.innerHTML = `<span class="tag-tag">#${group}</span>`;
            } else {
                tagsEl.innerHTML = '<span class="tag-tag" style="background: var(--bg-tertiary); color: var(--fg-tertiary);">untagged</span>';
            }
        }

        if (linkEl) {
            const url = node.data('url');
            if (url) {
                linkEl.href = url;
                linkEl.textContent = 'Open Note →';
                linkEl.style.display = 'inline-flex';
            } else {
                linkEl.style.display = 'none';
            }
        }

        this.infoPanel.classList.remove('hidden');
    }

    hideNodeInfo() {
        if (this.infoPanel) {
            this.infoPanel.classList.add('hidden');
        }
    }

    highlightConnections(node) {
        // Mark all as inactive
        this.cy.nodes().addClass('inactive');
        this.cy.edges().addClass('inactive');

        // Highlight this node and its neighbors
        node.removeClass('inactive');
        node.neighborhood().removeClass('inactive');
        node.connectedEdges().removeClass('inactive');
    }

    clearHighlight() {
        this.cy.nodes().removeClass('inactive highlighted');
        this.cy.edges().removeClass('inactive');
        this.hideNodeInfo();
    }

    renderEmpty() {
        const container = document.getElementById('graph-container');
        if (container) {
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--fg-tertiary); text-align: center; padding: 2rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🕸️</div>
                    <h3>No graph data available</h3>
                    <p>Build the site with notes containing wiki-links to generate the graph.</p>
                </div>
            `;
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    // Only init on graph.html page
    if (document.getElementById('graph-container')) {
        window.knowledgeGraph = new KnowledgeGraph();
        window.knowledgeGraph.init();
    }
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = KnowledgeGraph;
}