import android.os.FileObserver;
import android.os.SystemClock;
import java.io.*;
import java.util.concurrent.CountDownLatch;
public final class FiremodBridge {
 static FileObserver observer;
 static Object manager;
 static java.lang.reflect.Method launchMethod;
 static final File dir=new File("/sdcard/Android/data/org.firemod.home/files");
 static String read(File f)throws Exception{try(FileInputStream in=new FileInputStream(f);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[256];for(int n;(n=in.read(b))!=-1;)out.write(b,0,n);return out.toString("UTF-8").trim();}}
 static void write(File f,String s)throws Exception{try(FileOutputStream out=new FileOutputStream(f)){out.write(s.getBytes("UTF-8"));}}
 public static void main(String[] args)throws Exception{
  manager=Class.forName("android.app.ActivityManagerNative").getMethod("getDefault").invoke(null);
  for(java.lang.reflect.Method m:Class.forName("android.app.IActivityManager").getMethods())if(m.getName().equals("startActivityAsUser")){launchMethod=m;break;}
  if(launchMethod==null)throw new IllegalStateException("No activity launch interface");
  System.out.println(launchMethod.toString());
  dir.mkdirs();String boot=read(new File("/proc/sys/kernel/random/boot_id"));
  observer=new FileObserver(dir.getAbsolutePath(),FileObserver.CLOSE_WRITE){public void onEvent(int event,String name){
   if(!"home-request".equals(name))return;
   try{
    String request=read(new File(dir,"home-request"));
    if(!request.matches("[0-9]{1,20}"))return;
    android.content.Intent target=new android.content.Intent().setComponent(new android.content.ComponentName("com.luncher.launcher","com.luncher.launcher.home.HomeActivity")).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK|android.content.Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
    Class<?>[] types=launchMethod.getParameterTypes();Object[] params=new Object[types.length];int integers=0,strings=0;
    for(int i=0;i<types.length;i++){
     if(types[i]==android.content.Intent.class)params[i]=target;
     else if(types[i]==int.class)params[i]=integers++==0?-1:0;
     else if(types[i]==String.class)params[i]=strings++==0?"com.android.shell":null;
    }
    int result=((Integer)launchMethod.invoke(manager,params)).intValue();int status=result>=0?0:result;
    if(status==0)write(new File(dir,"home-response"),request);
    System.out.println("Launch at "+SystemClock.elapsedRealtime()+" status="+status);
   }catch(Exception e){System.out.println(e.toString());}
  }};
  observer.startWatching();write(new File(dir,"home-bridge-ready"),boot);System.out.println("File bridge ready uid="+android.os.Process.myUid());new CountDownLatch(1).await();
 }
}
