package com.nanami128sketch.routinefit;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Message;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.webkit.WebViewAssetLoader;

import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Native container for the existing offline-first RoutineFit web app. */
public final class MainActivity extends Activity {
    private static final String ROOT = "https://appassets.androidplatform.net/assets/";
    private static final int REQUEST_IMPORT = 401;
    private static final int REQUEST_EXPORT = 402;
    private static final int MAX_BACKUP_LENGTH = 10 * 1024 * 1024;
    private WebView webView;
    private ValueCallback<Uri[]> pendingImport;
    private String pendingBackup;

    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        webView = new WebView(this);
        webView.setBackgroundColor(0xff09131b);
        setContentView(webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true); // Needed only for JSON backup import via file picker.
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(true);
        settings.setSupportMultipleWindows(true);
        webView.addJavascriptInterface(new NativeBridge(), "RoutineFitNative");
        webView.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
                return assetLoader.shouldInterceptRequest(req.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                if (req.getUrl().toString().startsWith(ROOT)) return false;
                openExternal(req.getUrl());
                return true;
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                                       FileChooserParams params) {
                if (pendingImport != null) pendingImport.onReceiveValue(null);
                pendingImport = callback;
                try {
                    startActivityForResult(params.createIntent(), REQUEST_IMPORT);
                    return true;
                } catch (ActivityNotFoundException e) {
                    pendingImport = null;
                    callback.onReceiveValue(null);
                    toast("파일 선택 앱을 찾을 수 없습니다.");
                    return true;
                }
            }
            @Override public boolean onCreateWindow(WebView view, boolean isDialog,
                                                    boolean isUserGesture, Message resultMsg) {
                if (!isUserGesture) return false;
                WebView child = new WebView(MainActivity.this);
                child.setWebViewClient(new WebViewClient() {
                    @Override public boolean shouldOverrideUrlLoading(WebView unused, WebResourceRequest req) {
                        openExternal(req.getUrl());
                        return true;
                    }
                });
                WebView.WebViewTransport transport = (WebView.WebViewTransport) resultMsg.obj;
                transport.setWebView(child);
                resultMsg.sendToTarget();
                return true;
            }
        });
        webView.loadUrl(ROOT + "index.html");
    }

    private void openExternal(Uri url) {
        String scheme = url.getScheme();
        if (!"https".equalsIgnoreCase(scheme) && !"http".equalsIgnoreCase(scheme)) return;
        try { startActivity(new Intent(Intent.ACTION_VIEW, url)); }
        catch (ActivityNotFoundException e) { toast("링크를 열 앱이 없습니다."); }
    }

    private void toast(String message) {
        runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_SHORT).show());
    }

    private final class NativeBridge {
        @JavascriptInterface public void saveBackup(String json) {
            if (json == null || json.length() > MAX_BACKUP_LENGTH) {
                toast("백업 파일이 너무 큽니다.");
                return;
            }
            runOnUiThread(() -> {
                pendingBackup = json;
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                String stamp = new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(new Date());
                intent.putExtra(Intent.EXTRA_TITLE, "routinefit-backup-" + stamp + ".json");
                try { startActivityForResult(intent, REQUEST_EXPORT); }
                catch (ActivityNotFoundException e) { pendingBackup = null; toast("파일 저장 앱을 찾을 수 없습니다."); }
            });
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_IMPORT) {
            if (pendingImport != null) {
                pendingImport.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode, data));
                pendingImport = null;
            }
        } else if (requestCode == REQUEST_EXPORT) {
            if (resultCode == RESULT_OK && data != null && data.getData() != null && pendingBackup != null) {
                try (OutputStream out = getContentResolver().openOutputStream(data.getData())) {
                    if (out == null) throw new IllegalStateException("No output stream");
                    out.write(pendingBackup.getBytes(StandardCharsets.UTF_8));
                    toast("루틴핏 백업 저장 완료");
                } catch (Exception e) { toast("백업 저장 실패: 다른 위치를 선택해 주세요."); }
            }
            pendingBackup = null;
        }
    }

    @Override protected void onDestroy() {
        if (pendingImport != null) pendingImport.onReceiveValue(null);
        if (webView != null) {
            webView.removeJavascriptInterface("RoutineFitNative");
            webView.destroy();
        }
        super.onDestroy();
    }
}
