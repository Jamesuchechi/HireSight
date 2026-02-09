/**
 * Warmup Wizard Logic
 * Handles device testing (camera/microphone) before joining the interview room.
 */

document.addEventListener('DOMContentLoaded', () => {
    // === CONFIGURATION ===
    const configData = JSON.parse(document.getElementById('interview-data').textContent);
    const { id: interviewId, isInterviewer } = configData;

    // === STATE ===
    let localStream = null;
    let audioVisualizerActive = false;

    // === DOM ELEMENTS ===
    const lobbyLocalVideo = document.getElementById('lobby-local-video');
    const audioSelect = document.getElementById('audio-input-select');
    const videoSelect = document.getElementById('video-input-select');
    const joinForm = document.getElementById('join-form');

    // === INITIALIZATION ===
    function init() {
        initWarmupWizard();

        // Device selection handlers
        audioSelect.addEventListener('change', async (e) => {
            await changeDevice('audio', e.target.value);
        });

        videoSelect.addEventListener('change', async (e) => {
            await changeDevice('video', e.target.value);
        });

        // Form submission handler - save selected devices
        if (joinForm) {
            joinForm.addEventListener('submit', (e) => {
                // Store selected devices before submitting
                document.getElementById('selected-video-device').value = videoSelect.value;
                document.getElementById('selected-audio-device').value = audioSelect.value;

                // Stop media streams before navigating away
                if (localStream) {
                    localStream.getTracks().forEach(track => track.stop());
                }
                audioVisualizerActive = false;
            });
        }

        // Populate device lists initially
        getDevices();
    }

    // === WARMUP WIZARD LOGIC ===
    function initWarmupWizard() {
        const startCamBtn = document.getElementById('startCameraTest');
        const camContinueBtn = document.getElementById('cameraTestContinue');
        const startMicBtn = document.getElementById('startMicTest');
        const micContinueBtn = document.getElementById('micTestContinue');
        const prevBtns = document.querySelectorAll('.prevStep');

        if (startCamBtn) startCamBtn.addEventListener('click', startCameraTest);
        if (camContinueBtn) camContinueBtn.addEventListener('click', () => nextStep('cameraTest', 'microphoneTest', 2));
        if (startMicBtn) startMicBtn.addEventListener('click', startMicTest);
        if (micContinueBtn) micContinueBtn.addEventListener('click', () => nextStep('microphoneTest', 'finalConfirmation', 3));

        prevBtns.forEach(btn => {
            btn.addEventListener('click', prevStep);
        });
    }

    async function startCameraTest() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });

            // If we already had audio (back navigation), keep it
            if (localStream && localStream.getAudioTracks().length > 0) {
                localStream.getVideoTracks().forEach(t => t.stop()); // Stop old video
                if (localStream.getVideoTracks()[0]) {
                    localStream.removeTrack(localStream.getVideoTracks()[0]);
                }
                localStream.addTrack(stream.getVideoTracks()[0]);
            } else {
                localStream = stream;
            }

            lobbyLocalVideo.srcObject = localStream;
            lobbyLocalVideo.classList.remove('hidden');
            document.getElementById('cameraPlaceholder').classList.add('hidden');
            document.getElementById('cameraSuccess').classList.remove('hidden');
            document.getElementById('cameraStatus').classList.add('hidden');
            document.getElementById('cameraTestContinue').disabled = false;

            // Refresh devices now that we have permission
            getDevices();
        } catch (e) {
            console.error('Camera Error:', e);
            document.getElementById('cameraStatusText').textContent = 'Could not access camera. Please check permissions.';
            document.getElementById('cameraStatus').classList.remove('hidden');
        }
    }

    async function startMicTest() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Merge into localStream
            if (localStream) {
                // If we already had audio, stop it first
                localStream.getAudioTracks().forEach(t => t.stop());
                localStream.addTrack(stream.getAudioTracks()[0]);
            } else {
                localStream = stream;
            }

            // Start visualizer
            setupAudioVisualizer(localStream);

            document.getElementById('micStatus').innerHTML = '<i class="fas fa-microphone-lines"></i> Listening...';

            // Show success after a brief moment
            setTimeout(() => {
                document.getElementById('micSuccess').classList.remove('hidden');
                document.getElementById('micTestContinue').disabled = false;
            }, 1000);

            // Refresh devices
            getDevices();
        } catch (e) {
            console.error('Mic Error:', e);
            document.getElementById('micStatus').innerHTML = '<i class="fas fa-exclamation-triangle text-red-400"></i> Could not access microphone.';
        }
    }

    function nextStep(currentId, nextId, stepNum) {
        document.getElementById(currentId).classList.add('hidden');
        document.getElementById(nextId).classList.remove('hidden');
        document.getElementById('warmupProgress').textContent = `Step ${stepNum} of 3`;
    }

    function prevStep() {
        const steps = ['cameraTest', 'microphoneTest', 'finalConfirmation'];
        // Find visible step
        let currentIndex = steps.findIndex(id => !document.getElementById(id).classList.contains('hidden'));

        if (currentIndex > 0) {
            document.getElementById(steps[currentIndex]).classList.add('hidden');
            document.getElementById(steps[currentIndex - 1]).classList.remove('hidden');
            document.getElementById('warmupProgress').textContent = `Step ${currentIndex} of 3`;
        }
    }

    // === AUDIO VISUALIZER ===
    function setupAudioVisualizer(stream) {
        if (!stream.getAudioTracks().length) return;

        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const src = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 64; // smaller FFT for 4 bars
        src.connect(analyser);

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const bars = document.querySelectorAll('.audioBar');

        audioVisualizerActive = true;

        function draw() {
            if (!audioVisualizerActive) {
                audioContext.close();
                return;
            }
            requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);

            // Simple visualization: map frequency chunks to 4 bars
            bars.forEach((bar, index) => {
                // Approximate 4 equally spaced blocks from the frequency data
                const i = Math.floor(index * (bufferLength / 4));
                const value = dataArray[i];
                const percent = (value / 255) * 100;

                bar.style.height = `${Math.max(10, percent)}%`; // Min 10% height
                bar.style.backgroundColor = value > 100 ? '#3b82f6' : '#334155'; // Blue if active, dark slate if quiet
            });
        }
        draw();
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

    async function changeDevice(type, deviceId) {
        if (!localStream) return;

        try {
            const constraints = type === 'audio'
                ? { audio: { deviceId: { exact: deviceId } }, video: false }
                : { audio: false, video: { deviceId: { exact: deviceId } } };

            const newStream = await navigator.mediaDevices.getUserMedia(constraints);
            const newTrack = type === 'audio' ? newStream.getAudioTracks()[0] : newStream.getVideoTracks()[0];
            const oldTrack = type === 'audio' ? localStream.getAudioTracks()[0] : localStream.getVideoTracks()[0];

            // Replace track in local stream
            if (oldTrack) {
                localStream.removeTrack(oldTrack);
                oldTrack.stop();
            }
            localStream.addTrack(newTrack);

            // Update video element
            lobbyLocalVideo.srcObject = localStream;

            // Restart audio visualizer if changing audio
            if (type === 'audio') {
                setupAudioVisualizer(localStream);
            }
        } catch (e) {
            console.error(`Error changing ${type} device:`, e);
        }
    }

    init();
});
