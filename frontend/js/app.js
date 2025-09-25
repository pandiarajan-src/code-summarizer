// Code Summarizer Frontend Application

class CodeSummarizerApp {
    constructor() {
        try {
            this.apiConfig = window.API_CONFIG;
            this.selectedFiles = [];
            this.analysisResult = null;

            this.initializeElements();
            this.bindEvents();
            this.initializeApp();
        } catch (error) {
            console.error('Error in CodeSummarizerApp constructor:', error);
            throw error;
        }
    }

    initializeElements() {
        // Main elements
        this.fileInput = document.getElementById('fileInput');
        this.fileInfo = document.getElementById('fileInfo');
        this.analyzeBtn = document.getElementById('analyzeBtn');

        if (this.analyzeBtn) {
            this.btnText = this.analyzeBtn.querySelector('.btn-text');
            this.btnLoader = this.analyzeBtn.querySelector('.btn-loader');
        }

        // Options
        this.extractArchives = document.getElementById('extractArchives');
        this.verboseOutput = document.getElementById('verboseOutput');

        // Progress elements
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.uploadIcon = document.getElementById('uploadIcon');
        this.analyzeIcon = document.getElementById('analyzeIcon');

        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.markdownPreview = document.getElementById('markdownPreview');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.clearBtn = document.getElementById('clearBtn');

        // Modal elements
        this.supportedLangsLink = document.getElementById('supportedLangsLink');
        this.supportedLangsModal = document.getElementById('supportedLangsModal');
        this.supportedLangsList = document.getElementById('supportedLangsList');
        this.closeModal = document.getElementById('closeModal');

        // Theme toggle
        this.darkModeToggle = document.getElementById('darkModeToggle');

        // API version
        this.apiVersion = document.getElementById('apiVersion');

        // Prompt editor elements
        this.togglePromptEditor = document.getElementById('togglePromptEditor');
        this.promptEditorContainer = document.getElementById('promptEditorContainer');
        this.promptTabs = document.querySelectorAll('.prompt-tab');
        this.promptEditor = document.getElementById('promptEditor');
        this.promptLabelText = document.getElementById('promptLabelText');
        this.promptCharCount = document.getElementById('promptCharCount');
        this.promptStatus = document.getElementById('promptStatus');
        this.resetPromptBtn = document.getElementById('resetPromptBtn');
        this.resetAllPromptsBtn = document.getElementById('resetAllPromptsBtn');
    }

