#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

#ifdef _WIN32
#define TB_EXPORT extern "C" __declspec(dllexport)
#else
#define TB_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {
constexpr int ABI=1, MAX_TICKS=144, MAX_STATES=145, PRE=16, LOCK=16, BLACKOUT=4, TEMPLATES=8;
constexpr double PI=3.141592653589793238462643383279502884, DT=.25, VG=4.0*PI;
constexpr double BX=-450, BY=250, BZ=15;
struct V2 { double x,y; };
struct V3 { double x,y,z; };
V2 add(V2 a,V2 b){return {a.x+b.x,a.y+b.y};}
V2 sub(V2 a,V2 b){return {a.x-b.x,a.y-b.y};}
V2 mul(V2 a,double s){return {a.x*s,a.y*s};}
double dot(V2 a,V2 b){return a.x*b.x+a.y*b.y;}
double norm(V2 a){return std::sqrt(dot(a,a));}
double clip(double x,double lo,double hi){return std::min(std::max(x,lo),hi);}
V2 clipnorm(V2 a,double lim){double n=norm(a);return n<=lim||n==0?a:mul(a,lim/n);}
bool finite2(V2 a){return std::isfinite(a.x)&&std::isfinite(a.y);}

double d_obs(V2 p){double dx=std::max({-80-p.x,0.0,p.x-80}),dy=std::max({-260-p.y,0.0,p.y-80});return std::sqrt(dx*dx+dy*dy);}
bool legal(V2 p){return p.x>=-550&&p.x<=550&&p.y>=-350&&p.y<=350&&d_obs(p)>=20;}
double orient(V2 a,V2 b,V2 c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
bool onseg(V2 a,V2 b,V2 p){return p.x>=std::min(a.x,b.x)&&p.x<=std::max(a.x,b.x)&&p.y>=std::min(a.y,b.y)&&p.y<=std::max(a.y,b.y)&&orient(a,b,p)==0;}
bool intersect(V2 a,V2 b,V2 c,V2 d){double o1=orient(a,b,c),o2=orient(a,b,d),o3=orient(c,d,a),o4=orient(c,d,b);if(((o1>0&&o2<0)||(o1<0&&o2>0))&&((o3>0&&o4<0)||(o3<0&&o4>0)))return true;return(o1==0&&onseg(a,b,c))||(o2==0&&onseg(a,b,d))||(o3==0&&onseg(c,d,a))||(o4==0&&onseg(c,d,b));}
double point_seg2(V2 p,V2 a,V2 b){V2 ab=sub(b,a);double den=dot(ab,ab),t=den==0?0:clip(dot(sub(p,a),ab)/den,0,1);V2 q=add(a,mul(ab,t)),d=sub(p,q);return dot(d,d);}
double seg_seg2(V2 a,V2 b,V2 c,V2 d){if(intersect(a,b,c,d))return 0;return std::min({point_seg2(a,c,d),point_seg2(b,c,d),point_seg2(c,a,b),point_seg2(d,a,b)});}
double seg_obs2(V2 a,V2 b){if((a.x>=-80&&a.x<=80&&a.y>=-260&&a.y<=80)||(b.x>=-80&&b.x<=80&&b.y>=-260&&b.y<=80))return 0;V2 c[4]={{-80,-260},{80,-260},{80,80},{-80,80}};double best=std::numeric_limits<double>::infinity();for(int i=0;i<4;i++)best=std::min(best,seg_seg2(a,b,c[i],c[(i+1)%4]));return best;}
bool legal_tick(V2 p,V2 v){V2 e=add(p,mul(v,DT));return p.x>=-550&&p.x<=550&&p.y>=-350&&p.y<=350&&e.x>=-550&&e.x<=550&&e.y>=-350&&e.y<=350&&seg_obs2(p,e)>=400;}
bool los(V3 a,V3 d){double lo=-std::numeric_limits<double>::infinity(),hi=std::numeric_limits<double>::infinity();double av[3]={a.x,a.y,a.z},dv[3]={d.x,d.y,d.z},mn[3]={-80,-260,0},mx[3]={80,80,140};for(int i=0;i<3;i++){double de=dv[i]-av[i];if(de==0){if(av[i]<mn[i]||av[i]>mx[i])return true;continue;}double f=(mn[i]-av[i])/de,s=(mx[i]-av[i])/de;if(f>s)std::swap(f,s);lo=std::max(lo,f);hi=std::min(hi,s);if(lo>hi)return true;}return !(lo<=hi&&hi>0&&lo<1);}
V2 project(V2 p){if(legal(p))return p;std::vector<V2> c;V2 cl={clip(p.x,-550,550),clip(p.y,-350,350)};if(legal(cl))c.push_back(cl);V2 q[4]={{-100,clip(p.y,-260,80)},{100,clip(p.y,-260,80)},{clip(p.x,-80,80),-280},{clip(p.x,-80,80),100}};for(auto v:q)if(legal(v))c.push_back(v);double cx[4]={-80,-80,80,80},cy[4]={-260,80,-260,80};int sx[4]={-1,-1,1,1},sy[4]={-1,1,-1,1};for(int i=0;i<4;i++){V2 de={p.x-cx[i],p.y-cy[i]};double n=norm(de);if(n>0){V2 r={cx[i]+20*de.x/n,cy[i]+20*de.y/n};if(sx[i]*(r.x-cx[i])>=0&&sy[i]*(r.y-cy[i])>=0&&legal(r))c.push_back(r);}V2 e1={cx[i]+20*sx[i],cy[i]},e2={cx[i],cy[i]+20*sy[i]};if(legal(e1))c.push_back(e1);if(legal(e2))c.push_back(e2);}if(c.empty())return {std::numeric_limits<double>::quiet_NaN(),std::numeric_limits<double>::quiet_NaN()};auto better=[&](V2 a,V2 b){V2 da=sub(a,p),db=sub(b,p);double aa=dot(da,da),bb=dot(db,db);return aa<bb||(aa==bb&&(a.x<b.x||(a.x==b.x&&a.y<b.y)));};V2 best=c[0];for(auto v:c)if(better(v,best))best=v;return best;}

void route(int cls,int dir,double lateral,double time,V2& base,V2& tangent,V2& normal){double scored=cls==0?32:128,duration=scored*DT;if(cls==0){double u=std::max(time,0.0)/duration,phi=PI/4+dir*(u-.5)*PI/2;base={80+64*std::cos(phi)+lateral/std::sqrt(2.0),80+64*std::sin(phi)+lateral/std::sqrt(2.0)};tangent={dir*-std::sin(phi),dir*std::cos(phi)};if(time<0){double p0=PI/4-dir*PI/4;V2 b0={80+64*std::cos(p0)+lateral/std::sqrt(2.0),80+64*std::sin(p0)+lateral/std::sqrt(2.0)};tangent={dir*-std::sin(p0),dir*std::cos(p0)};base=add(b0,mul(tangent,time*VG));}}else{double u=std::max(time,0.0)/duration;base={dir*64*PI*(2*u-1),200+lateral};tangent={(double)dir,0};if(time<0)base=add({-dir*64*PI,200+lateral},mul(tangent,time*VG));}normal={-tangent.y,tangent.x};}
double m0(V3 a,V3 d){double dist=std::sqrt((a.x-d.x)*(a.x-d.x)+(a.y-d.y)*(a.y-d.y)+(a.z-d.z)*(a.z-d.z));return 25-20*std::log10(std::max(dist,1.0)/100)-(los(a,d)?0:30);}
bool plan(V2 x,V2 v,V2 pr,V2& wt,V2& wr){wt=project(add(x,mul(v,2)));if(!finite2(wt))return false;V3 wt3={wt.x,wt.y,80},b={BX,BY,BZ};bool found=false;double bs=0,bd=0;for(double f:{.5,.75,1.0}){V2 base={BX+f*(wt.x-BX),BY+f*(wt.y-BY)};V2 offs[5]={{0,0},{120,0},{-120,0},{0,120},{0,-120}};for(auto o:offs){V2 c=add(base,o);if(!legal(c))continue;V3 c3={c.x,c.y,100};double travel=norm(sub(c,pr)),score=std::min(m0(wt3,c3),m0(c3,b))-.01*travel;if(!found||score>bs||(score==bs&&(travel<bd||(travel==bd&&(c.x<wr.x||(c.x==wr.x&&c.y<wr.y)))))){found=true;bs=score;bd=travel;wr=c;}}}return found;}
std::vector<V2> registry(double vmax){std::vector<V2> r={{0,0}};for(double f:{.5,1.0})for(int h=0;h<16;h++){double a=2*PI*h/16;r.push_back({f*vmax*std::cos(a),f*vmax*std::sin(a)});}return r;}
double minsep(V2 pt,V2 vt,V2 pr,V2 vr){V2 r=sub(pt,pr),v=sub(vt,vr);double den=dot(v,v),t=den==0?0:clip(-dot(r,v)/den,0,DT);return norm(add(r,mul(v,t)));}
struct Control {int it=-1,ir=-1,uit=-1,uir=-1;V2 at{},ar{},gt{},gr{};double sep=0;bool ok=false;};
Control control(V2 pt,V2 pr,V2 wt,V2 wr,V2 windt,V2 windr){static auto at=registry(18.0),ar=registry(22.0);V2 nt=clipnorm(mul(sub(wt,pt),.5),18),nr=clipnorm(mul(sub(wr,pr),.5),22);Control out;double uo=0,ua=0,bo=0,ba=0;bool uf=false,bf=false;for(int i=0;i<33;i++){V2 gt=add(at[i],windt);for(int j=0;j<33;j++){V2 gr=add(ar[j],windr);double obj=dot(sub(gt,nt),sub(gt,nt))+dot(sub(gr,nr),sub(gr,nr)),air=norm(at[i])+norm(ar[j]);if(!uf||obj<uo||(obj==uo&&(air<ua||(air==ua&&(i<out.uit||(i==out.uit&&j<out.uir)))))){uf=true;uo=obj;ua=air;out.uit=i;out.uir=j;}if(!legal_tick(pt,gt)||!legal_tick(pr,gr))continue;double sep=minsep(pt,gt,pr,gr);if(sep<30)continue;if(!bf||obj<bo||(obj==bo&&(air<ba||(air==ba&&(i<out.it||(i==out.it&&j<out.ir)))))){bf=true;bo=obj;ba=air;out.it=i;out.ir=j;out.at=at[i];out.ar=ar[j];out.gt=gt;out.gr=gr;out.sep=sep;}}}out.ok=bf;return out;}
void radio(V3 a,V3 d,double sh,double u,int& l,double& margin,double& prob,int& trial){l=los(a,d);double dist=std::sqrt((a.x-d.x)*(a.x-d.x)+(a.y-d.y)*(a.y-d.y)+(a.z-d.z)*(a.z-d.z));margin=25-20*std::log10(std::max(dist,1.0)/100)-(l?0:30)+sh;prob=1/(1+std::exp(-margin/3));trial=u<prob;}
}

