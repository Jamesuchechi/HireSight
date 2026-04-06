/**
 * VideoAnalyzer - Real-time video analysis using MediaPipe Face Mesh
 * 
 * Analyzes:
 * - Eye gaze direction (looking at camera %)
 * - Head pose (pitch, yaw, roll angles)
 * - Blink rate
 * - Mouth movement (speaking detection)
 * 
 * @class VideoAnalyzer
 */
class VideoAnalyzer {
    constructor(config = {}) {
        this.config = {
            updateInterval: config.updateInterval || 1000, // Calculate metrics every 1 second
            videoElement: config.videoElement || null,
            canvasElement: config.canvasElement || null,
            onMetricsUpdate: config.onMetricsUpdate || null,
            onFrameUpdate: config.onFrameUpdate || null, // Real-time frame updates
            onError: config.onError || null,
            ...config
        };

        this.faceMesh = null;
        this.isRunning = false;
        this.camera = null;
        this.metrics = [];
        this.frameBuffer = [];
        this.eyeOpenBuffer = [];
        this.mouthOpenBuffer = [];
        this.gazeFrameBuffer = [];
        this.headPoseBuffer = [];
        this.lastUpdateTime = Date.now();
        this.recordingStartTime = null;
    }

    /**
     * Initialize MediaPipe Face Mesh and camera
     */
    async init() {
        try {
            const faceLandmarksDetection = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');

            const { FaceLandmarker, FilesetResolver } = faceLandmarksDetection;

            const wasmRuntime = await FilesetResolver.forVisionTasks(
                'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm'
            );

            console.log("FilesetResolver loaded for vision tasks");

            this.faceMesh = await FaceLandmarker.createFromOptions(wasmRuntime, {
                baseOptions: {
                    modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task',
                    delegate: 'GPU'
                },
                runningMode: 'VIDEO',
                numFaces: 1
            });
            console.log("FaceLandmarker initialized successfully");

            await this._initCamera();
            console.log("Camera initialized successfully");

            this.isRunning = true;
            this.recordingStartTime = Date.now();
            this._detectLoop();

            return true;
        } catch (error) {
            console.error('Failed to initialize VideoAnalyzer:', error);
            if (this.config.onError) {
                this.config.onError(error);
            }
            return false;
        }
    }

    /**
     * Initialize camera stream
     */
    async _initCamera() {
        if (!this.config.videoElement) {
            throw new Error('Video element not provided');
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: true
            });

            this.config.videoElement.srcObject = stream;

