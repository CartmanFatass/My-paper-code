#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <new>

#ifdef _WIN32
#define SCDMP_EXPORT extern "C" __declspec(dllexport)
#else
#define SCDMP_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {
constexpr int ABI_VERSION = 2;
constexpr int HORIZON = 420;
constexpr int MAX_QUERIES = 105;
constexpr int MAX_HOLD = 14;
constexpr std::uint64_t FIXTURE_MAGIC = UINT64_C(0x5343444D50553032);
constexpr std::uint64_t STATE_MAGIC = UINT64_C(0x5350445354415445);

struct ResetInput {
    std::uint64_t fixture_magic; int abi_version; int event_order; int regime; int switch_tick;
    double initial_v; double initial_phi;
    double eta_v[HORIZON]; double eta_omega[HORIZON];
};
struct Input {
    std::uint64_t fixture_magic; int abi_version; int event_order; int regime; int switch_tick;
    double initial_v; double initial_phi; int actions[MAX_QUERIES];
    double eta_v[HORIZON]; double eta_omega[HORIZON];
};
struct Tick {
    int tick,k,queried,action_code,u1,u2,u3;
    double x_before,x_after,v_after,phi_after,omega_after,z_after,f_after;
    double tau1_after,tau2_after,tau3_after,reward,effort;
    int overload,swing,formation,delivery,timeout,terminal;
};
struct RenewalOutput {
    int status,event_order,regime,switch_tick;
    double public_observation[14];
    int token_first,token_second;
    double chronology_q;
    int realized_duration,primitive_reward_count;
    double primitive_rewards[MAX_HOLD];
    double reward_sum;
    int terminal,delivery,timeout,physical_failure,overload,swing,formation;
    int allocated_slots,integrated_ticks,masked_slots,policy_queries,terminal_tick;
    double delivery_time_seconds,completion_time_seconds,cumulative_reward,mean_active_effort;
};
struct Output {
    int status,event_order,regime,switch_tick;
    double initial_observation[14]; double hidden_d;
    int mode,token_first,token_second; double chronology_q;
    int allocated_slots,integrated_ticks,masked_slots,policy_queries;
    int delivery,timeout,physical_failure,overload,swing,formation,terminal_tick;
    double delivery_time_seconds,completion_time_seconds,cumulative_reward,mean_active_effort;
    double final_x,final_v,final_phi,final_omega,final_z,final_f;
    double final_tau1,final_tau2,final_tau3;
    Tick ticks[HORIZON];
};
struct State {
    std::uint64_t state_magic;
    int event_order,regime,switch_tick,token_first,token_second;
    double chronology_q,eta_v[HORIZON],eta_omega[HORIZON];
    double x,v,phi,omega,z,formation_state,tau1,tau2,tau3;
    int previous1,previous2,previous3;
    double d; int mode,n,queries;
    bool terminal,delivery,timeout,overload,swing,formation;
    double cumulative_reward,cumulative_effort;
};

