import SwiftUI
import WebKit

enum PointGo {
    /// Same room on the phone and on the glasses. Change both together.
    static let room = "worn-pg-k7x2m9q4"
    static let base = "https://francolinx.github.io/worn-smart-glasses/"
    static var phoneURL: URL { URL(string: base + "indoor.html?room=" + room)! }
}

struct ContentView: View {
    @State private var reloadToken = 0
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("Point & Go").font(.headline)
                Spacer()
                Text("room: " + PointGo.room).font(.caption).foregroundColor(.secondary)
                Button("Reload") { reloadToken += 1 }.padding(.leading, 8)
            }.padding(.horizontal, 12).padding(.vertical, 6).background(Color.black)
            WebView(url: PointGo.phoneURL, reloadToken: reloadToken)
        }.background(Color.black)
    }
}

struct WebView: UIViewRepresentable {
    let url: URL
    let reloadToken: Int

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.allowsInlineMediaPlayback = true
        cfg.websiteDataStore = .default()                       // keeps the survey pack (IndexedDB) between launches
        let v = WKWebView(frame: .zero, configuration: cfg)
        v.uiDelegate = context.coordinator
        v.navigationDelegate = context.coordinator
        v.isOpaque = false
        v.backgroundColor = .black
        v.scrollView.backgroundColor = .black
        v.allowsBackForwardNavigationGestures = true
        v.load(URLRequest(url: url, cachePolicy: .reloadRevalidatingCacheData))
        return v
    }

    func updateUIView(_ v: WKWebView, context: Context) {
        if context.coordinator.lastToken != reloadToken { context.coordinator.lastToken = reloadToken; v.load(URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData)) }
    }

    /// The page uses alert / confirm / prompt and opens the glasses page in a new tab. A bare WKWebView ignores all of these.
    final class Coordinator: NSObject, WKUIDelegate, WKNavigationDelegate {
        var lastToken = 0
        private func top() -> UIViewController? {
            var c = UIApplication.shared.connectedScenes.compactMap { ($0 as? UIWindowScene)?.keyWindow }.first?.rootViewController
            while let p = c?.presentedViewController { c = p }
            return c
        }
        func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
            let a = UIAlertController(title: nil, message: message, preferredStyle: .alert)
            a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler() })
            if let t = top() { t.present(a, animated: true) } else { completionHandler() }
        }
        func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
            let a = UIAlertController(title: nil, message: message, preferredStyle: .alert)
            a.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(false) })
            a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) })
            if let t = top() { t.present(a, animated: true) } else { completionHandler(false) }
        }
        func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String, defaultText: String?, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
            let a = UIAlertController(title: nil, message: prompt, preferredStyle: .alert)
            a.addTextField { $0.text = defaultText }
            a.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(nil) })
            a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(a.textFields?.first?.text) })
            if let t = top() { t.present(a, animated: true) } else { completionHandler(nil) }
        }
        func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
            if let u = navigationAction.request.url { UIApplication.shared.open(u) }       // links with target=_blank open in Safari
            return nil
        }
        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            webView.loadHTMLString("<body style='background:#000;color:#fff;font:20px -apple-system;padding:40px'>No connection.<br><br>\(error.localizedDescription)<br><br>Tap Reload.</body>", baseURL: nil)
        }
    }
}
