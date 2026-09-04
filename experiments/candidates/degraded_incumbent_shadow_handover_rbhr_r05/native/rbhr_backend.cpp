#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

#if defined(_WIN32)
#define DISH_EXPORT extern "C" __declspec(dllexport)
#else
#define DISH_EXPORT extern "C"
#endif

namespace {

constexpr int ABI_VERSION = 1;
constexpr int TICKS = 1200;
constexpr double DT = 0.1;
constexpr double PI = 3.141592653589793238462643383279502884;

struct FixtureInput {
    std::uint64_t fixture_key;
    std::int32_t arm;
    std::int32_t package;
    std::int32_t reflection;
    std::int32_t initial_owner;
    std::int32_t k_initial;
    std::int32_t k_new;
    std::int32_t switch_tick;
    std::int32_t tau_d_tick;
    std::int32_t phase;
    std::int32_t route_speed;
    std::int32_t turn_magnitude_deg;
    std::int32_t turn_sign;
    std::int32_t initial_ux;
    std::int32_t initial_uy;
};

struct HostOutput {
    std::int32_t service_ticks;
    std::int32_t owner;
    std::int32_t service_epoch;
    std::int32_t next_payload_sequence;
    std::int32_t handover_used;
    std::int32_t noop_count;
    std::int32_t transaction_shell_bytes;
    std::int32_t invalid_commit;
    std::int32_t token_gap;
    std::int32_t dual_owner;
    std::int32_t dual_payload;
    std::int32_t buffer_clear;
    std::int32_t separation_breach;
    std::int32_t protocol_bytes;
    std::int32_t terminal_tick;
    double final_separation;
    double total_energy;
    std::uint64_t state_digest;
};

struct GeneratorInput {
    std::uint64_t fixture_key;
    std::uint32_t start;
    std::uint32_t count;
    std::int32_t stratum;
};

struct GeneratorOutput {
    std::int64_t winning_ordinal;
    std::uint64_t winning_word;
};

struct ProtocolInput {
    std::int32_t integrity;
    std::int32_t request_transfer;
    std::int32_t origin_pass;
    std::int32_t handover_unused;
    std::int32_t application_tick;
    std::int32_t origin_tick;
    std::int32_t readiness_tick;
    std::int32_t bound_readiness_tick;
    std::int32_t snapshot_tick;
    std::int32_t current_owner;
    std::int32_t old_owner;
    std::int32_t new_owner;
    std::int32_t current_epoch;
    std::int32_t intent_epoch;
    std::int32_t current_next_sequence;
    std::int32_t intent_next_sequence;
    std::int32_t source0_sequence;
    std::int32_t source1_sequence;
    std::int32_t intent_source_sequence;
    std::int32_t current_k_epoch;
    std::int32_t intent_k_epoch;
    std::int32_t terminal;
    std::int32_t batteries_positive;
    std::int32_t buffers_present;
    std::int32_t separation_current;
    std::int32_t separation_next;
    std::int32_t slew_ok;
    std::int32_t sham;
    std::int32_t never_arm;
};

struct ProtocolOutput {
    std::int32_t success;
    std::int32_t reason_code;
    std::int32_t invalid_commit;
    std::int32_t noop_count;
    std::int32_t owner;
    std::int32_t service_epoch;
    std::int32_t next_sequence;
    std::int32_t handover_used;
    std::int32_t source_buffers_preserved;
    std::int32_t base_buffer_preserved;
    std::int32_t transaction_shell_bytes;
    std::int32_t forbidden_leak_count;
};

struct FilterInput { double mean[4]; double covariance[16]; std::int32_t camera_present; double z[2]; };
struct FilterOutput { double mean[4]; double covariance[16]; std::int32_t finite; };

struct CertificateInput {
    std::int32_t renew,unused,match,age,warm,maintain,separation,slew,g_latch;
    double mahalanobis_squared,q95;
};

struct Sha256 {
    std::array<std::uint32_t, 8> h{
        0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
        0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U};
    std::array<std::uint8_t, 64> buffer{};
    std::uint64_t total = 0;
    std::size_t used = 0;

