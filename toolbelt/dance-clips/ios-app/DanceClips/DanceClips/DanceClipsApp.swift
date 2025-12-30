import SwiftUI
import AVFoundation

@main
struct DanceClipsApp: App {
    init() {
        // Configure audio session on app launch
        AudioManager.shared.configureAudioSession()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