double clip(double value,double lower,double upper){return std::min(std::max(value,lower),upper);}
bool valid_common(std::uint64_t magic,int abi,int event_order,int regime,int switch_tick,
                  double initial_v,double initial_phi,const double* eta_v,const double* eta_omega){
    if(magic!=FIXTURE_MAGIC||abi!=ABI_VERSION||event_order<0||event_order>1||regime<0||regime>5)return false;
    const bool switched=regime==4||regime==5;
    if(switched){if(switch_tick!=168&&switch_tick!=252)return false;}else if(switch_tick!=0)return false;
    if(!std::isfinite(initial_v)||initial_v<0||initial_v>0.04||!std::isfinite(initial_phi)||initial_phi<-.015||initial_phi>.015)return false;
    for(int t=0;t<HORIZON;++t){if(eta_v[t]!=-.004&&eta_v[t]!=.004)return false;if(eta_omega[t]!=-.006&&eta_omega[t]!=.006)return false;}
    return true;
}
bool valid_reset(const ResetInput& i){return valid_common(i.fixture_magic,i.abi_version,i.event_order,i.regime,i.switch_tick,i.initial_v,i.initial_phi,i.eta_v,i.eta_omega);}
bool valid_input(const Input& i){
    if(!valid_common(i.fixture_magic,i.abi_version,i.event_order,i.regime,i.switch_tick,i.initial_v,i.initial_phi,i.eta_v,i.eta_omega))return false;
    for(int j=0;j<MAX_QUERIES;++j)if(i.actions[j]<0||i.actions[j]>=27)return false;return true;
}
int initial_k(int r){constexpr int v[6]={4,10,6,14,6,14};return v[r];}
int final_k(int r){constexpr int v[6]={4,10,6,14,14,6};return v[r];}
int current_k(const State& s){return((s.regime==4||s.regime==5)&&s.n>=s.switch_tick)?final_k(s.regime):initial_k(s.regime);}
void fill_public(const State& s,double* o){
    o[0]=s.x/36.;o[1]=s.v/1.8;o[2]=s.phi/.48;o[3]=s.omega/.5;o[4]=s.z/.55;o[5]=s.formation_state/.42;
    o[6]=s.tau1/1.25;o[7]=s.tau2/1.25;o[8]=s.tau3/1.25;o[9]=s.previous1/2.;o[10]=s.previous2/2.;o[11]=s.previous3/2.;o[12]=s.n/420.;o[13]=current_k(s)/14.;
}
void initialize_state(State& s,int event_order,int regime,int switch_tick,double initial_v,double initial_phi,const double* eta_v,const double* eta_omega){
    std::memset(&s,0,sizeof(State));s.state_magic=STATE_MAGIC;s.event_order=event_order;s.regime=regime;s.switch_tick=switch_tick;
    std::memcpy(s.eta_v,eta_v,sizeof(s.eta_v));std::memcpy(s.eta_omega,eta_omega,sizeof(s.eta_omega));
    if(event_order==0){s.token_first=0;s.token_second=1;s.mode=1;s.d=clip(s.d+.55*s.mode,0.,1.);s.chronology_q=1.;}
    else{s.token_first=1;s.token_second=0;s.d=clip(s.d+.55*s.mode,0.,1.);s.mode=1;s.chronology_q=0.;}
    s.x=0.;s.v=initial_v;s.phi=initial_phi;s.omega=s.z=s.formation_state=0.;s.tau1=s.tau2=s.tau3=0.;s.previous1=s.previous2=s.previous3=0;s.n=0;
}
void fill_renewal(const State& s,RenewalOutput& o,int duration,const double* rewards,double reward_sum){
    std::memset(&o,0,sizeof(RenewalOutput));o.status=0;o.event_order=s.event_order;o.regime=s.regime;o.switch_tick=s.switch_tick;fill_public(s,o.public_observation);
    o.token_first=s.token_first;o.token_second=s.token_second;o.chronology_q=s.chronology_q;o.realized_duration=duration;o.primitive_reward_count=duration;
    for(int i=0;i<duration;++i)o.primitive_rewards[i]=rewards[i];o.reward_sum=reward_sum;o.terminal=s.terminal;o.delivery=s.delivery;o.timeout=s.timeout;
    o.overload=s.overload;o.swing=s.swing;o.formation=s.formation;o.physical_failure=s.overload||s.swing||s.formation;
    o.allocated_slots=HORIZON;o.integrated_ticks=s.n;o.masked_slots=s.terminal?HORIZON-s.n:0;o.policy_queries=s.queries;o.terminal_tick=s.terminal?s.n:0;
    o.delivery_time_seconds=s.delivery?.1*s.n:-1.;o.completion_time_seconds=s.terminal?(s.delivery?.1*s.n:42.):-1.;
    o.cumulative_reward=s.cumulative_reward;o.mean_active_effort=s.n>0?s.cumulative_effort/s.n:0.;
}
int advance_state(State& s,int action,RenewalOutput& out,Tick* trace){
    if(s.state_magic!=STATE_MAGIC)return 1;
    if(s.terminal){if(action!=-1)return 2;const double empty[MAX_HOLD]={};fill_renewal(s,out,0,empty,0.);return 0;}
    if(action<0||action>=27||s.queries>=MAX_QUERIES)return 3;
    const int k=current_k(s),u1=action/9,u2=(action/3)%3,u3=action%3;double rewards[MAX_HOLD]={},reward_sum=0.;int duration=0;++s.queries;
    for(int offset=0;offset<k&&s.n<HORIZON&&!s.terminal;++offset){
        Tick r{};r.tick=s.n;r.k=k;r.queried=offset==0;r.action_code=action;r.u1=u1;r.u2=u2;r.u3=u3;r.x_before=s.x;
        const double a=(u1+u2+u3)/3.,b=std::max({std::abs(u1-a),std::abs(u2-a),std::abs(u3-a)});
        s.tau1=.42+.17*u1+.11*std::abs(u1-a)+.20*s.d*a*a+.07*std::abs(s.phi);
        s.tau2=.42+.17*u2+.11*std::abs(u2-a)+.20*s.d*a*a+.07*std::abs(s.phi);
        s.tau3=.42+.17*u3+.11*std::abs(u3-a)+.20*s.d*a*a+.07*std::abs(s.phi);
        const double epsilon=std::max(0.,std::max({s.tau1,s.tau2,s.tau3})-(1.04-.16*s.d));
        s.omega=.90*s.omega-.12*s.phi+.055*b+.035*s.d*a+s.eta_omega[s.n];s.phi=clip(s.phi+.1*s.omega,-.70,.70);
        s.v=clip(.94*s.v+.06*a-.018*s.d*a*a-.025*std::abs(s.phi)+s.eta_v[s.n],0.,1.8);s.x+=.1*s.v;
        s.z=.86*s.z+epsilon;s.formation_state=.84*s.formation_state+.09*b+.08*std::abs(s.phi);s.previous1=u1;s.previous2=u2;s.previous3=u3;++s.n;
        s.overload=s.z>.55;s.swing=std::abs(s.phi)>.48;s.formation=s.formation_state>.42;const bool physical=s.overload||s.swing||s.formation;
        s.delivery=!physical&&s.x>=36.;s.timeout=!physical&&!s.delivery&&s.n>=HORIZON;s.terminal=physical||s.delivery||s.timeout;
        const double squares=u1*u1+u2*u2+u3*u3,effort=squares/12.;double reward=.02*(s.x-r.x_before)-.001*squares/3.-.002*s.phi*s.phi-.002*s.formation_state*s.formation_state;
        if(s.delivery)reward+=1.;else if(physical)reward-=1.;else if(s.timeout)reward-=.5;s.cumulative_reward+=reward;s.cumulative_effort+=effort;rewards[duration]=reward;reward_sum+=reward;
        r.x_after=s.x;r.v_after=s.v;r.phi_after=s.phi;r.omega_after=s.omega;r.z_after=s.z;r.f_after=s.formation_state;r.tau1_after=s.tau1;r.tau2_after=s.tau2;r.tau3_after=s.tau3;r.reward=reward;r.effort=effort;
        r.overload=s.overload;r.swing=s.swing;r.formation=s.formation;r.delivery=s.delivery;r.timeout=s.timeout;r.terminal=s.terminal;if(trace)trace[duration]=r;++duration;
    }
    fill_renewal(s,out,duration,rewards,reward_sum);return 0;
}
void fill_full(const State& s,const double* initial,Output& o){
    o.status=0;o.event_order=s.event_order;o.regime=s.regime;o.switch_tick=s.switch_tick;std::memcpy(o.initial_observation,initial,sizeof(o.initial_observation));
    o.hidden_d=s.d;o.mode=s.mode;o.token_first=s.token_first;o.token_second=s.token_second;o.chronology_q=s.chronology_q;o.allocated_slots=HORIZON;o.integrated_ticks=s.n;o.masked_slots=HORIZON-s.n;o.policy_queries=s.queries;
    o.delivery=s.delivery;o.timeout=s.timeout;o.overload=s.overload;o.swing=s.swing;o.formation=s.formation;o.physical_failure=s.overload||s.swing||s.formation;o.terminal_tick=s.n;
    o.delivery_time_seconds=s.delivery?.1*s.n:-1.;o.completion_time_seconds=s.delivery?.1*s.n:42.;o.cumulative_reward=s.cumulative_reward;o.mean_active_effort=s.n>0?s.cumulative_effort/s.n:0.;
    o.final_x=s.x;o.final_v=s.v;o.final_phi=s.phi;o.final_omega=s.omega;o.final_z=s.z;o.final_f=s.formation_state;o.final_tau1=s.tau1;o.final_tau2=s.tau2;o.final_tau3=s.tau3;
}
int run_one(const Input& input,Output& output){
    std::memset(&output,0,sizeof(Output));if(!valid_input(input)){output.status=1;return 1;}State s{};initialize_state(s,input.event_order,input.regime,input.switch_tick,input.initial_v,input.initial_phi,input.eta_v,input.eta_omega);
    double initial[14];fill_public(s,initial);while(!s.terminal){if(s.queries>=MAX_QUERIES){output.status=2;return 2;}const int action=input.actions[s.queries],start=s.n;Tick ticks[MAX_HOLD]{};RenewalOutput renewal{};const int status=advance_state(s,action,renewal,ticks);if(status){output.status=status;return status;}for(int i=0;i<renewal.realized_duration;++i)output.ticks[start+i]=ticks[i];}
    fill_full(s,initial,output);return 0;
}
}