    static constexpr std::array<std::uint32_t, 64> K{
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U};

    static std::uint32_t rotr(std::uint32_t x, unsigned n) { return (x >> n) | (x << (32U - n)); }

    void transform(const std::uint8_t* block) {
        std::array<std::uint32_t, 64> w{};
        for (int i = 0; i < 16; ++i) {
            w[i] = (static_cast<std::uint32_t>(block[4*i]) << 24U) |
                   (static_cast<std::uint32_t>(block[4*i+1]) << 16U) |
                   (static_cast<std::uint32_t>(block[4*i+2]) << 8U) |
                   static_cast<std::uint32_t>(block[4*i+3]);
        }
        for (int i = 16; i < 64; ++i) {
            const auto s0 = rotr(w[i-15],7) ^ rotr(w[i-15],18) ^ (w[i-15] >> 3U);
            const auto s1 = rotr(w[i-2],17) ^ rotr(w[i-2],19) ^ (w[i-2] >> 10U);
            w[i] = w[i-16] + s0 + w[i-7] + s1;
        }
        auto a=h[0], b=h[1], c=h[2], d=h[3], e=h[4], f=h[5], g=h[6], hh=h[7];
        for (int i=0;i<64;++i) {
            const auto S1=rotr(e,6)^rotr(e,11)^rotr(e,25);
            const auto ch=(e&f)^((~e)&g);
            const auto t1=hh+S1+ch+K[i]+w[i];
            const auto S0=rotr(a,2)^rotr(a,13)^rotr(a,22);
            const auto maj=(a&b)^(a&c)^(b&c);
            const auto t2=S0+maj;
            hh=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
        }
        h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d; h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=hh;
    }

    void update(const std::uint8_t* data, std::size_t size) {
        total += size;
        while (size > 0) {
            const auto take = std::min(size, buffer.size()-used);
            std::memcpy(buffer.data()+used, data, take);
            used += take; data += take; size -= take;
            if (used == buffer.size()) { transform(buffer.data()); used = 0; }
        }
    }

