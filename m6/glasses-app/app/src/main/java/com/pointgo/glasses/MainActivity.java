package com.pointgo.glasses;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/**
 * Point & Go on the MicroLumin M6: a full-screen web view on the hosted glasses page.
 * The page does everything (floor schematic, route, arrow). This shell keeps the screen on, keeps the background black
 * (black is see-through on the waveguide), passes the touchpad / ring keys to the page, and retries when Wi-Fi drops.
 *
 * Change the page or the room without rebuilding:
 *   adb shell am start -n com.pointgo.glasses/.MainActivity --es room demo1
 *   adb shell am start -n com.pointgo.glasses/.MainActivity --es url "https://example.org/glasses.html?room=demo1"
 *   adb shell am start -n com.pointgo.glasses/.MainActivity --es mono 1        (green-only display)
 */
public class MainActivity extends Activity {
    static final String BASE = "https://francolinx.github.io/worn-smart-glasses/glasses.html";
    static final String DEFAULT_ROOM = "worn-pg-k7x2m9q4";
    private WebView web;
    private String url;
    private final Handler handler = new Handler();

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON | WindowManager.LayoutParams.FLAG_FULLSCREEN);
        web = new WebView(this);
        web.setBackgroundColor(Color.BLACK);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(false);
        s.setUseWideViewPort(false);
        s.setTextZoom(100);
        web.setWebViewClient(new WebViewClient() {
            @Override public void onReceivedError(WebView v, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) offline("No connection to the page (" + err.getDescription() + ")");
            }
            @Override public void onPageFinished(WebView v, String u) { v.requestFocus(); }
        });
        setContentView(web);
        web.setFocusable(true); web.setFocusableInTouchMode(true); web.requestFocus();
        load(getIntent());
    }

    @Override protected void onNewIntent(Intent i) { super.onNewIntent(i); load(i); }

    private void load(Intent i) {
        SharedPreferences p = getSharedPreferences("pg", MODE_PRIVATE);
        String room = i.getStringExtra("room"), u = i.getStringExtra("url"), mono = i.getStringExtra("mono");
        if (room != null) p.edit().putString("room", room).remove("url").apply();
        if (u != null) p.edit().putString("url", u).apply();
        if (mono != null) p.edit().putString("mono", mono).apply();
        String saved = p.getString("url", null);
        url = saved != null ? saved : BASE + "?m6=1&room=" + p.getString("room", DEFAULT_ROOM) + ("1".equals(p.getString("mono", "0")) ? "&mono=1" : "");
        web.loadUrl(url);
    }

    private void offline(String why) {
        String html = "<html><body style='background:#000;color:#3dff7a;font:28px sans-serif;text-align:center;padding-top:150px'>POINT &amp; GO<br><span style='font-size:20px;color:#fff'>"
                + why + "<br>Join the glasses to Wi-Fi in MLDemo. Retrying every 5 s.</span><br><span style='font-size:14px;color:#888'>" + url + "<br>" + web.getSettings().getUserAgentString() + "</span></body></html>";
        web.loadDataWithBaseURL(null, html, "text/html", "utf-8", null);
        handler.removeCallbacksAndMessages(null);
        handler.postDelayed(() -> web.loadUrl(url), 5000);
    }

    @Override protected void onResume() {
        super.onResume();
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        web.onResume();
    }

    @Override protected void onPause() { web.onPause(); super.onPause(); }

    /** Back reloads the page instead of leaving the app, so a stray swipe on the temple cannot close the display mid-demo. */
    @Override public boolean onKeyDown(int code, KeyEvent e) {
        if (code == KeyEvent.KEYCODE_BACK) { web.loadUrl(url); return true; }
        return super.onKeyDown(code, e);
    }
}