            return new Promise((resolve) => {
                this.config.videoElement.onloadedmetadata = () => {
                    this.config.videoElement.play();
                    resolve();
                };
            });
        } catch (error) {
            throw new Error(`Failed to access camera: ${error.message}`);
        }
    }

    /**
     * Main detection loop
     */
    _detectLoop = () => {
        if (!this.isRunning || !this.faceMesh) {
            return;
        }

        this._detect();
        requestAnimationFrame(this._detectLoop);
    }

    /**
     * Perform face detection on current frame
     */
    _detect() {
        if (!this.config.videoElement || this.config.videoElement.readyState < 2) {
            return;
        }

        try {
            const results = this.faceMesh.detectForVideo(this.config.videoElement, performance.now());

            if (results.faceLandmarks && results.faceLandmarks.length > 0) {
                const landmarks = results.faceLandmarks[0];

                // Analyze frame
                const frameAnalysis = {
                    timestamp: Date.now(),
                    landmarks: landmarks,
                    eyeOpen: this._getEyeOpenStatus(landmarks),
                    mouthOpen: this._getMouthOpenStatus(landmarks),
                    gaze: this._getGazeDirection(landmarks),
                    headPose: this._getHeadPose(landmarks)
                };

                this.frameBuffer.push(frameAnalysis);
                this.eyeOpenBuffer.push(frameAnalysis.eyeOpen);
                this.mouthOpenBuffer.push(frameAnalysis.mouthOpen);
                this.gazeFrameBuffer.push(frameAnalysis.gaze);
                this.headPoseBuffer.push(frameAnalysis.headPose);

                // Update real-time UI if callback provided
                if (this.config.onFrameUpdate) {
                    this.config.onFrameUpdate(frameAnalysis);
                }

                // Update metrics every updateInterval
                const now = Date.now();
                if (now - this.lastUpdateTime >= this.config.updateInterval) {
                    this._calculateAndStoreMetrics();
                    this.lastUpdateTime = now;
                }

                // Draw visualization if canvas provided
                if (this.config.canvasElement) {
                    this._drawVisualization(landmarks, frameAnalysis);
                }
            }
        } catch (error) {
            console.error('Detection error:', error);
        }
    }

    /**
     * Determine if eyes are open (based on eyelid distance)
     */
    _getEyeOpenStatus(landmarks) {
        // Eye landmarks: 33 (left eye right), 133 (left eye left), 159 (left eyelid upper), 145 (left eyelid lower)
        const leftEyeRight = landmarks[33];
        const leftEyeLeft = landmarks[133];
        const leftEyeUpper = landmarks[159];
        const leftEyeLower = landmarks[145];

        // Calculate vertical distance (for upper eye)
        const verticalDistance = Math.sqrt(
            Math.pow(leftEyeUpper.x - leftEyeLower.x, 2) +
            Math.pow(leftEyeUpper.y - leftEyeLower.y, 2)
        );

        // Threshold for eye open (adjust based on camera distance)
        const EYE_OPEN_THRESHOLD = 0.015;
        return verticalDistance > EYE_OPEN_THRESHOLD ? 1.0 : 0.0;
    }

    /**
     * Determine if mouth is open (based on mouth distance)
     */
    _getMouthOpenStatus(landmarks) {
        // Mouth landmarks: 78 (upper lip), 13 (lower lip)
        const upperLip = landmarks[13];
        const lowerLip = landmarks[14];

        // Calculate vertical distance
        const mouthDistance = Math.abs(upperLip.y - lowerLip.y);

        // Threshold for mouth open
        const MOUTH_OPEN_THRESHOLD = 0.02;
        return mouthDistance > MOUTH_OPEN_THRESHOLD ? 1.0 : 0.0;
    }

    /**
     * Determine gaze direction (looking at camera percentage)
     */
    _getGazeDirection(landmarks) {
        // Key facial landmarks for gaze using accurate indices
        // Left Eye: 33 (outer), 133 (inner)
        // Right Eye: 263 (outer), 362 (inner)
        // Nose Tip: 1
        const leftEyeInner = landmarks[133];
        const rightEyeInner = landmarks[362];
        const noseTip = landmarks[1];

        // Calculate eye-to-nose distance to determine if looking at camera
        const leftEyeToNose = Math.sqrt(
            Math.pow(leftEyeInner.x - noseTip.x, 2) +
            Math.pow(leftEyeInner.y - noseTip.y, 2)
        );

        const rightEyeToNose = Math.sqrt(
            Math.pow(rightEyeInner.x - noseTip.x, 2) +
            Math.pow(rightEyeInner.y - noseTip.y, 2)
        );

        // Average distance
        const avgEyeToNose = (leftEyeToNose + rightEyeToNose) / 2;

        // If eyes and nose are close, person is looking at camera
        const LOOKING_AT_CAMERA_THRESHOLD = 0.15;

        if (avgEyeToNose < LOOKING_AT_CAMERA_THRESHOLD) {
            const score = Math.max(0, 1 - avgEyeToNose / LOOKING_AT_CAMERA_THRESHOLD);
            return {
                direction: 'center',
                score: score,
                confidence: score, // fallback
                x: 0,
                y: 0
            };
        }

        // Determine direction (left/right/up/down)
        const eyeCenterX = (leftEyeInner.x + rightEyeInner.x) / 2;
        const eyeCenterY = (leftEyeInner.y + rightEyeInner.y) / 2;

        let directionX = eyeCenterX < 0.4 ? 'left' : (eyeCenterX > 0.6 ? 'right' : 'center');
        let directionY = eyeCenterY < 0.4 ? 'up' : (eyeCenterY > 0.6 ? 'down' : 'center');

        return {
            direction: `${directionY}-${directionX}`,
            score: Math.max(0, 0.5 - (avgEyeToNose - LOOKING_AT_CAMERA_THRESHOLD)),
            confidence: Math.min(avgEyeToNose, 1.0),
            x: eyeCenterX,
            y: eyeCenterY
        };
    }

    /**
     * Calculate head pose (pitch, yaw, roll angles)
     */
    _getHeadPose(landmarks) {
        // Use key landmarks to estimate head rotation
        const noseTip = landmarks[1];
        const leftEarLobe = landmarks[234]; // Left ear
        const rightEarLobe = landmarks[454]; // Right ear
        const chin = landmarks[152]; // Chin
        const forehead = landmarks[10]; // Forehead

        // Calculate yaw (left/right rotation)
        const earDistance = rightEarLobe.x - leftEarLobe.x;
        const noseOffsetX = noseTip.x - (leftEarLobe.x + rightEarLobe.x) / 2;
        const yaw = (noseOffsetX / earDistance) * 45; // Convert to degrees (approx)

        // Calculate pitch (up/down rotation)
        const verticalCenter = (forehead.y + chin.y) / 2;
        const noseOffsetY = noseTip.y - verticalCenter;
        const pitch = (noseOffsetY * 45);

        // Calculate roll (tilt rotation)
        const eyeLeftInner = landmarks[133];
        const eyeRightInner = landmarks[362];
        const eyeAngle = Math.atan2(eyeRightInner.y - eyeLeftInner.y, eyeRightInner.x - eyeLeftInner.x);
        const roll = (eyeAngle * 180) / Math.PI;

        return {
            pitch: parseFloat(pitch.toFixed(2)),
            yaw: parseFloat(yaw.toFixed(2)),
            roll: parseFloat(roll.toFixed(2))
        };
    }

    /**
     * Calculate and store metrics
     */
    _calculateAndStoreMetrics() {
        if (this.frameBuffer.length === 0) {
            return;
        }

        // Calculate average metrics from frame buffer
        const avgEyeOpen = this.eyeOpenBuffer.reduce((a, b) => a + b, 0) / this.eyeOpenBuffer.length;
        const avgMouthOpen = this.mouthOpenBuffer.reduce((a, b) => a + b, 0) / this.mouthOpenBuffer.length;

        // Blink rate: count transitions from eye open to closed
        const blinkCount = this._countBlinks(this.eyeOpenBuffer);
        const blinkRate = (blinkCount / (this.config.updateInterval / 1000)) * 60; // Per minute

        // Gaze direction: percentage looking at camera
        const gazeAtCameraCount = this.gazeFrameBuffer.filter(g => g.direction === 'center').length;
        const gazeAtCameraPercent = (gazeAtCameraCount / this.gazeFrameBuffer.length) * 100;

        // Average head pose
        const avgPitch = this.headPoseBuffer.reduce((a, b) => a + b.pitch, 0) / this.headPoseBuffer.length;
        const avgYaw = this.headPoseBuffer.reduce((a, b) => a + b.yaw, 0) / this.headPoseBuffer.length;
        const avgRoll = this.headPoseBuffer.reduce((a, b) => a + b.roll, 0) / this.headPoseBuffer.length;

        // Create metric entry
        const metric = {
            timestamp: Date.now(),
            secondsElapsed: (Date.now() - this.recordingStartTime) / 1000,
            eyeOpenPercentage: parseFloat((avgEyeOpen * 100).toFixed(2)),
            mouthOpenPercentage: parseFloat((avgMouthOpen * 100).toFixed(2)),
            blinkRatePerMinute: parseFloat(blinkRate.toFixed(2)),
            gazeAtCameraPercent: parseFloat(gazeAtCameraPercent.toFixed(2)),
            headPose: {
                pitch: parseFloat(avgPitch.toFixed(2)),
                yaw: parseFloat(avgYaw.toFixed(2)),
                roll: parseFloat(avgRoll.toFixed(2))
            },
            speakingDetected: avgMouthOpen > 0.3 // Simple speech detection
        };

        this.metrics.push(metric);

        // Notify callback
        if (this.config.onMetricsUpdate) {
            this.config.onMetricsUpdate(metric);
        }

        // Reset buffers
        this.frameBuffer = [];
        this.eyeOpenBuffer = [];
        this.mouthOpenBuffer = [];
        this.gazeFrameBuffer = [];
        this.headPoseBuffer = [];
    }

    /**
     * Count eye blinks in a buffer of eye open status
     */
    _countBlinks(eyeBuffer) {
        let blinks = 0;
        for (let i = 1; i < eyeBuffer.length; i++) {
            // Blink detected: transition from open to closed (1 to 0)
            if (eyeBuffer[i - 1] > 0.5 && eyeBuffer[i] < 0.5) {
                blinks++;
            }
        }
        return blinks;
    }

    /**
     * Draw visualization on canvas
     */
    _drawVisualization(landmarks, frameAnalysis) {
        if (!this.config.canvasElement) {
            return;
        }

        const ctx = this.config.canvasElement.getContext('2d');
        const canvas = this.config.canvasElement;

        // Sync canvas size with video once or when changed to avoid flickering/context reset
        if (this.config.videoElement && (canvas.width !== this.config.videoElement.videoWidth || canvas.height !== this.config.videoElement.videoHeight)) {
            canvas.width = this.config.videoElement.videoWidth;
            canvas.height = this.config.videoElement.videoHeight;
        }

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw face mesh dots
        const dotSize = 2;
        landmarks.forEach(landmark => {
            const x = landmark.x * canvas.width;
            const y = landmark.y * canvas.height;

            ctx.beginPath();
            ctx.arc(x, y, dotSize, 0, 2 * Math.PI);
            ctx.fillStyle = 'rgba(0, 255, 0, 0.6)';
            ctx.fill();
        });

        // Draw head pose indicator
        this._drawHeadPoseIndicator(ctx, frameAnalysis.headPose, canvas);

        // Draw gaze indicator
        this._drawGazeIndicator(ctx, frameAnalysis.gaze, canvas);
    }

    /**
     * Draw head pose on canvas
     */
    _drawHeadPoseIndicator(ctx, headPose, canvas) {
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 40;

        // Draw circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw orientation indicator
        const yaw = (headPose.yaw / 90) * radius;
        const pitch = (headPose.pitch / 90) * radius;

        ctx.beginPath();
        ctx.arc(centerX + yaw, centerY + pitch, 8, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(0, 255, 0, 0.8)';
        ctx.fill();
    }

    /**
     * Draw gaze indicator on canvas
     */
    _drawGazeIndicator(ctx, gaze, canvas) {
        const x = gaze.x * canvas.width;
        const y = gaze.y * canvas.height;
        const radius = 20;

        // Color based on confidence
        let color = gaze.direction === 'center'
            ? 'rgba(0, 255, 0, 0.7)'  // Green - looking at camera
            : 'rgba(255, 165, 0, 0.7)'; // Orange - looking away

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.stroke();
    }

    /**
     * Stop analysis and clean up
     */
    stop() {
        this.isRunning = false;

        // Final flush of metrics if there are pending frames
        if (this.frameBuffer.length > 0) {
            this._calculateAndStoreMetrics();
        }

        if (this.config.videoElement && this.config.videoElement.srcObject) {
            const tracks = this.config.videoElement.srcObject.getTracks();
            tracks.forEach(track => track.stop());
        }

        return this.metrics;
    }

    /**
     * Get collected metrics
     */
    getMetrics() {
        return this.metrics;
    }

    /**
     * Get summary statistics
     */
    getSummary() {
        if (this.metrics.length === 0) {
            return null;
        }

        const avgGazeAtCamera = this.metrics.reduce((a, b) => a + b.gazeAtCameraPercent, 0) / this.metrics.length;
        const avgBlinkRate = this.metrics.reduce((a, b) => a + b.blinkRatePerMinute, 0) / this.metrics.length;
        const avgEyeOpen = this.metrics.reduce((a, b) => a + b.eyeOpenPercentage, 0) / this.metrics.length;
        const speakingPercentage = (this.metrics.filter(m => m.speakingDetected).length / this.metrics.length) * 100;

        // Calculate average head pose
        const avgHeadPose = {
            pitch: this.metrics.reduce((a, b) => a + b.headPose.pitch, 0) / this.metrics.length,
            yaw: this.metrics.reduce((a, b) => a + b.headPose.yaw, 0) / this.metrics.length,
            roll: this.metrics.reduce((a, b) => a + b.headPose.roll, 0) / this.metrics.length
        };

        return {
            totalDuration: (Date.now() - this.recordingStartTime) / 1000,
            averageGazeAtCamera: parseFloat(avgGazeAtCamera.toFixed(2)),
            averageBlinkRate: parseFloat(avgBlinkRate.toFixed(2)),
            averageEyeOpenPercentage: parseFloat(avgEyeOpen.toFixed(2)),
            speakingPercentage: parseFloat(speakingPercentage.toFixed(2)),
            averageHeadPose: {
                pitch: parseFloat(avgHeadPose.pitch.toFixed(2)),
                yaw: parseFloat(avgHeadPose.yaw.toFixed(2)),
                roll: parseFloat(avgHeadPose.roll.toFixed(2))
            },
            metricsCount: this.metrics.length
        };
    }
}

// Export for use as module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoAnalyzer;
}
export default VideoAnalyzer;
window.VideoAnalyzer = VideoAnalyzer;
