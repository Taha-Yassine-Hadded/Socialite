class WebRTCManager {
    constructor() {
        this.localStream = null;
        this.remoteStream = null;
        this.peerConnection = null;
        this.socket = null;
        this.currentCall = null;
        this.isCallActive = false;
        this.isMuted = false;
        this.isVideoEnabled = true;
        this.callStartTime = null;
        this.callTimer = null;
        
        // WebRTC configuration
        this.configuration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
    }
    
    setSocket(socket) {
        console.log('Setting WebSocket for WebRTC manager:', socket);
        this.socket = socket;
        console.log('WebSocket set successfully, setting up listeners...');
        this.setupSocketListeners();
    }
    
    setupSocketListeners() {
        this.socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket message:', data);
            
            switch (data.type) {
                case 'call_offer':
                    console.log('Received call offer from user:', data.sender_id);
                    this.handleCallOffer(data);
                    break;
                case 'call_answer':
                    console.log('Received call answer from user:', data.sender_id);
                    this.handleCallAnswer(data);
                    break;
                case 'ice_candidate':
                    console.log('Received ICE candidate from user:', data.sender_id);
                    this.handleIceCandidate(data);
                    break;
                case 'call_end':
                    console.log('Received call end from user:', data.sender_id);
                    this.handleCallEnd(data);
                    break;
                case 'call_declined':
                    console.log('Received call declined from user:', data.sender_id);
                    this.handleCallDeclined(data);
                    break;
            }
        });
    }
    
    async initializeCall(isVideo = false) {
        try {
            console.log('Requesting media access - Audio: true, Video:', isVideo);
            
            // Get user media
            const constraints = {
                audio: true,
                video: isVideo
            };
            
            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log('Media access granted, local stream:', this.localStream);
            
            // Create peer connection
            this.peerConnection = new RTCPeerConnection(this.configuration);
            console.log('Peer connection created:', this.peerConnection);
            
            // Add local stream to peer connection
            this.localStream.getTracks().forEach(track => {
                console.log('Adding track to peer connection:', track.kind);
                this.peerConnection.addTrack(track, this.localStream);
            });
            
            // Handle remote stream
            this.peerConnection.ontrack = (event) => {
                console.log('Received remote stream:', event.streams[0]);
                this.remoteStream = event.streams[0];
                this.displayRemoteStream();
            };
            
            // Handle ICE candidates
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    console.log('Sending ICE candidate:', event.candidate);
                    this.sendSignalingMessage({
                        type: 'ice_candidate',
                        candidate: event.candidate,
                        room_id: this.currentCall.roomId
                    });
                }
            };
            
            return true;
        } catch (error) {
            console.error('Error initializing call:', error);
            if (error.name === 'NotAllowedError') {
                this.showError('Camera/microphone access denied. Please allow access and try again.');
            } else if (error.name === 'NotFoundError') {
                this.showError('No camera/microphone found. Please check your devices.');
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                this.showError('Camera/microphone is already in use by another application or browser tab. Please close other tabs or use a different browser.');
            } else if (error.name === 'OverconstrainedError') {
                this.showError('Camera/microphone constraints cannot be satisfied. Try using a different device.');
            } else {
                this.showError('Unable to access camera/microphone: ' + error.message + ' (Error: ' + error.name + ')');
            }
            return false;
        }
    }
    
    async startCall(userId, isVideo = false) {
        console.log('=== STARTING CALL ===');
        console.log('startCall called with userId:', userId, 'isVideo:', isVideo);
        console.log('Current socket:', this.socket);
        console.log('Is call active:', this.isCallActive);
        console.log('Browser info:', navigator.userAgent);
        console.log('Available media devices check...');
        
        // Check available media devices
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            console.log('Available devices:', devices.filter(d => d.kind === 'videoinput' || d.kind === 'audioinput'));
        } catch (e) {
            console.log('Could not enumerate devices:', e);
        }
        
        if (this.isCallActive) {
            console.log('Call already active, showing error');
            this.showError('A call is already in progress');
            return;
        }
        
        if (!this.socket) {
            console.error('No WebSocket connection available for call');
            this.showError('No connection available. Please try again.');
            return;
        }
        
        console.log('Initializing call...');
        const initialized = await this.initializeCall(isVideo);
        if (!initialized) {
            console.log('Call initialization failed');
            return;
        }
        
        this.currentCall = {
            userId: userId,
            roomId: `call_${Date.now()}`,
            isVideo: isVideo,
            isInitiator: true
        };
        
        console.log('Call initialized, setting up UI and creating offer...');
        this.isCallActive = true;
        this.showCallUI('outgoing');
        
        try {
            // Create offer
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);
            
            // Send call offer
            this.sendSignalingMessage({
                type: 'call_offer',
                offer: offer,
                room_id: this.currentCall.roomId,
                recipient_id: userId,
                is_video: isVideo
            });
            
        } catch (error) {
            console.error('Error starting call:', error);
            this.endCall();
        }
    }
    
    async handleCallOffer(data) {
        console.log('Processing incoming call offer:', data);
        
        if (this.isCallActive) {
            console.log('Already in a call, declining incoming call');
            // Decline if already in a call
            this.sendSignalingMessage({
                type: 'call_declined',
                room_id: data.room_id,
                recipient_id: data.sender_id
            });
            return;
        }

        this.currentCall = {
            userId: data.sender_id,
            roomId: data.room_id,
            isVideo: data.is_video,
            isInitiator: false,
            offer: data.offer
        };

        console.log('Showing incoming call UI for:', data.sender_name);
        // Show incoming call UI
        this.showIncomingCallUI(data);
    }
    
    async acceptCall() {
        const initialized = await this.initializeCall(this.currentCall.isVideo);
        if (!initialized) {
            this.declineCall();
            return;
        }
        
        this.isCallActive = true;
        this.showCallUI('active');
        
        try {
            // Set remote description
            await this.peerConnection.setRemoteDescription(this.currentCall.offer);
            
            // Create answer
            const answer = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(answer);
            
            // Send answer
            this.sendSignalingMessage({
                type: 'call_answer',
                answer: answer,
                room_id: this.currentCall.roomId,
                recipient_id: this.currentCall.userId
            });
            
        } catch (error) {
            console.error('Error accepting call:', error);
            this.endCall();
        }
    }
    
    declineCall() {
        this.sendSignalingMessage({
            type: 'call_declined',
            room_id: this.currentCall.roomId,
            recipient_id: this.currentCall.userId
        });
        
        this.hideIncomingCallUI();
        this.currentCall = null;
    }
    
    async handleCallAnswer(data) {
        try {
            await this.peerConnection.setRemoteDescription(data.answer);
            this.showCallUI('active');
        } catch (error) {
            console.error('Error handling call answer:', error);
            this.endCall();
        }
    }
    
    async handleIceCandidate(data) {
        try {
            await this.peerConnection.addIceCandidate(data.candidate);
        } catch (error) {
            console.error('Error adding ICE candidate:', error);
        }
    }
    
    handleCallEnd(data) {
        this.endCall();
    }
    
    handleCallDeclined(data) {
        this.showError('Call declined');
        this.endCall();
    }
    
    endCall() {
        // Send end call signal
        if (this.currentCall && this.isCallActive) {
            this.sendSignalingMessage({
                type: 'call_end',
                room_id: this.currentCall.roomId,
                recipient_id: this.currentCall.userId
            });
        }
        
        // Clean up streams
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }
        
        // Clean up peer connection
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }
        
        // Reset state
        this.isCallActive = false;
        this.currentCall = null;
        this.remoteStream = null;
        
        // Hide call UI
        this.hideCallUI();
    }
    
    toggleMute() {
        if (this.localStream) {
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                this.isMuted = !audioTrack.enabled;
                this.updateMuteButton();
            }
        }
    }
    
    toggleVideo() {
        if (this.localStream) {
            const videoTrack = this.localStream.getVideoTracks()[0];
            if (videoTrack) {
                videoTrack.enabled = !videoTrack.enabled;
                this.isVideoEnabled = videoTrack.enabled;
                this.updateVideoButton();
            }
        }
    }
    
    sendSignalingMessage(message) {
        console.log('Sending WebRTC signaling message:', message);
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
            console.log('WebRTC message sent successfully');
        } else {
            console.error('WebSocket not connected, cannot send WebRTC message');
        }
    }
    
    showCallUI(state) {
        console.log('Showing call UI with state:', state);
        
        // Create or show call interface
        let callUI = document.getElementById('call-interface');
        if (!callUI) {
            console.log('Creating new call UI');
            callUI = this.createCallUI();
            document.body.appendChild(callUI);
        }
        
        callUI.style.display = 'flex';
        callUI.className = `call-interface call-${state}`;
        
        // Display local video if available
        setTimeout(() => {
            if (this.localStream) {
                const localVideo = document.getElementById('local-video');
                if (localVideo) {
                    console.log('Setting local video stream');
                    localVideo.srcObject = this.localStream;
                    localVideo.play().catch(e => console.error('Error playing local video:', e));
                } else {
                    console.error('Local video element not found');
                }
            } else {
                console.log('No local stream available yet');
            }
        }, 200);
    }
    
    showIncomingCallUI(data) {
        let incomingCallUI = document.getElementById('incoming-call');
        if (!incomingCallUI) {
            incomingCallUI = this.createIncomingCallUI();
            document.body.appendChild(incomingCallUI);
        }
        
        // Store offer for later use
        this.currentCall.offer = data.offer;
        
        // Update UI with caller info
        const callerName = document.getElementById('caller-name');
        const callType = document.getElementById('call-type');
        
        if (callerName) callerName.textContent = `User ${data.sender_id}`;
        if (callType) callType.textContent = data.is_video ? 'Video Call' : 'Voice Call';
        
        incomingCallUI.style.display = 'flex';
    }
    
    hideIncomingCallUI() {
        const incomingCallUI = document.getElementById('incoming-call');
        if (incomingCallUI) {
            incomingCallUI.style.display = 'none';
        }
    }
    
    hideCallUI() {
        const callUI = document.getElementById('call-interface');
        if (callUI) {
            callUI.style.display = 'none';
        }
        this.hideIncomingCallUI();
    }
    
    displayRemoteStream() {
        console.log('Displaying remote stream:', this.remoteStream);
        const remoteVideo = document.getElementById('remote-video');
        if (remoteVideo && this.remoteStream) {
            console.log('Setting remote video stream');
            remoteVideo.srcObject = this.remoteStream;
            remoteVideo.play().catch(e => console.error('Error playing remote video:', e));
        } else {
            console.error('Remote video element not found or no remote stream');
        }
    }
    
    updateMuteButton() {
        const muteBtn = document.getElementById('mute-btn');
        if (muteBtn) {
            muteBtn.innerHTML = this.isMuted ? 
                '<ion-icon name="mic-off"></ion-icon>' : 
                '<ion-icon name="mic"></ion-icon>';
            muteBtn.classList.toggle('muted', this.isMuted);
        }
    }
    
    updateVideoButton() {
        const videoBtn = document.getElementById('video-btn');
        if (videoBtn) {
            videoBtn.innerHTML = this.isVideoEnabled ? 
                '<ion-icon name="videocam"></ion-icon>' : 
                '<ion-icon name="videocam-off"></ion-icon>';
            videoBtn.classList.toggle('disabled', !this.isVideoEnabled);
        }
    }
    
    showError(message) {
        // Show error notification
        console.error('WebRTC Error:', message);
        
        // Create and show error notification
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            z-index: 10000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    createCallUI() {
        const callUI = document.createElement('div');
        callUI.id = 'call-interface';
        callUI.innerHTML = `
            <div class="call-overlay">
                <div class="call-container">
                    <div class="video-container">
                        <video id="remote-video" autoplay playsinline class="remote-video"></video>
                        <video id="local-video" autoplay playsinline muted class="local-video"></video>
                    </div>
                    <div class="call-controls">
                        <button id="mute-btn" class="control-btn">
                            <ion-icon name="mic"></ion-icon>
                        </button>
                        <button id="video-btn" class="control-btn">
                            <ion-icon name="videocam"></ion-icon>
                        </button>
                        <button id="end-call-btn" class="control-btn end-call">
                            <ion-icon name="call"></ion-icon>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners after creating the UI
        setTimeout(() => {
            const muteBtn = document.getElementById('mute-btn');
            const videoBtn = document.getElementById('video-btn');
            const endCallBtn = document.getElementById('end-call-btn');
            
            if (muteBtn) {
                muteBtn.addEventListener('click', () => this.toggleMute());
            }
            if (videoBtn) {
                videoBtn.addEventListener('click', () => this.toggleVideo());
            }
            if (endCallBtn) {
                endCallBtn.addEventListener('click', () => this.endCall());
            }
        }, 100);
        
        return callUI;
    }
    
    createIncomingCallUI() {
        const incomingUI = document.createElement('div');
        incomingUI.id = 'incoming-call';
        incomingUI.innerHTML = `
            <div class="incoming-call-overlay">
                <div class="incoming-call-container">
                    <div class="caller-info">
                        <div class="caller-avatar">
                            <ion-icon name="person-circle"></ion-icon>
                        </div>
                        <h3 id="caller-name">Unknown Caller</h3>
                        <p id="call-type">Voice Call</p>
                    </div>
                    <div class="call-actions">
                        <button class="accept-btn" id="accept-call-btn">
                            <ion-icon name="call"></ion-icon>
                        </button>
                        <button class="decline-btn" id="decline-call-btn">
                            <ion-icon name="call"></ion-icon>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners after creating the UI
        setTimeout(() => {
            const acceptBtn = document.getElementById('accept-call-btn');
            const declineBtn = document.getElementById('decline-call-btn');
            
            if (acceptBtn) {
                acceptBtn.addEventListener('click', () => this.acceptCall());
            }
            if (declineBtn) {
                declineBtn.addEventListener('click', () => this.declineCall());
            }
        }, 100);
        
        return incomingUI;
    }
}