/**
 * Video Interview Room Logic
 * Handles WebRTC, Signaling, Recording, and UI interactions.
 * Note: Warmup wizard is now handled by warmup.js in a separate page.
 */

document.addEventListener('DOMContentLoaded', () => {
    // === CONFIGURATION ===
    const configData = JSON.parse(document.getElementById('interview-data').textContent);
    const { id: interviewId, isInterviewer, userEmail, iceServers, wsUrl } = configData;

    // === STATE ===
    let localStream;
    let peerConnection;
    let socket;
    let mediaRecorder;
    let audioRecorder; // For transcription
    let isMuted = false;
    let isVideoOff = false;
    let isRecording = false;
    let recordingChunkIndex = 0;

    // Coding Session
    let codingSession;

    // === DOM ELEMENTS ===
    const localVideo = document.getElementById('local-video');
    const remoteVideo = document.getElementById('remote-video');

    // Controls
    const toggleMicBtn = document.getElementById('toggle-mic-btn');
    const toggleCameraBtn = document.getElementById('toggle-camera-btn');
    const shareScreenBtn = document.getElementById('share-screen-btn');
    const leaveBtn = document.getElementById('leave-room-btn');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const roomSidebar = document.getElementById('room-sidebar');

    // UI Status
    const connectionStatusDot = document.getElementById('connection-status-dot');
    const connectionStatusText = document.getElementById('connection-status-text');
    const remoteWaitingState = document.getElementById('remote-waiting-state');

    // === INITIALIZATION ===
    async function init() {
        // Request media access and connect immediately (warmup already completed)
        await initializeMedia();
        connectSocket();

        // Setup control listeners
        toggleMicBtn.addEventListener('click', toggleMic);
        toggleCameraBtn.addEventListener('click', toggleCamera);
        shareScreenBtn.addEventListener('click', startScreenShare);
        leaveBtn.addEventListener('click', leaveRoom);

        // Sidebar logic
        if (toggleSidebarBtn) {
            toggleSidebarBtn.addEventListener('click', () => {
                roomSidebar.classList.toggle('translate-x-full');
                roomSidebar.classList.toggle('hidden');
            });
        }

        // Tab logic
        document.querySelectorAll('[data-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
                document.getElementById(`tab-${tab}`).classList.remove('hidden');

                // Update active state style
                document.querySelectorAll('[data-tab]').forEach(b => {
                    b.classList.remove('text-blue-400', 'border-b-2', 'border-blue-500');
                    b.classList.add('text-gray-400');
                });
                e.target.classList.add('text-blue-400', 'border-b-2', 'border-blue-500');
                e.target.classList.remove('text-gray-400');
            });
        });

        // Rating Logic (Interviewer Only)
        if (isInterviewer) {
            document.querySelectorAll('.star-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const rating = e.target.dataset.value;
                    sendRating(rating);
                    // Update UI
                    document.querySelectorAll('.star-btn').forEach(s => {
                        s.classList.toggle('text-yellow-400', s.dataset.value <= rating);
                        s.classList.toggle('text-gray-600', s.dataset.value > rating);
                    });
                });
            });

            // Notes Logic
            const notesArea = document.getElementById('private-notes-area');
            let typingTimer;
            if (notesArea) {
                notesArea.addEventListener('input', () => {
                    document.getElementById('notes-save-status').textContent = 'Saving...';
                    clearTimeout(typingTimer);
                    typingTimer = setTimeout(() => {
                        sendNotes(notesArea.value);
                        document.getElementById('notes-save-status').textContent = 'Saved';
                    }, 1000);
                });
            }
        }

        // Initialize Coding Session
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        codingSession = new CodingSession({
            ...configData,
            csrfToken: csrfToken
        });

        // Transcript Tools
        setupTranscriptTools();

        // Keyboard shortcuts
        setupKeyboardShortcuts();
    }

    // === MEDIA INITIALIZATION ===
    async function initializeMedia() {
        try {
            // Request both audio and video
            localStream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: true
            });

            localVideo.srcObject = localStream;

            // Only start recording if interviewer
            if (isInterviewer) {
                startRecording();
            }

            // Start audio transcription for everyone
            startAudioTranscription();

        } catch (e) {
            console.error('Media access error:', e);
            updateConnectionStatus('Media Error', 'red');
        }
    }

    function setupTranscriptTools() {
        const searchInput = document.getElementById('transcript-search');
        const container = document.getElementById('transcript-container');
        const downloadBtn = document.getElementById('download-transcript-btn');

        if (!searchInput || !container || !downloadBtn) return;

        // Search Filter
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const items = container.querySelectorAll('.transcript-item');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(term) ? 'block' : 'none';
            });
        });

        // Download
        downloadBtn.addEventListener('click', () => {
            const items = container.querySelectorAll('.transcript-item');
            let content = "Interview Transcript\n\n";
            items.forEach(item => {
                content += item.textContent.trim() + "\n";
            });

            const blob = new Blob([content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcript-${interviewId}.txt`;
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }

    // === WEBSOCKET CONNECTION ===
    function connectSocket() {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WebSocket Connected');
            updateConnectionStatus('Connected', 'green');

            // Pass socket to coding session
            if (codingSession) codingSession.setWebSocket(socket);
        };

        socket.onmessage = async (e) => {
            const data = JSON.parse(e.data);
            handleSignalingMessage(data);
        };

        socket.onclose = () => updateConnectionStatus('Disconnected', 'red');
        socket.onerror = (e) => console.error('Socket error:', e);
    }

    // === WEBRTC SIGNALING ===
    async function handleSignalingMessage(data) {
        const { type, message, sender } = data;

        if (type === 'peer_status') {
            if (data.status === 'joined') {
                console.log('Peer joined!');
                remoteWaitingState.classList.add('hidden');
                // Initiate call if we are the interviewer (convention to avoid glare)
                if (isInterviewer) {
                    await createPeerConnection();
                    await createOffer();
                }
            } else if (data.status === 'left') {
                console.log('Peer left');
                remoteVideo.srcObject = null;
                remoteWaitingState.classList.remove('hidden');
                closePeerConnection();
            }
        } else if (type === 'signaling_message') {
            if (!peerConnection) await createPeerConnection();

            if (message.type === 'offer') {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
                await createAnswer();
                remoteWaitingState.classList.add('hidden');
            } else if (message.type === 'answer') {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
            } else if (message.type === 'candidate') {
                if (message.candidate) {
                    await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
                }
            }
        } else if (type === 'transcript_update') {
            appendTranscript(data.text, data.sender);
        } else if (type === 'code_update') {
            if (codingSession) codingSession.handleRemoteUpdate(data);
        }
    }

    // === WEBRTC CONNECTION ===
    async function createPeerConnection() {
        if (peerConnection) return;

        const config = { iceServers: iceServers };
        peerConnection = new RTCPeerConnection(config);

        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                sendSignal({ type: 'candidate', candidate: event.candidate });
            }
        };

        peerConnection.ontrack = (event) => {
            remoteVideo.srcObject = event.streams[0];
            remoteWaitingState.classList.add('hidden');
        };

        // Add local tracks
        if (localStream) {
            localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });
        }
    }

    async function createOffer() {
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        sendSignal(offer);
    }

    async function createAnswer() {
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        sendSignal(answer);
    }

    function closePeerConnection() {
        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
        }
    }

    function sendSignal(message) {
        socket.send(JSON.stringify({
            type: message.type || 'signal',
            ...message
        }));
    }

    // === RECORDING ===
    function startRecording() {
        if (!localStream) return;

        if (!MediaRecorder.isTypeSupported('video/webm;codecs=vp9')) {
            console.warn('VP9 codec not supported, recording might fail');
        }

        mediaRecorder = new MediaRecorder(localStream, { mimeType: 'video/webm' });

        mediaRecorder.ondataavailable = async (e) => {
            if (e.data.size > 0) {
                await uploadChunk(e.data);
            }
        };

        // Slice every 10 seconds
        mediaRecorder.start(10000);
        isRecording = true;
        const recordIndicator = document.getElementById('record-indicator');
        if (recordIndicator) recordIndicator.classList.remove('hidden');
    }

    function startAudioTranscription() {
        if (!localStream) return;

        // Use audio track only
        const audioStream = new MediaStream(localStream.getAudioTracks());

        try {
            audioRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });

            audioRecorder.ondataavailable = async (e) => {
                if (e.data.size > 0 && socket && socket.readyState === WebSocket.OPEN) {
                    const reader = new FileReader();
                    reader.readAsDataURL(e.data);
                    reader.onloadend = () => {
                        const base64Audio = reader.result;

                        socket.send(JSON.stringify({
                            type: 'process_audio',
                            audio: base64Audio,
                            speaker_name: isInterviewer ? 'Interviewer' : 'Candidate'
                        }));
                    };
                }
            };

            // Send chunks every 4 seconds for near real-time transcription
            audioRecorder.start(4000);
            console.log('Audio transcription started');

        } catch (e) {
            console.error('Failed to start audio transcription recorder:', e);
        }
    }

    async function uploadChunk(blob) {
        const formData = new FormData();
        formData.append('video_chunk', blob);
        formData.append('chunk_index', recordingChunkIndex++);

        // Get CSRF Token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Get current language prefix from URL
        const langPrefix = window.location.pathname.match(/^\/[a-z]{2}\//)?.[0] || '/';

        try {
            await fetch(`${langPrefix}interviews/recording/${interviewId}/upload/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });
        } catch (e) {
            console.error('Upload failed', e);
        }
    }

    // === LIVE IO ===
    function sendNotes(notes) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'update_notes',
                notes: notes
            }));
        }
    }

    function sendRating(rating) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'update_rating',
                rating: rating
            }));
        }
    }

    function appendTranscript(text, sender) {
        const container = document.getElementById('transcript-container');
        if (!container) return;

        // Remove placeholder on first transcript
        const placeholder = container.querySelector('.text-center');
        if (placeholder) {
            placeholder.remove();
        }

        const div = document.createElement('div');
        div.className = 'transcript-item bg-gray-800/50 p-3 rounded-lg border border-gray-700 text-sm';

        // Create elements safely to prevent XSS
        const senderSpan = document.createElement('span');
        senderSpan.className = 'font-bold text-blue-400';
        senderSpan.textContent = sender + ': ';

        const textSpan = document.createElement('span');
        textSpan.className = 'text-gray-300 transcript-text';
        textSpan.textContent = text;

        div.appendChild(senderSpan);
        div.appendChild(textSpan);
        container.appendChild(div);

        // Respect search filter immediately if active
        const searchInput = document.getElementById('transcript-search');
        if (searchInput && searchInput.value) {
            const term = searchInput.value.toLowerCase();
            div.style.display = div.textContent.toLowerCase().includes(term) ? 'block' : 'none';
        }

        container.scrollTop = container.scrollHeight;
    }

    // === UI HELPERS ===
    function updateConnectionStatus(status, color) {
        if (connectionStatusText) connectionStatusText.textContent = status;
        if (connectionStatusDot) {
            const colorClasses = {
                'green': 'bg-green-500',
                'red': 'bg-red-500',
                'yellow': 'bg-yellow-500',
                'blue': 'bg-blue-500'
            };
            connectionStatusDot.className = `w-2 h-2 rounded-full ${colorClasses[color] || 'bg-gray-500'}`;
        }
    }

    function toggleMic() {
        if (!localStream || !localStream.getAudioTracks().length) return;
        isMuted = !isMuted;
        localStream.getAudioTracks()[0].enabled = !isMuted;
        toggleMicBtn.innerHTML = isMuted ? '<i class="fas fa-microphone-slash"></i>' : '<i class="fas fa-microphone"></i>';
        toggleMicBtn.classList.toggle('bg-red-500', isMuted);
    }

    function toggleCamera() {
        if (!localStream || !localStream.getVideoTracks().length) return;
        isVideoOff = !isVideoOff;
        localStream.getVideoTracks()[0].enabled = !isVideoOff;
        toggleCameraBtn.innerHTML = isVideoOff ? '<i class="fas fa-video-slash"></i>' : '<i class="fas fa-video"></i>';
        toggleCameraBtn.classList.toggle('bg-red-500', isVideoOff);
    }

    async function startScreenShare() {
        try {
            const screenStream = await navigator.mediaDevices.getDisplayMedia({ cursor: true });
            const screenTrack = screenStream.getVideoTracks()[0];

            if (peerConnection) {
                const sender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender) sender.replaceTrack(screenTrack);
            }

            localVideo.srcObject = screenStream;

            screenTrack.onended = () => {
                // Revert to camera
                if (peerConnection && localStream) {
                    const sender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
                    if (sender && localStream.getVideoTracks().length) {
                        sender.replaceTrack(localStream.getVideoTracks()[0]);
                    }
                }
                localVideo.srcObject = localStream;
            };
        } catch (e) {
            console.error("Screen share failed", e);
        }
    }

    function leaveRoom() {
        // Stop all tracks
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
        }

        // Stop recording
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        if (audioRecorder && audioRecorder.state !== 'inactive') {
            audioRecorder.stop();
        }

        // Close peer connection
        closePeerConnection();

        // Close WebSocket
        if (socket) {
            socket.close();
        }

        // Redirect
        window.location.href = `/interviews/${interviewId}/summary/`;
    }

    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+D: Toggle Mic
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                toggleMic();
            }
            // Ctrl+E: Toggle Camera
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                toggleCamera();
            }
        });
    }

    init();
});
