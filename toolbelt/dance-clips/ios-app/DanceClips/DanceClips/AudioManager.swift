import AVFoundation

/// Manages audio session to allow background music while recording
class AudioManager {
    static let shared = AudioManager()

    private init() {}

    /// Configure audio session to allow music playback during recording
    /// This is the KEY to making background music work!
    func configureAudioSession() {
        let audioSession = AVAudioSession.sharedInstance()

        do {
            // .playAndRecord: Allows both playback and recording
            // .mixWithOthers: Don't interrupt other audio (Spotify, Apple Music, etc.)
            // .defaultToSpeaker: Route audio to speaker (not earpiece)
            try audioSession.setCategory(
                .playAndRecord,
                mode: .videoRecording,
                options: [.mixWithOthers, .defaultToSpeaker, .allowBluetooth]
            )

            // Activate the session
            try audioSession.setActive(true)

            print("Audio session configured: background music should keep playing!")

        } catch {
            print("Failed to configure audio session: \(error)")
        }
    }

    /// Check if audio session is properly configured
    func isConfiguredForMixing() -> Bool {
        let audioSession = AVAudioSession.sharedInstance()
        return audioSession.category == .playAndRecord &&
               audioSession.categoryOptions.contains(.mixWithOthers)
    }
}