    std::array<std::uint8_t,32> final() {
        const auto bits = total * 8U;
        buffer[used++] = 0x80U;
        if (used > 56) { while (used < 64) buffer[used++] = 0; transform(buffer.data()); used=0; }
        while (used < 56) buffer[used++] = 0;
        for (int i=7;i>=0;--i) buffer[used++] = static_cast<std::uint8_t>((bits >> (8U*i)) & 0xffU);
        transform(buffer.data());
        std::array<std::uint8_t,32> out{};
        for (int i=0;i<8;++i) for(int j=0;j<4;++j) out[4*i+j]=static_cast<std::uint8_t>((h[i]>>(24U-8U*j))&0xffU);
        return out;
    }
};

std::uint64_t rng_word(std::uint64_t key, const std::string& address) {
    std::array<std::uint8_t,8> key_bytes{};
    for (int i=0;i<8;++i) key_bytes[i]=static_cast<std::uint8_t>((key>>(56U-8U*i))&0xffU);
    const std::uint8_t zero=0;
    Sha256 sha;
    sha.update(key_bytes.data(),key_bytes.size());
    sha.update(&zero,1);
    sha.update(reinterpret_cast<const std::uint8_t*>(address.data()),address.size());
    const auto digest=sha.final();
    std::uint64_t value=0;
    for(int i=0;i<8;++i) value=(value<<8U)|digest[i];
    return value;
}

double rng_uniform(std::uint64_t key, const std::string& address) {
    return (static_cast<double>(rng_word(key,address)>>11U)+0.5)/9007199254740992.0;
}

double rng_normal(std::uint64_t key, const std::string& address) {
    const auto u1=rng_uniform(key,address+"/0");
    const auto u2=rng_uniform(key,address+"/1");
    return std::sqrt(-2.0*std::log(u1))*std::cos(2.0*PI*u2);
}

struct Vec2 { double x=0.0,y=0.0; };
double norm(Vec2 a){ return std::hypot(a.x,a.y); }
Vec2 clip_norm(Vec2 a,double limit){ const auto n=norm(a); if(n==0.0||n<=limit)return a; const auto s=limit/std::max(n,1e-12); return {a.x*s,a.y*s}; }
double distance(Vec2 a,Vec2 b){ return std::hypot(a.x-b.x,a.y-b.y); }

double terrain(double x,double y){ return 135.0*std::exp(-std::pow(x/75.0,2)-std::pow(y/220.0,4))+55.0*std::exp(-std::pow((x-90.0)/35.0,2)-std::pow((y+40.0)/85.0,2)); }

bool blocked(const std::array<double,3>& a,const std::array<double,3>& b,double clearance){
    for(int j=1;j<128;++j){ const auto f=static_cast<double>(j)/128.0; const auto x=a[0]+f*(b[0]-a[0]); const auto y=a[1]+f*(b[1]-a[1]); const auto z=a[2]+f*(b[2]-a[2]); if(z<=terrain(x,y)+clearance)return true; }
    return false;
}

struct Route { double x,y,vx,vy; };
Route route(const FixtureInput& f,int tick){
    const auto t=tick*DT; const auto tau=f.tau_d_tick*DT; const auto speed=static_cast<double>(f.route_speed); const auto theta=f.turn_sign*f.turn_magnitude_deg*PI/180.0;
    if(t<=tau)return {-speed*tau+speed*t, f.reflection*(-120.0), speed, 0.0};
    return {speed*(t-tau)*std::cos(theta), f.reflection*(-120.0+speed*(t-tau)*std::sin(theta)), speed*std::cos(theta), f.reflection*speed*std::sin(theta)};
}

double radio_margin(const FixtureInput& f,int tick,const std::string& hop,const std::array<double,3>& a,const std::array<double,3>& b,double extra=0.0){
    const auto dx=a[0]-b[0],dy=a[1]-b[1],dz=a[2]-b[2]; const auto d=std::sqrt(dx*dx+dy*dy+dz*dz); const auto obstruction=blocked(a,b,8.0)?1.0:0.0;
    return 30.0-20.0*std::log10(std::max(d,1.0)/100.0)-35.0*obstruction-extra+rng_normal(f.fixture_key,"RADIO/"+std::to_string(tick)+"/"+hop);
}

struct Source { int sequence=-1,tick=-1; double x=0,y=0,vx=0,vy=0,first_margin=-std::numeric_limits<double>::infinity(); };
struct Relay { bool exists=false; Source source{}; int relay_tick=-1,epoch=0,payload_sequence=0,sender=0; double second_margin=-std::numeric_limits<double>::infinity(); };

std::uint64_t mix(std::uint64_t value,std::uint64_t item){ value^=item; return value*1099511628211ULL; }

bool valid_fixture(const FixtureInput& f){
    const bool arm=f.arm>=0&&f.arm<=4,package=f.package==0||f.package==1,refl=f.reflection==-1||f.reflection==1,owner=f.initial_owner==0||f.initial_owner==1;
    const auto kv=[](int k){return k==4||k==8||k==12;};
    return arm&&package&&refl&&owner&&kv(f.k_initial)&&kv(f.k_new)&&f.switch_tick>=0&&f.switch_tick<TICKS&&f.tau_d_tick>=0&&f.tau_d_tick<TICKS&&f.phase>=0&&f.phase<f.k_initial;
}

int run_one(const FixtureInput& f,HostOutput& out){
    if(!valid_fixture(f))return 2;
    const auto r0=route(f,0); Vec2 qa{r0.x+f.initial_ux,r0.y+f.reflection*f.initial_uy},qb{r0.x-f.initial_ux,r0.y-f.reflection*f.initial_uy};
    std::array<Vec2,2> p{qa,qb},v{},a{}; Vec2 wind{}; std::array<double,2>battery{200000.0,200000.0};
    int owner=f.initial_owner,epoch=0,next_seq=0,handover=0,noop=0,transaction_shell_bytes=0,invalid=0,gap=0,dual=0,dual_payload=0,buffer_clear=0,separation_breach=0,bytes=0,service=0,terminal_tick=-1;
    double energy=0.0; std::array<Source,2> q{}; std::array<Source,2> pending{}; std::array<bool,2> pending_valid{false,false}; Relay relay{},base{}; bool relay_valid=false;
    int countdown=f.phase,k_active=f.k_initial; bool switch_seen=false,pending_switch=false; std::uint64_t digest=1469598103934665603ULL;
    for(int tick=0;tick<TICKS;++tick){
        const auto sep=distance(p[0],p[1]); const bool terminal=sep<15.0||std::min(battery[0],battery[1])<=0.0||terminal_tick>=0;
        if(terminal&&terminal_tick<0){terminal_tick=tick;separation_breach+=sep<15.0?1:0;}
        if(terminal){energy+=2.0*650.0*DT;battery[0]=std::max(0.0,battery[0]-650.0*DT);battery[1]=std::max(0.0,battery[1]-650.0*DT);continue;}
        for(int i=0;i<2;++i){if(pending_valid[i]&&pending[i].sequence>q[i].sequence)q[i]=pending[i];pending_valid[i]=false;}
        if(relay_valid&&relay.exists){
            const std::array<long long,5> cand{relay.source.sequence,relay.relay_tick,relay.epoch,relay.payload_sequence,-relay.sender};
            const std::array<long long,5> cur{base.exists?base.source.sequence:-1,base.relay_tick,base.epoch,base.payload_sequence,-base.sender};
            if(cand>cur)base=relay;
        }
        relay_valid=false;
        if(!switch_seen&&f.k_new!=f.k_initial&&tick>=f.switch_tick){pending_switch=true;switch_seen=true;}
        const bool renew=countdown==0;
        if(renew){if(pending_switch){k_active=f.k_new;pending_switch=false;}countdown=k_active-1;}else --countdown;
        if(renew&&!handover&&tick>=f.tau_d_tick&&tick+1<TICKS){
            if(f.arm==0||f.arm==1||f.arm==3){owner=1-owner;++epoch;handover=1;transaction_shell_bytes=24;}
            else if(f.arm==4){++epoch;handover=1;transaction_shell_bytes=24;}
            else if(f.arm==2){++noop;}
        }
        const auto g=route(f,tick); const std::array<double,3> target{g.x,g.y,0.0};
        for(int i=0;i<2;++i){const Vec2 desired{i==owner?g.x-40.0:g.x-300.0,i==owner?g.y:g.y+60.0*f.reflection}; const Vec2 raw{0.08*(desired.x-p[i].x)-0.60*v[i].x,0.08*(desired.y-p[i].y)-0.60*v[i].y}; const auto bounded=clip_norm(raw,3.0); const auto delta=clip_norm({bounded.x-a[i].x,bounded.y-a[i].y},1.5); a[i]=clip_norm({a[i].x+delta.x,a[i].y+delta.y},3.0);}
        std::array<std::array<double,3>,2> uav{{{p[0].x,p[0].y,90.0},{p[1].x,p[1].y,90.0}}};
        Source body{};body.sequence=tick;body.tick=tick;body.x=g.x+2.0*rng_normal(f.fixture_key,"SOURCE/"+std::to_string(tick)+"/PX");body.y=g.y+2.0*rng_normal(f.fixture_key,"SOURCE/"+std::to_string(tick)+"/PY");body.vx=g.vx+0.25*rng_normal(f.fixture_key,"SOURCE/"+std::to_string(tick)+"/VX");body.vy=g.vy+0.25*rng_normal(f.fixture_key,"SOURCE/"+std::to_string(tick)+"/VY");
        for(int i=0;i<2;++i){const auto margin=radio_margin(f,tick,"G_TO_U"+std::to_string(i),target,uav[i]);if(margin>=6.0){pending[i]=body;pending[i].first_margin=margin;pending_valid[i]=true;}}
        bytes+=40+128;
        if(q[owner].sequence>=0){const std::array<double,3> base_point{-600.0,0.0,20.0};double extra=0.0;if(f.package==1&&tick>=f.tau_d_tick&&tick<f.tau_d_tick+40&&owner==f.initial_owner)extra=35.0;const auto margin=radio_margin(f,tick,"U"+std::to_string(owner)+"_TO_BASE",uav[owner],base_point,extra);relay={margin>=6.0,q[owner],tick,epoch,next_seq,owner,margin};relay_valid=true;++next_seq;bytes+=64;}
        if(base.exists){const auto age=(tick-base.source.tick)*DT;const Vec2 est{base.source.x+age*base.source.vx,base.source.y+age*base.source.vy};if(age<=0.5&&distance(est,{g.x,g.y})<=8.0&&base.source.first_margin>=6.0&&base.second_margin>=6.0)++service;}
        for(int i=0;i<2;++i){const auto power=650.0+1.5*(v[i].x*v[i].x+v[i].y*v[i].y)+12.0*(a[i].x*a[i].x+a[i].y*a[i].y);const auto byte_energy=0.02*(64+(i==owner&&q[i].sequence>=0?64:0));energy+=DT*power+byte_energy;battery[i]=std::max(0.0,battery[i]-DT*power-byte_energy);p[i].x+=DT*v[i].x;p[i].y+=DT*v[i].y;v[i]=clip_norm({v[i].x+DT*(a[i].x+wind.x),v[i].y+DT*(a[i].y+wind.y)},18.0);}
        wind.x=std::max(-1.5,std::min(1.5,0.95*wind.x+0.05*rng_normal(f.fixture_key,"WIND/"+std::to_string(tick)+"/X")));wind.y=std::max(-1.5,std::min(1.5,0.95*wind.y+0.05*rng_normal(f.fixture_key,"WIND/"+std::to_string(tick)+"/Y")));
        digest=mix(digest,tick);digest=mix(digest,owner);digest=mix(digest,epoch);digest=mix(digest,next_seq);digest=mix(digest,base.exists?1:0);digest=mix(digest,renew?1:0);
    }
    out={service,owner,epoch,next_seq,handover,noop,transaction_shell_bytes,invalid,gap,dual,dual_payload,buffer_clear,separation_breach,bytes,terminal_tick,distance(p[0],p[1]),energy,digest};
    return 0;
}

bool qualifies(double value,int stratum){return (stratum==0&&value<=0.01)||(stratum==1&&value>=0.49&&value<=0.51)||(stratum==2&&value>=0.99);}

} // namespace