SCDMP_EXPORT int scdmp_uav_sp_abi_version(){return ABI_VERSION;}
SCDMP_EXPORT std::size_t scdmp_uav_sp_sizeof_reset_input(){return sizeof(ResetInput);}
SCDMP_EXPORT std::size_t scdmp_uav_sp_sizeof_full_input(){return sizeof(Input);}
SCDMP_EXPORT std::size_t scdmp_uav_sp_sizeof_tick(){return sizeof(Tick);}
SCDMP_EXPORT std::size_t scdmp_uav_sp_sizeof_renewal_output(){return sizeof(RenewalOutput);}
SCDMP_EXPORT std::size_t scdmp_uav_sp_sizeof_full_output(){return sizeof(Output);}
SCDMP_EXPORT int scdmp_uav_sp_run_batch(const Input* inputs,int count,Output* outputs){if(!inputs||!outputs||count<=0)return 10;for(int i=0;i<count;++i){int s=run_one(inputs[i],outputs[i]);if(s)return 1000+i*10+s;}return 0;}
SCDMP_EXPORT int scdmp_uav_sp_reset_batch(const ResetInput* inputs,int count,void** states,RenewalOutput* outputs){
    if(!inputs||!states||!outputs||count<=0)return 20;for(int i=0;i<count;++i)states[i]=nullptr;
    for(int i=0;i<count;++i){if(!valid_reset(inputs[i])){for(int j=0;j<i;++j)delete static_cast<State*>(states[j]);return 2000+i*10+1;}State* s=new(std::nothrow)State;if(!s){for(int j=0;j<i;++j)delete static_cast<State*>(states[j]);return 2000+i*10+2;}initialize_state(*s,inputs[i].event_order,inputs[i].regime,inputs[i].switch_tick,inputs[i].initial_v,inputs[i].initial_phi,inputs[i].eta_v,inputs[i].eta_omega);states[i]=s;const double empty[MAX_HOLD]={};fill_renewal(*s,outputs[i],0,empty,0.);}return 0;
}
SCDMP_EXPORT int scdmp_uav_sp_renew_batch(void* const* states,const int* actions,int count,RenewalOutput* outputs){if(!states||!actions||!outputs||count<=0)return 30;for(int i=0;i<count;++i){State* s=static_cast<State*>(states[i]);if(!s||s->state_magic!=STATE_MAGIC)return 3000+i*10+1;int status=advance_state(*s,actions[i],outputs[i],nullptr);if(status)return 3000+i*10+status;}return 0;}
SCDMP_EXPORT int scdmp_uav_sp_close_batch(void** states,int count){if(!states||count<=0)return 40;for(int i=0;i<count;++i){State* s=static_cast<State*>(states[i]);if(!s)continue;if(s->state_magic!=STATE_MAGIC)return 4000+i*10+1;s->state_magic=0;delete s;states[i]=nullptr;}return 0;}
