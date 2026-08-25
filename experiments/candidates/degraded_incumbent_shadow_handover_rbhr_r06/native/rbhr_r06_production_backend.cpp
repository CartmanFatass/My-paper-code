#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#define DISH_EXPORT extern "C" __declspec(dllexport)
#else
#define DISH_EXPORT extern "C"
#endif

namespace {
constexpr std::int32_t ABI_VERSION = 1;
constexpr double DT = 0.1;
constexpr std::int32_t TICKS = 1200;
constexpr double PI = 3.1415926535897932384626433832795;

#pragma pack(push, 8)
struct ResetInput {
  std::uint64_t fixture_key;
  std::uint8_t master[32];
  std::int32_t test_mode, package, reflection, initial_owner, qa_owner;
  std::int32_t k_initial, k_new, switch_tick, tau_d_tick, phase;
  std::int32_t route_speed, turn_magnitude_deg, turn_sign, initial_ux, initial_uy;
  std::int32_t block, split, schedule, evaluation_slot, lane, cycle;
  std::int32_t arm_substream, degradation_flag, mask_enabled, fork_branch, episode;
};

struct StepInput {
  double raw_action[4];
  double prediction_mean[8];
  double prediction_covariance[32];
  double service_q[20];
  double controller_hidden[512];
  std::int32_t prepare[2], commit[2];
  double promotion_alpha;
  std::int32_t arm_mode;
};

struct HostState {
  std::int32_t initialized, terminal, tick, package, reflection, initial_owner, owner;
  std::int32_t service_epoch, next_payload_sequence, handover_used;
  std::int32_t k_active, k_new, k_epoch, countdown, pending_switch, switch_tick, tau_d_tick;
  std::int32_t route_speed, turn_magnitude_deg, turn_sign, prepare_latched, warmup;
  std::int32_t pending_intent, intent_owner, intent_epoch, intent_next_sequence, intent_k_epoch;
  std::int32_t intent_certificate, intent_origin_tick;
  std::int32_t source_exists[2], source_sequence[2], source_tick[2];
  std::int32_t pending_source_exists, pending_source_sequence, pending_source_tick;
  std::int32_t base_exists, base_source_sequence, base_source_tick, base_relay_tick;
  std::int32_t pending_relay_exists, pending_relay_source_sequence, pending_relay_source_tick;
  std::int32_t pending_relay_tick, pending_relay_epoch, pending_relay_sequence, pending_relay_sender;
  std::int32_t partner_present[2], partner_tick[2];
  std::int32_t invalid_commit, token_gap, dual_owner, dual_payload, buffer_clear;
  std::int32_t command_slew_breach, separation_breach, service_ticks;
  std::uint8_t master[32];
  std::int32_t block, split, schedule, evaluation_slot, lane, cycle;
  std::int32_t arm_substream, degradation_flag, mask_enabled, fork_branch, episode;
  std::uint64_t protocol_bytes;
  double p[4], v[4], a[4], battery[2], wind[2];
  double filter_mean[8], filter_covariance[32];
  double source_z[8], source_first_margin[2];
  double pending_source_z[4], pending_source_margin[2];
  double base_z[4], base_first_margin, base_second_margin;
  double pending_relay_z[4], pending_relay_first_margin, pending_relay_second_margin;
  double last_radio_margin[6];
  double controller_hidden[512];
  double min_separation, total_energy;
  std::int32_t test_mode, lineage_lock[2], lineage_sequence[2];
  std::int32_t pending_snapshot, pending_snapshot_sender, pending_snapshot_sequence;
  std::int32_t pending_snapshot_tick, snapshot_accepted, snapshot_tick;
  std::int32_t readiness_accepted, readiness_tick, readiness_snapshot_tick;
  std::int32_t application_reason, cas_applied, actuator_owner;
  std::uint64_t protocol_wire_hash, protocol_wire_messages;
  std::int32_t pending_readiness, pending_readiness_tick;
  std::int32_t intent_readiness_tick, intent_snapshot_tick;
  double pending_snapshot_margin, pending_readiness_margin, pending_intent_margin, intent_alpha;
  double pending_snapshot_payload[18], accepted_snapshot_payload[18];
  double pending_readiness_candidate[2], accepted_readiness_candidate[2];
};

struct StepOutput {
  double actor[216]; // four controller copies x 54
  double critic[58];
  std::int32_t service, renew, terminal, owner, service_epoch, next_payload_sequence;
  std::int32_t handover_used, invalid_commit, token_gap, dual_owner, dual_payload;
  std::int32_t buffer_clear, command_slew_breach, separation_breach, tick;
  std::uint64_t protocol_bytes;
  double min_separation, total_energy;
  std::int32_t snapshot_accepted, readiness_accepted, application_reason, cas_applied, actuator_owner;
  std::uint64_t protocol_wire_hash, protocol_wire_messages;
  double snapshot_payload[18], readiness_candidate[2];
  std::int32_t snapshot_delivery_mask, readiness_delivery_mask, version_match;
};

struct ForkOutput {
  HostState real_state, sham_state;
  std::uint8_t real_telemetry_sha256[32], sham_telemetry_sha256[32];
  std::int32_t byte_identical_telemetry;
};
struct PassiveLabelOutput {
  double target[4], links[8];
  std::int32_t missing[4], q_labels[20], q_mask, next_mask, q_copy_index;
};
struct ScriptOutput { double raw_action[4]; std::int32_t transfer; double score; };
struct RecoveryWitnessOutput {
  std::int32_t origin_exists, origin_tick, real_service_ticks, retain_service_ticks;
  std::int32_t opportunities_checked, rejection_mask;
};
struct ProtocolAuditOutput {
  std::int32_t message_count, all_integrity_verified, all_tamper_rejected;
  std::uint32_t sizes[8];
  std::uint8_t aggregate_sha256[32];
};
struct ProtocolTransitionOutput {
  std::int32_t source_lineage_preserved, locks_released, cas_applied, application_reason;
  std::int32_t owner_before, owner_after, service_epoch_after, actuator_owner_after;
  std::int32_t recurrent_promotion_verified;
  std::uint64_t protocol_wire_hash, protocol_wire_messages;
};
#pragma pack(pop)

struct Sha256 {
  std::array<std::uint32_t,8> h{0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U};
  std::array<std::uint8_t,64> buffer{}; std::uint64_t total=0; std::size_t used=0;
  static constexpr std::array<std::uint32_t,64> K{
    0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
    0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
    0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
    0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
    0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
    0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
    0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
    0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U};
  static std::uint32_t rotr(std::uint32_t x,unsigned n){return (x>>n)|(x<<(32U-n));}
  void transform(const std::uint8_t* block){std::array<std::uint32_t,64>w{};for(int i=0;i<16;++i)w[i]=(static_cast<std::uint32_t>(block[4*i])<<24U)|(static_cast<std::uint32_t>(block[4*i+1])<<16U)|(static_cast<std::uint32_t>(block[4*i+2])<<8U)|block[4*i+3];for(int i=16;i<64;++i){const auto s0=rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3U);const auto s1=rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10U);w[i]=w[i-16]+s0+w[i-7]+s1;}auto a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];for(int i=0;i<64;++i){const auto s1=rotr(e,6)^rotr(e,11)^rotr(e,25),ch=(e&f)^((~e)&g),t1=hh+s1+ch+K[i]+w[i],s0=rotr(a,2)^rotr(a,13)^rotr(a,22),maj=(a&b)^(a&c)^(b&c),t2=s0+maj;hh=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=hh;}
  void update(const std::uint8_t* data,std::size_t size){total+=size;while(size){const auto take=std::min(size,buffer.size()-used);std::memcpy(buffer.data()+used,data,take);used+=take;data+=take;size-=take;if(used==64){transform(buffer.data());used=0;}}}
  std::array<std::uint8_t,32> final(){const auto bits=total*8U;buffer[used++]=0x80U;if(used>56){while(used<64)buffer[used++]=0;transform(buffer.data());used=0;}while(used<56)buffer[used++]=0;for(int i=7;i>=0;--i)buffer[used++]=static_cast<std::uint8_t>((bits>>(8U*i))&0xffU);transform(buffer.data());std::array<std::uint8_t,32>out{};for(int i=0;i<8;++i)for(int j=0;j<4;++j)out[4*i+j]=static_cast<std::uint8_t>((h[i]>>(24U-8U*j))&0xffU);return out;}
};

inline std::uint64_t rng_word(const std::uint8_t* master,const char* address,std::size_t length){const std::uint8_t zero=0;Sha256 sha;sha.update(master,32);sha.update(&zero,1);sha.update(reinterpret_cast<const std::uint8_t*>(address),length);const auto digest=sha.final();std::uint64_t value=0;for(int i=0;i<8;++i)value=(value<<8U)|digest[i];return value;}

struct PhysicsTick;
inline double predictive_q95(const double* q);
inline double mahalanobis_position(const StepInput& in);