DISH_EXPORT int dish_rbhr_abi_version(){return ABI_VERSION;}
DISH_EXPORT std::uint64_t dish_rbhr_input_size(){return sizeof(FixtureInput);}
DISH_EXPORT std::uint64_t dish_rbhr_output_size(){return sizeof(HostOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_generator_input_size(){return sizeof(GeneratorInput);}
DISH_EXPORT std::uint64_t dish_rbhr_generator_output_size(){return sizeof(GeneratorOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_protocol_input_size(){return sizeof(ProtocolInput);}
DISH_EXPORT std::uint64_t dish_rbhr_protocol_output_size(){return sizeof(ProtocolOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_filter_input_size(){return sizeof(FilterInput);}
DISH_EXPORT std::uint64_t dish_rbhr_filter_output_size(){return sizeof(FilterOutput);}

DISH_EXPORT int dish_rbhr_run_batch(const FixtureInput* input,std::uint64_t count,HostOutput* output){
    if((count>0&&(!input||!output))||count>1000000ULL)return 1;
    for(std::uint64_t i=0;i<count;++i){const auto code=run_one(input[i],output[i]);if(code!=0)return code;}
    return 0;
}

DISH_EXPORT int dish_rbhr_generator_scan_batch(const GeneratorInput* input,std::uint64_t count,GeneratorOutput* output){
    if((count>0&&(!input||!output))||count>1000000ULL)return 1;
    for(std::uint64_t i=0;i<count;++i){if(input[i].stratum<0||input[i].stratum>2)return 2;output[i].winning_ordinal=-1;output[i].winning_word=0;const auto end=static_cast<std::uint64_t>(input[i].start)+input[i].count;for(std::uint64_t ordinal=input[i].start;ordinal<end;++ordinal){const auto address="GENERATOR/"+std::to_string(ordinal)+"/ASSAY";const auto word=rng_word(input[i].fixture_key,address);const auto value=(static_cast<double>(word>>11U)+0.5)/9007199254740992.0;if(qualifies(value,input[i].stratum)){output[i].winning_ordinal=static_cast<std::int64_t>(ordinal);output[i].winning_word=word;break;}}}
    return 0;
}

DISH_EXPORT std::uint64_t dish_rbhr_rng_word(std::uint64_t key,const char* address,std::uint64_t length){
    if(!address&&length>0)return 0;return rng_word(key,std::string(address,address+length));
}

DISH_EXPORT int dish_rbhr_protocol_apply_batch(const ProtocolInput* input,std::uint64_t count,ProtocolOutput* output){
    if((count>0&&(!input||!output))||count>1000000ULL)return 1;
    for(std::uint64_t i=0;i<count;++i){
        const auto& p=input[i];
        ProtocolOutput value{};
        value.owner=p.current_owner;value.service_epoch=p.current_epoch;value.next_sequence=p.current_next_sequence;
        value.handover_used=p.handover_unused?0:1;value.source_buffers_preserved=1;value.base_buffer_preserved=1;value.forbidden_leak_count=0;
        if(p.never_arm){value.noop_count=p.request_transfer?1:0;output[i]=value;continue;}
        int reason=0;
        if(!p.integrity||!p.request_transfer)reason=1;
        else if(!p.origin_pass)reason=2;
        else if(!p.handover_unused)reason=3;
        else if(p.application_tick!=p.origin_tick+1||p.readiness_tick!=p.bound_readiness_tick||p.bound_readiness_tick!=p.origin_tick-1||p.snapshot_tick!=p.origin_tick)reason=4;
        else if(p.current_owner!=p.old_owner)reason=5;
        else if(p.current_epoch!=p.intent_epoch)reason=6;
        else if(p.current_next_sequence!=p.intent_next_sequence)reason=7;
        else if(p.source0_sequence!=p.intent_source_sequence||p.source1_sequence!=p.intent_source_sequence)reason=8;
        else if(p.current_k_epoch!=p.intent_k_epoch)reason=9;
        else if(p.terminal)reason=10;
        else if(!p.batteries_positive||!p.buffers_present)reason=11;
        else if(!p.separation_current||!p.separation_next)reason=12;
        else if(!p.slew_ok)reason=13;
        value.reason_code=reason;
        if(reason==0){value.success=1;value.owner=p.sham?p.current_owner:p.new_owner;value.service_epoch=p.current_epoch+1;value.handover_used=1;value.transaction_shell_bytes=24;}
        else {value.invalid_commit=1;}
        output[i]=value;
    }
    return 0;
}

DISH_EXPORT int dish_rbhr_redact_observation_batch(const double* causal54,const double* forbidden8,std::uint64_t count,double* output54){
    if((count>0&&(!causal54||!forbidden8||!output54))||count>1000000ULL)return 1;
    for(std::uint64_t row=0;row<count;++row){for(int column=0;column<54;++column)output54[row*54+column]=causal54[row*54+column];}
    return 0;
}

DISH_EXPORT int dish_rbhr_filter_step_batch(const FilterInput* input,std::uint64_t count,FilterOutput* output){
    if((count>0&&(!input||!output))||count>1000000ULL)return 1;
    const double F[16]={1,0,DT,0, 0,1,0,DT, 0,0,1,0, 0,0,0,1};
    const double Q[4]={0.04,0.04,0.25,0.25};
    for(std::uint64_t row=0;row<count;++row){
        double predicted_mean[4]{};double temp[16]{};double predicted[16]{};
        for(int i=0;i<4;++i)for(int j=0;j<4;++j)predicted_mean[i]+=F[4*i+j]*input[row].mean[j];
        for(int i=0;i<4;++i)for(int j=0;j<4;++j)for(int k=0;k<4;++k)temp[4*i+j]+=F[4*i+k]*input[row].covariance[4*k+j];
        for(int i=0;i<4;++i)for(int j=0;j<4;++j)for(int k=0;k<4;++k)predicted[4*i+j]+=temp[4*i+k]*F[4*j+k];
        for(int i=0;i<4;++i)predicted[4*i+i]+=Q[i];
        std::copy(predicted_mean,predicted_mean+4,output[row].mean);std::copy(predicted,predicted+16,output[row].covariance);
        if(input[row].camera_present){
            const double s00=predicted[0]+4.0+1e-9,s01=predicted[1],s10=predicted[4],s11=predicted[5]+4.0+1e-9;const double determinant=s00*s11-s01*s10;
            if(!(determinant>0.0)||!std::isfinite(determinant)){output[row].finite=0;continue;}
            const double inv[4]={s11/determinant,-s01/determinant,-s10/determinant,s00/determinant};double gain[8]{};
            for(int i=0;i<4;++i){gain[2*i]=predicted[4*i]*inv[0]+predicted[4*i+1]*inv[2];gain[2*i+1]=predicted[4*i]*inv[1]+predicted[4*i+1]*inv[3];}
            const double innovation[2]={input[row].z[0]-predicted_mean[0],input[row].z[1]-predicted_mean[1]};for(int i=0;i<4;++i)output[row].mean[i]=predicted_mean[i]+gain[2*i]*innovation[0]+gain[2*i+1]*innovation[1];
            double A[16]={1-gain[0],-gain[1],0,0, -gain[2],1-gain[3],0,0, -gain[4],-gain[5],1,0, -gain[6],-gain[7],0,1};double AP[16]{};double joseph[16]{};
            for(int i=0;i<4;++i)for(int j=0;j<4;++j)for(int k=0;k<4;++k)AP[4*i+j]+=A[4*i+k]*predicted[4*k+j];
            for(int i=0;i<4;++i)for(int j=0;j<4;++j){for(int k=0;k<4;++k)joseph[4*i+j]+=AP[4*i+k]*A[4*j+k];joseph[4*i+j]+=4.0*(gain[2*i]*gain[2*j]+gain[2*i+1]*gain[2*j+1]);}
            std::copy(joseph,joseph+16,output[row].covariance);
        }
        output[row].finite=1;for(double value:output[row].mean)if(!std::isfinite(value))output[row].finite=0;for(double value:output[row].covariance)if(!std::isfinite(value))output[row].finite=0;
    }
    return 0;
}

DISH_EXPORT int dish_rbhr_certificate_batch(const CertificateInput* input,std::uint64_t count,std::int32_t* output){
    if((count>0&&(!input||!output))||count>1000000ULL)return 1;
    for(std::uint64_t i=0;i<count;++i){const auto& c=input[i];output[i]=(c.renew&&c.unused&&c.match&&c.age&&c.warm&&std::isfinite(c.mahalanobis_squared)&&c.mahalanobis_squared<=5.99&&std::isfinite(c.q95)&&c.q95>=0.60&&c.maintain&&c.separation&&c.slew&&c.g_latch)?1:0;}
    return 0;
}

DISH_EXPORT int dish_rbhr_wire_size(std::int32_t message_code){
    const int sizes[8]={40,64,64,96,48,32,32,24};
    return message_code>=0&&message_code<8?sizes[message_code]:-1;
}
