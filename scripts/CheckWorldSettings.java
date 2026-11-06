import java.io.File;
import com.mojang.serialization.*;
public class CheckWorldSettings {
 public static void main(String[] args) throws Exception {
  vm.a();
  gn.b registry=gn.b();
  vh<mt> ops=vh.a(mo.a,new vh.b.a(),registry);
  md data=mn.a(new File(args[0])).p("Data").p("WorldGenSettings");
  DataResult<chw> result=chw.a.parse(ops,data);
  System.out.println("RESULT="+result);
  System.out.println("LIFECYCLE="+result.lifecycle());
  if(!result.result().isPresent())System.exit(2);
  if(result.lifecycle()!=Lifecycle.stable())System.exit(3);
 }
}