template<std::size_t N> inline void put_u8(std::array<std::uint8_t,N>& out,std::size_t& p,std::uint8_t value){out[p++]=value;}
template<std::size_t N> inline void put_u16(std::array<std::uint8_t,N>& out,std::size_t& p,std::uint16_t value){out[p++]=value&0xffU;out[p++]=(value>>8U)&0xffU;}
template<std::size_t N> inline void put_u32(std::array<std::uint8_t,N>& out,std::size_t& p,std::uint32_t value){for(int i=0;i<4;++i)out[p++]=(value>>(8U*i))&0xffU;}
template<std::size_t N> inline void put_f32(std::array<std::uint8_t,N>& out,std::size_t& p,double value){const float rounded=static_cast<float>(value);std::uint32_t bits=0;std::memcpy(&bits,&rounded,4);put_u32(out,p,bits);}
template<std::size_t N> inline void finish_wire(std::array<std::uint8_t,N>& out,std::size_t body){Sha256 sha;sha.update(out.data(),body);const auto digest=sha.final();for(int i=0;i<4;++i)out[body+i]=digest[i];}
template<std::size_t N> inline bool verify_wire(const std::array<std::uint8_t,N>& out,std::size_t body){Sha256 sha;sha.update(out.data(),body);const auto digest=sha.final();for(int i=0;i<4;++i)if(out[body+i]!=digest[i])return false;for(std::size_t i=body+4;i<N;++i)if(out[i])return false;return true;}
template<std::size_t N> inline void account_wire(HostState& s,const std::array<std::uint8_t,N>& wire){std::uint64_t hash=s.protocol_wire_hash? s.protocol_wire_hash:1469598103934665603ULL;for(const auto value:wire){hash^=value;hash*=1099511628211ULL;}s.protocol_wire_hash=hash;++s.protocol_wire_messages;s.protocol_bytes+=N;}

inline std::array<std::uint8_t,40> source_wire(std::uint32_t sequence,std::uint32_t tick,const double* z){std::array<std::uint8_t,40> out{};std::size_t p=0;put_u32(out,p,sequence);put_u32(out,p,tick);for(int i=0;i<4;++i)put_f32(out,p,z[i]);finish_wire(out,p);return out;}
inline std::array<std::uint8_t,64> relay_wire(const HostState& s,int sender){std::array<std::uint8_t,64> out{};std::size_t p=0;put_u16(out,p,static_cast<std::uint16_t>(s.service_epoch));put_u32(out,p,static_cast<std::uint32_t>(s.pending_relay_sequence));put_u32(out,p,static_cast<std::uint32_t>(s.tick));put_u8(out,p,static_cast<std::uint8_t>(sender));const auto source=source_wire(s.source_sequence[sender],s.source_tick[sender],s.source_z+4*sender);std::memcpy(out.data()+p,source.data(),source.size());p+=source.size();put_f32(out,p,s.source_first_margin[sender]);finish_wire(out,p);return out;}
inline std::array<std::uint8_t,64> state_wire(const HostState& s,const PhysicsTick& ph,int sender);
inline std::array<std::uint8_t,96> snapshot_wire(const HostState& s,const StepInput& in){std::array<std::uint8_t,96>out{};std::size_t p=0;put_u8(out,p,s.owner);put_u16(out,p,s.service_epoch);put_u32(out,p,s.next_payload_sequence);put_u32(out,p,s.source_sequence[0]);put_u16(out,p,s.k_epoch);put_u32(out,p,s.tick);for(int i=0;i<4;++i)put_f32(out,p,in.prediction_mean[i]);for(int i=0;i<10;++i)put_f32(out,p,in.prediction_covariance[i]);put_f32(out,p,s.last_radio_margin[2+s.owner]);put_f32(out,p,s.last_radio_margin[s.owner]);put_f32(out,p,in.raw_action[2*s.owner]);put_f32(out,p,in.raw_action[2*s.owner+1]);finish_wire(out,p);return out;}
inline std::array<std::uint8_t,48> readiness_wire(const HostState& s,const StepInput& in){std::array<std::uint8_t,48>out{};std::size_t p=0;put_u8(out,p,1-s.owner);put_u8(out,p,s.owner);put_u32(out,p,s.tick);put_u32(out,p,s.snapshot_tick);put_u16(out,p,s.service_epoch);put_u32(out,p,s.next_payload_sequence);put_u32(out,p,s.source_sequence[0]);put_u16(out,p,s.k_epoch);put_f32(out,p,predictive_q95(in.service_q));put_f32(out,p,mahalanobis_position(in));put_f32(out,p,in.raw_action[2*(1-s.owner)]);put_f32(out,p,in.raw_action[2*(1-s.owner)+1]);put_f32(out,p,in.commit[s.owner]?1.0:0.0);finish_wire(out,p);return out;}
inline std::array<std::uint8_t,32> intent_wire(const HostState& s,bool request){std::array<std::uint8_t,32>out{};std::size_t p=0;put_u32(out,p,s.intent_origin_tick);put_u32(out,p,s.readiness_tick);put_u8(out,p,s.intent_owner);put_u8(out,p,1-s.intent_owner);put_u16(out,p,s.intent_epoch);put_u32(out,p,s.intent_next_sequence);put_u32(out,p,s.source_sequence[0]);put_u16(out,p,s.intent_k_epoch);put_u8(out,p,s.intent_certificate);put_u8(out,p,request?1:0);finish_wire(out,p);return out;}
inline std::array<std::uint8_t,24> result_wire(std::uint32_t tick,std::uint8_t success,std::uint8_t reason,std::uint8_t owner,std::uint16_t epoch,std::uint32_t sequence,std::uint16_t k_epoch){std::array<std::uint8_t,24>out{};std::size_t p=0;put_u32(out,p,tick);put_u8(out,p,success);put_u8(out,p,reason);put_u8(out,p,owner);put_u16(out,p,epoch);put_u32(out,p,sequence);put_u16(out,p,k_epoch);finish_wire(out,p);return out;}

struct Vec2 { double x, y; };
struct Vec3 { double x, y, z; };
inline double sq(double x);
inline void route(const HostState& s,int tick,double& x,double& y,double& vx,double& vy);

inline const char* split_name(int value){switch(value){case 0:return "TRAIN";case 1:return "CLAIM";case 2:return "CALIBRATION";case 3:return "FORK";case 4:return "BOOTSTRAP";default:return "NONE";}}
inline const char* schedule_name(int value){switch(value){case 0:return "K4";case 1:return "K8";case 2:return "K12";case 3:return "K4_TO_K12";case 4:return "K12_TO_K4";default:return "NONE";}}
inline const char* regime_name(int value){switch(value){case 0:return "TARGET_VISUAL_MASK";case 1:return "TERRAIN_RELAY_MASK";default:return "NONE";}}
inline const char* arm_name(int value){switch(value){case 0:return "COMMON";case 1:return "SLOT0";case 2:return "SLOT1";case 3:return "SLOT2";case 4:return "SLOT3";case 5:return "SLOT4";default:return "NONE";}}
inline const char* degradation_name(int value){switch(value){case 0:return "PAIR_SHARED";case 1:return "DEGRADED_ONLY";case 2:return "NO_DEGRADATION_ONLY";default:return "NONE";}}
inline const char* fork_name(int value){switch(value){case 0:return "PREFORK";case 1:return "REAL";case 2:return "SHAM";case 3:return "SCRIPT_TRANSFER";case 4:return "SCRIPT_RETAIN";default:return "NONE";}}
inline std::string scalar(int value){return value<0?"NONE":std::to_string(value);}
inline std::string address(const HostState& s,const char* purpose,const char* field,int tick,const char* hop="NONE",int draw=0,const char* message="NONE",int packet_sequence=-1,int inference=-1){
  return std::string("DISH/RBHR/R06/")+purpose+"/"+scalar(s.block)+"/"+split_name(s.split)+"/"+regime_name(s.package)+"/"+schedule_name(s.schedule)+"/"+scalar(s.evaluation_slot)+"/"+scalar(s.lane)+"/"+scalar(s.cycle)+"/"+arm_name(s.arm_substream)+"/"+degradation_name(s.degradation_flag)+"/"+fork_name(s.fork_branch)+"/"+scalar(s.episode)+"/"+scalar(tick)+"/"+message+"/"+scalar(packet_sequence)+"/"+hop+"/"+scalar(inference)+"/"+field+"/"+std::to_string(draw);
}
inline double uniform(const HostState& s,const std::string& a){return (static_cast<double>(rng_word(s.master,a.data(),a.size())>>11U)+0.5)/9007199254740992.0;}
inline double normal(const HostState& s,const char* purpose,const char* field,int tick,const char* hop="NONE"){
  const double u1=uniform(s,address(s,purpose,field,tick,hop,0)),u2=uniform(s,address(s,purpose,field,tick,hop,1));return std::sqrt(-2.0*std::log(u1))*std::cos(2.0*PI*u2);
}
inline double terrain(double x,double y){return 135.0*std::exp(-sq(x/75.0)-std::pow(y/220.0,4))+55.0*std::exp(-sq((x-90.0)/35.0)-sq((y+40.0)/85.0));}
inline bool ray_blocked(const HostState& s,Vec3 a,Vec3 b,double clearance){for(int j=1;j<=127;++j){const double q=j/128.0,x=a.x+q*(b.x-a.x),y=a.y+q*(b.y-a.y),z=a.z+q*(b.z-a.z);if(z<=terrain(x,s.reflection*y)+clearance)return true;}return false;}
inline bool ray_prism(const HostState& s,Vec3 a,Vec3 b,double xmin,double xmax,double ymin,double ymax,double zmin,double zmax){for(int j=0;j<=128;++j){const double q=j/128.0,x=a.x+q*(b.x-a.x),y=s.reflection*(a.y+q*(b.y-a.y)),z=a.z+q*(b.z-a.z);if(x>=xmin&&x<=xmax&&y>=ymin&&y<=ymax&&z>=zmin&&z<=zmax)return true;}return false;}
inline double radio_margin(const HostState& s,Vec3 a,Vec3 b,const char* hop,bool relay_mask){const double d=std::sqrt(sq(a.x-b.x)+sq(a.y-b.y)+sq(a.z-b.z));double blocked=ray_blocked(s,a,b,8.0)?1.0:0.0;if(relay_mask)blocked+=1.0;return 30.0-20.0*std::log10(std::max(d,1.0)/100.0)-35.0*blocked+normal(s,"RADIO","RADIO_EPSILON",s.tick,hop);}

