package org.firemod.home;
import android.content.Context;
import android.os.SystemClock;
import android.util.Log;
import java.io.*;
final class FileBridge {
 static String read(File f)throws Exception{try(FileInputStream in=new FileInputStream(f);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[256];for(int n;(n=in.read(b))!=-1;)out.write(b,0,n);return out.toString("UTF-8").trim();}}
 static boolean launch(Context context){
  try{
   File dir=context.getExternalFilesDir(null);if(dir==null)return false;
   File ready=new File(dir,"home-bridge-ready");if(!ready.exists())return false;
   String boot=read(new File("/proc/sys/kernel/random/boot_id"));if(!boot.equals(read(ready)))return false;
   String request=Long.toString(SystemClock.elapsedRealtime());
   try(FileOutputStream out=new FileOutputStream(new File(dir,"home-request"))){out.write(request.getBytes("UTF-8"));}
   long deadline=SystemClock.elapsedRealtime()+1200;
   while(SystemClock.elapsedRealtime()<deadline){
    File response=new File(dir,"home-response");if(response.exists()&&request.equals(read(response))){Log.i("FiremodHome","File bridge launch acknowledged at "+SystemClock.elapsedRealtime());return true;}
    SystemClock.sleep(20);
   }
   ready.delete();
  }catch(Exception e){Log.w("FiremodHome","File bridge unavailable: "+e);}
  return false;
 }
}
