/**
 * HireSight Dropzone Configuration
 * Advanced file upload handling with progress tracking and validation
 */

/**
 * Initialize Dropzone with HireSight-specific configuration
 * @param {string} selector - Dropzone element selector
 * @param {string} uploadUrl - Server endpoint for file uploads
 * @param {Object} options - Additional Dropzone options
 */
function initializeHireSightDropzone(selector, uploadUrl, options = {}) {
    // Default configuration
    const defaultConfig = {
        url: uploadUrl,
        maxFilesize: 10, // MB
        acceptedFiles: '.pdf,.doc,.docx,.PDF,.DOC,.DOCX',
        autoProcessQueue: false,
        uploadMultiple: true,
        parallelUploads: 3,
        maxFiles: 100,

        // Localization
        dictDefaultMessage: 'Drop files here to upload or click to browse',
        dictInvalidFileType: 'You cannot upload files of this type',
        dictFileTooBig: 'File is too big ({{filesize}}MB). Max filesize: {{maxFilesize}}MB',
        dictResponseError: 'Server responded with {{statusCode}} code',
        dictCancelUpload: 'Cancel upload',
        dictCancelUploadConfirmation: 'Are you sure you want to cancel this upload?',
        dictRemoveFile: 'Remove file',
        dictRemoveFileConfirmation: null,
        dictMaxFilesExceeded: 'You can only upload {{maxFiles}} files',

        // Styling
        previewsContainer: options.previewsContainer || '#file-list',

        // Response handling
        success: function (file, response) {
            console.log('File uploaded successfully:', file.name, response);
            if (response.success) {
                file.acceptedFile = true;
                // Update UI
                const fileElement = file.previewElement;
                if (fileElement) {
                    fileElement.classList.add('dz-complete');
                    fileElement.classList.remove('dz-processing');
                }
            } else {
                this.removeFile(file);
                console.error('Upload failed:', response.message);
            }
        },

        error: function (file, errorMessage, xhr) {
            console.error('Error uploading file:', file.name, errorMessage);
            const fileElement = file.previewElement;
            if (fileElement) {
                fileElement.classList.add('dz-error');
                // Add error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'dz-error-message text-red-600 text-xs mt-1';
                errorDiv.textContent = errorMessage;
                fileElement.appendChild(errorDiv);
            }
        },

        removedfile: function (file) {
            if (file.previewElement) {
                file.previewElement.parentNode.removeChild(file.previewElement);
            }
        },

        // Validation
        accept: function (file, done) {
            // Validate file type
            const validExtensions = ['pdf', 'doc', 'docx'];
            const fileExtension = file.name.split('.').pop().toLowerCase();

            if (!validExtensions.includes(fileExtension)) {
                done('Invalid file type. Please upload PDF, DOC, or DOCX files.');
            }
            // Validate file size
            else if (file.size > 10 * 1024 * 1024) { // 10MB
                done('File is too large. Maximum file size is 10MB.');
            }
            // Validate MIME type for extra security
            else if (!isValidMimeType(file.type)) {
                done('Invalid file MIME type.');
            }
            else {
                done();
            }
        },

        // Additional hooks
        init: function () {
            // Store reference to dropzone instance
            window.dropzoneInstance = this;

            // Handle drag enter/leave
            this.on('dragenter', function () {
                document.querySelector(selector).classList.add('dz-drag-hover');
            });

            this.on('dragleave', function () {
                document.querySelector(selector).classList.remove('dz-drag-hover');
            });

            // File added
            this.on('addedfile', function (file) {
                document.querySelector(selector).classList.remove('dz-drag-hover');
                updateFileCount();
            });

            // Upload started
            this.on('sending', function (file, xhr, formData) {
                // Add custom headers if needed
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            });

            // Queue completion
            this.on('queuecomplete', function () {
                console.log('All files processed');
                updateStats();
            });
        }
    };

    // Merge with provided options
    const config = { ...defaultConfig, ...options };

    return new Dropzone(selector, config);
}

/**
 * Validate MIME type against allowed types
 * @param {string} mimeType - File MIME type
 * @returns {boolean} - True if valid
 */
function isValidMimeType(mimeType) {
    const validMimeTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-word.document.macroEnabled.12',
    ];

    return validMimeTypes.includes(mimeType) || mimeType.includes('word') || mimeType.includes('pdf');
}

/**
 * Update file count display
 */