struct PhysicsTick { double gx,gy,gvx,gvy; double camera_z[4]; std::int32_t camera_present[2]; double radio[6]; double source_noise[4]; double wind_eta[2]; };

inline PhysicsTick physics_tick(const HostState& s){
  PhysicsTick p{};route(s,s.tick,p.gx,p.gy,p.gvx,p.gvy);const bool active=s.tick>=s.tau_d_tick&&s.tick<s.tau_d_tick+40;Vec3 g{p.gx,p.gy,0.0},base{-600.0,0.0,20.0},u[2]{{s.p[0],s.p[1],90.0},{s.p[2],s.p[3],90.0}};
  for(int i=0;i<2;++i){bool clear=!ray_blocked(s,u[i],g,5.0)&&std::sqrt(sq(u[i].x-g.x)+sq(u[i].y-g.y)+8100.0)<=500.0;if(s.mask_enabled&&s.package==0&&active&&i==s.initial_owner&&ray_prism(s,u[i],g,-20,30,-155,-85,0,120))clear=false;p.camera_present[i]=clear;if(clear){const char* fx=i==0?"CAMERA_U0_X":"CAMERA_U1_X";const char* fy=i==0?"CAMERA_U0_Y":"CAMERA_U1_Y";p.camera_z[2*i]=p.gx+2.0*normal(s,"CAMERA",fx,s.tick);p.camera_z[2*i+1]=p.gy+2.0*s.reflection*normal(s,"CAMERA",fy,s.tick);}}
  p.radio[0]=radio_margin(s,g,u[0],"G_TO_U0",false);p.radio[1]=radio_margin(s,g,u[1],"G_TO_U1",false);
  p.radio[2]=radio_margin(s,u[0],base,"U0_TO_BASE",s.mask_enabled&&s.package==1&&active&&s.initial_owner==0&&ray_prism(s,u[0],base,-30,45,-80,80,0,130));
  p.radio[3]=radio_margin(s,u[1],base,"U1_TO_BASE",s.mask_enabled&&s.package==1&&active&&s.initial_owner==1&&ray_prism(s,u[1],base,-30,45,-80,80,0,130));
  p.radio[4]=radio_margin(s,u[0],u[1],"U0_TO_U1",false);p.radio[5]=radio_margin(s,u[1],u[0],"U1_TO_U0",false);
  p.source_noise[0]=2.0*normal(s,"PACKET","SOURCE_POSITION_X",s.tick);p.source_noise[1]=2.0*s.reflection*normal(s,"PACKET","SOURCE_POSITION_Y",s.tick);p.source_noise[2]=0.25*normal(s,"PACKET","SOURCE_VELOCITY_X",s.tick);p.source_noise[3]=0.25*s.reflection*normal(s,"PACKET","SOURCE_VELOCITY_Y",s.tick);
  p.wind_eta[0]=normal(s,"WIND","WIND_X",s.tick);p.wind_eta[1]=s.reflection*normal(s,"WIND","WIND_Y",s.tick);
  if(s.test_mode==2){for(double& value:p.radio)value=12.0;p.camera_present[s.owner]=0;}
  return p;
}

inline std::array<std::uint8_t,64> state_wire(const HostState& s,const PhysicsTick& ph,int sender){std::array<std::uint8_t,64>out{};std::size_t p=0;const int o=2*sender;put_u32(out,p,s.tick);put_f32(out,p,s.p[o]);put_f32(out,p,s.p[o+1]);put_f32(out,p,s.v[o]);put_f32(out,p,s.v[o+1]);put_f32(out,p,s.a[o]);put_f32(out,p,s.a[o+1]);put_f32(out,p,s.battery[sender]);put_u8(out,p,ph.camera_present[sender]?0:1);put_f32(out,p,ph.radio[sender]);put_f32(out,p,ph.radio[2+sender]);put_u8(out,p,s.owner==sender);put_u16(out,p,s.service_epoch);put_u16(out,p,s.k_epoch);const bool d=!ph.camera_present[s.owner]||ph.radio[2+s.owner]<6.0;put_u8(out,p,d);put_u8(out,p,s.prepare_latched);put_u8(out,p,s.prepare_latched);finish_wire(out,p);return out;}

inline double sq(double x) { return x*x; }
inline double norm(Vec2 x) { return std::sqrt(sq(x.x)+sq(x.y)); }
inline Vec2 clipped(Vec2 x, double cap) {
  const double n=norm(x); if(n<=cap || n<=1e-12) return x;
  const double q=cap/n; return {x.x*q,x.y*q};
}
inline Vec2 project(Vec2 previous, Vec2 raw) {
  raw=clipped(raw,3.0); Vec2 delta=clipped({raw.x-previous.x,raw.y-previous.y},1.5);
  return clipped({previous.x+delta.x,previous.y+delta.y},3.0);
}
inline double separation(const HostState& s) {
  return std::hypot(s.p[0]-s.p[2],s.p[1]-s.p[3]);
}

inline void route(const HostState& s, int tick, double& x, double& y, double& vx, double& vy) {
  const double t=tick*DT, td=s.tau_d_tick*DT, speed=static_cast<double>(s.route_speed);
  const double angle=s.turn_sign*s.turn_magnitude_deg*PI/180.0;
  if(t<=td){x=-speed*td+speed*t;y=-120.0;vx=speed;vy=0.0;}
  else{x=speed*(t-td)*std::cos(angle);y=-120.0+speed*(t-td)*std::sin(angle);vx=speed*std::cos(angle);vy=speed*std::sin(angle);}
  y*=s.reflection; vy*=s.reflection;
}

inline bool terminal_at(const HostState& s) {
  return s.terminal || s.battery[0]<=0.0 || s.battery[1]<=0.0 || separation(s)<15.0;
}

inline void filter_step(double* mean, double* covariance, bool present, double zx, double zy) {
  constexpr double F[16]={1,0,DT,0, 0,1,0,DT, 0,0,1,0, 0,0,0,1};
  constexpr double q[4]={0.04,0.04,0.25,0.25};
  double pm[4]={}; double pp[16]={};
  for(int i=0;i<4;++i) for(int j=0;j<4;++j) pm[i]+=F[i*4+j]*mean[j];
  for(int i=0;i<4;++i) for(int j=0;j<4;++j) for(int a=0;a<4;++a) for(int b=0;b<4;++b)
    pp[i*4+j]+=F[i*4+a]*covariance[a*4+b]*F[j*4+b];
  for(int i=0;i<4;++i) pp[i*4+i]+=q[i];
  if(!present){std::memcpy(mean,pm,sizeof(pm));std::memcpy(covariance,pp,sizeof(pp));return;}
  const double s00=pp[0]+4.0+1e-9,s01=pp[1],s11=pp[5]+4.0+1e-9,det=s00*s11-s01*s01;
  if(!(det>0.0) || !std::isfinite(det)){std::memcpy(mean,pm,sizeof(pm));std::memcpy(covariance,pp,sizeof(pp));return;}
  const double i00=s11/det,i01=-s01/det,i11=s00/det;
  double k[8]={};
  for(int i=0;i<4;++i){k[i*2]=pp[i*4]*i00+pp[i*4+1]*i01;k[i*2+1]=pp[i*4]*i01+pp[i*4+1]*i11;}
  const double e0=zx-pm[0],e1=zy-pm[1]; for(int i=0;i<4;++i) mean[i]=pm[i]+k[i*2]*e0+k[i*2+1]*e1;
  double ikh[16]={}; for(int i=0;i<4;++i){ikh[i*4+i]=1.0;ikh[i*4]-=k[i*2];ikh[i*4+1]-=k[i*2+1];}
  double temp[16]={}, out[16]={};
  for(int i=0;i<4;++i) for(int j=0;j<4;++j) for(int a=0;a<4;++a) temp[i*4+j]+=ikh[i*4+a]*pp[a*4+j];
  for(int i=0;i<4;++i) for(int j=0;j<4;++j) for(int a=0;a<4;++a) out[i*4+j]+=temp[i*4+a]*ikh[j*4+a];
  for(int i=0;i<4;++i) for(int j=0;j<4;++j) out[i*4+j]+=4.0*(k[i*2]*k[j*2]+k[i*2+1]*k[j*2+1]);
  std::memcpy(covariance,out,sizeof(out));
}

