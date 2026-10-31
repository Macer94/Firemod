package org.firemod.home;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** Starts the inspected Firehome watcher and opens the separately installed Luncher. */
public class HomeActivity extends Activity {
    static final String AMAZON_HOME = "com.amazon.tv.launcher";
    static final String TARGET_HOME = "com.luncher.launcher";

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        startService(new Intent(this, HomeWatcher.class));
        Intent target = getPackageManager().getLeanbackLaunchIntentForPackage(TARGET_HOME);
        if (target == null) {
            target = getPackageManager().getLaunchIntentForPackage(TARGET_HOME);
        }
        if (target != null) {
            startActivity(target.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        }
        finish();
    }
}
