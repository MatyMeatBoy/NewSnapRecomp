// Public authored fixture; actual prepared Ryujinx methods are inserted below.
using System;
using System.Numerics;

enum OperandType { Constant, LocalVariable }
enum MaxShift { U32=0, U64=2, S64=3 }
sealed class Operand {
 public uint Bits; public OperandType Type; public int Value => unchecked((int)Bits);
 public Operand(uint value, bool constant=false) {Bits=value; Type=constant?OperandType.Constant:OperandType.LocalVariable;}
}
sealed class EmitterContext {
 public uint Result, Flags; public int Invalid, FlagWrites;
 Operand O(uint v)=>new Operand(v);
 public Operand BitwiseAnd(Operand a,Operand b)=>O(a.Bits&b.Bits);
 public Operand BitwiseOr(Operand a,Operand b)=>O(a.Bits|b.Bits);
 public Operand ISubtract(Operand a,Operand b)=>O(unchecked(a.Bits-b.Bits));
 public Operand IMinimumU32(Operand a,Operand b)=>O(Math.Min(a.Bits,b.Bits));
 public Operand ICompareEqual(Operand a,Operand b)=>O(a.Bits==b.Bits?1u:0u);
 public Operand ICompareGreaterOrEqualUnsigned(Operand a,Operand b)=>O(a.Bits>=b.Bits?1u:0u);
 public Operand ICompareLessUnsigned(Operand a,Operand b)=>O(a.Bits<b.Bits?1u:0u);
 public Operand ConditionalSelect(Operand c,Operand a,Operand b)=>O(c.Bits!=0?a.Bits:b.Bits);
 uint Count(Operand b){if(b.Bits>=32)Invalid++;return b.Bits&31;}
 public Operand ShiftLeft(Operand a,Operand b)=>O(a.Bits<<(int)Count(b));
 public Operand ShiftRightU32(Operand a,Operand b)=>O(a.Bits>>(int)Count(b));
 public Operand ShiftRightS32(Operand a,Operand b)=>O(unchecked((uint)(a.Value>>(int)Count(b))));
 void Field(Operand p,Operand n){if(p.Bits>32 || n.Bits>32 || p.Bits+n.Bits>32)Invalid++;}
 public Operand BitfieldExtractU32(Operand a,Operand p,Operand n){Field(p,n);int w=(int)(n.Bits&31);uint mask=n.Bits==32?uint.MaxValue:(1u<<w)-1;return O((a.Bits>>(int)(p.Bits&31))&mask);}
 public Operand BitfieldExtractS32(Operand a,Operand p,Operand n){var r=BitfieldExtractU32(a,p,n);if(n.Bits>0&&n.Bits<32&&(r.Bits&(1u<<((int)n.Bits-1)))!=0)r.Bits|=uint.MaxValue<<(int)n.Bits;return r;}
 public Operand BitfieldInsert(Operand c,Operand a,Operand p,Operand n){Field(p,n);uint mask=n.Bits==32?uint.MaxValue:(1u<<(int)(n.Bits&31))-1;mask<<=(int)(p.Bits&31);return O((c.Bits&~mask)|((a.Bits<<(int)(p.Bits&31))&mask));}
 public Operand BitfieldReverse(Operand a){uint r=0;for(int i=0;i<32;i++)r|=((a.Bits>>i)&1u)<<(31-i);return O(r);}
 public void Copy(Operand dest,Operand src){Result=src.Bits;}
}
static class InstEmitAluHelper {
 public static void SetZnFlags(EmitterContext c,Operand o,bool writeCC){if(writeCC){c.Flags=(o.Bits==0?1u:0u)|(o.Bits>>31)*2;c.FlagWrites++;}}
}
static class Actual {
 static Operand Const(int n)=>new Operand(unchecked((uint)n),true);
 static Operand GetDest(int n)=>Const(n);
 @METHODS@
 public static EmitterContext Bfe(uint a,uint packed,bool signed,bool reverse,bool constant){var c=new EmitterContext();EmitBfe(c,new Operand(a),new Operand(packed,constant),0,reverse,signed);return c;}
 public static EmitterContext Bfi(uint a,uint packed,uint dst,bool constant){var c=new EmitterContext();EmitBfi(c,new Operand(a),new Operand(packed,constant),new Operand(dst),0);return c;}
 public static EmitterContext Shf(uint a,uint b,uint d,int mode,bool mask,bool left,bool cc,bool constant){var c=new EmitterContext();EmitShf(c,(MaxShift)mode,new Operand(a),new Operand(b,constant),new Operand(d),0,mask,left,cc);return c;}
}
static class Program {
 static long cases; static int failures; static string first="";
 static void Check(EmitterContext got,uint expected,string label){cases++;if(got.Result!=expected||got.Invalid!=0){failures++;if(first=="")first=$"{label}: got {got.Result:x8}, expected {expected:x8}, undefined ops {got.Invalid}";}}
 static uint Reverse(uint v){uint r=0;for(int i=0;i<32;i++)r|=((v>>i)&1u)<<(31-i);return r;}
 // Independent per-bit oracle; does not reuse the patched clamp arithmetic.
 static uint Bfe(uint v,int p,int n,bool signed){if(n==0)return 0;uint sign=signed?(v>>Math.Min(p+n-1,31))&1u:0;uint r=0;for(int i=0;i<32;i++){uint b=i<n&&p+i<32?(v>>(p+i))&1u:sign;r|=b<<i;}return r;}
 static uint Bfi(uint a,uint dst,int p,int n){uint r=dst;for(int i=0;i<32;i++)if(i>=p&&i-p<n)r=(r&~(1u<<i))|(((a>>(i-p))&1u)<<i);return r;}
 static uint Shf(uint a,uint d,uint count,int mode,bool mask,bool left){int max=mode>=2?64:32;uint n=mask?count&(uint)(max-1):count;if(n>=(uint)max)return 0;ulong pair=((ulong)d<<32)|a;if(left)return (uint)((pair<<(int)n)>>32);if(mode==3)return unchecked((uint)((long)pair>>(int)n));return (uint)(pair>>(int)n);}
 static int Main(string[] args){
  uint[] values={0,1,0x80000000,0xffffffff,0x55aa55aa,0xaa55aa55,0x12345678};
  if(args.Length==0||args[0]=="bitfield"){
   for(int p=0;p<256;p++)for(int n=0;n<256;n++)foreach(bool constant in new[]{false,true}){
    uint a=values[(p+n)%values.Length],d=values[(p*3+n+1)%values.Length],packed=(uint)(p|(n<<8));
    foreach(bool signed in new[]{false,true})foreach(bool reverse in new[]{false,true})Check(Actual.Bfe(a,packed,signed,reverse,constant),Bfe(reverse?Reverse(a):a,p,n,signed),$"BFE {p}/{n}/{signed}/{reverse}/{constant}");
    Check(Actual.Bfi(a,packed,d,constant),Bfi(a,d,p,n),$"BFI {p}/{n}/{constant}");
   }
  }
  if(args.Length==0||args[0]=="funnel"){
   foreach(int mode in new[]{0,2,3})foreach(bool mask in new[]{false,true})foreach(bool left in new[]{false,true})foreach(bool constant in new[]{false,true})foreach(bool cc in new[]{false,true})foreach(uint a in values)foreach(uint d in new[]{~a,0u,0x13579bdfu})for(uint index=0;index<260;index++){
    uint count=index<256?index:new uint[]{0x100,0x7fffffff,0x80000000,0xffffffff}[index-256];
    uint expected=Shf(a,d,count,mode,mask,left);var c=Actual.Shf(a,count,d,mode,mask,left,cc,constant);Check(c,expected,$"SHF {mode}/{mask}/{left}/{constant}/{count}");
    if(c.FlagWrites!=(cc?1:0)||cc&&c.Flags!=((expected==0?1u:0u)|(expected>>31)*2)){failures++;if(first=="")first="CC changed";}
   }
  }
  Console.WriteLine($"cases={cases} failures={failures} first={first}");return failures==0?0:1;
 }
}
