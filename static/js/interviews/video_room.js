/**
 * Video Interview Room Logic
 * Handles WebRTC, Signaling, Recording, and UI interactions.
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
    const lobbyScreen = document.getElementById('lobby-screen');
    const lobbyLocalVideo = document.getElementById('lobby-local-video');
    const interviewRoom = document.getElementById('interview-room');
    const localVideo = document.getElementById('local-video');
    const remoteVideo = document.getElementById('remote-video');
    const joinBtn = document.getElementById('join-room-btn');
    const audioSelect = document.getElementById('audio-input-select');
    const videoSelect = document.getElementById('video-input-select');
    const micLevelBar = document.getElementById('mic-level-bar');

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
        await getDevices();
        await startLobbyStream();

        joinBtn.addEventListener('click', joinRoom);

        // Setup control listeners
        toggleMicBtn.addEventListener('click', toggleMic);
        toggleCameraBtn.addEventListener('click', toggleCamera);
        shareScreenBtn.addEventListener('click', startScreenShare);
        leaveBtn.addEventListener('click', () => window.location.href = '/interviews/');

        // Sidebar logic
        if (toggleSidebarBtn) {
            toggleSidebarBtn.addEventListener('click', () => {
                roomSidebar.classList.toggle('translate-x-full');
                roomSidebar.classList.toggle('w-0');
                roomSidebar.classList.toggle('hidden'); // simple toggle
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
            notesArea.addEventListener('input', () => {
                document.getElementById('notes-save-status').textContent = 'Saving...';
                clearTimeout(typingTimer);
                typingTimer = setTimeout(() => {
                    sendNotes(notesArea.value);
                    document.getElementById('notes-save-status').textContent = 'Saved';
                }, 1000);
            });
        }

        // Initialize Coding Session
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        codingSession = new CodingSession({
            ...configData,
            csrfToken: csrfToken
        });

        // Transcript Tools
        setupTranscriptTools();
    }

    function setupTranscriptTools() {
        const searchInput = document.getElementById('transcript-search');
        const container = document.getElementById('transcript-container');
        const downloadBtn = document.getElementById('download-transcript-btn');

        // Search Filter
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const items = container.querySelectorAll('.transcript-item'); // We need to add this class to items
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
                // simple parsing or just textContent
                // Expected format: "Sender: Text"
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

    // === DEVICE MANAGEMENT ===
    async function getDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            audioSelect.innerHTML = '';
            videoSelect.innerHTML = '';

            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `${device.kind} - ${device.deviceId.slice(0, 5)}`;
                if (device.kind === 'audioinput') audioSelect.appendChild(option);
                else if (device.kind === 'videoinput') videoSelect.appendChild(option);
            });
        } catch (e) {
            console.error('Error getting devices:', e);
        }
    }

    async function startLobbyStream() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: true // default
            });
            lobbyLocalVideo.srcObject = stream;
            localStream = stream;
            setupAudioVisualizer(stream);
        } catch (e) {
            console.error('Error starting stream:', e);
            alert('Could not access camera/microphone. Please check permissions.');
        }
    }

    function setupAudioVisualizer(stream) {
        const audioContext = new AudioContext();
        const src = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        src.connect(analyser);
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        function draw() {
            if (!localStream) return;
            requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
            const average = sum / bufferLength;
            micLevelBar.style.width = `${Math.min(100, average * 2)}%`; // Amplify a bit
        }
        draw();
    }

    // === JOIN ROOM & WEBSOCKET ===
    async function joinRoom() {
        // Transition UI
        lobbyScreen.classList.add('hidden');
        interviewRoom.classList.remove('hidden');
        setTimeout(() => interviewRoom.classList.remove('opacity-0'), 100);

        // Move stream to main room
        localVideo.srcObject = localStream;

        // Only start recording if configured (e.g. Host/Interviewer or if allowed)
        // For simplicity, we start recording for whoever joins first or both, 
        // but backend policy prevents unauthorized uploads.
        if (isInterviewer || true) { // Defaulting to true for verifying feature
            startRecording();
        }

        connectSocket();
    }

    function connectSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${protocol}//${window.location.host}${wsUrl}`);

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
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });
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
            type: message.type || 'signal', // offer/answer/candidate types match RTCSessionDescriptionInit
            ...message
        }));
    }

    // === RECORDING ===
    function startRecording() {
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
        document.getElementById('record-indicator').classList.remove('hidden');

        // Start separate audio recording for transcription
        startAudioTranscription();
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
                        const base64Audio = reader.result; // "data:audio/webm;base64,..."

                        socket.send(JSON.stringify({
                            type: 'process_audio',
                            audio: base64Audio,
                            speaker_name: isInterviewer ? 'Interviewer' : 'Candidate' // logic to get real name if available
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

        try {
            await fetch(`/interviews/recording/${interviewId}/upload/`, {
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
        socket.send(JSON.stringify({
            type: 'update_notes',
            notes: notes
        }));
    }

    function sendRating(rating) {
        socket.send(JSON.stringify({
            type: 'update_rating',
            rating: rating
        }));
    }

    function appendTranscript(text, sender) {
        const container = document.getElementById('transcript-container');
        const div = document.createElement('div');
        div.className = 'transcript-item bg-gray-800/50 p-3 rounded-lg border border-gray-700 text-sm';
        div.innerHTML = `<span class="font-bold text-blue-400">${sender}:</span> <span class="text-gray-300 transcript-text">${text}</span>`;
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
        connectionStatusText.textContent = status;
        connectionStatusDot.className = `w-2 h-2 rounded-full bg-${color}-500`;
    }

    function toggleMic() {
        isMuted = !isMuted;
        localStream.getAudioTracks()[0].enabled = !isMuted;
        toggleMicBtn.innerHTML = isMuted ? '<i class="fas fa-microphone-slash"></i>' : '<i class="fas fa-microphone"></i>';
        toggleMicBtn.classList.toggle('bg-red-500', isMuted);
    }

    function toggleCamera() {
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
                const sender = peerConnection.getSenders().find(s => s.track.kind === 'video');
                sender.replaceTrack(screenTrack);
            }

            localVideo.srcObject = screenStream;

            screenTrack.onended = () => {
                // Revert to camera
                if (peerConnection) {
                    const sender = peerConnection.getSenders().find(s => s.track.kind === 'video');
                    sender.replaceTrack(localStream.getVideoTracks()[0]);
                }
                localVideo.srcObject = localStream;
            };
        } catch (e) {
            console.error("Screen share failed", e);
        }
    }

    init();
});