inline void actor_row(const HostState& s, const PhysicsTick& ph, int vehicle, int copy, bool renew, double* o) {
  std::fill(o,o+54,0.0); const int other=1-vehicle, po=2*vehicle, qo=2*other;
  o[copy]=1.0; o[2]=(s.owner==vehicle); o[3]=s.handover_used;
  o[4]=s.p[po]+600.0; o[5]=s.p[po+1]; o[6]=s.v[po]; o[7]=s.v[po+1]; o[8]=s.a[po]; o[9]=s.a[po+1]; o[10]=s.battery[vehicle];
  o[11]=ph.camera_present[vehicle]; if(ph.camera_present[vehicle]){o[12]=ph.camera_z[po]-s.p[po];o[13]=ph.camera_z[po+1]-s.p[po+1];} o[14]=!ph.camera_present[vehicle];
  o[15]=s.filter_mean[4*vehicle]-s.p[po];o[16]=s.filter_mean[4*vehicle+1]-s.p[po+1];o[17]=s.filter_mean[4*vehicle+2];o[18]=s.filter_mean[4*vehicle+3];
  o[19]=s.filter_covariance[16*vehicle];o[20]=s.filter_covariance[16*vehicle+1];o[21]=s.filter_covariance[16*vehicle+5];
  o[22]=ph.radio[vehicle];o[23]=ph.radio[2+vehicle];o[24]=ph.radio[4+(vehicle==0?0:1)];
  o[25]=s.source_exists[vehicle];o[26]=s.source_exists[vehicle]?(s.tick-s.source_tick[vehicle])*DT:1e6;
  o[27]=s.partner_present[vehicle];o[28]=s.partner_present[vehicle]?(s.tick-s.partner_tick[vehicle])*DT:1e6;
  if(s.partner_present[vehicle]){o[29]=s.p[qo]-s.p[po];o[30]=s.p[qo+1]-s.p[po+1];o[31]=s.v[qo];o[32]=s.v[qo+1];o[33]=s.a[qo];o[34]=s.a[qo+1];o[35]=s.battery[other];o[36]=!ph.camera_present[other];o[37]=(s.owner==other);}
  o[38]=s.k_active==4;o[39]=s.k_active==8;o[40]=s.k_active==12;o[41]=s.k_epoch;o[42]=s.countdown;o[43]=renew;
  const bool d=!ph.camera_present[s.owner] || ph.radio[2+s.owner]<6.0;
  o[44]=d;o[45]=s.prepare_latched;o[46]=s.prepare_latched;o[47]=s.prepare_latched;o[48]=std::min(s.warmup,20);o[49]=s.prepare_latched;o[50]=s.prepare_latched?0.0:1e6;o[51]=s.prepare_latched;o[52]=s.prepare_latched?1.0:1e6;o[53]=s.prepare_latched && !s.handover_used;
}

inline void critic_row(const HostState& s, const PhysicsTick& ph, bool renew, double* x) {
  std::fill(x,x+58,0.0); double gx,gy,gvx,gvy;route(s,s.tick,gx,gy,gvx,gvy);x[0]=gx;x[1]=gy;x[2]=gvx;x[3]=gvy;
  int cursor=4; for(int i=0;i<2;++i){const int p=2*i;x[cursor++]=s.p[p];x[cursor++]=s.p[p+1];x[cursor++]=s.v[p];x[cursor++]=s.v[p+1];x[cursor++]=s.a[p];x[cursor++]=s.a[p+1];x[cursor++]=s.battery[i];x[cursor++]=ph.camera_present[i];x[cursor++]=ph.camera_present[i]?ph.camera_z[p]:0;x[cursor++]=ph.camera_present[i]?ph.camera_z[p+1]:0;x[cursor++]=!ph.camera_present[i];x[cursor++]=ph.radio[i];x[cursor++]=ph.radio[2+i];x[cursor++]=ph.radio[4+(i==0?0:1)];x[cursor++]=s.source_exists[i];x[cursor++]=s.source_exists[i]?(s.tick-s.source_tick[i])*DT:1e6;x[cursor++]=s.source_exists[i]?s.source_sequence[i]:0;x[cursor++]=s.owner==i;}
  x[cursor++]=s.base_exists;x[cursor++]=s.base_exists?(s.tick-s.base_source_tick)*DT:1e6;x[cursor++]=0.0;x[cursor++]=s.base_exists?s.base_first_margin:-1e6;x[cursor++]=s.base_exists?s.base_second_margin:-1e6;
  x[cursor++]=s.owner==0;x[cursor++]=s.owner==1;x[cursor++]=s.service_epoch;x[cursor++]=s.next_payload_sequence;x[cursor++]=s.handover_used;
  x[cursor++]=s.k_active==4;x[cursor++]=s.k_active==8;x[cursor++]=s.k_active==12;x[cursor++]=s.k_epoch;x[cursor++]=s.countdown;x[cursor++]=renew;x[cursor++]=s.pending_switch;x[cursor++]=s.terminal;
}

inline double predictive_q95(const double* q){double dp[21]={};dp[0]=1.0;for(int j=0;j<20;++j){const double p=std::clamp(q[j],1e-6,1.0-1e-6);for(int m=j+1;m>=0;--m){const double keep=dp[m]*(1.0-p),add=m>0?dp[m-1]*p:0.0;dp[m]=keep+add;}}for(int m=20;m>=0;--m){double tail=0;for(int k=m;k<=20;++k)tail+=dp[k];if(tail>=0.95)return m/20.0;}return 0.0;}
inline double mahalanobis_position(const StepInput& in){const double dx=in.prediction_mean[0]-in.prediction_mean[4],dy=in.prediction_mean[1]-in.prediction_mean[5];const double s00=in.prediction_covariance[0]+in.prediction_covariance[16]+1e-6,s01=in.prediction_covariance[1]+in.prediction_covariance[17],s11=in.prediction_covariance[5]+in.prediction_covariance[21]+1e-6,det=s00*s11-s01*s01;if(!(det>0)||!std::isfinite(det))return std::numeric_limits<double>::infinity();return (dx*dx*s11-2*dx*dy*s01+dy*dy*s00)/det;}
inline bool native_origin_certificate(const HostState& s,const StepInput& in,bool renew){if(!renew||s.handover_used||!s.prepare_latched||s.warmup<10||!s.source_exists[0]||!s.source_exists[1]||s.source_sequence[0]!=s.source_sequence[1]||s.terminal)return false;const double dm=mahalanobis_position(in),q95=predictive_q95(in.service_q);if(!std::isfinite(dm)||dm>5.99||q95<0.60||separation(s)<15.0)return false;for(int i=0;i<2;++i){Vec2 previous{s.a[2*i],s.a[2*i+1]},raw{in.raw_action[2*i],in.raw_action[2*i+1]},bounded=clipped(raw,3.0);if(norm({bounded.x-previous.x,bounded.y-previous.y})>1.5+1e-12)return false;}return true;}

inline void promote_recurrent_state(HostState& s,int old_owner,double alpha){
  alpha=std::clamp(alpha,0.0,1.0);const int standby=1-old_owner;
  const int old_i=(2*old_owner)*128,old_s=(2*old_owner+1)*128;
  const int new_i=(2*standby)*128,new_s=(2*standby+1)*128;
  double owner_i[128]={},standby_s[128]={};
  std::memcpy(owner_i,s.controller_hidden+old_i,sizeof(owner_i));
  std::memcpy(standby_s,s.controller_hidden+new_s,sizeof(standby_s));
  for(int j=0;j<128;++j)s.controller_hidden[new_i+j]=std::clamp(alpha*standby_s[j]+(1.0-alpha)*owner_i[j],-1.0,1.0);
  std::memcpy(s.controller_hidden+old_s,owner_i,sizeof(owner_i));
  // The remaining I_old and S_standby copies retain their pre-CAS values.
  s.actuator_owner=standby;
}

inline bool validate_reset(const ResetInput& x) {
  return (x.test_mode==0||x.test_mode==1||x.test_mode==2) && (x.package==0||x.package==1) && (x.reflection==1||x.reflection==-1) && (x.initial_owner==0||x.initial_owner==1) && (x.qa_owner==0||x.qa_owner==1)
    && (x.k_initial==4||x.k_initial==8||x.k_initial==12) && (x.k_new==4||x.k_new==8||x.k_new==12)
    && x.phase>=0 && x.phase<x.k_initial && x.switch_tick>=0 && x.switch_tick<TICKS && x.tau_d_tick>=0 && x.tau_d_tick<TICKS
    && (x.route_speed==4||x.route_speed==6||x.route_speed==8) && (x.turn_magnitude_deg==25||x.turn_magnitude_deg==35||x.turn_magnitude_deg==45)
    && (x.turn_sign==1||x.turn_sign==-1) && (x.mask_enabled==0||x.mask_enabled==1);
}

inline void reset_one(const ResetInput& x, HostState& s, StepOutput& out) {
  std::memset(&s,0,sizeof(s)); s.initialized=1;s.package=x.package;s.reflection=x.reflection;s.initial_owner=x.initial_owner;s.owner=x.initial_owner;
  s.test_mode=x.test_mode;s.actuator_owner=x.initial_owner;
  std::memcpy(s.master,x.master,32);s.block=x.block;s.split=x.split;s.schedule=x.schedule;s.evaluation_slot=x.evaluation_slot;s.lane=x.lane;s.cycle=x.cycle;s.arm_substream=x.arm_substream;s.degradation_flag=x.degradation_flag;s.mask_enabled=x.mask_enabled;s.fork_branch=x.fork_branch;s.episode=x.episode;
  s.k_active=x.k_initial;s.k_new=x.k_new;s.countdown=x.phase;s.switch_tick=x.switch_tick;s.tau_d_tick=x.tau_d_tick;s.route_speed=x.route_speed;s.turn_magnitude_deg=x.turn_magnitude_deg;s.turn_sign=x.turn_sign;
  double gx,gy,gvx,gvy;route(s,0,gx,gy,gvx,gvy);const double qax=gx+x.initial_ux,qay=gy+x.initial_uy*x.reflection,qbx=gx-x.initial_ux,qby=gy-x.initial_uy*x.reflection;
  if(x.qa_owner==0){s.p[0]=qax;s.p[1]=qay;s.p[2]=qbx;s.p[3]=qby;}
  else{s.p[0]=qbx;s.p[1]=qby;s.p[2]=qax;s.p[3]=qay;}
  s.battery[0]=s.battery[1]=200000.0;s.min_separation=separation(s);
  for(int u=0;u<2;++u){s.filter_covariance[16*u]=250000;s.filter_covariance[16*u+5]=250000;s.filter_covariance[16*u+10]=100;s.filter_covariance[16*u+15]=100;}
  PhysicsTick blank{};blank.radio[0]=blank.radio[1]=blank.radio[2]=blank.radio[3]=blank.radio[4]=blank.radio[5]=-1e6;
  std::memset(&out,0,sizeof(out));for(int i=0;i<2;++i)for(int c=0;c<2;++c)actor_row(s,blank,i,c,s.countdown==0,out.actor+(i*2+c)*54);critic_row(s,blank,s.countdown==0,out.critic);out.owner=s.owner;out.tick=0;out.min_separation=s.min_separation;
}

