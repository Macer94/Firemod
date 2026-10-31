package org.firemod.home;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;
import android.util.Log;

/** Starts the watcher at boot; it opens HomeActivity if Amazon's home is what came up (see HomeWatcher.catchUp). */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        Log.i("FiremodHome", "Startup event " + intent.getAction() + " at " + SystemClock.elapsedRealtime());
        context.startService(new Intent(context, HomeWatcher.class));
    }
}