    bindEvents() {
        // File input events
        this.fileInput.addEventListener('change', (e) => this.handleFileSelection(e));

        // Button events
        this.analyzeBtn.addEventListener('click', () => this.analyzeFiles());
        this.downloadBtn.addEventListener('click', () => this.downloadResults());
        this.clearBtn.addEventListener('click', () => this.clearResults());

        // Modal events
        this.supportedLangsLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.showSupportedLanguages();
        });
        this.closeModal.addEventListener('click', () => this.closeSupportedLanguagesModal());
        this.supportedLangsModal.addEventListener('click', (e) => {
            if (e.target === this.supportedLangsModal) {
                this.closeSupportedLanguagesModal();
            }
        });

        // Theme toggle events
        if (this.darkModeToggle) {
            this.darkModeToggle.addEventListener('change', () => {
                this.toggleTheme();
            });
        }

        // Prompt editor events with robust binding
        const bindToggleEvent = () => {
            const toggleElement = document.getElementById('togglePromptEditor');
            if (toggleElement) {
                toggleElement.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.togglePromptEditorVisibility();
                });
            }
        };

        // Try immediate binding
        bindToggleEvent();

        // Also add document delegation as fallback
        document.addEventListener('click', (e) => {
            if (e.target && (e.target.id === 'togglePromptEditor' || e.target.closest('#togglePromptEditor'))) {
                e.preventDefault();
                e.stopPropagation();
                this.togglePromptEditorVisibility();
            }
        });

        if (this.promptTabs) {
            this.promptTabs.forEach(tab => {
                tab.addEventListener('click', (e) => this.switchPromptTab(e.target.dataset.prompt));
            });
        }

        if (this.promptEditor) {
            this.promptEditor.addEventListener('input', () => this.updatePromptStatus());
        }

        if (this.resetPromptBtn) {
            this.resetPromptBtn.addEventListener('click', () => this.resetCurrentPrompt());
        }

        if (this.resetAllPromptsBtn) {
            this.resetAllPromptsBtn.addEventListener('click', () => this.resetAllPrompts());
        }

        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSupportedLanguagesModal();
            }
        });
    }

    async initializeApp() {
        try {
            // Initialize theme
            this.initializeTheme();

            // Initialize prompts
            await this.initializePrompts();

            await this.checkApiHealth();
            this.loadApiVersion();
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to connect to API. Please check if the server is running.');
        }
    }

    async checkApiHealth() {
        try {
            const response = await fetch(`${this.apiConfig.baseUrl}${this.apiConfig.endpoints.health}`);
            if (!response.ok) {
                throw new Error('API health check failed');
            }
            return await response.json();
        } catch (error) {
            throw new Error(`API connection failed: ${error.message}`);
        }
    }

    async loadApiVersion() {
        try {
            const health = await this.checkApiHealth();
            const version = health.version || 'Unknown';
            this.apiVersion.textContent = `API v${version}`;
        } catch (error) {
            this.apiVersion.textContent = 'API Offline';
            this.apiVersion.style.color = '#dc3545';
        }
    }

    handleFileSelection(event) {
        const files = Array.from(event.target.files);
        this.selectedFiles = files;

        if (files.length === 0) {
            this.fileInfo.textContent = 'No files selected';
            this.analyzeBtn.disabled = true;
            return;
        }

        // Update file info
        if (files.length === 1) {
            this.fileInfo.textContent = `Selected: ${files[0].name}`;
        } else {
            this.fileInfo.textContent = `Selected: ${files.length} files`;
        }

        // Enable analyze button
        this.analyzeBtn.disabled = false;

        // Reset progress
        this.resetProgress();
    }

    async analyzeFiles() {
        if (this.selectedFiles.length === 0) {
            this.showError('Please select files to analyze');
            return;
        }

        try {
            this.setAnalyzeButtonLoading(true);
            this.resetProgress();

            // Determine if this should be batch analysis
            const isBatchAnalysis = this.selectedFiles.length > 1 ||
                                   this.selectedFiles.some(file => file.name.endsWith('.zip'));

            // Start upload progress
            this.updateProgress(10, 'Uploading files...', 'upload');

            // Create form data
            const formData = new FormData();
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            // Add options
            formData.append('extract_archives', this.extractArchives.checked);
            formData.append('verbose', this.verboseOutput.checked);
            formData.append('output_format', 'markdown');

            // Add custom prompts if any are configured
            const customPrompts = this.getCustomPrompts();
            if (customPrompts) {
                formData.append('custom_prompts', JSON.stringify(customPrompts));
            }

            if (isBatchAnalysis) {
                formData.append('force_batch', 'true');
            }

            // Choose endpoint
            const endpoint = isBatchAnalysis ?
                this.apiConfig.endpoints.batchAnalyze :
                this.apiConfig.endpoints.analyze;

            // Upload and analyze
            this.updateProgress(30, 'Files uploaded, starting analysis...', 'analyze');

            const response = await fetch(`${this.apiConfig.baseUrl}${endpoint}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            // Analysis progress
            this.updateProgress(70, 'Processing analysis...', 'analyze');

            const result = await response.json();
            this.analysisResult = result;

            // Complete progress
            this.updateProgress(100, 'Analysis complete!', 'complete');

            // Display results
            this.displayResults(result);

        } catch (error) {
            console.error('Analysis failed:', error);
            this.showError(`Analysis failed: ${error.message}`);
            this.updateProgress(0, 'Analysis failed', 'error');
        } finally {
            this.setAnalyzeButtonLoading(false);
        }
    }

    displayResults(result) {
        // Show results section
        this.resultsSection.style.display = 'block';

        // Display markdown content
        let markdownContent = '';

        if (result.markdown_output) {
            markdownContent = result.markdown_output;
        } else if (result.project_summary) {
            markdownContent = `# Analysis Summary\n\n${result.project_summary}`;
        } else {
            markdownContent = '# Analysis Complete\n\nNo markdown output available.';
        }

        // Add metadata
        const metadata = this.generateMetadata(result);
        markdownContent = metadata + '\n\n' + markdownContent;

        // Convert markdown to HTML
        const htmlContent = marked.parse(markdownContent);
        const sanitizedContent = DOMPurify.sanitize(htmlContent);

        this.markdownPreview.innerHTML = sanitizedContent;

        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    generateMetadata(result) {
        const metadata = [
            '# Code Analysis Report',
            '',
            '## Analysis Metadata',
            `- **Analysis ID**: ${result.analysis_id || result.batch_analysis_id || 'N/A'}`,
            `- **Timestamp**: ${new Date(result.timestamp).toLocaleString()}`,
            `- **Files Analyzed**: ${result.files_analyzed || result.total_files_analyzed || 0}`,
            `- **Total Processing Time**: ${(result.total_processing_time_seconds || 0).toFixed(2)} seconds`,
            `- **Tokens Used**: ${result.total_tokens_used || 0}`,
            ''
        ];

        if (result.total_batches) {
            metadata.splice(-1, 0, `- **Total Batches**: ${result.total_batches}`);
        }

        return metadata.join('\n');
    }

    downloadResults() {
        if (!this.analysisResult) {
            this.showError('No analysis results to download');
            return;
        }

        try {
            let content = '';
            let filename = 'code-analysis-report.md';

            if (this.analysisResult.markdown_output) {
                content = this.analysisResult.markdown_output;
            } else {
                // Create markdown from the analysis result
                content = this.generateDownloadableMarkdown(this.analysisResult);
            }

            // Add metadata to the beginning
            const metadata = this.generateMetadata(this.analysisResult);
            content = metadata + '\n\n' + content;

            // Create and download file
            const blob = new Blob([content], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showSuccess('Report downloaded successfully!');
        } catch (error) {
            console.error('Download failed:', error);
            this.showError('Failed to download report');
        }
    }

    generateDownloadableMarkdown(result) {
        const sections = [];

        if (result.project_summary) {
            sections.push('## Project Summary');
            sections.push(result.project_summary);
            sections.push('');
        }

        if (result.batch_results && result.batch_results.length > 0) {
            sections.push('## Batch Analysis Results');
            result.batch_results.forEach((batch, index) => {
                sections.push(`### Batch ${index + 1}`);
                if (batch.summary) {
                    sections.push(batch.summary);
                }
                if (batch.files && batch.files.length > 0) {
                    sections.push('**Files in this batch:**');
                    batch.files.forEach(file => {
                        sections.push(`- ${file.filename || file}`);
                    });
                }
                sections.push('');
            });
        }

        return sections.join('\n');
    }

    clearResults() {
        this.resultsSection.style.display = 'none';
        this.markdownPreview.innerHTML = '';
        this.analysisResult = null;
        this.resetProgress();

        // Clear file selection
        this.fileInput.value = '';
        this.selectedFiles = [];
        this.fileInfo.textContent = 'No files selected';
        this.analyzeBtn.disabled = true;
    }

    async showSupportedLanguages() {
        try {
            this.supportedLangsList.textContent = 'Loading...';
            this.supportedLangsModal.style.display = 'flex';

            const response = await fetch(`${this.apiConfig.baseUrl}${this.apiConfig.endpoints.supportedTypes}`);

            if (!response.ok) {
                throw new Error('Failed to fetch supported types');
            }

            const data = await response.json();
            const extensions = data.supported_extensions || [];

            // Group extensions by type
            const grouped = this.groupExtensionsByType(extensions);

            let html = '<div class="supported-languages">';

            for (const [category, exts] of Object.entries(grouped)) {
                html += `<div class="language-category">`;
                html += `<h4>${category}</h4>`;
                html += `<div class="language-tags">`;
                exts.forEach(ext => {
                    html += `<span class="language-tag">${ext}</span>`;
                });
                html += `</div></div>`;
            }

            html += '</div>';
            html += `<p><strong>Note:</strong> ${data.note || 'ZIP archives are also supported and will be automatically extracted'}</p>`;

            this.supportedLangsList.innerHTML = html;

        } catch (error) {
            console.error('Failed to load supported languages:', error);
            this.supportedLangsList.innerHTML = '<p>Failed to load supported languages. Please try again later.</p>';
        }
    }

    groupExtensionsByType(extensions) {
        const groups = {
            'Web Development': ['.html', '.css', '.js', '.ts', '.jsx', '.tsx', '.vue', '.php'],
            'Systems Programming': ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.rs', '.go'],
            'Application Development': ['.java', '.cs', '.kt', '.swift', '.py', '.rb'],
            'Functional Programming': ['.scala', '.clj', '.hs', '.ml', '.elm'],
            'Data & Scripting': ['.r', '.m', '.sql', '.sh', '.ps1', '.bat'],
            'Configuration & Data': ['.json', '.yaml', '.yml', '.xml', '.toml', '.ini'],
            'Documentation': ['.md', '.rst', '.txt'],
            'Archives': ['.zip']
        };

        const result = {};
        const ungrouped = [];

        // Group extensions
        for (const ext of extensions) {
            let grouped = false;
            for (const [category, categoryExts] of Object.entries(groups)) {
                if (categoryExts.includes(ext)) {
                    if (!result[category]) result[category] = [];
                    result[category].push(ext);
                    grouped = true;
                    break;
                }
            }
            if (!grouped) {
                ungrouped.push(ext);
            }
        }

        // Add ungrouped extensions
        if (ungrouped.length > 0) {
            result['Other'] = ungrouped;
        }

        return result;
    }

    closeSupportedLanguagesModal() {
        this.supportedLangsModal.style.display = 'none';
    }

    updateProgress(percentage, message, stage) {
        this.progressFill.style.width = `${percentage}%`;
        this.progressText.textContent = message;

        // Update icons
        this.uploadIcon.textContent = '⏳';
        this.analyzeIcon.textContent = '⏳';

        const uploadStep = this.uploadIcon.parentElement.querySelector('.step-text');
        const analyzeStep = this.analyzeIcon.parentElement.querySelector('.step-text');

        switch (stage) {
            case 'upload':
                this.uploadIcon.textContent = '🔄';
                uploadStep.textContent = 'Upload: In Progress';
                analyzeStep.textContent = 'Analysis: Waiting';
                break;
            case 'analyze':
                this.uploadIcon.textContent = '✅';
                this.uploadIcon.classList.add('step-success');
                this.analyzeIcon.textContent = '🔄';
                uploadStep.textContent = 'Upload: Complete';
                analyzeStep.textContent = 'Analysis: In Progress';
                break;
            case 'complete':
                this.uploadIcon.textContent = '✅';
                this.analyzeIcon.textContent = '✅';
                this.uploadIcon.classList.add('step-success');
                this.analyzeIcon.classList.add('step-success');
                uploadStep.textContent = 'Upload: Complete';
                analyzeStep.textContent = 'Analysis: Complete';
                break;
            case 'error':
                this.uploadIcon.textContent = '❌';
                this.analyzeIcon.textContent = '❌';
                this.uploadIcon.classList.add('step-error');
                this.analyzeIcon.classList.add('step-error');
                uploadStep.textContent = 'Upload: Failed';
                analyzeStep.textContent = 'Analysis: Failed';
                break;
        }
    }

    resetProgress() {
        this.progressFill.style.width = '0%';
        this.progressText.textContent = 'Ready to upload';

        // Reset icons
        this.uploadIcon.textContent = '⏳';
        this.analyzeIcon.textContent = '⏳';
        this.uploadIcon.classList.remove('step-success', 'step-error', 'step-warning');
        this.analyzeIcon.classList.remove('step-success', 'step-error', 'step-warning');

        const uploadStep = this.uploadIcon.parentElement.querySelector('.step-text');
        const analyzeStep = this.analyzeIcon.parentElement.querySelector('.step-text');
        uploadStep.textContent = 'Upload: Ready';
        analyzeStep.textContent = 'Analysis: Waiting';
    }

    setAnalyzeButtonLoading(loading) {
        if (loading) {
            this.analyzeBtn.disabled = true;
            this.btnText.style.display = 'none';
            this.btnLoader.style.display = 'inline-block';
        } else {
            this.analyzeBtn.disabled = false;
            this.btnText.style.display = 'inline-block';
            this.btnLoader.style.display = 'none';
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem 2rem',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '600',
            zIndex: '9999',
            maxWidth: '400px',
            boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });

        // Set background color based on type
        switch (type) {
            case 'error':
                notification.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
                break;
            case 'success':
                notification.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
                break;
            default:
                notification.style.background = 'linear-gradient(135deg, #007bff, #0056b3)';
        }

        // Add to DOM
        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 4000);

        // Allow manual dismissal
        notification.addEventListener('click', () => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
    }

    // Theme Management Methods
    initializeTheme() {
        try {
            // Check for saved theme preference, default to dark mode
            const savedTheme = localStorage.getItem('theme') || 'dark';

            // Set the initial theme
            this.setTheme(savedTheme);

            // Update toggle state if element exists
            if (this.darkModeToggle) {
                this.darkModeToggle.checked = savedTheme === 'dark';
            }
        } catch (error) {
            console.error('Error initializing theme:', error);
        }
    }

    toggleTheme() {
        try {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            this.setTheme(newTheme);

            // Save preference
            localStorage.setItem('theme', newTheme);

            // Update toggle state
            if (this.darkModeToggle) {
                this.darkModeToggle.checked = newTheme === 'dark';
            }
        } catch (error) {
            console.error('Error toggling theme:', error);
        }
    }

    setTheme(theme) {
        try {
            // Always remove first, then set if dark
            document.documentElement.removeAttribute('data-theme');

            if (theme === 'dark') {
                document.documentElement.setAttribute('data-theme', 'dark');
            }

            // Force a style recalculation
            document.documentElement.offsetHeight;

            // Add smooth transition class temporarily
            document.documentElement.style.transition = 'color 0.3s ease, background-color 0.3s ease';

            // Remove transition after animation completes
            setTimeout(() => {
                document.documentElement.style.transition = '';
            }, 300);
        } catch (error) {
            console.error('Error in setTheme:', error);
        }
    }

    // Prompt Management Methods
    async initializePrompts() {
        try {
            // Load default prompts from API
            await this.loadDefaultPrompts();

            // Initialize current prompt type
            this.currentPromptType = 'single_file_analysis';

            // Initialize user prompts from localStorage or defaults
            this.userPrompts = this.loadUserPrompts();

            // Display initial prompt
            this.displayCurrentPrompt();
        } catch (error) {
            console.error('Failed to initialize prompts:', error);
            this.showError('Failed to load prompts. Using fallback defaults.');
        }
    }

    async loadDefaultPrompts() {
        try {
            const response = await fetch(`${this.apiConfig.baseUrl}${this.apiConfig.endpoints.prompts}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch prompts: ${response.status}`);
            }
            const data = await response.json();
            this.defaultPrompts = data.prompts;
        } catch (error) {
            console.error('Error loading default prompts:', error);
            // Fallback to empty prompts
            this.defaultPrompts = {
                single_file_analysis: 'Default single file analysis prompt not available.',
                batch_analysis: 'Default batch analysis prompt not available.',
                language_detection: 'Default language detection prompt not available.',
                project_summary: 'Default project summary prompt not available.'
            };
        }
    }

    loadUserPrompts() {
        try {
            const stored = localStorage.getItem('customPrompts');
            return stored ? JSON.parse(stored) : {};
        } catch (error) {
            console.error('Error loading user prompts from localStorage:', error);
            return {};
        }
    }

    saveUserPrompts() {
        try {
            localStorage.setItem('customPrompts', JSON.stringify(this.userPrompts));
        } catch (error) {
            console.error('Error saving user prompts to localStorage:', error);
        }
    }

    togglePromptEditorVisibility() {
        // Ensure we have the required elements
        if (!this.promptEditorContainer) {
            this.promptEditorContainer = document.getElementById('promptEditorContainer');
        }
        if (!this.togglePromptEditor) {
            this.togglePromptEditor = document.getElementById('togglePromptEditor');
        }

        if (!this.promptEditorContainer || !this.togglePromptEditor) {
            console.error('Required elements for prompt editor toggle not found');
            return;
        }

        const isVisible = this.promptEditorContainer.style.display !== 'none';

        if (isVisible) {
            this.promptEditorContainer.style.display = 'none';
            this.togglePromptEditor.innerHTML = `
                <span class="toggle-text">Show Prompts</span>
                <span class="toggle-icon">▼</span>
            `;
        } else {
            this.promptEditorContainer.style.display = 'block';
            this.togglePromptEditor.innerHTML = `
                <span class="toggle-text">Hide Prompts</span>
                <span class="toggle-icon">▲</span>
            `;
        }
    }

    switchPromptTab(promptType) {
        // Update active tab
        this.promptTabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.prompt === promptType);
        });

        // Save current prompt before switching
        if (this.currentPromptType && this.promptEditor.value.trim()) {
            this.userPrompts[this.currentPromptType] = this.promptEditor.value;
            this.saveUserPrompts();
        }

        // Switch to new prompt type
        this.currentPromptType = promptType;
        this.displayCurrentPrompt();
    }

    displayCurrentPrompt() {
        if (!this.currentPromptType || !this.defaultPrompts) return;

        // Get current prompt (user custom or default)
        const currentPrompt = this.userPrompts[this.currentPromptType] ||
                             this.defaultPrompts[this.currentPromptType] || '';

        // Update UI
        this.promptEditor.value = currentPrompt;
        this.updatePromptLabel();
        this.updatePromptStatus();
    }

    updatePromptLabel() {
        const labels = {
            single_file_analysis: 'Single File Analysis Prompt:',
            batch_analysis: 'Batch Analysis Prompt:',
            language_detection: 'Language Detection Prompt:',
            project_summary: 'Project Summary Prompt:'
        };

        this.promptLabelText.textContent = labels[this.currentPromptType] || 'Prompt:';
    }

    updatePromptStatus() {
        const currentValue = this.promptEditor.value.trim();
        const defaultValue = this.defaultPrompts[this.currentPromptType] || '';

        // Update character count
        this.promptCharCount.textContent = currentValue.length;

        // Update status
        if (!currentValue) {
            this.promptStatus.textContent = 'Empty';
            this.promptStatus.className = 'prompt-status empty';
        } else if (currentValue === defaultValue) {
            this.promptStatus.textContent = 'Default';
            this.promptStatus.className = 'prompt-status default';
        } else {
            this.promptStatus.textContent = 'Custom';
            this.promptStatus.className = 'prompt-status custom';
        }

        // Save to user prompts
        if (currentValue !== defaultValue) {
            this.userPrompts[this.currentPromptType] = currentValue;
            this.saveUserPrompts();
        } else {
            // Remove from user prompts if it matches default
            delete this.userPrompts[this.currentPromptType];
            this.saveUserPrompts();
        }
    }

    resetCurrentPrompt() {
        if (!this.currentPromptType || !this.defaultPrompts) return;

        const defaultPrompt = this.defaultPrompts[this.currentPromptType] || '';
        this.promptEditor.value = defaultPrompt;

        // Remove from user customizations
        delete this.userPrompts[this.currentPromptType];
        this.saveUserPrompts();

        this.updatePromptStatus();
    }

    resetAllPrompts() {
        if (!confirm('Are you sure you want to reset all prompts to defaults? This cannot be undone.')) {
            return;
        }

        // Clear all user customizations
        this.userPrompts = {};
        this.saveUserPrompts();

        // Redisplay current prompt
        this.displayCurrentPrompt();
    }

    getCustomPrompts() {
        // Return custom prompts for API submission
        const customPrompts = {};

        // Include current editor content if modified
        const currentValue = this.promptEditor.value.trim();
        const defaultValue = this.defaultPrompts[this.currentPromptType] || '';

        if (currentValue && currentValue !== defaultValue) {
            this.userPrompts[this.currentPromptType] = currentValue;
        }

        // Only include prompts that differ from defaults
        for (const [key, value] of Object.entries(this.userPrompts)) {
            if (value && value.trim() && value !== (this.defaultPrompts[key] || '')) {
                customPrompts[key] = value;
            }
        }

        return Object.keys(customPrompts).length > 0 ? customPrompts : null;
    }
}

// Add styles for notification system and language modal
const additionalStyles = `
<style>
.notification {
    cursor: pointer;
    user-select: none;
}

.supported-languages {
    display: grid;
    gap: 1.5rem;
}

.language-category h4 {
    color: var(--primary-blue);
    margin-bottom: 0.5rem;
    font-size: 1.1rem;
}

.language-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.language-tag {
    background: var(--sky-blue);
    color: var(--dark-blue);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
}
</style>
`;

// Add the additional styles to the document
document.head.insertAdjacentHTML('beforeend', additionalStyles);

// Single initialization with proper singleton pattern
function initializeApp() {
    if (window.codeSummarizerApp) {
        return;
    }

    try {
        window.codeSummarizerApp = new CodeSummarizerApp();
    } catch (error) {
        console.error('Failed to create CodeSummarizerApp:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Fallback: initialize after window loads if not already done
window.addEventListener('load', () => {
    initializeApp();
});