inline int step_one(HostState& s, const StepInput& in, StepOutput& out, bool scripted_transfer=false) {
  if(!s.initialized || s.tick<0 || s.tick>=TICKS) return 11;
  std::memset(&out,0,sizeof(out));if(in.arm_mode<0||in.arm_mode>4)return 14;bool noop_intent_emitted=false;
  if(terminal_at(s)) s.terminal=1;
  if(s.terminal){s.total_energy+=130.0;s.battery[0]=std::max(0.0,s.battery[0]-65.0);s.battery[1]=std::max(0.0,s.battery[1]-65.0);++s.tick;out.terminal=1;out.tick=s.tick;out.owner=s.owner;out.service_epoch=s.service_epoch;out.next_payload_sequence=s.next_payload_sequence;out.handover_used=s.handover_used;out.total_energy=s.total_energy;out.min_separation=s.min_separation;return 0;}
  const PhysicsTick ph=physics_tick(s);std::memcpy(s.controller_hidden,in.controller_hidden,sizeof(s.controller_hidden));

  bool snapshot_delivered_this_tick=false,readiness_delivered_this_tick=false;
  // Delivery suborder: SNAPSHOT/intent headers arm the one-tick lineage lock
  // before SOURCE replacement.  The lock releases only after application.
  if(s.pending_snapshot){
    const int sender=s.pending_snapshot_sender,receiver=1-sender;
    s.lineage_lock[sender]=1;s.lineage_sequence[sender]=s.pending_snapshot_sequence;
    if(s.pending_snapshot_margin>=6.0){
      s.lineage_lock[receiver]=1;s.lineage_sequence[receiver]=s.pending_snapshot_sequence;
      if(s.owner==sender && s.source_exists[0] && s.source_exists[1] &&
         s.source_sequence[0]==s.pending_snapshot_sequence &&
         s.source_sequence[1]==s.pending_snapshot_sequence){
        s.snapshot_accepted=1;s.snapshot_tick=s.pending_snapshot_tick;
        std::memcpy(s.accepted_snapshot_payload,s.pending_snapshot_payload,sizeof(s.accepted_snapshot_payload));snapshot_delivered_this_tick=true;
      }
    }
    s.pending_snapshot=0;
  }
  if(s.pending_source_exists){for(int i=0;i<2;++i)if(s.pending_source_margin[i]>=6.0&&!s.lineage_lock[i]){s.source_exists[i]=1;s.source_sequence[i]=s.pending_source_sequence;s.source_tick[i]=s.pending_source_tick;std::memcpy(s.source_z+4*i,s.pending_source_z,4*sizeof(double));s.source_first_margin[i]=s.pending_source_margin[i];}}
  if(s.pending_relay_exists && s.pending_relay_second_margin>=6.0){s.base_exists=1;s.base_source_sequence=s.pending_relay_source_sequence;s.base_source_tick=s.pending_relay_source_tick;s.base_relay_tick=s.pending_relay_tick;std::memcpy(s.base_z,s.pending_relay_z,4*sizeof(double));s.base_first_margin=s.pending_relay_first_margin;s.base_second_margin=s.pending_relay_second_margin;}
  for(int receiver=0;receiver<2;++receiver){const int sender=1-receiver;const double margin=ph.radio[4+sender];if(margin>=6.0){s.partner_present[receiver]=1;s.partner_tick[receiver]=s.tick;}}
  if(s.pending_readiness){
    if(s.pending_readiness_margin>=6.0 && s.snapshot_accepted){s.readiness_accepted=1;s.readiness_tick=s.pending_readiness_tick;s.readiness_snapshot_tick=s.snapshot_tick;std::memcpy(s.accepted_readiness_candidate,s.pending_readiness_candidate,sizeof(s.accepted_readiness_candidate));readiness_delivered_this_tick=true;}
    s.pending_readiness=0;
  }

  bool renew=s.countdown==0; if(s.tick>=s.switch_tick && s.k_active!=s.k_new) s.pending_switch=1;
  if(renew && s.pending_switch){s.k_active=s.k_new;++s.k_epoch;s.pending_switch=0;}
  s.application_reason=0;s.cas_applied=0;
  if(s.pending_intent){
    if(s.intent_readiness_tick==0&&s.intent_origin_tick>0){s.intent_readiness_tick=s.readiness_tick;s.intent_snapshot_tick=s.snapshot_tick;}
    int reason=0;
    if(s.pending_intent_margin<6.0){s.pending_intent=0;for(int i=0;i<2;++i)s.lineage_lock[i]=0;}
    else{
      if(!s.intent_certificate)reason=2;
      else if(s.handover_used)reason=3;
      else if(s.intent_origin_tick+1!=s.tick||s.intent_readiness_tick!=s.intent_origin_tick-1||s.intent_snapshot_tick!=s.intent_origin_tick||s.snapshot_tick!=s.intent_origin_tick)reason=4;
      else if(s.owner!=s.intent_owner)reason=5;
      else if(s.service_epoch!=s.intent_epoch)reason=6;
      else if(s.next_payload_sequence!=s.intent_next_sequence)reason=7;
      else if(!s.source_exists[0]||!s.source_exists[1]||s.source_sequence[0]!=s.source_sequence[1])reason=8;
      else if(s.k_epoch!=s.intent_k_epoch)reason=9;
      else if(s.terminal)reason=10;
      else if(s.battery[0]<=0||s.battery[1]<=0)reason=11;
      else if(separation(s)<15.0||std::hypot((s.p[0]+DT*s.v[0])-(s.p[2]+DT*s.v[2]),(s.p[1]+DT*s.v[1])-(s.p[3]+DT*s.v[3]))<15.0)reason=12;
      else for(int i=0;i<2;++i){const Vec2 bounded=clipped({in.raw_action[2*i],in.raw_action[2*i+1]},3.0);if(norm({bounded.x-s.a[2*i],bounded.y-s.a[2*i+1]})>1.5+1e-12){reason=13;break;}}
      const int old_owner=s.owner;
      if(reason==0){promote_recurrent_state(s,old_owner,s.intent_alpha);s.owner=1-s.owner;++s.service_epoch;s.handover_used=1;s.cas_applied=1;}
      else ++s.invalid_commit;
      s.application_reason=reason;
      const auto result=result_wire(s.tick,reason==0,static_cast<std::uint8_t>(reason),static_cast<std::uint8_t>(1-old_owner),static_cast<std::uint16_t>(s.service_epoch),static_cast<std::uint32_t>(s.next_payload_sequence),static_cast<std::uint16_t>(s.k_epoch));account_wire(s,result);
      s.pending_intent=0;for(int i=0;i<2;++i)s.lineage_lock[i]=0;
    }
  }
  // The evaluator-only tape-qualification branch applies at this exact
  // application boundary: after arrivals and before current observations,
  // reservation, or motion.  It emits no learned control message.
  if(scripted_transfer){
    if(s.handover_used || s.terminal || s.battery[0]<=0.0 || s.battery[1]<=0.0 ||
       !s.source_exists[0] || !s.source_exists[1] ||
       s.source_sequence[0]!=s.source_sequence[1] || separation(s)<15.0) return 12;
    const int old_owner=s.owner;promote_recurrent_state(s,old_owner,1.0);s.owner=1-s.owner; ++s.service_epoch; s.handover_used=1;
  }

  for(int i=0;i<2;++i)filter_step(s.filter_mean+4*i,s.filter_covariance+16*i,ph.camera_present[i]!=0,ph.camera_z[2*i],ph.camera_z[2*i+1]);
  if((!ph.camera_present[s.owner]||ph.radio[2+s.owner]<6.0) && in.prepare[s.owner])s.prepare_latched=1;
  if(s.prepare_latched)++s.warmup;
  if(renew){for(int i=0;i<2;++i){Vec2 previous{s.a[2*i],s.a[2*i+1]}, raw{in.raw_action[2*i],in.raw_action[2*i+1]}, applied=project(previous,raw);if(norm({clipped(raw,3.0).x-previous.x,clipped(raw,3.0).y-previous.y})>1.5+1e-12){}s.a[2*i]=applied.x;s.a[2*i+1]=applied.y;}}

  // Reserve the unique owner's service packet before intent serialization.
  s.pending_relay_exists=0; if(s.source_exists[s.owner]){const int i=s.owner;s.pending_relay_exists=1;s.pending_relay_source_sequence=s.source_sequence[i];s.pending_relay_source_tick=s.source_tick[i];s.pending_relay_tick=s.tick;s.pending_relay_epoch=s.service_epoch;s.pending_relay_sequence=s.next_payload_sequence++;s.pending_relay_sender=i;std::memcpy(s.pending_relay_z,s.source_z+4*i,4*sizeof(double));s.pending_relay_first_margin=s.source_first_margin[i];s.pending_relay_second_margin=ph.radio[2+i];}
  const bool common_source=s.source_exists[0]&&s.source_exists[1]&&s.source_sequence[0]==s.source_sequence[1];
  bool emit_snapshot=s.prepare_latched&&!s.handover_used&&common_source&&(!s.snapshot_accepted||s.tick-s.snapshot_tick>=2||renew);
  if(emit_snapshot){s.pending_snapshot=1;s.pending_snapshot_sender=s.owner;s.pending_snapshot_sequence=s.source_sequence[0];s.pending_snapshot_tick=s.tick;s.pending_snapshot_margin=ph.radio[4+s.owner];s.lineage_lock[s.owner]=1;s.lineage_sequence[s.owner]=s.source_sequence[0];int cursor=0;for(int i=0;i<4;++i)s.pending_snapshot_payload[cursor++]=static_cast<float>(in.prediction_mean[i]);constexpr int upper[10]={0,1,2,3,5,6,7,10,11,15};for(const int index:upper)s.pending_snapshot_payload[cursor++]=static_cast<float>(in.prediction_covariance[index]);s.pending_snapshot_payload[cursor++]=static_cast<float>(ph.radio[2+s.owner]);s.pending_snapshot_payload[cursor++]=static_cast<float>(ph.radio[s.owner]);s.pending_snapshot_payload[cursor++]=static_cast<float>(in.raw_action[2*s.owner]);s.pending_snapshot_payload[cursor++]=static_cast<float>(in.raw_action[2*s.owner+1]);const auto wire=snapshot_wire(s,in);account_wire(s,wire);}
  if(s.snapshot_accepted&&!s.handover_used){s.pending_readiness=1;s.pending_readiness_tick=s.tick;s.pending_readiness_margin=ph.radio[4+(1-s.owner)];s.pending_readiness_candidate[0]=static_cast<float>(in.raw_action[2*(1-s.owner)]);s.pending_readiness_candidate[1]=static_cast<float>(in.raw_action[2*(1-s.owner)+1]);const auto wire=readiness_wire(s,in);account_wire(s,wire);}
  const bool version_ready=s.readiness_accepted&&s.readiness_tick==s.tick-1&&s.readiness_snapshot_tick==s.snapshot_tick;
  if(renew&&version_ready&&s.prepare_latched&&!s.handover_used&&in.commit[s.owner]){if(in.arm_mode==2){const auto wire=intent_wire(s,false);account_wire(s,wire);noop_intent_emitted=true;}else{s.pending_intent=1;s.intent_owner=s.owner;s.intent_epoch=s.service_epoch;s.intent_next_sequence=s.next_payload_sequence;s.intent_k_epoch=s.k_epoch;s.intent_certificate=native_origin_certificate(s,in,renew);s.intent_origin_tick=s.tick;s.intent_readiness_tick=s.readiness_tick;s.intent_snapshot_tick=s.tick;s.intent_alpha=std::isfinite(in.promotion_alpha)?std::clamp(in.promotion_alpha,0.0,1.0):1.0;s.pending_intent_margin=ph.radio[4+s.owner];const auto wire=intent_wire(s,true);account_wire(s,wire);}}

  const double gx=ph.gx,gy=ph.gy,gvx=ph.gvx,gvy=ph.gvy;s.pending_source_exists=1;s.pending_source_sequence=s.tick;s.pending_source_tick=s.tick;s.pending_source_z[0]=gx+ph.source_noise[0];s.pending_source_z[1]=gy+ph.source_noise[1];s.pending_source_z[2]=gvx+ph.source_noise[2];s.pending_source_z[3]=gvy+ph.source_noise[3];s.pending_source_margin[0]=ph.radio[0];s.pending_source_margin[1]=ph.radio[1];
  std::memcpy(s.last_radio_margin,ph.radio,sizeof(s.last_radio_margin));
  const auto source=source_wire(s.tick,s.tick,s.pending_source_z);account_wire(s,source);
  for(int sender=0;sender<2;++sender){const auto wire=state_wire(s,ph,sender);account_wire(s,wire);}
  if(s.pending_relay_exists){const auto wire=relay_wire(s,s.pending_relay_sender);account_wire(s,wire);}
  int service=0;if(s.base_exists){const double age=(s.tick-s.base_source_tick)*DT;const double hx=s.base_z[0]+age*s.base_z[2],hy=s.base_z[1]+age*s.base_z[3];service=age<=0.5&&std::hypot(hx-gx,hy-gy)<=8.0&&s.base_first_margin>=6.0&&s.base_second_margin>=6.0;}s.service_ticks+=service;

  std::uint64_t tx_bytes[2]={64,64};if(s.pending_relay_exists)tx_bytes[s.pending_relay_sender]+=64;if(emit_snapshot)tx_bytes[s.owner]+=96;if(s.pending_readiness)tx_bytes[1-s.owner]+=48;if(s.pending_intent)tx_bytes[s.intent_owner]+=32;if(noop_intent_emitted)tx_bytes[s.owner]+=32;if(s.application_reason||s.cas_applied)tx_bytes[s.owner]+=24;
  for(int i=0;i<2;++i){const int p=2*i;const double power=650+1.5*(sq(s.v[p])+sq(s.v[p+1]))+12*(sq(s.a[p])+sq(s.a[p+1]));const double byte_energy=0.02*tx_bytes[i];const double energy=DT*power+byte_energy;s.total_energy+=energy;s.battery[i]=std::max(0.0,s.battery[i]-energy);s.p[p]+=DT*s.v[p];s.p[p+1]+=DT*s.v[p+1];s.v[p]+=DT*(s.a[p]+s.wind[0]);s.v[p+1]+=DT*(s.a[p+1]+s.wind[1]);Vec2 vv=clipped({s.v[p],s.v[p+1]},18);s.v[p]=vv.x;s.v[p+1]=vv.y;}
  s.wind[0]=std::clamp(0.95*s.wind[0]+0.05*ph.wind_eta[0],-1.5,1.5);s.wind[1]=std::clamp(0.95*s.wind[1]+0.05*ph.wind_eta[1],-1.5,1.5);
  const double sep=separation(s);s.min_separation=std::min(s.min_separation,sep);if(sep<15.0){++s.separation_breach;s.terminal=1;}
  if(renew)s.countdown=s.k_active-1;else --s.countdown;
  for(int i=0;i<2;++i)for(int c=0;c<2;++c)actor_row(s,ph,i,c,renew,out.actor+(i*2+c)*54);critic_row(s,ph,renew,out.critic);
  if(s.tick==TICKS-1)s.terminal=1;
  ++s.tick;out.service=service;out.renew=renew;out.terminal=s.terminal;out.owner=s.owner;out.service_epoch=s.service_epoch;out.next_payload_sequence=s.next_payload_sequence;out.handover_used=s.handover_used;out.invalid_commit=s.invalid_commit;out.token_gap=s.token_gap;out.dual_owner=s.dual_owner;out.dual_payload=s.dual_payload;out.buffer_clear=s.buffer_clear;out.command_slew_breach=s.command_slew_breach;out.separation_breach=s.separation_breach;out.tick=s.tick;out.protocol_bytes=s.protocol_bytes;out.min_separation=s.min_separation;out.total_energy=s.total_energy;out.snapshot_accepted=s.snapshot_accepted;out.readiness_accepted=s.readiness_accepted;out.application_reason=s.application_reason;out.cas_applied=s.cas_applied;out.actuator_owner=s.actuator_owner;out.protocol_wire_hash=s.protocol_wire_hash;out.protocol_wire_messages=s.protocol_wire_messages;std::memcpy(out.snapshot_payload,s.accepted_snapshot_payload,sizeof(out.snapshot_payload));std::memcpy(out.readiness_candidate,s.accepted_readiness_candidate,sizeof(out.readiness_candidate));out.snapshot_delivery_mask=snapshot_delivered_this_tick;out.readiness_delivery_mask=readiness_delivered_this_tick;out.version_match=s.readiness_accepted&&s.snapshot_accepted&&s.readiness_snapshot_tick==s.snapshot_tick;return 0;
}

