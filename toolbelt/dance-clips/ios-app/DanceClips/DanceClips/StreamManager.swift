import AVFoundation
import UIKit

/// Manages camera capture and streaming to relay server
class StreamManager: NSObject, ObservableObject {
    @Published var isStreaming = false
    @Published var status = "Initializing..."
    @Published var showDebug = true
    @Published var cameraReady = false

    private var captureSession: AVCaptureSession?
    private var videoOutput: AVCaptureVideoDataOutput?
    private var audioOutput: AVCaptureAudioDataOutput?
    private var webSocket: URLSessionWebSocketTask?

    private let relayURL = "wss://dance.danyelica.fish"
    private var clientId: String?
    private var streamKey: String?

    // Video encoding
    private var assetWriter: AVAssetWriter?
    private var videoInput: AVAssetWriterInput?
    private var audioInput: AVAssetWriterInput?
    private var isWriting = false

    private let sessionQueue = DispatchQueue(label: "camera.session")
    private let outputQueue = DispatchQueue(label: "camera.output")

    func setup() {
        sessionQueue.async { [weak self] in
            self?.setupCaptureSession()
        }
    }

    private func setupCaptureSession() {
        let session = AVCaptureSession()
        session.sessionPreset = .hd1280x720

        // Video input (front camera)
        guard let videoDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front),
              let videoInput = try? AVCaptureDeviceInput(device: videoDevice) else {
            updateStatus("Camera not available")
            return
        }

        if session.canAddInput(videoInput) {
            session.addInput(videoInput)
        }

        // Audio input (microphone) - THIS captures background music via speakers!
        if let audioDevice = AVCaptureDevice.default(for: .audio),
           let audioInput = try? AVCaptureDeviceInput(device: audioDevice) {
            if session.canAddInput(audioInput) {
                session.addInput(audioInput)
                print("Audio input added - mic will capture background music")
            }
        }

        // Video output
        let videoOutput = AVCaptureVideoDataOutput()
        videoOutput.setSampleBufferDelegate(self, queue: outputQueue)
        videoOutput.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
        ]
        if session.canAddOutput(videoOutput) {
            session.addOutput(videoOutput)
        }
        self.videoOutput = videoOutput

        // Audio output
        let audioOutput = AVCaptureAudioDataOutput()
        audioOutput.setSampleBufferDelegate(self, queue: outputQueue)
        if session.canAddOutput(audioOutput) {
            session.addOutput(audioOutput)
        }
        self.audioOutput = audioOutput

        self.captureSession = session
        session.startRunning()

        DispatchQueue.main.async {
            self.cameraReady = true
            self.updateStatus("Ready - set phone down to stream")
        }
    }

    func startStreaming() {
        guard !isStreaming, cameraReady else { return }

        clientId = "ios_\(Int(Date().timeIntervalSince1970 * 1000))"
        updateStatus("Creating YouTube broadcast...")

        // For now, use a test stream key or implement YouTube OAuth
        // This is a placeholder - you'll need to add YouTube API integration
        Task {
            await registerWithRelay()
            await connectWebSocket()

            DispatchQueue.main.async {
                self.isStreaming = true
                self.updateStatus("LIVE")
            }
        }
    }

    func stopStreaming() {
        guard isStreaming else { return }

        isStreaming = false
        webSocket?.cancel(with: .normalClosure, reason: nil)
        webSocket = nil

        updateStatus("Stopped")
    }

    private func registerWithRelay() async {
        guard let clientId = clientId else { return }

        // TODO: Get actual stream key from YouTube API
        // For testing, you can hardcode a stream key temporarily
        let testStreamKey = "YOUR-STREAM-KEY-HERE"
        self.streamKey = testStreamKey

        let url = URL(string: "\(relayURL.replacingOccurrences(of: "wss://", with: "https://"))/start-stream")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "streamKey": testStreamKey,
            "clientId": clientId,
            "mimeType": "video/mp4"  // iOS uses MP4
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                print("Registered with relay server")
            }
        } catch {
            print("Failed to register: \(error)")
        }
    }

    private func connectWebSocket() async {
        guard let clientId = clientId else { return }

        let url = URL(string: "\(relayURL)?clientId=\(clientId)")!
        let session = URLSession(configuration: .default)
        webSocket = session.webSocketTask(with: url)
        webSocket?.resume()

        print("WebSocket connected")
    }

    private func sendVideoData(_ data: Data) {
        guard let webSocket = webSocket, isStreaming else { return }

        let message = URLSessionWebSocketTask.Message.data(data)
        webSocket.send(message) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }

    private func updateStatus(_ text: String) {
        DispatchQueue.main.async {
            self.status = text
        }
    }
}

// MARK: - AVCaptureVideoDataOutputSampleBufferDelegate
extension StreamManager: AVCaptureVideoDataOutputSampleBufferDelegate, AVCaptureAudioDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard isStreaming else { return }

        // TODO: Encode and send video/audio data
        // For a full implementation, you'd use VideoToolbox or AVAssetWriter
        // to encode H.264 video + AAC audio, then send over WebSocket

        // Placeholder: just count frames for now
        if output == videoOutput {
            // Video frame received
        } else if output == audioOutput {
            // Audio samples received (includes background music!)
        }
    }
}
