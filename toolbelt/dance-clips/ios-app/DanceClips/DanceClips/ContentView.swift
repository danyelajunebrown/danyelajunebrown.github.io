import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var streamManager = StreamManager()
    @StateObject private var motionManager = MotionManager()

    var body: some View {
        ZStack {
            // Full screen color indicator
            (streamManager.isStreaming ? Color.green : Color.red)
                .ignoresSafeArea()

            // Debug info (tap to toggle)
            VStack {
                Spacer()

                if streamManager.showDebug {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Status: \(streamManager.status)")
                        Text("Audio mixing: \(AudioManager.shared.isConfiguredForMixing() ? "YES" : "NO")")
                        Text("Motion: \(motionManager.isStill ? "STILL" : "MOVING")")
                        Text("Camera: \(streamManager.cameraReady ? "READY" : "...")")
                    }
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(.white)
                    .padding()
                    .background(Color.black.opacity(0.7))
                    .cornerRadius(8)
                    .padding()
                }
            }
        }
        .onTapGesture {
            streamManager.showDebug.toggle()
        }
        .onAppear {
            streamManager.setup()
            motionManager.startMonitoring()
        }
        .onChange(of: motionManager.isStill) { isStill in
            if isStill && !streamManager.isStreaming {
                // Phone set down - start streaming after delay
                DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                    if motionManager.isStill {
                        streamManager.startStreaming()
                    }
                }
            } else if !isStill && streamManager.isStreaming {
                // Phone picked up - stop streaming
                streamManager.stopStreaming()
            }
        }
    }
}

#Preview {
    ContentView()
}
