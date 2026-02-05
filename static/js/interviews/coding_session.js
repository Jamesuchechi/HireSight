/**
 * Coding Session Manager
 * Handles Monaco Editor, Real-time Sync, and Code Execution
 */
class CodingSession {
    constructor(config) {
        this.config = config;
        this.editor = null;
        this.ws = null; // WebSocket reference
        this.isSilentUpdate = false; // Flag to prevent echo loops
        this.saveInterval = null;
        this.language = 'python';

        // DOM Elements
        this.panel = document.getElementById('code-panel');
        this.editorContainer = document.getElementById('code-editor');
        this.outputContainer = document.getElementById('code-output');
        this.toggleBtn = document.getElementById('toggle-code-btn');
        this.runBtn = document.getElementById('run-code-btn');
        this.langSelect = document.getElementById('language-select');
        this.statusEl = document.getElementById('code-status');

        this.boilerplates = {
            'python': "# Write your Python code here\nprint('Hello, Interview!')",
            'javascript': "// Write your Node.js code here\nconsole.log('Hello, Interview!');",
            'rust': "// Write your Rust code here\nfn main() {\n    println!(\"Hello, Interview!\");\n}",
            'go': "// Write your Go code here\npackage main\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, Interview!\")\n}",
            'cpp': "// Write your C++ code here\n#include <iostream>\nint main() {\n    std::cout << \"Hello, Interview!\" << std::endl;\n    return 0;\n}",
            'php': "<?php\n// Write your PHP code here\necho \"Hello, Interview!\";\n?>",
            'ruby': "# Write your Ruby code here\nputs 'Hello, Interview!'"
        };

        this.init();
    }

    async init() {
        if (!this.panel) return;

        // Initialize Monaco Editor
        await this.initMonaco();

        // Event Listeners
        this.toggleBtn.addEventListener('click', () => this.togglePanel());
        this.runBtn.addEventListener('click', () => this.runCode());
        this.langSelect.addEventListener('change', (e) => this.setLanguage(e.target.value));

        // Auto-save every 30 seconds
        this.saveInterval = setInterval(() => this.saveSnapshot(), 30000);
    }

    setWebSocket(ws) {
        this.ws = ws;
    }

    async initMonaco() {
        return new Promise((resolve) => {
            require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs' } });
            require(['vs/editor/editor.main'], () => {
                this.editor = monaco.editor.create(this.editorContainer, {
                    value: this.boilerplates[this.language] || '',
                    language: 'python',
                    theme: 'vs-dark',
                    minimap: { enabled: false },
                    fontSize: 14,
                    automaticLayout: true
                });

                // Add change listener for Sync
                this.editor.onDidChangeModelContent((e) => {
                    if (!this.isSilentUpdate) {
                        this.broadcastUpdate();
                    }
                });

                resolve();
            });
        });
    }

    togglePanel() {
        this.panel.classList.toggle('hidden');
        this.toggleBtn.classList.toggle('bg-blue-600');
        this.toggleBtn.classList.toggle('text-white');

        if (!this.panel.classList.contains('hidden')) {
            // Resize editor when shown
            if (this.editor) this.editor.layout();
        }
    }

    setLanguage(lang) {
        const oldLang = this.language;
        this.language = lang;
        if (this.editor) {
            monaco.editor.setModelLanguage(this.editor.getModel(), lang);

            // If current content is a boilerplate, swap it
            const currentCode = this.editor.getValue();
            if (Object.values(this.boilerplates).includes(currentCode) || currentCode.trim() === '') {
                this.editor.setValue(this.boilerplates[lang]);
            }

            this.broadcastUpdate(); // Sync language change
        }
    }

    broadcastUpdate() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        const code = this.editor.getValue();
        this.ws.send(JSON.stringify({
            'type': 'code_update',
            'code': code,
            'language': this.language,
            'from_user': this.config.userEmail
        }));
    }

    handleRemoteUpdate(data) {
        if (!this.editor) return;

        // Ignore own updates (should be handled by sender check in consumer, but safety net)
        if (data.from_user === this.config.userEmail) return;

        this.statusEl.textContent = `${data.from_user} is typing...`;
        this.isSilentUpdate = true;

        // Create full edit operation to preserve cursor if possible or just replace
        // Simple replace for now
        const currentPos = this.editor.getPosition();
        this.editor.setValue(data.code);
        this.editor.setPosition(currentPos);

        if (data.language && data.language !== this.language) {
            this.language = data.language;
            this.langSelect.value = data.language;
            monaco.editor.setModelLanguage(this.editor.getModel(), data.language);
        }

        this.isSilentUpdate = false;

        setTimeout(() => {
            this.statusEl.textContent = 'Ready';
        }, 1000);
    }

    async runCode() {
        if (!this.editor) return;

        const code = this.editor.getValue();
        this.runBtn.disabled = true;
        this.runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        this.outputContainer.innerHTML = '<div class="text-gray-400">Executing...</div>';

        try {
            const response = await fetch('/interviews/execute-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify({
                    'interview_id': this.config.id,
                    'code': code,
                    'language': this.language
                })
            });

            const result = await response.json();

            if (result.success) {
                this.outputContainer.innerHTML = `<pre class="text-green-400">${result.output || 'No output'}</pre>`;
            } else {
                this.outputContainer.innerHTML = `<pre class="text-red-400">${result.error || 'Unknown error'}</pre>`;
            }
        } catch (err) {
            this.outputContainer.innerHTML = `<div class="text-red-500">Network Error: ${err.message}</div>`;
        } finally {
            this.runBtn.disabled = false;
            this.runBtn.innerHTML = '<i class="fas fa-play text-xs"></i> Run';
        }
    }

    async saveSnapshot() {
        if (!this.editor) return;

        const code = this.editor.getValue();
        try {
            await fetch(`/interviews/coding-session/${this.config.id}/save/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify({
                    'code': code,
                    'language': this.language
                })
            });
            console.log('Code snapshot saved');
        } catch (e) {
            console.error('Failed to save code snapshot', e);
        }
    }
}
