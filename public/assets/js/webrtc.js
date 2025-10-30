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
        this.socket = socket;
        this.setupSocketListeners();
    }
    
    setupSocketListeners() {
        this.socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'call_offer':
                    this.handleCallOffer(data);
                    break;
                case 'call_answer':
                    this.handleCallAnswer(data);
                    break;
                case 'ice_candidate':
                    this.handleIceCandidate(data);
                    break;
                case 'call_end':
                    this.handleCallEnd(data);
                    break;
                case 'call_declined':
                    this.handleCallDeclined(data);
                    break;
            }
        });
    }
    
    async initializeCall(isVideo = false) {
        try {
            // Get user media
            const constraints = {
                audio: true,
                video: isVideo
            };
            
            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Create peer connection
            this.peerConnection = new RTCPeerConnection(this.configuration);
            
            // Add local stream to peer connection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });
            
            // Handle remote stream
            this.peerConnection.ontrack = (event) => {
                this.remoteStream = event.streams[0];
                this.displayRemoteStream();
            };
            
            // Handle ICE candidates
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
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
            this.showError('Unable to access camera/microphone');
            return false;
        }
    }
    
    async startCall(userId, isVideo = false) {
        if (this.isCallActive) {
            this.showError('A call is already in progress');
            return;
        }
        
        const initialized = await this.initializeCall(isVideo);
        if (!initialized) return;
        
        this.currentCall = {
            userId: userId,
            roomId: `call_${Date.now()}`,
            isVideo: isVideo,
            isInitiator: true
        };
        
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
        if (this.isCallActive) {
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
            isInitiator: false
        };
        
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
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        }
    }
    
    showCallUI(state) {
        // Create or show call interface
        let callUI = document.getElementById('call-interface');
        if (!callUI) {
            callUI = this.createCallUI();
            document.body.appendChild(callUI);
        }
        
        callUI.style.display = 'flex';
        callUI.className = `call-interface call-${state}`;
        
        // Display local video if video call
        if (this.currentCall.isVideo && this.localStream) {
            const localVideo = document.getElementById('local-video');
            if (localVideo) {
                localVideo.srcObject = this.localStream;
            }
        }
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
        const remoteVideo = document.getElementById('remote-video');
        if (remoteVideo && this.remoteStream) {
            remoteVideo.srcObject = this.remoteStream;
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
        // You can integrate with your existing notification system here
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
                        <button id="mute-btn" class="control-btn" onclick="webrtcManager.toggleMute()">
                            <ion-icon name="mic"></ion-icon>
                        </button>
                        <button id="video-btn" class="control-btn" onclick="webrtcManager.toggleVideo()">
                            <ion-icon name="videocam"></ion-icon>
                        </button>
                        <button id="end-call-btn" class="control-btn end-call" onclick="webrtcManager.endCall()">
                            <ion-icon name="call"></ion-icon>
                        </button>
                    </div>
                </div>
            </div>
        `;
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
                        <button class="accept-btn" onclick="webrtcManager.acceptCall()">
                            <ion-icon name="call"></ion-icon>
                        </button>
                        <button class="decline-btn" onclick="webrtcManager.declineCall()">
                            <ion-icon name="call"></ion-icon>
                        </button>
                    </div>
                </div>
            </div>
        `;
        return incomingUI;
    }
}

// Initialize WebRTC manager
window.webrtcManager = new WebRTCManager();