inline bool first_application_valid(const HostState& s,const StepInput& in){
  if(!s.initialized||!s.pending_intent||s.pending_intent_margin<6.0)return false;
  if(!s.intent_certificate||s.handover_used)return false;
  const int readiness_tick=s.intent_readiness_tick==0&&s.intent_origin_tick>0?s.readiness_tick:s.intent_readiness_tick;
  const int snapshot_tick=s.intent_snapshot_tick==0&&s.intent_origin_tick>0?s.snapshot_tick:s.intent_snapshot_tick;
  if(s.intent_origin_tick+1!=s.tick||readiness_tick!=s.intent_origin_tick-1||snapshot_tick!=s.intent_origin_tick||s.snapshot_tick!=s.intent_origin_tick)return false;
  if(s.owner!=s.intent_owner||s.service_epoch!=s.intent_epoch||s.next_payload_sequence!=s.intent_next_sequence)return false;
  if(!s.source_exists[0]||!s.source_exists[1]||s.source_sequence[0]!=s.source_sequence[1]||s.k_epoch!=s.intent_k_epoch)return false;
  if(s.terminal||s.battery[0]<=0||s.battery[1]<=0)return false;
  if(separation(s)<15.0||std::hypot((s.p[0]+DT*s.v[0])-(s.p[2]+DT*s.v[2]),(s.p[1]+DT*s.v[1])-(s.p[3]+DT*s.v[3]))<15.0)return false;
  for(int i=0;i<2;++i){const Vec2 bounded=clipped({in.raw_action[2*i],in.raw_action[2*i+1]},3.0);if(norm({bounded.x-s.a[2*i],bounded.y-s.a[2*i+1]})>1.5+1e-12)return false;}
  return true;
}

