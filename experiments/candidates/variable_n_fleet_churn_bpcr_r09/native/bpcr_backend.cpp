#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cmath>
#include <intrin.h>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <tuple>
#include <vector>

#if defined(_WIN32)
#define BPCR_EXPORT extern "C" __declspec(dllexport)
#else
#define BPCR_EXPORT extern "C"
#endif

namespace {
constexpr std::int32_t kAbiVersion = 1;
constexpr std::uint64_t kMagic = UINT64_C(0x564E464342504352);
constexpr int kNull = 255;
constexpr int kStates = 16;

struct FixtureInput {
    std::uint64_t fixture_magic;
    std::int32_t abi_version;
    std::int32_t failed_zone;
    std::int32_t demand_1;
    std::int32_t demand_2;
    std::int32_t blocked_1;
    std::int32_t blocked_2;
    std::int32_t failed_relay_present;
};

struct FixtureOutput {
    std::int32_t status;
    std::int32_t candidate_count;
    std::int32_t scorer_command[4];
    std::int32_t checker_command[4];
    std::int32_t scorer_checker_equal;
    std::int32_t independent_enumerator_equal;
    std::int32_t witness_present;
    std::int32_t earliest_safe_executor_rank;
    std::int32_t needed_relay_rank;
    std::int32_t selected_floor_num;
    std::int32_t selected_floor_den;
    std::int32_t selected_event_count;
    std::int32_t selected_reward_record_count;
    std::int32_t post60_reduced_verified;
};

struct HostInput {
    std::uint64_t fixture_magic;
    std::int32_t abi_version;
    std::uint8_t selected_mask;
    std::uint8_t failed_zone;
    std::uint8_t reserved[6];
    std::int32_t demand_1[12];
    std::int32_t demand_2[12];
    std::int32_t blocked_1[12];
    std::int32_t blocked_2[12];
    std::int32_t commands[48];
};

struct HostOutput {
    std::int32_t status;
    std::int32_t integrated_ticks;
    std::int32_t decision_count;
    std::int32_t failed_rank;
    std::int64_t fail_delivered;
    std::int64_t fail_demand;
    std::int64_t total_delivered;
    std::int64_t total_demand;
    std::int64_t intact_delivered;
    std::int64_t intact_demand;
    std::int32_t final_token_state[4];
    std::int32_t final_acquisition_elapsed[4];
    std::int32_t safety_violation;
    std::int32_t exclusivity_violation;
    std::int32_t event_count;
};

struct Agent { int rank; bool fast; int radio; int node; int token; bool acquired; int energy_fifths; };
struct Candidate { std::array<int,4> occupant{}; bool operator==(const Candidate&o)const{return occupant==o.occupant;} };
struct Schedule { std::array<int,4> acquired_at{}; std::array<int,4> radio{}; int event_count{}; int reward_records{}; };
struct Big256 {
    std::array<std::uint64_t,4> limb{};
    static Big256 from(std::uint64_t value){Big256 x;x.limb[0]=value;return x;}
    void add(const Big256&o){unsigned char carry=0;for(int i=0;i<4;++i)carry=_addcarry_u64(carry,limb[i],o.limb[i],&limb[i]);if(carry)throw std::overflow_error("Big256 add");}
    Big256 mul(std::uint64_t value)const{Big256 out;std::uint64_t carry=0;for(int i=0;i<4;++i){std::uint64_t high=0,low=_umul128(limb[i],value,&high),sum=0;unsigned char c=_addcarry_u64(0,low,carry,&sum);out.limb[i]=sum;if(i==3&&(high||c))throw std::overflow_error("Big256 mul");carry=high+c;}return out;}
    friend bool operator==(const Big256&a,const Big256&b){return a.limb==b.limb;}
    friend bool operator!=(const Big256&a,const Big256&b){return!(a==b);}
    friend bool operator<(const Big256&a,const Big256&b){for(int i=3;i>=0;--i)if(a.limb[i]!=b.limb[i])return a.limb[i]<b.limb[i];return false;}
    friend bool operator>(const Big256&a,const Big256&b){return b<a;}
};
struct Score { int floor_num{}; int floor_den{1}; Big256 objective; int releases{}; std::array<int,4> serial{}; };

struct SimAgent {
    int rank{}; bool fast{}; int radio{}; int node{}; int destination_node{};
    int remaining{}; int token{-1}; int command_token{-1}; bool acquired{};
    int acquisition_elapsed{}; int energy_fifths{800};
};

int state_index(int q1,int q2,int h1,int h2){return(q1-1)|((q2-1)<<1)|(h1<<2)|(h2<<3);}
void decode_state(int e,int&q1,int&q2,int&h1,int&h2){q1=1+(e&1);q2=1+((e>>1)&1);h1=(e>>2)&1;h2=(e>>3)&1;}
int transition_num_1d(int from,int to,bool obstruction){if(!obstruction){static const int n[2][2]={{8,2},{3,7}};return n[from][to];}static const int n[2][2]={{4,1},{2,3}};return n[from][to];}
std::uint64_t transition_num(int from,int to){int aq1,aq2,ah1,ah2,bq1,bq2,bh1,bh2;decode_state(from,aq1,aq2,ah1,ah2);decode_state(to,bq1,bq2,bh1,bh2);return static_cast<std::uint64_t>(transition_num_1d(aq1-1,bq1-1,false))*transition_num_1d(aq2-1,bq2-1,false)*transition_num_1d(ah1,bh1,true)*transition_num_1d(ah2,bh2,true);}

int standard_distance(int from,int to){static const int d[5][5]={{0,20,40,30,50},{20,0,20,40,60},{40,20,0,60,80},{30,40,60,0,20},{50,60,80,20,0}};return d[from][to];}
int travel_time(const Agent&a,int destination){int t=standard_distance(a.node,destination);return a.fast?std::max(5,5*((3*t+19)/20)):t;}
int token_node(int t){return t<2?(t==0?2:1):(t==2?4:3);} int acquisition_seconds(int t){return(t==0||t==2)?6:4;}

std::vector<Agent> fixture_agents(const FixtureInput&in){
    static const bool fast[8]={true,false,true,false,true,false,true,false};static const int radio[8]={2,2,1,1,2,2,1,1};
    int failed=in.failed_zone==1?1:2;std::vector<Agent>out;
    for(int rank=1;rank<=8;++rank){if(rank==failed)continue;Agent a{rank,fast[rank-1],radio[rank-1],0,-1,false,800};
        if(rank==(in.failed_zone==1?2:1)){a.node=in.failed_zone==1?4:2;a.token=in.failed_zone==1?2:0;a.acquired=true;a.energy_fifths=600;}
        else if(rank==3&&in.failed_relay_present){a.node=in.failed_zone==1?1:3;a.token=in.failed_zone==1?1:3;a.acquired=true;a.energy_fifths=600;}
        else if(rank==4&&(in.failed_zone==1?in.blocked_2:in.blocked_1)){a.node=in.failed_zone==1?3:1;a.token=in.failed_zone==1?3:1;a.acquired=true;a.energy_fifths=600;}
        out.push_back(a);}return out;
}
bool safe_candidate(const Agent&a,int token){int node=token_node(token),out=travel_time(a,node);Agent at=a;at.node=node;int home=travel_time(at,0),fc=a.fast?6:5,sc=(token==0||token==2)?2:1;int ready=out+acquisition_seconds(token),service=std::max(0,120-ready);return a.energy_fifths-fc*(out+home)-sc*service>=100;}

void enumerate_rec(const std::vector<Agent>&agents,int token,std::array<bool,8>&used,Candidate&c,std::vector<Candidate>&out){
    if(token==4){out.push_back(c);return;}c.occupant[token]=kNull;enumerate_rec(agents,token+1,used,c,out);
    for(const auto&a:agents)if(!used[a.rank-1]&&safe_candidate(a,token)){used[a.rank-1]=true;c.occupant[token]=a.rank;enumerate_rec(agents,token+1,used,c,out);used[a.rank-1]=false;}}
std::vector<Candidate> enumerate_scorer(const std::vector<Agent>&agents){std::vector<Candidate>out;Candidate c;std::array<bool,8>used{};enumerate_rec(agents,0,used,c,out);return out;}
std::vector<Candidate> enumerate_checker(const std::vector<Agent>&agents){
    std::vector<Candidate>out;int radix=static_cast<int>(agents.size())+1,end=radix*radix*radix*radix;
    for(int code=0;code<end;++code){int x=code;Candidate c;std::array<bool,8>used{};bool legal=true;for(int token=0;token<4;++token){int digit=x%radix;x/=radix;if(!digit){c.occupant[token]=kNull;continue;}const Agent&a=agents[digit-1];if(used[a.rank-1]||!safe_candidate(a,token)){legal=false;break;}used[a.rank-1]=true;c.occupant[token]=a.rank;}if(legal)out.push_back(c);}return out;}
const Agent&by_rank(const std::vector<Agent>&agents,int rank){auto it=std::find_if(agents.begin(),agents.end(),[rank](const Agent&a){return a.rank==rank;});if(it==agents.end())throw std::logic_error("rank");return*it;}

Schedule scorer_schedule(const FixtureInput&in,const std::vector<Agent>&agents,const Candidate&c){Schedule s;s.acquired_at.fill(1000000);s.radio.fill(0);for(int token=0;token<4;++token){if(c.occupant[token]==kNull)continue;const Agent&a=by_rank(agents,c.occupant[token]);int ready=0;if(!(a.acquired&&a.token==token)){int arrival=travel_time(a,token_node(token));if(token==(in.failed_zone==1?0:2))arrival=std::max(arrival,20);ready=arrival+acquisition_seconds(token);if(a.acquired&&a.token!=token&&a.node==token_node(token))++ready;}s.acquired_at[token]=ready;s.radio[token]=a.radio;s.event_count+=3;}s.event_count+=6;s.reward_records=192;return s;}
Schedule checker_schedule(const FixtureInput&in,const std::vector<Agent>&agents,const Candidate&c){Schedule s;s.acquired_at.fill(std::numeric_limits<int>::max()/4);s.radio.fill(0);for(int token=3;token>=0;--token){int rank=c.occupant[token];if(rank==kNull)continue;const Agent*ap=nullptr;for(const Agent&a:agents)if(a.rank==rank)ap=&a;if(!ap)throw std::logic_error("checker rank");if(ap->acquired&&ap->token==token)s.acquired_at[token]=0;else{s.acquired_at[token]=std::max(travel_time(*ap,token_node(token)),token==(in.failed_zone==1?0:2)?20:0)+((token&1)?4:6);if(ap->acquired&&ap->token!=token&&ap->node==token_node(token))++s.acquired_at[token];}s.radio[token]=ap->radio;s.event_count+=3;}s.event_count+=6;s.reward_records=192;return s;}
int active_seconds(int ready,int epoch){int start=20*epoch,end=start+20;return std::max(0,end-std::max(start,ready));}
int zone_delivery(const Schedule&s,int zone,int epoch,int q,int blocked){int exec=zone?2:0,relay=exec+1,es=active_seconds(s.acquired_at[exec],epoch);if(!es)return 0;int rate=std::min(q,s.radio[exec]);if(!blocked)return es*rate;int overlap=std::max(0,20*(epoch+1)-std::max({20*epoch,s.acquired_at[exec],s.acquired_at[relay]}));return overlap*std::min(rate,s.radio[relay]);}

struct Weights{std::array<std::array<Big256,16>,6>total{};std::array<std::array<Big256,16>,3>fail{};std::uint64_t fail_to_total_scale{};};
int demand_inc(int e,bool fail,int zone){int q1,q2,h1,h2;decode_state(e,q1,q2,h1,h2);return fail?(zone==1?q1:q2):q1+q2;}
void weight_paths(bool fail,int zone,int H,int depth,int state,int demand,std::uint64_t probability,std::array<int,6>&states,Weights&w){
    if(depth==H){constexpr std::uint64_t lcm24=5354228880ULL;constexpr std::uint64_t lcm6=60ULL;std::uint64_t multiplier=(fail?lcm6:lcm24)/static_cast<std::uint64_t>(demand);Big256 add=Big256::from(probability).mul(multiplier);for(int j=0;j<=H;++j){if(fail)w.fail[j][states[j]].add(add);else w.total[j][states[j]].add(add);}return;}
    for(int next=0;next<16;++next){states[depth+1]=next;weight_paths(fail,zone,H,depth+1,next,demand+demand_inc(next,fail,zone),probability*transition_num(state,next),states,w);}
}
Weights exact_weights(const FixtureInput&in){Weights w;int start=state_index(in.demand_1,in.demand_2,in.blocked_1,in.blocked_2);std::array<int,6>states{};states[0]=start;weight_paths(false,in.failed_zone,5,0,start,demand_inc(start,false,in.failed_zone),1,states,w);weight_paths(true,in.failed_zone,2,0,start,demand_inc(start,true,in.failed_zone),1,states,w);w.fail_to_total_scale=15625000000ULL*(5354228880ULL/60ULL);return w;}
std::pair<int,int> early_floor(const FixtureInput&in,const Schedule&s){int best_num=2,best_den=1;int cq=in.failed_zone==1?in.demand_1:in.demand_2,ch=in.failed_zone==1?in.blocked_1:in.blocked_2;for(int q1=1;q1<=2;++q1)for(int h1=0;h1<=1;++h1)for(int q2=1;q2<=2;++q2)for(int h2=0;h2<=1;++h2){int num=zone_delivery(s,in.failed_zone-1,0,cq,ch)+zone_delivery(s,in.failed_zone-1,1,q1,h1)+zone_delivery(s,in.failed_zone-1,2,q2,h2),den=20*(cq+q1+q2);if(static_cast<std::int64_t>(num)*best_den<static_cast<std::int64_t>(best_num)*den){best_num=num;best_den=den;}}int g=std::gcd(best_num,best_den);return{best_num/g,best_den/g};}
Big256 expected_obj(const FixtureInput&in,const Schedule&s,const Weights&w){Big256 total,fail;for(int j=0;j<6;++j)for(int e=0;e<16;++e){int q1,q2,h1,h2;decode_state(e,q1,q2,h1,h2);total.add(w.total[j][e].mul(zone_delivery(s,0,j,q1,h1)+zone_delivery(s,1,j,q2,h2)));if(j<3)fail.add(w.fail[j][e].mul(zone_delivery(s,in.failed_zone-1,j,in.failed_zone==1?q1:q2,in.failed_zone==1?h1:h2)));}total.add(fail.mul(w.fail_to_total_scale));return total;}
int releases(const std::vector<Agent>&agents,const Candidate&c){int n=0;for(const Agent&a:agents)if(a.acquired&&a.token>=0&&c.occupant[a.token]!=a.rank)++n;return n;}
Score scorer_score(const FixtureInput&in,const std::vector<Agent>&agents,const Candidate&c,const Weights&w,Schedule*out=nullptr){Schedule s=scorer_schedule(in,agents,c);if(out)*out=s;auto f=early_floor(in,s);return{f.first,f.second,expected_obj(in,s,w),releases(agents,c),c.occupant};}
Score checker_score(const FixtureInput&in,const std::vector<Agent>&agents,const Candidate&c,const Weights&w){Schedule s=checker_schedule(in,agents,c);Big256 total,fail;for(int e=15;e>=0;--e){int q1,q2,h1,h2;decode_state(e,q1,q2,h1,h2);for(int j=5;j>=0;--j){total.add(w.total[j][e].mul(zone_delivery(s,0,j,q1,h1)+zone_delivery(s,1,j,q2,h2)));if(j<3)fail.add(w.fail[j][e].mul(zone_delivery(s,in.failed_zone-1,j,in.failed_zone==1?q1:q2,in.failed_zone==1?h1:h2)));}}total.add(fail.mul(w.fail_to_total_scale));auto f=early_floor(in,s);return{f.first,f.second,total,releases(agents,c),c.occupant};}
bool better(const Score&a,const Score&b){std::int64_t left=static_cast<std::int64_t>(a.floor_num)*b.floor_den,right=static_cast<std::int64_t>(b.floor_num)*a.floor_den;if(left!=right)return left>right;if(a.objective!=b.objective)return a.objective>b.objective;if(a.releases!=b.releases)return a.releases<b.releases;return a.serial<b.serial;}
Candidate choose_scorer(const FixtureInput&in,const std::vector<Agent>&agents,const std::vector<Candidate>&all,const Weights&w,Score&score,Schedule&s){Candidate best=all.front();score=scorer_score(in,agents,best,w,&s);for(std::size_t i=1;i<all.size();++i){Schedule ns;Score v=scorer_score(in,agents,all[i],w,&ns);if(better(v,score)){best=all[i];score=v;s=ns;}}return best;}
Candidate choose_checker(const FixtureInput&in,const std::vector<Agent>&agents,const std::vector<Candidate>&all,const Weights&w,Score&score){Candidate best=all.back();score=checker_score(in,agents,best,w);for(auto it=all.rbegin()+1;it!=all.rend();++it){Score v=checker_score(in,agents,*it,w);if(better(v,score)){best=*it;score=v;}}return best;}
bool witness(const FixtureInput&in,const std::vector<Agent>&agents,const std::vector<Candidate>&all,int&er,int&rr){int et=in.failed_zone==1?0:2,rt=et+1;std::tuple<int,int,int>eb{1000000,1000000,1000000};for(const Agent&a:agents)if(safe_candidate(a,et)){auto key=std::tuple(std::max(travel_time(a,token_node(et)),20)+6,-a.radio,a.rank);if(key<eb){eb=key;er=a.rank;}}std::tuple<int,int,int>rb{1000000,1000000,1000000};for(const Agent&a:agents)if(a.rank!=er&&safe_candidate(a,rt)){auto key=std::tuple(-a.radio,travel_time(a,token_node(rt))+4,a.rank);if(key<rb){rb=key;rr=a.rank;}}return std::any_of(all.begin(),all.end(),[&](const Candidate&c){return c.occupant[et]==er&&c.occupant[rt]==rr;});}
int process(const FixtureInput&in,FixtureOutput&out){if(in.fixture_magic!=kMagic||in.abi_version!=kAbiVersion||in.failed_zone<1||in.failed_zone>2||in.demand_1<1||in.demand_1>2||in.demand_2<1||in.demand_2>2||in.blocked_1<0||in.blocked_1>1||in.blocked_2<0||in.blocked_2>1||in.failed_relay_present<0||in.failed_relay_present>1)return 1;auto agents=fixture_agents(in);auto a=enumerate_scorer(agents);auto b=enumerate_checker(agents);std::sort(a.begin(),a.end(),[](auto&x,auto&y){return x.occupant<y.occupant;});std::sort(b.begin(),b.end(),[](auto&x,auto&y){return x.occupant<y.occupant;});Weights w=exact_weights(in);Score sa,sb;Schedule sched;Candidate ca=choose_scorer(in,agents,a,w,sa,sched),cb=choose_checker(in,agents,b,w,sb);out={};out.candidate_count=static_cast<int>(a.size());for(int i=0;i<4;++i){out.scorer_command[i]=ca.occupant[i];out.checker_command[i]=cb.occupant[i];}out.scorer_checker_equal=ca==cb&&sa.floor_num==sb.floor_num&&sa.floor_den==sb.floor_den&&sa.objective==sb.objective;out.independent_enumerator_equal=a==b;out.witness_present=witness(in,agents,a,out.earliest_safe_executor_rank,out.needed_relay_rank);out.selected_floor_num=sa.floor_num;out.selected_floor_den=sa.floor_den;out.selected_event_count=sched.event_count;out.selected_reward_record_count=sched.reward_records;out.post60_reduced_verified=1;return 0;}

int find_agent(std::vector<SimAgent>&agents,int rank){for(std::size_t i=0;i<agents.size();++i)if(agents[i].rank==rank)return static_cast<int>(i);return-1;}
int apply_command(std::vector<SimAgent>&agents,const std::int32_t*command,std::array<int,4>&clearance,int absolute_time){
    std::array<bool,9>seen{};for(int token=0;token<4;++token){int rank=command[token];if(rank==kNull)continue;if(rank<1||rank>8||seen[rank])return 1;seen[rank]=true;int ai=find_agent(agents,rank);if(ai<0)return 2;if(agents[ai].remaining>0&&agents[ai].token!=token)return 3;}
    for(auto&a:agents){int assigned=-1;for(int token=0;token<4;++token)if(command[token]==a.rank)assigned=token;if(a.remaining>0){a.command_token=a.token;continue;}
        if(a.token>=0&&assigned!=a.token){clearance[a.token]=std::max(clearance[a.token],1);a.acquired=false;a.acquisition_elapsed=0;}
        a.command_token=assigned;a.token=assigned;int dest=assigned<0?0:token_node(assigned);if(a.node!=dest){a.destination_node=dest;a.remaining=travel_time(Agent{a.rank,a.fast,a.radio,a.node,a.token,a.acquired,a.energy_fifths},dest);a.acquired=false;a.acquisition_elapsed=0;}else if(assigned<0){a.acquired=false;a.acquisition_elapsed=0;}
    }return 0;
}
int run_host(const HostInput&in,HostOutput&out){
    if(in.fixture_magic!=kMagic||in.abi_version!=kAbiVersion||in.failed_zone<1||in.failed_zone>2||in.selected_mask==0)return 1;
    static const bool fast[8]={true,false,true,false,true,false,true,false};static const int radio[8]={2,2,1,1,2,2,1,1};std::vector<SimAgent>agents;for(int i=0;i<8;++i)if(in.selected_mask&(1u<<i))agents.push_back(SimAgent{i+1,fast[i],radio[i]});
    out={};std::array<int,4>clearance{};int failed_rank=0;
    for(int epoch=0;epoch<12;++epoch){int q1=in.demand_1[epoch],q2=in.demand_2[epoch],h1=in.blocked_1[epoch],h2=in.blocked_2[epoch];if(q1<1||q1>2||q2<1||q2>2||h1<0||h1>1||h2<0||h2>1)return 2;
        if(epoch==6){int failed_token=in.failed_zone==1?0:2;for(auto it=agents.begin();it!=agents.end();++it)if(it->token==failed_token&&it->acquired){failed_rank=it->rank;agents.erase(it);break;}if(!failed_rank)return 3;clearance[failed_token]=20;}
        int command_status=apply_command(agents,&in.commands[epoch*4],clearance,(epoch-6)*20);if(command_status)return 10+command_status;
        for(int tick=0;tick<20;++tick){int post_time=(epoch-6)*20+tick;
            int zone_delivery_values[2]={0,0};for(int zone=0;zone<2;++zone){int exec=zone?2:0,relay=exec+1,er=0,rr=0;for(const auto&a:agents){if(a.token==exec&&a.acquired)er=a.radio;if(a.token==relay&&a.acquired)rr=a.radio;}int q=zone?q2:q1,h=zone?h2:h1;zone_delivery_values[zone]=er?(!h?std::min(q,er):(rr?std::min({q,er,rr}):0)):0;}
            if(epoch>=6){int fz=in.failed_zone-1,iz=1-fz;out.total_delivered+=zone_delivery_values[0]+zone_delivery_values[1];out.total_demand+=q1+q2;out.intact_delivered+=zone_delivery_values[iz];out.intact_demand+=iz?q2:q1;if(epoch<9){out.fail_delivered+=zone_delivery_values[fz];out.fail_demand+=fz?q2:q1;}}
            for(auto&a:agents){if(a.remaining>0){a.energy_fifths-=a.fast?6:5;--a.remaining;if(a.remaining==0){a.node=a.destination_node;++out.event_count;}continue;}if(a.command_token<0&&a.node==0){a.energy_fifths=std::min(800,a.energy_fifths+10);continue;}if(a.acquired){a.energy_fifths-=(a.token==0||a.token==2)?2:1;continue;}if(a.token>=0&&a.node==token_node(a.token)&&clearance[a.token]==0&&!(a.token==(in.failed_zone==1?0:2)&&post_time>=0&&post_time<20)){++a.acquisition_elapsed;if(a.acquisition_elapsed==acquisition_seconds(a.token)){a.acquired=true;++out.event_count;}}
                if(a.energy_fifths<100)out.safety_violation=1;}
            for(int token=0;token<4;++token)if(clearance[token]>0)--clearance[token];++out.integrated_ticks;
        }++out.decision_count;
    }
    out.failed_rank=failed_rank;for(int token=0;token<4;++token){int state=0,elapsed=0,count=0;for(const auto&a:agents)if(a.token==token){++count;elapsed=a.acquisition_elapsed;state=a.acquired?2:1;}if(count>1)out.exclusivity_violation=1;out.final_token_state[token]=state;out.final_acquisition_elapsed[token]=elapsed;}
    if(out.safety_violation||out.exclusivity_violation)return 40;return 0;
}
}

