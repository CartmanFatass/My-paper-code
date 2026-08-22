#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <numeric>
#include <vector>
#include "event_transform_table.h"

#ifdef _WIN32
#define H90_EXPORT extern "C" __declspec(dllexport)
#else
#define H90_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {
constexpr int MAX_TICKS=144, MAX_STATES=145, PRE=16, LOCK=16, BLACKOUT=4;
constexpr double PI=3.141592653589793238462643383279502884, DT=.25, VG=4.0*PI;
constexpr double BX=-450, BY=250, BZ=15;
struct V2 { double x,y; };
struct V3 { double x,y,z; };
V2 add(V2 a,V2 b){return {a.x+b.x,a.y+b.y};} V2 sub(V2 a,V2 b){return {a.x-b.x,a.y-b.y};}
V2 mul(V2 a,double s){return {a.x*s,a.y*s};} double dot(V2 a,V2 b){return a.x*b.x+a.y*b.y;}
double norm(V2 a){return std::sqrt(a.x*a.x+a.y*a.y);} double clip(double x,double lo,double hi){return std::min(std::max(x,lo),hi);}
V2 clipnorm(V2 a,double lim){double n=norm(a); return n<=lim||n==0?a:mul(a,lim/n);}
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
V2 project(V2 p){if(legal(p))return p;std::vector<V2> c;V2 cl={clip(p.x,-550,550),clip(p.y,-350,350)};if(legal(cl))c.push_back(cl);V2 q[4]={{-100,clip(p.y,-260,80)},{100,clip(p.y,-260,80)},{clip(p.x,-80,80),-280},{clip(p.x,-80,80),100}};for(auto v:q)if(legal(v))c.push_back(v);double cx[4]={-80,-80,80,80},cy[4]={-260,80,-260,80};int sx[4]={-1,-1,1,1},sy[4]={-1,1,-1,1};for(int i=0;i<4;i++){V2 de={p.x-cx[i],p.y-cy[i]};double n=norm(de);if(n>0){V2 r={cx[i]+20*de.x/n,cy[i]+20*de.y/n};if(sx[i]*(r.x-cx[i])>=0&&sy[i]*(r.y-cy[i])>=0&&legal(r))c.push_back(r);}V2 e1={cx[i]+20*sx[i],cy[i]},e2={cx[i],cy[i]+20*sy[i]};if(legal(e1))c.push_back(e1);if(legal(e2))c.push_back(e2);}auto better=[&](V2 a,V2 b){V2 da=sub(a,p),db=sub(b,p);double aa=dot(da,da),bb=dot(db,db);return aa<bb||(aa==bb&&(a.x<b.x||(a.x==b.x&&a.y<b.y)));};V2 best=c[0];for(auto v:c)if(better(v,best))best=v;return best;}
void route(int cls,int dir,double lateral,int tick,V2& base,V2& tangent,V2& normal){double time=(tick-PRE)*DT, scored=cls==0?32:128,duration=scored*DT;if(cls==0){double u=std::max(time,0.0)/duration,phi=PI/4+dir*(u-.5)*PI/2;base={80+64*std::cos(phi)+lateral/std::sqrt(2.0),80+64*std::sin(phi)+lateral/std::sqrt(2.0)};tangent={dir*-std::sin(phi),dir*std::cos(phi)};if(time<0){double p0=PI/4-dir*PI/4;V2 b0={80+64*std::cos(p0)+lateral/std::sqrt(2.0),80+64*std::sin(p0)+lateral/std::sqrt(2.0)};tangent={dir*-std::sin(p0),dir*std::cos(p0)};base=add(b0,mul(tangent,time*VG));}}else{double u=std::max(time,0.0)/duration;base={dir*64*PI*(2*u-1),200+lateral};tangent={(double)dir,0};if(time<0)base=add({-dir*64*PI,200+lateral},mul(tangent,time*VG));}normal={-tangent.y,tangent.x};}
double m0(V3 a,V3 d){double dist=std::sqrt((a.x-d.x)*(a.x-d.x)+(a.y-d.y)*(a.y-d.y)+(a.z-d.z)*(a.z-d.z));return 25-20*std::log10(std::max(dist,1.0)/100)-(los(a,d)?0:30);}
bool plan(V2 x,V2 v,V2 pr,V2& wt,V2& wr){wt=project(add(x,mul(v,2)));V3 wt3={wt.x,wt.y,80},b={BX,BY,BZ};bool found=false;double bs=0,bd=0;for(double f:{.5,.75,1.0}){V2 base={BX+f*(wt.x-BX),BY+f*(wt.y-BY)};V2 offs[5]={{0,0},{120,0},{-120,0},{0,120},{0,-120}};for(auto o:offs){V2 c=add(base,o);if(!legal(c))continue;V3 c3={c.x,c.y,100};double travel=norm(sub(c,pr)),score=std::min(m0(wt3,c3),m0(c3,b))-.01*travel;if(!found||score>bs||(score==bs&&(travel<bd||(travel==bd&&(c.x<wr.x||(c.x==wr.x&&c.y<wr.y)))))){found=true;bs=score;bd=travel;wr=c;}}}return found;}
std::vector<V2> registry(double vmax){std::vector<V2> r={{0,0}};for(double f:{.5,1.0})for(int h=0;h<16;h++){double a=2*PI*h/16;r.push_back({f*vmax*std::cos(a),f*vmax*std::sin(a)});}return r;}
double minsep(V2 pt,V2 vt,V2 pr,V2 vr){V2 r=sub(pt,pr),v=sub(vt,vr);double den=dot(v,v),t=den==0?0:clip(-dot(r,v)/den,0,DT);return norm(add(r,mul(v,t)));}
struct Control {int it=-1,ir=-1,uit=-1,uir=-1;V2 at{},ar{},gt{},gr{};double sep=0;bool ok=false;};
Control control(V2 pt,V2 pr,V2 wt,V2 wr,V2 windt,V2 windr){static auto at=registry(18.0),ar=registry(22.0);V2 nt=clipnorm(mul(sub(wt,pt),.5),18),nr=clipnorm(mul(sub(wr,pr),.5),22);Control out;double uo=0,ua=0,bo=0,ba=0;bool uf=false,bf=false;for(int i=0;i<33;i++){V2 gt=add(at[i],windt);for(int j=0;j<33;j++){V2 gr=add(ar[j],windr);double obj=dot(sub(gt,nt),sub(gt,nt))+dot(sub(gr,nr),sub(gr,nr)),air=norm(at[i])+norm(ar[j]);if(!uf||obj<uo||(obj==uo&&(air<ua||(air==ua&&(i<out.uit||(i==out.uit&&j<out.uir)))))){uf=true;uo=obj;ua=air;out.uit=i;out.uir=j;}if(!legal_tick(pt,gt)||!legal_tick(pr,gr))continue;double sep=minsep(pt,gt,pr,gr);if(sep<30)continue;if(!bf||obj<bo||(obj==bo&&(air<ba||(air==ba&&(i<out.it||(i==out.it&&j<out.ir)))))){bf=true;bo=obj;ba=air;out.it=i;out.ir=j;out.at=at[i];out.ar=ar[j];out.gt=gt;out.gr=gr;out.sep=sep;}}}out.ok=bf;return out;}
struct Frac{int64_t n,d;}; Frac normf(int64_t n,int64_t d){if(d<0){n=-n;d=-d;}int64_t g=std::gcd(n<0?-n:n,d);return {n/g,d/g};}Frac addf(Frac a,Frac b){return normf(a.n*b.d+b.n*a.d,a.d*b.d);}Frac mulf(Frac a,Frac b){return normf(a.n*b.n,a.d*b.d);}
double from_bits(std::uint64_t bits){double value;std::memcpy(&value,&bits,sizeof(value));return value;}
bool transform(Frac q,double& lambda,double& probability){if(q.d<=0)return false;int64_t scaled=q.n*1024;if(scaled%q.d!=0)return false;int64_t index=scaled/q.d;if(index<0||index>896)return false;lambda=from_bits(H90_LAMBDA_BITS[index]);probability=from_bits(H90_EVENT_BITS[index]);return true;}
}