function updateFileCount() {
    const dropzone = window.dropzoneInstance;
    if (dropzone) {
        const totalFiles = dropzone.files.length;
        const uploadedFiles = dropzone.getUploadedFiles().length;
        const addedFiles = dropzone.getAddedFiles().length;

        document.getElementById('total-files').textContent = totalFiles;
        document.getElementById('files-uploaded').textContent = uploadedFiles;
        document.getElementById('pending-count').textContent = addedFiles - uploadedFiles;
    }
}

/**
 * Update statistics display
 */
function updateStats() {
    const dropzone = window.dropzoneInstance;
    if (dropzone) {
        const files = dropzone.files;
        const successful = files.filter(f => f.status === 'success').length;
        const failed = files.filter(f => f.status === 'error').length;

        document.getElementById('successful-count').textContent = successful;
        document.getElementById('error-count').textContent = failed;
    }
}

/**
 * Get total upload progress as percentage
 * @returns {number} - Progress percentage (0-100)
 */
function getOverallProgress() {
    const dropzone = window.dropzoneInstance;
    if (!dropzone || dropzone.files.length === 0) return 0;

    const totalProgress = dropzone.files.reduce((sum, file) => {
        return sum + (file.upload?.progress || 0);
    }, 0);

    return Math.round(totalProgress / dropzone.files.length);
}

/**
 * Remove all files from the queue
 */
function clearAllFiles() {
    const dropzone = window.dropzoneInstance;
    if (dropzone) {
        dropzone.removeAllFiles(true);
        document.getElementById('upload-overview').classList.add('hidden');
        updateFileCount();
    }
}

/**
 * Remove a specific file
 * @param {Object} file - File object to remove
 */
function removeFile(file) {
    const dropzone = window.dropzoneInstance;
    if (dropzone) {
        dropzone.removeFile(file);
        updateFileCount();
    }
}

/**
 * Start processing the upload queue
 * @returns {Promise} - Upload completion promise
 */
function startUpload() {
    const dropzone = window.dropzoneInstance;
    if (!dropzone) {
        console.error('Dropzone instance not found');
        return Promise.reject('Dropzone not initialized');
    }

    if (dropzone.files.length === 0) {
        return Promise.reject('No files to upload');
    }

    return new Promise((resolve, reject) => {
        dropzone.on('successmultiple', function (files, response) {
            resolve(response);
        });

        dropzone.on('errormultiple', function (files, response) {
            reject(response);
        });

        // Start the upload process
        dropzone.processQueue();
    });
}

/**
 * Get file statistics
 * @returns {Object} - Statistics object
 */
function getFileStats() {
    const dropzone = window.dropzoneInstance;
    if (!dropzone) return null;

    const files = dropzone.files;
    const uploadedFiles = dropzone.getUploadedFiles();
    const addedFiles = dropzone.getAddedFiles();

    return {
        total: files.length,
        uploaded: uploadedFiles.length,
        pending: addedFiles.length - uploadedFiles.length,
        successful: files.filter(f => f.status === 'success').length,
        failed: files.filter(f => f.status === 'error').length,
        processing: files.filter(f => f.status === 'processing').length,
        totalSize: files.reduce((sum, f) => sum + f.size, 0),
        progress: getOverallProgress(),
    };
}

/**
 * Format bytes to human readable format
 * @param {number} bytes - Number of bytes
 * @returns {string} - Formatted string
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Show upload notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds
 */
function showNotification(message, type = 'info', duration = 4000) {
    const notificationClass = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    }[type] || 'bg-blue-500';

    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-4 ${notificationClass} text-white rounded-lg shadow-lg animate-pulse z-50`;
    notification.innerHTML = `
        <div class="flex items-center">
            ${getNotificationIcon(type)}
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

/**
 * Get notification icon SVG
 * @param {string} type - Notification type
 * @returns {string} - SVG HTML
 */
function getNotificationIcon(type) {
    const icons = {
        success: '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        error: '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l-2-2m0 0l-2-2m2 2l2-2m-2 2l-2 2"></path></svg>',
        warning: '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4v2m0-12a9 9 0 110 18 9 9 0 010-18z"></path></svg>',
        info: '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };
    return icons[type] || icons.info;
}

// Auto-initialize if dropzone element exists on page load
document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('resumeDropzone')) {
        // Dropzone is initialized in the template's script tag
        console.log('Dropzone ready for initialization');
    }
});
