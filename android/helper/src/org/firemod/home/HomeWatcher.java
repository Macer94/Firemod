package org.firemod.home;

import android.app.Notification;
import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.SystemClock;
import android.util.Log;

import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * Fire OS sends Home to com.amazon.tv.launcher whatever else is installed, and silently drops any accessibility
 * service ADB tries to switch on. It does let ADB grant READ_LOGS, and ActivityManager logs every Home press as
 * "START u0 {... cat=[android.intent.category.HOME] ... cmp=com.amazon.tv.launcher/...}". This service follows
 * the log and puts HomeActivity on top each time.
 */
public class HomeWatcher extends Service {
    private static long pausedUntil;
    private static long lastLaunch;
    private Thread reader;

    /** Leave Amazon's home alone for a while, for the "Fire TV home" button. */
    static void pause(long millis) {
        pausedUntil = SystemClock.elapsedRealtime() + millis;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (reader == null) {
            Log.i("FiremodHome", "Home watcher started at " + SystemClock.elapsedRealtime());
            // foreground, so the low-memory killer on a 1 GB stick leaves the watcher running
            startForeground(1, new Notification.Builder(this)
                    .setSmallIcon(R.drawable.icon)
                    .setContentTitle(getString(R.string.app_name))
                    .setPriority(Notification.PRIORITY_MIN)
                    .build());
            reader = new Thread(this::follow, "home-watcher");
            reader.setDaemon(true);
            reader.start();
        }
        return START_STICKY;
    }

    private void follow() {
        catchUp();
        while (true) {
            Process logcat = null;
            try {
                // -T 1 starts at the newest line, so Home presses already in the buffer are not replayed
                logcat = new ProcessBuilder("logcat", "-v", "brief", "-T", "1", "ActivityManager:I", "*:S")
                        .redirectErrorStream(true).start();
                BufferedReader lines = new BufferedReader(new InputStreamReader(logcat.getInputStream()));
                for (String line; (line = lines.readLine()) != null; ) {
                    if (isAmazonHome(line) || isAutomaticProfilePicker(line)) {
                        Log.i("FiremodHome", "Redirect at " + SystemClock.elapsedRealtime() + ": " + line);
                        amazonHomeStarted();
                    }
                }
            } catch (Exception e) {
                // logcat ended or could not start; try again below
            } finally {
                if (logcat != null) {
                    logcat.destroy();
                }
            }
            SystemClock.sleep(2000);
        }
    }

    /**
     * At boot, or when the system restarts this service, Amazon's home may already be on screen. Only take over
     * if it was the last thing started, so a video someone opened in the meantime is left alone.
     */
    private void catchUp() {
        String last = null;
        try {
            Process dump = new ProcessBuilder("logcat", "-d", "-v", "brief", "ActivityManager:I", "*:S")
                    .redirectErrorStream(true).start();
            BufferedReader lines = new BufferedReader(new InputStreamReader(dump.getInputStream()));
            for (String line; (line = lines.readLine()) != null; ) {
                if (line.contains("START u0")) {
                    last = line;
                }
            }
            dump.waitFor();
        } catch (Exception e) {
            return;
        }
        if (last != null && (isAmazonHome(last) || isAutomaticProfilePicker(last))) {
            Log.i("FiremodHome", "Catch-up redirect at " + SystemClock.elapsedRealtime() + ": " + last);
            amazonHomeStarted();
        }
    }

    private boolean isAmazonHome(String line) {
        if (!line.contains("android.intent.category.HOME")
                || !line.contains("cmp=" + HomeActivity.AMAZON_HOME + "/")) {
            return false;
        }
        try {
            int launcherUid = getPackageManager().getApplicationInfo(HomeActivity.AMAZON_HOME, 0).uid;
            // Fire OS implements System Settings as a HOME intent issued by its own launcher.
            // Leave that internal navigation alone; physical Home presses come from the system.
            if (line.contains("from uid " + launcherUid + " ")) {
                return false;
            }
        } catch (android.content.pm.PackageManager.NameNotFoundException ignored) {
        }
        return true;
    }

    private static boolean isAutomaticProfilePicker(String line) {
        // Keep this startup-only: reopening the picker after sleep needs native profile activation.
        return SystemClock.elapsedRealtime() < 120000L
                && line.contains("START u0")
                && line.contains("cmp=com.amazon.ftv.profilepicker/")
                && line.contains("PickerActivity")
                && (line.contains("from uid 1000 ") || line.contains("from uid 0 "));
    }

    private void amazonHomeStarted() {
        long now = SystemClock.elapsedRealtime();
        if (now < pausedUntil || now - lastLaunch < 200) {
            return;
        }
        lastLaunch = now;
        Intent target = getPackageManager().getLeanbackLaunchIntentForPackage(HomeActivity.TARGET_HOME);
        if (target == null) {
            target = getPackageManager().getLaunchIntentForPackage(HomeActivity.TARGET_HOME);
        }
        if (target != null) {
            if (!FileBridge.launch(this)) {
                Log.i("FiremodHome", "Standard launch fallback at " + SystemClock.elapsedRealtime());
                startActivity(target.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT));
            }
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
