// Language-aware voice search using Web Speech API
(function () {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition || window.msSpeechRecognition;
    const searchBtn = document.getElementById('voice-search-btn');
    const searchInput = document.getElementById('voice-search-input');

    function getPreferredLangs() {
        const pageLang = (document.body && document.body.dataset && document.body.dataset.currentLang) || 'en';
        const browserLang = (navigator.language || (navigator.languages && navigator.languages[0]) || 'en-US').toLowerCase();
        const preferred = [];
        const map = {
            en: ['en-IN', 'en-US'],
            hi: ['hi-IN', 'en-IN', 'en-US'],
            gu: ['gu-IN', 'hi-IN', 'en-IN', 'en-US']
        };

        const base = (pageLang || browserLang || 'en').toLowerCase();
        for (const key in map) {
            if (base.startsWith(key)) {
                preferred.push(...map[key]);
                break;
            }
        }

        if (!preferred.length) {
            preferred.push('en-IN', 'en-US');
        }

        if (browserLang.startsWith('hi')) preferred.unshift('hi-IN');
        if (browserLang.startsWith('gu')) preferred.unshift('gu-IN');

        return [...new Set(preferred)];
    }

    function showStatus(message) {
        const status = document.getElementById('voice-status');
        if (status) {
            status.textContent = message;
        }
    }

    function showBrowserFallback() {
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.title = 'Voice search is not supported in this browser. Please use Chrome or Edge.';
            searchBtn.classList.add('opacity-50');
        }
        showStatus('Voice search unavailable in this browser');
    }

    function showErrorToast(message) {
        if (!document.body) return;

        const toast = document.createElement('div');
        toast.className = 'position-fixed bottom-0 start-50 translate-middle-x mb-3';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <div class="alert alert-warning alert-dismissible fade show shadow-sm rounded-3 mb-0" role="alert">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 7000);
    }

    function showInterimResultsModal(transcript) {
        const existingModal = document.getElementById('voice-result-modal');
        if (existingModal) existingModal.remove();

        const modal = document.createElement('div');
        modal.id = 'voice-result-modal';
        modal.className = 'modal fade';
        modal.tabIndex = -1;
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title"><i class="bi bi-mic-fill me-2"></i>Voice Search Result</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted mb-2">Here's what I heard:</p>
                        <div class="alert alert-info rounded-3 p-3 mb-0">
                            <strong class="text-dark">"${transcript}"</strong>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Try Again</button>
                        <button type="button" class="btn btn-success voice-confirm-btn">Confirm & Search</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();

        modal.querySelector('.voice-confirm-btn').addEventListener('click', function () {
            if (searchInput) searchInput.value = transcript;
            modal.remove();
            const form = searchInput && searchInput.closest('form');
            if (form) setTimeout(() => form.submit(), 200);
        });

        modal.addEventListener('hidden.bs.modal', function () {
            modal.remove();
        });
    }

    function startRecognitionWithFallback(langCodes, retryIndex = 0) {
        if (!SpeechRecognitionCtor) {
            showBrowserFallback();
            return;
        }

        const recognition = new SpeechRecognitionCtor();
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.maxAlternatives = 1;
        recognition.lang = langCodes[retryIndex] || 'en-IN';

        let interimTranscript = '';

        recognition.onstart = function () {
            showStatus('Listening... speak now');
            if (searchBtn) {
                searchBtn.classList.add('btn-success', 'listening-pulse');
                searchBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
            }
            if (searchInput) {
                searchInput.placeholder = 'Listening...';
                searchInput.style.color = '';
            }
        };

        recognition.onresult = function (event) {
            interimTranscript = '';
            let finalText = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript.trim();
                if (event.results[i].isFinal) {
                    finalText = transcript;
                } else {
                    interimTranscript += transcript + ' ';
                }
            }

            if (finalText) {
                if (searchInput) searchInput.value = finalText;
                showStatus('Voice captured successfully');
                showInterimResultsModal(finalText);
                recognition.stop();
                return;
            }

            if (interimTranscript.trim()) {
                if (searchInput) {
                    searchInput.value = interimTranscript.trim();
                    searchInput.style.color = '#666';
                }
                showStatus('Listening...');
            }
        };

        recognition.onerror = function (event) {
            console.error('Speech recognition error:', event.error, 'lang:', recognition.lang);

            if (searchBtn) {
                searchBtn.classList.remove('btn-success', 'listening-pulse');
            }

            const nextLang = langCodes[retryIndex + 1];
            if ((event.error === 'no-speech' || event.error === 'audio-capture') && nextLang) {
                startRecognitionWithFallback(langCodes, retryIndex + 1);
                return;
            }

            let message = 'Could not detect your voice. Please try again.';
            if (event.error === 'no-speech') {
                message = 'No speech detected. Please speak clearly and try again. If it still fails, allow microphone access and use English for the best detection.';
            } else if (event.error === 'not-allowed') {
                message = 'Microphone permission was denied. Please allow microphone access and try again.';
            } else if (event.error === 'network') {
                message = 'Network issue while listening. Please check your connection and try again.';
            }

            showErrorToast(message);
            showStatus('Voice not detected');
        };

        recognition.onend = function () {
            if (searchBtn) {
                searchBtn.classList.remove('btn-success', 'listening-pulse');
                searchBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
            }
            if (searchInput) {
                searchInput.style.color = '';
                searchInput.placeholder = 'Search products...';
            }
        };

        try {
            recognition.start();
        } catch (error) {
            console.warn('Speech recognition start failed:', error);
            const nextLang = langCodes[retryIndex + 1];
            if (nextLang) {
                startRecognitionWithFallback(langCodes, retryIndex + 1);
                return;
            }
            showErrorToast('Voice detection is blocked by the browser. Please try again in a moment.');
            showStatus('Voice detection blocked');
        }
    }

    function startVoiceSearch() {
        if (!searchBtn || !searchInput) {
            showBrowserFallback();
            return;
        }

        if (!SpeechRecognitionCtor) {
            showBrowserFallback();
            return;
        }

        const languages = getPreferredLangs();
        startRecognitionWithFallback(languages, 0);
    }

    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            startVoiceSearch();
        });
    } else if (!SpeechRecognitionCtor) {
        showBrowserFallback();
    }
})();