inline int passive_labels_one(const HostState& source,const StepInput& input,PassiveLabelOutput& out){
  std::memset(&out,0,sizeof(out));if(!source.initialized)return 1;
  HostState future=source;StepOutput next{};const int next_rc=step_one(future,input,next);if(next_rc)return next_rc;
  const PhysicsTick next_ph=physics_tick(future);
  out.target[0]=next_ph.gx;out.target[1]=next_ph.gy;out.target[2]=next_ph.gvx;out.target[3]=next_ph.gvy;
  for(int vehicle=0;vehicle<2;++vehicle)for(int copy=0;copy<2;++copy){const int index=2*vehicle+copy;out.links[2*index]=next_ph.radio[vehicle];out.links[2*index+1]=next_ph.radio[2+vehicle];out.missing[index]=next_ph.camera_present[vehicle]?0:1;}
  out.next_mask=source.tick<=1198&&!future.terminal;
  const int standby=1-source.owner;out.q_copy_index=2*standby+1;
  const bool eligible=source.tick+2<=1199&&!source.terminal&&!source.handover_used&&source.battery[0]>0&&source.battery[1]>0&&source.source_exists[0]&&source.source_exists[1]&&source.source_sequence[0]==source.source_sequence[1]&&source.snapshot_accepted&&source.readiness_accepted&&source.readiness_snapshot_tick==source.snapshot_tick&&separation(source)>=15.0;
  if(!eligible)return 0;
  HostState clone=source;StepInput held=input;held.prepare[0]=held.prepare[1]=held.commit[0]=held.commit[1]=0;for(int i=0;i<4;++i)held.raw_action[i]=source.a[i];held.arm_mode=0;StepOutput transient{};
  for(int delay=0;delay<2;++delay){const int rc=step_one(clone,held,transient);if(rc)return rc;}
  const int old_owner=clone.owner,new_owner=1-old_owner;promote_recurrent_state(clone,old_owner,1.0);clone.owner=new_owner;++clone.service_epoch;clone.handover_used=1;
  held.raw_action[2*new_owner]=source.accepted_readiness_candidate[0];held.raw_action[2*new_owner+1]=source.accepted_readiness_candidate[1];
  for(int horizon=0;horizon<20;++horizon){if(clone.tick>=TICKS||clone.terminal){out.q_labels[horizon]=0;continue;}const int rc=step_one(clone,held,transient);if(rc)return rc;out.q_labels[horizon]=transient.service?1:0;}
  out.q_mask=1;return 0;
}

inline ScriptOutput script_one(const HostState& s) {
  constexpr double u[5][2]={{0,0},{3,0},{-3,0},{0,3},{0,-3}}; ScriptOutput best{};best.score=-1e300;int best_retain=0,best_i=0,best_j=0;
  double gx,gy,gvx,gvy;route(s,s.tick,gx,gy,gvx,gvy);
  for(int transfer=0;transfer<=1;++transfer)for(int i=0;i<5;++i)for(int j=0;j<5;++j){double score=0,energy=0;for(int v=0;v<2;++v){int q=v?j:i;Vec2 a=project({s.a[2*v],s.a[2*v+1]},{u[q][0],u[q][1]});double px=s.p[2*v]+2.0*s.v[2*v]+2.0*a.x,py=s.p[2*v+1]+2.0*s.v[2*v+1]+2.0*a.y;score-=std::hypot(px-(gx+2.0*gvx),py-(gy+2.0*gvy));energy+=sq(a.x)+sq(a.y);}score-=0.01*energy; if(transfer && s.handover_used)continue; const bool better=score>best.score || (score==best.score && (transfer<best_retain || (transfer==best_retain&&(i<best_i||(i==best_i&&j<best_j)))));if(better){best.score=score;best.transfer=transfer;best.raw_action[0]=u[i][0];best.raw_action[1]=u[i][1];best.raw_action[2]=u[j][0];best.raw_action[3]=u[j][1];best_retain=transfer;best_i=i;best_j=j;}}
  return best;
}

inline void advantage_script_input(const HostState& s, StepInput& in) {
  std::memset(&in,0,sizeof(in));
  for(int d=0;d<4;++d) in.prediction_covariance[d*4+d]=4.0;
  for(double& q:in.service_q) q=0.8;
  double gx,gy,gvx,gvy; route(s,s.tick,gx,gy,gvx,gvy);
  const Vec2 base{-600.0,0.0};
  for(int vehicle=0;vehicle<2;++vehicle){
    const bool owner=s.owner==vehicle;
    const Vec2 desired=owner ? Vec2{gx-40.0,gy} : Vec2{0.5*(gx+base.x),0.5*(gy+base.y)+60.0*s.reflection};
    const Vec2 raw{0.08*(desired.x-s.p[2*vehicle])-0.60*s.v[2*vehicle],
                   0.08*(desired.y-s.p[2*vehicle+1])-0.60*s.v[2*vehicle+1]};
    in.raw_action[2*vehicle]=raw.x; in.raw_action[2*vehicle+1]=raw.y;
  }
}

inline std::int32_t scripted_origin_rejection(const HostState& s, const StepInput& in) {
  std::int32_t rejected=0;
  if(s.terminal || s.handover_used) rejected|=1;
  if(s.countdown!=0) rejected|=2;
  if(!s.source_exists[0] || !s.source_exists[1] || s.source_sequence[0]!=s.source_sequence[1]) rejected|=4;
  if(!s.base_exists) rejected|=8;
  if(s.battery[0]<=1000.0 || s.battery[1]<=1000.0) rejected|=16;
  const int application_tick=s.tick+1;
  if(application_tick<s.tau_d_tick || application_tick>=s.tau_d_tick+150) rejected|=32;
  double gx,gy,gvx,gvy; route(s,s.tick,gx,gy,gvx,gvy);
  const int standby=1-s.owner;
  if(std::hypot(s.p[2*standby]-gx,s.p[2*standby+1]-gy)>350.0) rejected|=64;
  if(std::hypot(s.p[2*standby]+600.0,s.p[2*standby+1])>500.0) rejected|=128;
  Vec2 projected[2];
  for(int vehicle=0;vehicle<2;++vehicle)
    projected[vehicle]=project({s.a[2*vehicle],s.a[2*vehicle+1]},
                               {in.raw_action[2*vehicle],in.raw_action[2*vehicle+1]});
  const Vec2 p0{s.p[0]+DT*s.v[0],s.p[1]+DT*s.v[1]};
  const Vec2 p1{s.p[2]+DT*s.v[2],s.p[3]+DT*s.v[3]};
  if(std::hypot(p0.x-p1.x,p0.y-p1.y)<15.0) rejected|=256;
  // P_n is the registered norm/slew projection.  The application predicate
  // binds its projected command, so a finite projected pair already satisfies
  // the one-step held-action slew contract by construction.
  for(const Vec2 value:projected)
    if(!std::isfinite(value.x) || !std::isfinite(value.y)) rejected|=512;
  return rejected;
}

inline int recovery_witness_one(const ResetInput& reset, RecoveryWitnessOutput& result) {
  std::memset(&result,0,sizeof(result));result.origin_tick=-1;
  HostState base{};StepOutput output{};reset_one(reset,base,output);StepInput in{};
  while(base.tick<TICKS){
    advantage_script_input(base,in);const int rejection=scripted_origin_rejection(base,in);const int application_tick=base.tick+1;
    if(base.countdown==0&&application_tick>=base.tau_d_tick&&application_tick<base.tau_d_tick+150){++result.opportunities_checked;result.rejection_mask|=rejection;}
    if(rejection==0){
      result.origin_exists=1;result.origin_tick=base.tick;HostState real=base,retain=base;StepOutput real_out{},retain_out{};
      int rc=step_one(real,in,real_out);if(rc)return rc;rc=step_one(retain,in,retain_out);if(rc)return rc;
      for(int j=0;j<50;++j){StepInput real_in{},retain_in{};advantage_script_input(real,real_in);advantage_script_input(retain,retain_in);rc=step_one(real,real_in,real_out,j==0);if(rc)return rc;rc=step_one(retain,retain_in,retain_out,false);if(rc)return rc;result.real_service_ticks+=real_out.service;result.retain_service_ticks+=retain_out.service;}
      return 0;
    }
    const int rc=step_one(base,in,output);if(rc)return rc;
  }
  return 0;
}

} // namespace