extern "C" {
struct TBInput {
 int route_class,direction,lateral,arm;
 double target[MAX_STATES],wind_tx[MAX_STATES],wind_ty[MAX_STATES],wind_rx[MAX_STATES],wind_ry[MAX_STATES],sensor_x[MAX_STATES],sensor_y[MAX_STATES],shadow_tr[MAX_STATES],shadow_rb[MAX_STATES];
 double link_tr[MAX_TICKS],link_rb[MAX_TICKS];
};
struct TBTick {
 int tick,scored,scored_index,action_code,scheduled,shell,fit_available,selected_template,effective;
 double time,residuals[TEMPLATES],fit_t1,fit_t2,fit_z1x,fit_z1y,fit_z2x,fit_z2y,eta_raw,eta_patch,patch_x,patch_y,patch_vx,patch_vy;
 double target_x,target_y,tangent_x,tangent_y,normal_x,normal_y,zeta,wind_tx,wind_ty,wind_rx,wind_ry,pt_x,pt_y,pr_x,pr_y;
 double xpre_x,xpre_y,vpre_x,vpre_y,xhat_x,xhat_y,vhat_x,vhat_y;
 int sensor_visible; double sensor_x,sensor_y; int buffer_pre,buffer_post;
 double wt_x,wt_y,wr_x,wr_y,tracking_error; int tracking_valid;
 double shadow_tr,shadow_rb; int los_tr,los_rb; double margin_tr,margin_rb,prob_tr,prob_rb,link_u_tr,link_u_rb;
 int raw_trial_tr,raw_trial_rb,trial_tr,trial_rb,packet_valid,blackout,lockout;
 double et_before,er_before,et_after,er_after,at_x,at_y,ar_x,ar_y,gt_x,gt_y,gr_x,gr_y;
 int it,ir,uit,uir,safety_override; double min_separation,terrain_t_after,terrain_r_after;
 int terrain_penetration,geofence_exit,separation_breach,service,hard_failure,no_planner,no_safe,numerical_fault,battery;
};
struct TBOutput {
 int total_ticks,scored_valid,scheduled,shells,fit_count,effective_count,overrides,terrain_penetrations,geofence_exits,separation_breaches,hard_failure,no_planner,no_safe,numerical_fault,battery;
 TBTick ticks[MAX_TICKS];
};
}

