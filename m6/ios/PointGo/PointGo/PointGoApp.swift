import SwiftUI

/// Point & Go phone app for the demo: a full-screen web view on the hosted phone page.
/// The page takes the photo, matches it on the phone and sends the fix to the glasses. No MicroLumin SDK in this target.
@main
struct PointGoApp: App {
    var body: some Scene {
        WindowGroup { ContentView().ignoresSafeArea(.container, edges: .bottom).preferredColorScheme(.dark) }
    }
}