DISH_EXPORT std::int32_t dish_rbhr_r06_prod_abi_version(){return ABI_VERSION;}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_reset_input_size(){return sizeof(ResetInput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_step_input_size(){return sizeof(StepInput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_state_size(){return sizeof(HostState);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_step_output_size(){return sizeof(StepOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_fork_output_size(){return sizeof(ForkOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_passive_label_output_size(){return sizeof(PassiveLabelOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_script_output_size(){return sizeof(ScriptOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_recovery_witness_output_size(){return sizeof(RecoveryWitnessOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_protocol_audit_output_size(){return sizeof(ProtocolAuditOutput);}
DISH_EXPORT std::uint64_t dish_rbhr_r06_prod_protocol_transition_output_size(){return sizeof(ProtocolTransitionOutput);}

DISH_EXPORT std::int32_t dish_rbhr_r06_prod_reset_batch(const ResetInput* in,std::uint64_t count,HostState* state,StepOutput* out){if(!in||!state||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i){if(!validate_reset(in[i]))return 2;reset_one(in[i],state[i],out[i]);}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_reset_selected_batch(const ResetInput* in,const std::int32_t* selected,std::uint64_t count,HostState* state,StepOutput* out){if(!in||!selected||!state||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i)if(selected[i]){if(!validate_reset(in[i]))return 2;reset_one(in[i],state[i],out[i]);}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_step_batch(HostState* state,const StepInput* in,std::uint64_t count,StepOutput* out){if(!in||!state||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i){const int rc=step_one(state[i],in[i],out[i]);if(rc)return rc;}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_rollout_batch(HostState* state,const StepInput* in,std::uint64_t steps,std::uint64_t count,StepOutput* out){if(!in||!state||!out||count==0||steps==0)return 1;for(std::uint64_t t=0;t<steps;++t)for(std::uint64_t i=0;i<count;++i){const int rc=step_one(state[i],in[t*count+i],out[t*count+i]);if(rc)return rc;}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_passive_labels_batch(const HostState* state,const StepInput* in,std::uint64_t count,PassiveLabelOutput* out){if(!in||!state||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i){const int rc=passive_labels_one(state[i],in[i],out[i]);if(rc)return rc;}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_first_application_valid_batch(const HostState* state,const StepInput* in,std::uint64_t count,std::int32_t* out){if(!in||!state||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i)out[i]=first_application_valid(state[i],in[i])?1:0;return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_clone_real_sham_batch(const HostState* state,std::uint64_t count,ForkOutput* out){if(!state||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i){if(!state[i].initialized||state[i].handover_used||!state[i].pending_intent)return 2;out[i].real_state=state[i];out[i].sham_state=state[i];const int old_owner=state[i].owner,promoted=1-old_owner;promote_recurrent_state(out[i].real_state,old_owner,1.0);out[i].real_state.owner=promoted;++out[i].real_state.service_epoch;out[i].real_state.handover_used=1;++out[i].sham_state.service_epoch;out[i].sham_state.handover_used=1;out[i].sham_state.actuator_owner=old_owner;for(HostState* branch:{&out[i].real_state,&out[i].sham_state}){branch->pending_intent=0;branch->lineage_lock[0]=branch->lineage_lock[1]=0;branch->application_reason=0;branch->cas_applied=0;branch->total_energy+=0.48;branch->battery[old_owner]=std::max(0.0,branch->battery[old_owner]-0.48);}const auto wire=result_wire(state[i].tick,1,0,promoted,static_cast<std::uint16_t>(state[i].service_epoch+1),state[i].next_payload_sequence,state[i].k_epoch);account_wire(out[i].real_state,wire);account_wire(out[i].sham_state,wire);Sha256 real_sha;real_sha.update(wire.data(),wire.size());const auto real_digest=real_sha.final();std::memcpy(out[i].real_telemetry_sha256,real_digest.data(),32);std::memcpy(out[i].sham_telemetry_sha256,real_digest.data(),32);out[i].byte_identical_telemetry=1;}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_script_batch(const HostState* state,std::uint64_t count,ScriptOutput* out){if(!state||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i){if(!state[i].initialized)return 2;out[i]=script_one(state[i]);}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_recovery_witness_batch(const ResetInput* in,std::uint64_t count,RecoveryWitnessOutput* out){if(!in||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i){if(!validate_reset(in[i]))return 2;const int rc=recovery_witness_one(in[i],out[i]);if(rc)return rc;}return 0;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_protocol_audit(ProtocolAuditOutput* out){if(!out)return 1;std::memset(out,0,sizeof(*out));HostState s{};s.owner=1;s.service_epoch=2;s.next_payload_sequence=11;s.k_epoch=3;s.tick=9;s.source_exists[0]=s.source_exists[1]=1;s.source_sequence[0]=s.source_sequence[1]=7;s.source_tick[0]=s.source_tick[1]=9;s.pending_relay_sequence=10;s.snapshot_tick=9;s.readiness_tick=10;s.intent_origin_tick=11;s.intent_owner=1;s.intent_epoch=2;s.intent_next_sequence=11;s.intent_k_epoch=3;s.intent_certificate=1;for(int i=0;i<8;++i)s.source_z[i]=(i%4)+1;StepInput in{};for(int i=0;i<20;++i)in.service_q[i]=0.8;for(int i=0;i<8;++i)in.prediction_mean[i]=i+1;for(int i=0;i<10;++i)in.prediction_covariance[i]=i;PhysicsTick ph{};for(double& value:ph.radio)value=8.0;const auto source=source_wire(7,9,s.source_z);const auto relay=relay_wire(s,1);const auto state=state_wire(s,ph,1);const auto snapshot=snapshot_wire(s,in);const auto readiness=readiness_wire(s,in);const auto intent=intent_wire(s,true);const auto noop=intent_wire(s,false);const auto result=result_wire(12,1,0,0,3,11,3);out->sizes[0]=source.size();out->sizes[1]=relay.size();out->sizes[2]=state.size();out->sizes[3]=snapshot.size();out->sizes[4]=readiness.size();out->sizes[5]=intent.size();out->sizes[6]=noop.size();out->sizes[7]=result.size();const bool verified=verify_wire(source,24)&&verify_wire(relay,55)&&verify_wire(state,49)&&verify_wire(snapshot,89)&&verify_wire(readiness,42)&&verify_wire(intent,24)&&verify_wire(noop,24)&&verify_wire(result,15);auto bad=source;bad[0]^=1;const bool tamper=!verify_wire(bad,24);Sha256 sha;sha.update(source.data(),source.size());sha.update(relay.data(),relay.size());sha.update(state.data(),state.size());sha.update(snapshot.data(),snapshot.size());sha.update(readiness.data(),readiness.size());sha.update(intent.data(),intent.size());sha.update(noop.data(),noop.size());sha.update(result.data(),result.size());const auto digest=sha.final();std::memcpy(out->aggregate_sha256,digest.data(),32);out->message_count=8;out->all_integrity_verified=verified;out->all_tamper_rejected=tamper;return verified&&tamper?0:2;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_protocol_transition_probe(ProtocolTransitionOutput* out){if(!out)return 1;std::memset(out,0,sizeof(*out));ResetInput reset{};reset.fixture_key=1;reset.test_mode=1;reset.package=0;reset.reflection=1;reset.initial_owner=0;reset.k_initial=4;reset.k_new=4;reset.switch_tick=500;reset.tau_d_tick=420;reset.phase=0;reset.route_speed=4;reset.turn_magnitude_deg=25;reset.turn_sign=1;reset.initial_ux=40;reset.initial_uy=120;HostState s{};StepOutput initial{};reset_one(reset,s,initial);s.tick=100;s.countdown=0;s.source_exists[0]=s.source_exists[1]=1;s.source_sequence[0]=s.source_sequence[1]=7;s.source_tick[0]=s.source_tick[1]=99;s.base_exists=1;s.base_source_sequence=7;s.base_source_tick=99;s.lineage_lock[0]=s.lineage_lock[1]=1;s.lineage_sequence[0]=s.lineage_sequence[1]=7;s.pending_source_exists=1;s.pending_source_sequence=8;s.pending_source_tick=99;s.pending_source_margin[0]=s.pending_source_margin[1]=12.0;s.prepare_latched=1;s.warmup=12;s.snapshot_accepted=1;s.snapshot_tick=99;s.readiness_accepted=1;s.readiness_tick=98;s.readiness_snapshot_tick=99;s.pending_intent=1;s.pending_intent_margin=12.0;s.intent_owner=0;s.intent_epoch=0;s.intent_next_sequence=0;s.intent_k_epoch=0;s.intent_certificate=1;s.intent_origin_tick=99;s.intent_alpha=0.25;StepInput in{};for(int d=0;d<4;++d)in.prediction_covariance[d*4+d]=4.0;for(double& q:in.service_q)q=0.8;in.promotion_alpha=0.25;for(int j=0;j<128;++j){in.controller_hidden[j]=0.8;in.controller_hidden[3*128+j]=-0.4;}StepOutput step{};out->owner_before=s.owner;const int rc=step_one(s,in,step);if(rc)return rc;out->source_lineage_preserved=s.source_sequence[0]==7&&s.source_sequence[1]==7;out->locks_released=!s.lineage_lock[0]&&!s.lineage_lock[1];out->cas_applied=step.cas_applied;out->application_reason=step.application_reason;out->owner_after=s.owner;out->service_epoch_after=s.service_epoch;out->actuator_owner_after=s.actuator_owner;bool recurrent=true;for(int j=0;j<128;++j)if(std::abs(s.controller_hidden[2*128+j]-0.5)>1e-12){recurrent=false;break;}out->recurrent_promotion_verified=recurrent;out->protocol_wire_hash=s.protocol_wire_hash;out->protocol_wire_messages=s.protocol_wire_messages;return out->source_lineage_preserved&&out->locks_released&&out->cas_applied&&out->application_reason==0&&out->owner_after==1&&out->service_epoch_after==1&&out->actuator_owner_after==1&&out->recurrent_promotion_verified?0:2;}
DISH_EXPORT std::int32_t dish_rbhr_r06_prod_rng_words_batch(const std::uint8_t* master,const char* blob,const std::uint64_t* offsets,const std::uint64_t* lengths,std::uint64_t count,std::uint64_t* out){if(!master||!blob||!offsets||!lengths||!out||count==0)return 1;for(std::uint64_t i=0;i<count;++i){if(lengths[i]==0||lengths[i]>4096)return 2;out[i]=rng_word(master,blob+offsets[i],static_cast<std::size_t>(lengths[i]));}return 0;}