namespace {
struct Obs{double t;V2 z;};
struct Fit {bool available=false;int selected=-1;double residuals[TEMPLATES],eta_raw,eta_patch;V2 xpatch,vpatch;bool effective=false;Fit(){for(double& value:residuals)value=std::numeric_limits<double>::quiet_NaN();eta_raw=eta_patch=std::numeric_limits<double>::quiet_NaN();}};
Fit road_fit(const std::vector<Obs>& buf,V2 xpre,V2 vpre){Fit f;f.xpatch=xpre;f.vpatch=vpre;if(buf.size()!=2||!(buf[0].t<buf[1].t&&buf[1].t<=0))return f;f.available=true;double best=std::numeric_limits<double>::infinity();for(int j=0;j<TEMPLATES;j++){int cls=j/4,within=j%4,dir=within/2==0?-1:1,lat=within%2==0?-8:8;V2 b1,t1,n1,b2,t2,n2;route(cls,dir,lat,buf[0].t,b1,t1,n1);route(cls,dir,lat,buf[1].t,b2,t2,n2);f.residuals[j]=dot(sub(buf[0].z,b1),sub(buf[0].z,b1))+dot(sub(buf[1].z,b2),sub(buf[1].z,b2));if(f.residuals[j]<best){best=f.residuals[j];f.selected=j;}}
 int cls=f.selected/4,within=f.selected%4,dir=within/2==0?-1:1,lat=within%2==0?-8:8;V2 b2,t2,n2,b0,t0,n0;route(cls,dir,lat,buf[1].t,b2,t2,n2);route(cls,dir,lat,0,b0,t0,n0);f.eta_raw=dot(sub(buf[1].z,b2),n2);f.eta_patch=clip(f.eta_raw,-15,15);f.xpatch=add(b0,mul(n0,f.eta_patch));f.vpatch=mul(t0,VG);f.effective=norm(sub(f.xpatch,xpre))>=1||norm(sub(f.vpatch,vpre))>=1;return f;}
bool valid_input(const TBInput& in){if(in.route_class<0||in.route_class>1||!(in.direction==-1||in.direction==1)||!(in.lateral==-8||in.lateral==8)||in.arm<0||in.arm>3)return false;int total=in.route_class==0?48:144;for(int i=0;i<=total;i++){double values[9]={in.target[i],in.wind_tx[i],in.wind_ty[i],in.wind_rx[i],in.wind_ry[i],in.sensor_x[i],in.sensor_y[i],in.shadow_tr[i],in.shadow_rb[i]};for(double value:values)if(!std::isfinite(value))return false;}for(int i=0;i<total;i++)if(!std::isfinite(in.link_tr[i])||!std::isfinite(in.link_rb[i])||in.link_tr[i]<0||in.link_tr[i]>=1||in.link_rb[i]<0||in.link_rb[i]>=1)return false;return true;}
int run_one(const TBInput& in,TBOutput& out){if(!valid_input(in))return 1;int total=in.route_class==0?48:144;out={};out.total_ticks=total;double zeta=clip(2*in.target[0],-6,6);V2 base,tan,nor;route(in.route_class,in.direction,in.lateral,-4,base,tan,nor);V2 target=add(base,mul(nor,zeta)),pt=target,pr={0,180};V2 windt=clipnorm({2*in.wind_tx[0],2*in.wind_ty[0]},4),windr=clipnorm({2*in.wind_rx[0],2*in.wind_ry[0]},4);double sht=3*in.shadow_tr[0],shr=3*in.shadow_rb[0],et=40000,er=45000;V2 xhat={std::numeric_limits<double>::quiet_NaN(),std::numeric_limits<double>::quiet_NaN()},vhat=xhat,wt=pt,wr=pr;std::vector<Obs> buf;int lockuntil=0,blackuntil=0;bool hard=false,noplan=false,nosafe=false,battery=false;
 bool numerical=false;for(int tick=0;tick<total;tick++){TBTick& o=out.ticks[tick];o={};for(double& value:o.residuals)value=std::numeric_limits<double>::quiet_NaN();double time=(tick-PRE)*DT;bool scored=tick>=PRE;int k=tick-PRE;bool vis=norm(sub(target,pt))<=250&&los({target.x,target.y,0},{pt.x,pt.y,80});V2 obs=add(target,{3*in.sensor_x[tick],3*in.sensor_y[tick]});int action=0;
  if(tick==0){if(!vis)return 2;buf.push_back({time,obs});xhat=obs;vhat=clipnorm(mul(tan,VG),20);if(!plan(xhat,vhat,pr,wt,wr))hard=noplan=true;buf.clear();action=1;lockuntil=LOCK;blackuntil=BLACKOUT;}
  bool scheduled=tick==PRE;V2 xpre=xhat,vpre=vhat;int buffer_pre=(int)buf.size();Fit fit;fit.xpatch=xpre;fit.vpatch=vpre;Obs fit_a{},fit_b{};bool retained_samples=buf.size()==2;if(retained_samples){fit_a=buf[0];fit_b=buf[1];}
  if(scheduled){out.scheduled++;fit=road_fit(buf,xpre,vpre);out.fit_count+=fit.available;out.effective_count+=fit.effective;if(in.arm!=0){out.shells++;action=in.arm+1;lockuntil=tick+LOCK;blackuntil=tick+BLACKOUT;buf.clear();if(in.arm==2&&fit.available&&retained_samples){xhat=fit_b.z;vhat=clipnorm(mul(sub(fit_b.z,fit_a.z),1/(fit_b.t-fit_a.t)),20);}else if(in.arm==3&&fit.available){xhat=fit.xpatch;vhat=fit.vpatch;}}}
  bool blackout=tick<blackuntil,locked=tick<lockuntil;int ltr,lrb,ttr,trb;double mtr,mrb,ptr,prb;radio({pt.x,pt.y,80},{pr.x,pr.y,100},sht,in.link_tr[tick],ltr,mtr,ptr,ttr);radio({pr.x,pr.y,100},{BX,BY,BZ},shr,in.link_rb[tick],lrb,mrb,prb,trb);int rawt=ttr,rawr=trb;ttr=ttr&&!blackout;trb=trb&&!blackout;bool packet=ttr&&trb;double terr=norm(sub(xhat,target));bool track=terr<=15;if(!finite2(target)||!finite2(pt)||!finite2(pr)||!finite2(xhat)||!finite2(vhat)||!finite2(wt)||!finite2(wr)||!finite2(windt)||!finite2(windr)||!std::isfinite(terr)){numerical=hard=true;}double eb_t=et,eb_r=er;Control c;if(!hard&&!battery)c=control(pt,pr,wt,wr,windt,windr);if(!c.ok){if(!hard)hard=nosafe=true;c.sep=norm(sub(pt,pr));}bool override=c.ok&&(c.it!=c.uit||c.ir!=c.uir);out.overrides+=override;int service=scored&&track&&packet&&!blackout&&!battery&&!hard;out.scored_valid+=service;V2 npt=battery?pt:add(pt,mul(c.gt,DT)),npr=battery?pr:add(pr,mul(c.gr,DT));double charge=(action>=1&&action<=4)?200:0;et=std::max(0.0,et-DT*(300+dot(c.at,c.at))-charge);er=std::max(0.0,er-DT*(350+dot(c.ar,c.ar))-charge);if(et==0||er==0)hard=battery=true;double terrain_t=d_obs(npt),terrain_r=d_obs(npr);bool penetration=terrain_t<20||terrain_r<20,geofence=npt.x< -550||npt.x>550||npt.y< -350||npt.y>350||npr.x< -550||npr.x>550||npr.y< -350||npr.y>350,separation=c.sep<30;out.terrain_penetrations+=penetration;out.geofence_exits+=geofence;out.separation_breaches+=separation;
  o.tick=tick;o.time=time;o.scored=scored;o.scored_index=k;o.action_code=action;o.scheduled=scheduled;o.shell=scheduled&&in.arm!=0;o.fit_available=fit.available;o.selected_template=fit.selected;o.effective=fit.effective;for(int j=0;j<TEMPLATES;j++)o.residuals[j]=fit.residuals[j];o.fit_t1=o.fit_t2=o.fit_z1x=o.fit_z1y=o.fit_z2x=o.fit_z2y=std::numeric_limits<double>::quiet_NaN();if(scheduled&&fit.available&&retained_samples){o.fit_t1=fit_a.t;o.fit_t2=fit_b.t;o.fit_z1x=fit_a.z.x;o.fit_z1y=fit_a.z.y;o.fit_z2x=fit_b.z.x;o.fit_z2y=fit_b.z.y;}o.eta_raw=fit.eta_raw;o.eta_patch=fit.eta_patch;o.patch_x=fit.xpatch.x;o.patch_y=fit.xpatch.y;o.patch_vx=fit.vpatch.x;o.patch_vy=fit.vpatch.y;
  o.target_x=target.x;o.target_y=target.y;o.tangent_x=tan.x;o.tangent_y=tan.y;o.normal_x=nor.x;o.normal_y=nor.y;o.zeta=zeta;o.wind_tx=windt.x;o.wind_ty=windt.y;o.wind_rx=windr.x;o.wind_ry=windr.y;o.pt_x=pt.x;o.pt_y=pt.y;o.pr_x=pr.x;o.pr_y=pr.y;o.xpre_x=xpre.x;o.xpre_y=xpre.y;o.vpre_x=vpre.x;o.vpre_y=vpre.y;o.xhat_x=xhat.x;o.xhat_y=xhat.y;o.vhat_x=vhat.x;o.vhat_y=vhat.y;o.sensor_visible=vis;o.sensor_x=vis?obs.x:std::numeric_limits<double>::quiet_NaN();o.sensor_y=vis?obs.y:std::numeric_limits<double>::quiet_NaN();o.buffer_pre=buffer_pre;o.buffer_post=(int)buf.size();o.wt_x=wt.x;o.wt_y=wt.y;o.wr_x=wr.x;o.wr_y=wr.y;o.tracking_error=terr;o.tracking_valid=track;o.shadow_tr=sht;o.shadow_rb=shr;o.los_tr=ltr;o.los_rb=lrb;o.margin_tr=mtr;o.margin_rb=mrb;o.prob_tr=ptr;o.prob_rb=prb;o.link_u_tr=in.link_tr[tick];o.link_u_rb=in.link_rb[tick];o.raw_trial_tr=rawt;o.raw_trial_rb=rawr;o.trial_tr=ttr;o.trial_rb=trb;o.packet_valid=packet;o.blackout=blackout;o.lockout=locked;o.et_before=eb_t;o.er_before=eb_r;o.et_after=et;o.er_after=er;o.at_x=c.at.x;o.at_y=c.at.y;o.ar_x=c.ar.x;o.ar_y=c.ar.y;o.gt_x=c.gt.x;o.gt_y=c.gt.y;o.gr_x=c.gr.x;o.gr_y=c.gr.y;o.it=c.ok?c.it:-1;o.ir=c.ok?c.ir:-1;o.uit=c.ok?c.uit:-1;o.uir=c.ok?c.uir:-1;o.safety_override=override;o.min_separation=c.sep;o.terrain_t_after=terrain_t;o.terrain_r_after=terrain_r;o.terrain_penetration=penetration;o.geofence_exit=geofence;o.separation_breach=separation;o.service=service;o.hard_failure=hard;o.no_planner=noplan;o.no_safe=nosafe;o.numerical_fault=numerical;o.battery=battery;
  pt=npt;pr=npr;xhat=add(xhat,mul(vhat,DT));int nx=tick+1;zeta=clip(.96*zeta+2*std::sqrt(1-.96*.96)*in.target[nx],-6,6);double nt=(nx-PRE)*DT;route(in.route_class,in.direction,in.lateral,nt,base,tan,nor);target=add(base,mul(nor,zeta));windt=clipnorm(add(mul(windt,.9),{2*std::sqrt(1-.9*.9)*in.wind_tx[nx],2*std::sqrt(1-.9*.9)*in.wind_ty[nx]}),4);windr=clipnorm(add(mul(windr,.9),{2*std::sqrt(1-.9*.9)*in.wind_rx[nx],2*std::sqrt(1-.9*.9)*in.wind_ry[nx]}),4);sht=.95*sht+3*std::sqrt(1-.95*.95)*in.shadow_tr[nx];shr=.95*shr+3*std::sqrt(1-.95*.95)*in.shadow_rb[nx];bool nv=norm(sub(target,pt))<=250&&los({target.x,target.y,0},{pt.x,pt.y,80});if(nv){buf.push_back({nt,add(target,{3*in.sensor_x[nx],3*in.sensor_y[nx]})});if(buf.size()>2)buf.erase(buf.begin(),buf.end()-2);}
 }
 out.hard_failure=hard;out.no_planner=noplan;out.no_safe=nosafe;out.numerical_fault=numerical;out.battery=battery;return 0;}
}

TB_EXPORT int tbvuus_abi_version(){return ABI;}
TB_EXPORT std::uint64_t tbvuus_input_size(){return sizeof(TBInput);}
TB_EXPORT std::uint64_t tbvuus_tick_size(){return sizeof(TBTick);}
TB_EXPORT std::uint64_t tbvuus_output_size(){return sizeof(TBOutput);}
TB_EXPORT int tbvuus_run_batch(const TBInput* inputs,int count,std::uint64_t input_size,TBOutput* outputs,std::uint64_t output_size){if(!inputs||!outputs||count<0||count>512)return 1;if(input_size!=sizeof(TBInput)||output_size!=sizeof(TBOutput))return 2;for(int i=0;i<count;i++){int rc=run_one(inputs[i],outputs[i]);if(rc)return 1000+i*100+rc;}return 0;}
