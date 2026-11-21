import UIKit
import WebKit

/// OPTIONAL add-on for a fork of MLDemo (the kit's iOS sample). It is one self-contained file and calls no SDK API.
///
/// What it adds: the Point & Go phone page inside MLDemo, plus a "Use latest glasses photo" button. After you take a photo with
/// the glasses (MLDemo > Camera) and sync it (MLDemo > Files), the button finds the newest image inside MLDemo's own folders and
/// hands it to the page, so the fix comes from the glasses' camera instead of the phone's.
///
/// To wire it in (2 lines, in MLDemo's HomeViewController.swift or wherever its menu rows are built):
///     let vc = PointGoViewController()
///     navigationController?.pushViewController(vc, animated: true)
///
/// NOT TESTED on a device: where MLDemo saves synced files is not documented, so this searches Documents, Library and tmp.
/// If the button says "no image found", open MLDemo's Files screen, sync again, and check the Event Log for the save path.
final class PointGoViewController: UIViewController, WKUIDelegate {
    static let room = "worn-pg-k7x2m9q4"
    private let url = URL(string: "https://francolinx.github.io/worn-smart-glasses/indoor.html?room=" + PointGoViewController.room)!
    private var web: WKWebView!

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Point & Go"
        view.backgroundColor = .black
        web = WKWebView(frame: view.bounds, configuration: WKWebViewConfiguration())
        web.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        web.uiDelegate = self
        view.addSubview(web)
        web.load(URLRequest(url: url))
        navigationItem.rightBarButtonItems = [
            UIBarButtonItem(title: "Glasses photo", style: .plain, target: self, action: #selector(useLatestGlassesPhoto)),
            UIBarButtonItem(barButtonSystemItem: .refresh, target: self, action: #selector(reload))
        ]
    }

    @objc private func reload() { web.load(URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData)) }

    /// Newest .jpg / .jpeg / .png / .heic anywhere in this app's sandbox, sent to the page as a data URL.
    @objc private func useLatestGlassesPhoto() {
        let fm = FileManager.default
        let roots = [fm.urls(for: .documentDirectory, in: .userDomainMask).first, fm.urls(for: .libraryDirectory, in: .userDomainMask).first, URL(fileURLWithPath: NSTemporaryDirectory())].compactMap { $0 }
        var best: (URL, Date)?
        for root in roots {
            guard let e = fm.enumerator(at: root, includingPropertiesForKeys: [.contentModificationDateKey], options: [.skipsHiddenFiles]) else { continue }
            for case let f as URL in e where ["jpg", "jpeg", "png", "heic"].contains(f.pathExtension.lowercased()) {
                let d = (try? f.resourceValues(forKeys: [.contentModificationDateKey]).contentModificationDate) ?? .distantPast
                if best == nil || d > best!.1 { best = (f, d) }
            }
        }
        guard let (file, date) = best, let img = UIImage(contentsOfFile: file.path), let jpg = img.jpegData(compressionQuality: 0.85) else { return say("No image found in MLDemo's folders. Take a photo with the glasses (Camera), sync it (Files), then try again.") }
        let js = "window.PG_usePhoto && window.PG_usePhoto('data:image/jpeg;base64,\(jpg.base64EncodedString())')"
        web.evaluateJavaScript(js) { _, err in self.say(err == nil ? "Sent \(file.lastPathComponent) (\(Int(-date.timeIntervalSinceNow)) s old) to Point & Go." : "The page was not ready: \(err!.localizedDescription)") }
    }

    private func say(_ t: String) { let a = UIAlertController(title: nil, message: t, preferredStyle: .alert); a.addAction(UIAlertAction(title: "OK", style: .default)); present(a, animated: true) }

    // the page uses alert / confirm / prompt
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let a = UIAlertController(title: nil, message: message, preferredStyle: .alert); a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler() }); present(a, animated: true)
    }
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let a = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        a.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(false) }); a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) }); present(a, animated: true)
    }
    func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String, defaultText: String?, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
        let a = UIAlertController(title: nil, message: prompt, preferredStyle: .alert); a.addTextField { $0.text = defaultText }
        a.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(nil) }); a.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(a.textFields?.first?.text) }); present(a, animated: true)
    }
}
