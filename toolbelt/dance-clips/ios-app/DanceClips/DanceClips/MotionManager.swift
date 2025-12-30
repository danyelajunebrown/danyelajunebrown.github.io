import CoreMotion
import Combine

/// Detects when phone is set down (still) or picked up (moving)
class MotionManager: ObservableObject {
    private let motionManager = CMMotionManager()
    private var lastMotionTime = Date()

    @Published var isStill = false

    private let stillThreshold: Double = 0.15  // Movement threshold
    private let stillDuration: TimeInterval = 1.0  // Seconds to consider "still"

    func startMonitoring() {
        guard motionManager.isAccelerometerAvailable else {
            print("Accelerometer not available")
            return
        }

        motionManager.accelerometerUpdateInterval = 0.1

        motionManager.startAccelerometerUpdates(to: .main) { [weak self] data, error in
            guard let self = self, let data = data else { return }

            // Calculate movement magnitude (deviation from gravity)
            let x = data.acceleration.x
            let y = data.acceleration.y
            let z = data.acceleration.z
            let magnitude = sqrt(x*x + y*y + z*z)
            let movement = abs(magnitude - 1.0)  // 1.0 = gravity

            if movement > self.stillThreshold {
                self.lastMotionTime = Date()
                if self.isStill {
                    self.isStill = false
                    print("Motion detected - phone picked up")
                }
            } else {
                let stillTime = Date().timeIntervalSince(self.lastMotionTime)
                if stillTime > self.stillDuration && !self.isStill {
                    self.isStill = true
                    print("Phone is still - set down")
                }
            }
        }
    }

    func stopMonitoring() {
        motionManager.stopAccelerometerUpdates()
    }
}