extern "C" {
struct H90Input {
 int route_class,direction,lateral,policy_kind;
 int alpha_s,alpha_l,beta_s,beta_l,gamma_s,gamma_l;
 int64_t explicit_num[128],explicit_den[128];
 double target[MAX_STATES],wind_tx[MAX_STATES],wind_ty[MAX_STATES],wind_rx[MAX_STATES],wind_ry[MAX_STATES],sensor_x[MAX_STATES],sensor_y[MAX_STATES],shadow_tr[MAX_STATES],shadow_rb[MAX_STATES];
 double link_tr[MAX_TICKS],link_rb[MAX_TICKS],action[MAX_TICKS];
};
struct H90Tick {
 int tick,scored,scored_index,action_code,legal_opportunity,action_consumed;
 int64_t rate_num,rate_den;
 double time,action_uniform,rate_q,event_lambda,event_probability,eligible_time;
 double target_x,target_y,tangent_x,tangent_y,normal_x,normal_y,zeta,wind_t_x,wind_t_y,wind_r_x,wind_r_y;
 double pt_x,pt_y,pr_x,pr_y,xhat_x,xhat_y,vhat_x,vhat_y;
 int sensor_visible; double sensor_x,sensor_y; int buffer_count;
 double wt_x,wt_y,wr_x,wr_y,tracking_error; int tracking_valid;
 double shadow_tr,shadow_rb; int los_tr,los_rb; double margin_tr,margin_rb,prob_tr,prob_rb,link_u_tr,link_u_rb; int raw_trial_tr,raw_trial_rb,trial_tr,trial_rb,packet_valid,blackout,lockout;
 double et_before,er_before,et_after,er_after,at_x,at_y,ar_x,ar_y,gt_x,gt_y,gr_x,gr_y;
 int it,ir,uit,uir,safety_override; double min_separation,terrain_t_after,terrain_r_after; int terrain_penetration,geofence_exit,separation_breach;
 int service,hard_failure,no_planner,no_safe,battery;
};
struct H90Output {int total_ticks,scored_valid,updates,keeps,opportunities,overrides,hard_failure,no_planner,no_safe,battery;H90Tick ticks[MAX_TICKS];};
}