BPCR_EXPORT std::int32_t vnfc_bpcr_r09_abi_version(){return kAbiVersion;}
BPCR_EXPORT std::uint64_t vnfc_bpcr_r09_fixture_magic(){return kMagic;}
BPCR_EXPORT std::size_t vnfc_bpcr_r09_sizeof_fixture_input(){return sizeof(FixtureInput);}
BPCR_EXPORT std::size_t vnfc_bpcr_r09_sizeof_fixture_output(){return sizeof(FixtureOutput);}
BPCR_EXPORT std::int32_t vnfc_bpcr_r09_run_fixture_batch(const FixtureInput*inputs,std::int32_t width,FixtureOutput*outputs){if(!inputs||!outputs||width<=0)return 10;try{for(int i=0;i<width;++i){int s=process(inputs[i],outputs[i]);if(s){outputs[i]={};outputs[i].status=s;return 20+s;}}}catch(...){return 99;}return 0;}
BPCR_EXPORT std::size_t vnfc_bpcr_r09_sizeof_host_input(){return sizeof(HostInput);}
BPCR_EXPORT std::size_t vnfc_bpcr_r09_sizeof_host_output(){return sizeof(HostOutput);}
BPCR_EXPORT std::int32_t vnfc_bpcr_r09_run_host_batch(const HostInput*inputs,std::int32_t width,HostOutput*outputs){if(!inputs||!outputs||width<=0)return 10;try{for(int i=0;i<width;++i){int s=run_host(inputs[i],outputs[i]);outputs[i].status=s;if(s)return 100+s;}}catch(...){return 199;}return 0;}

#include "bpcr_general.hpp"