namespace {
Frac rate_for(const H90Input& in,int k,int anchor){int S=in.route_class==0?32:128;if(in.policy_kind==1)return normf(in.explicit_num[k],in.explicit_den[k]);int al=in.route_class==0?in.alpha_s:in.alpha_l,b=in.route_class==0?in.beta_s:in.beta_l,g=in.route_class==0?in.gamma_s:in.gamma_l;Frac r=normf(S-k,S),age=normf(k-anchor,128);if(age.n>age.d)age={1,1};Frac q=addf(normf(al,8),addf(mulf(normf(b,8),addf(r,{-1,2})),mulf(normf(g,8),addf(age,{-1,2}))));if(q.n<0)return {0,1};if(q.n*8>q.d*7)return {7,8};return q;}
void radio(V3 a,V3 d,double sh,double u,int& l,double& margin,double& prob,int& trial){l=los(a,d);double dist=std::sqrt((a.x-d.x)*(a.x-d.x)+(a.y-d.y)*(a.y-d.y)+(a.z-d.z)*(a.z-d.z));margin=25-20*std::log10(std::max(dist,1.0)/100)-(l?0:30)+sh;prob=1/(1+std::exp(-margin/3));trial=u<prob;}
int run_one(const H90Input& in,H90Output& out){int total=in.route_class==0?48:144;out={};out.total_ticks=total;double zeta=clip(2*in.target[0],-6,6);V2 base,tan,nor;route(in.route_class,in.direction,in.lateral,0,base,tan,nor);V2 target=add(base,mul(nor,zeta)),pt=target,pr={0,180},windt=clipnorm({2*in.wind_tx[0],2*in.wind_ty[0]},4),windr=clipnorm({2*in.wind_rx[0],2*in.wind_ry[0]},4);double sht=3*in.shadow_tr[0],shr=3*in.shadow_rb[0],et=40000,er=45000;V2 xhat{},vhat{},wt=pt,wr=pr;struct Obs{double t;V2 z;};std::vector<Obs> buf;int lockuntil=0,blackuntil=0,anchor=0;bool hard=false,noplan=false,nosafe=false,battery=false;
 for(int tick=0;tick<total;tick++){H90Tick& o=out.ticks[tick];o={};double time=(tick-PRE)*DT;bool scored=tick>=PRE;int k=tick-PRE;bool vis=norm(sub(target,pt))<=250&&los({target.x,target.y,0},{pt.x,pt.y,80});V2 obs=add(target,{3*in.sensor_x[tick],3*in.sensor_y[tick]});int action_code=0;if(tick==0){if(!vis)return 2;buf.push_back({time,obs});xhat=obs;vhat=clipnorm(mul(tan,VG),20);if(!plan(xhat,vhat,pr,wt,wr)){hard=noplan=true;}buf.clear();action_code=1;lockuntil=LOCK;blackuntil=BLACKOUT;}
  bool opportunity=scored&&tick>=lockuntil&&!hard;Frac rate{0,1};double lambda=0,pe=0,eu=0,au=std::numeric_limits<double>::quiet_NaN();if(opportunity){out.opportunities++;rate=rate_for(in,k,anchor);eu=DT;if(!transform(rate,lambda,pe))return 3;au=in.action[tick];if(au<pe){action_code=2;out.updates++;if(buf.size()>=2){Obs a=buf[buf.size()-2],b=buf.back();xhat=b.z;vhat=clipnorm(mul(sub(b.z,a.z),1/(b.t-a.t)),20);}else if(buf.size()==1)xhat=buf.back().z;buf.clear();if(!plan(xhat,vhat,pr,wt,wr)){hard=noplan=true;}lockuntil=tick+LOCK;blackuntil=tick+BLACKOUT;anchor=k;}else out.keeps++;}
  bool blackout=tick<blackuntil,locked=tick<lockuntil;int ltr,lrb,ttr,trb;double mtr,mrb,ptr,prb;radio({pt.x,pt.y,80},{pr.x,pr.y,100},sht,in.link_tr[tick],ltr,mtr,ptr,ttr);radio({pr.x,pr.y,100},{BX,BY,BZ},shr,in.link_rb[tick],lrb,mrb,prb,trb);int rawt=ttr,rawr=trb;ttr=ttr&&!blackout;trb=trb&&!blackout;bool packet=ttr&&trb;double terr=norm(sub(xhat,target));bool track=terr<=15;double eb_t=et,eb_r=er;Control c;if(!hard&&!battery)c=control(pt,pr,wt,wr,windt,windr);if(!c.ok){if(!hard){hard=nosafe=true;}c.sep=norm(sub(pt,pr));}bool override=c.ok&&(c.it!=c.uit||c.ir!=c.uir);out.overrides+=override;int service=scored&&track&&packet&&!blackout&&!battery&&!hard;out.scored_valid+=service;V2 npt=battery?pt:add(pt,mul(c.gt,DT)),npr=battery?pr:add(pr,mul(c.gr,DT));double charge=(action_code==1||action_code==2)?200:0;et=std::max(0.0,et-DT*(300+dot(c.at,c.at))-charge);er=std::max(0.0,er-DT*(350+dot(c.ar,c.ar))-charge);if(et==0||er==0){battery=hard=true;}
  o.tick=tick;o.time=time;o.scored=scored;o.scored_index=k;o.action_code=action_code;o.legal_opportunity=opportunity;o.action_consumed=opportunity;o.action_uniform=au;o.rate_num=rate.n;o.rate_den=rate.d;o.rate_q=(double)rate.n/rate.d;o.event_lambda=lambda;o.event_probability=pe;o.eligible_time=eu;o.target_x=target.x;o.target_y=target.y;o.tangent_x=tan.x;o.tangent_y=tan.y;o.normal_x=nor.x;o.normal_y=nor.y;o.zeta=zeta;o.wind_t_x=windt.x;o.wind_t_y=windt.y;o.wind_r_x=windr.x;o.wind_r_y=windr.y;o.pt_x=pt.x;o.pt_y=pt.y;o.pr_x=pr.x;o.pr_y=pr.y;o.xhat_x=xhat.x;o.xhat_y=xhat.y;o.vhat_x=vhat.x;o.vhat_y=vhat.y;o.sensor_visible=vis;o.sensor_x=vis?obs.x:std::numeric_limits<double>::quiet_NaN();o.sensor_y=vis?obs.y:std::numeric_limits<double>::quiet_NaN();o.buffer_count=(int)buf.size();o.wt_x=wt.x;o.wt_y=wt.y;o.wr_x=wr.x;o.wr_y=wr.y;o.tracking_error=terr;o.tracking_valid=track;o.shadow_tr=sht;o.shadow_rb=shr;o.los_tr=ltr;o.los_rb=lrb;o.margin_tr=mtr;o.margin_rb=mrb;o.prob_tr=ptr;o.prob_rb=prb;o.link_u_tr=in.link_tr[tick];o.link_u_rb=in.link_rb[tick];o.raw_trial_tr=rawt;o.raw_trial_rb=rawr;o.trial_tr=ttr;o.trial_rb=trb;o.packet_valid=packet;o.blackout=blackout;o.lockout=locked;o.et_before=eb_t;o.er_before=eb_r;o.et_after=et;o.er_after=er;o.at_x=c.at.x;o.at_y=c.at.y;o.ar_x=c.ar.x;o.ar_y=c.ar.y;o.gt_x=c.gt.x;o.gt_y=c.gt.y;o.gr_x=c.gr.x;o.gr_y=c.gr.y;o.it=c.ok?c.it:-1;o.ir=c.ok?c.ir:-1;o.uit=c.ok?c.uit:-1;o.uir=c.ok?c.uir:-1;o.safety_override=override;o.min_separation=c.sep;o.terrain_t_after=d_obs(npt);o.terrain_r_after=d_obs(npr);o.terrain_penetration=o.terrain_t_after<20||o.terrain_r_after<20;o.geofence_exit=npt.x< -550||npt.x>550||npt.y< -350||npt.y>350||npr.x< -550||npr.x>550||npr.y< -350||npr.y>350;o.separation_breach=c.sep<30;o.service=service;o.hard_failure=hard;o.no_planner=noplan;o.no_safe=nosafe;o.battery=battery;
  pt=npt;pr=npr;xhat=add(xhat,mul(vhat,DT));int nx=tick+1;zeta=clip(.96*zeta+2*std::sqrt(1-.96*.96)*in.target[nx],-6,6);route(in.route_class,in.direction,in.lateral,nx,base,tan,nor);target=add(base,mul(nor,zeta));windt=clipnorm(add(mul(windt,.9),{2*std::sqrt(1-.9*.9)*in.wind_tx[nx],2*std::sqrt(1-.9*.9)*in.wind_ty[nx]}),4);windr=clipnorm(add(mul(windr,.9),{2*std::sqrt(1-.9*.9)*in.wind_rx[nx],2*std::sqrt(1-.9*.9)*in.wind_ry[nx]}),4);sht=.95*sht+3*std::sqrt(1-.95*.95)*in.shadow_tr[nx];shr=.95*shr+3*std::sqrt(1-.95*.95)*in.shadow_rb[nx];double nt=(nx-PRE)*DT;bool nv=norm(sub(target,pt))<=250&&los({target.x,target.y,0},{pt.x,pt.y,80});if(nv){buf.push_back({nt,add(target,{3*in.sensor_x[nx],3*in.sensor_y[nx]})});if(buf.size()>2)buf.erase(buf.begin(),buf.end()-2);}
 }
 out.hard_failure=hard;out.no_planner=noplan;out.no_safe=nosafe;out.battery=battery;return 0;}
}

H90_EXPORT int headland90_abi_version(){return 1;}
H90_EXPORT int headland90_event_transform(int64_t numerator,int64_t denominator,std::uint64_t* lambda_bits,std::uint64_t* event_bits){if(!lambda_bits||!event_bits||denominator==0)return 1;Frac q=normf(numerator,denominator);double lambda,probability;if(!transform(q,lambda,probability))return 2;std::memcpy(lambda_bits,&lambda,sizeof(lambda));std::memcpy(event_bits,&probability,sizeof(probability));return 0;}
H90_EXPORT int headland90_run_batch(const H90Input* inputs,int count,H90Output* outputs){if(!inputs||!outputs||count<0)return 1;for(int i=0;i<count;i++){int rc=run_one(inputs[i],outputs[i]);if(rc)return 1000+i*10+rc;}return 0;}
