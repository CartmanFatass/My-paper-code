#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <tuple>
#include <vector>

#ifdef _WIN32
#define VQFP_EXPORT extern "C" __declspec(dllexport)
#else
#define VQFP_EXPORT extern "C"
#endif

namespace {
// A deliberately small, vendor-free signed arbitrary-width integer.  The
// representation is sign/magnitude with little-endian base-2^32 limbs.  It is
// used only behind Rat; no narrowing conversion participates in a normative
// comparison.  Division is binary long division: slower than a specialized
// library, but simple enough to audit and exact for every operand width.
class cpp_int {
 public:
  cpp_int() = default;
  cpp_int(int value) : cpp_int(int64_t(value)) {}
  cpp_int(int64_t value) {
    uint64_t magnitude;
    if (value < 0) {
      negative_ = true;
      magnitude = uint64_t(-(value + 1));
      ++magnitude;
    } else {
      magnitude = uint64_t(value);
    }
    if (magnitude) {
      limbs_.push_back(uint32_t(magnitude));
      if (magnitude >> 32) limbs_.push_back(uint32_t(magnitude >> 32));
    }
    normalize();
  }
  explicit cpp_int(const std::string& decimal) { parse(decimal); }

  bool is_zero() const { return limbs_.empty(); }
  bool negative() const { return negative_; }
  int to_int_checked() const {
    if (limbs_.size() > 1 || (!limbs_.empty() && limbs_[0] > uint32_t(std::numeric_limits<int>::max())))
      throw std::overflow_error("arbitrary integer does not fit int");
    int value = limbs_.empty() ? 0 : int(limbs_[0]);
    return negative_ ? -value : value;
  }

  std::string str() const {
    if (is_zero()) return "0";
    cpp_int work = abs(*this);
    std::vector<uint32_t> chunks;
    while (!work.is_zero()) chunks.push_back(work.div_small(1000000000u));
    std::ostringstream out;
    if (negative_) out << '-';
    out << chunks.back();
    for (size_t i = chunks.size() - 1; i-- > 0;)
      out << std::setw(9) << std::setfill('0') << chunks[i];
    return out.str();
  }

  friend cpp_int abs(const cpp_int& value) {
    cpp_int out = value;
    out.negative_ = false;
    return out;
  }
  friend cpp_int operator-(const cpp_int& value) {
    cpp_int out = value;
    if (!out.is_zero()) out.negative_ = !out.negative_;
    return out;
  }
  friend bool operator==(const cpp_int& a, const cpp_int& b) {
    return a.negative_ == b.negative_ && a.limbs_ == b.limbs_;
  }
  friend bool operator!=(const cpp_int& a, const cpp_int& b) { return !(a == b); }
  friend bool operator<(const cpp_int& a, const cpp_int& b) {
    if (a.negative_ != b.negative_) return a.negative_;
    int cmp = compare_abs(a, b);
    return a.negative_ ? cmp > 0 : cmp < 0;
  }
  friend bool operator>(const cpp_int& a, const cpp_int& b) { return b < a; }
  friend bool operator<=(const cpp_int& a, const cpp_int& b) { return !(b < a); }
  friend bool operator>=(const cpp_int& a, const cpp_int& b) { return !(a < b); }

  friend cpp_int operator+(const cpp_int& a, const cpp_int& b) {
    if (a.negative_ == b.negative_) {
      cpp_int out = add_abs(a, b);
      out.negative_ = a.negative_ && !out.is_zero();
      return out;
    }
    int cmp = compare_abs(a, b);
    if (cmp == 0) return {};
    cpp_int out = cmp > 0 ? sub_abs(a, b) : sub_abs(b, a);
    out.negative_ = cmp > 0 ? a.negative_ : b.negative_;
    return out;
  }
  friend cpp_int operator-(const cpp_int& a, const cpp_int& b) { return a + (-b); }
  friend cpp_int operator*(const cpp_int& a, const cpp_int& b) {
    cpp_int out;
    if (a.is_zero() || b.is_zero()) return out;
    out.limbs_.assign(a.limbs_.size() + b.limbs_.size(), 0);
    for (size_t i = 0; i < a.limbs_.size(); ++i) {
      uint64_t carry = 0;
      for (size_t j = 0; j < b.limbs_.size(); ++j) {
        uint64_t value = uint64_t(a.limbs_[i]) * b.limbs_[j] +
                         out.limbs_[i + j] + carry;
        out.limbs_[i + j] = uint32_t(value);
        carry = value >> 32;
      }
      size_t k = i + b.limbs_.size();
      while (carry) {
        uint64_t value = uint64_t(out.limbs_[k]) + carry;
        out.limbs_[k] = uint32_t(value);
        carry = value >> 32;
        ++k;
        if (k == out.limbs_.size() && carry) out.limbs_.push_back(0);
      }
    }
    out.negative_ = a.negative_ != b.negative_;
    out.normalize();
    return out;
  }
  friend cpp_int operator/(const cpp_int& a, const cpp_int& b) {
    return divmod(a, b).first;
  }
  friend cpp_int operator%(const cpp_int& a, const cpp_int& b) {
    return divmod(a, b).second;
  }
  cpp_int& operator+=(const cpp_int& value) { return *this = *this + value; }
  cpp_int& operator-=(const cpp_int& value) { return *this = *this - value; }
  cpp_int& operator*=(const cpp_int& value) { return *this = *this * value; }
  cpp_int& operator/=(const cpp_int& value) { return *this = *this / value; }
  bool magnitude_u64(uint64_t& value) const {
    if (limbs_.size() > 2) return false;
    value = limbs_.empty() ? 0 : limbs_[0];
    if (limbs_.size() == 2) value |= uint64_t(limbs_[1]) << 32;
    return true;
  }
  size_t public_bit_length() const { return bit_length(); }

 private:
  std::vector<uint32_t> limbs_;
  bool negative_ = false;

  void normalize() {
    while (!limbs_.empty() && limbs_.back() == 0) limbs_.pop_back();
    if (limbs_.empty()) negative_ = false;
  }
  static int compare_abs(const cpp_int& a, const cpp_int& b) {
    if (a.limbs_.size() != b.limbs_.size())
      return a.limbs_.size() < b.limbs_.size() ? -1 : 1;
    for (size_t i = a.limbs_.size(); i-- > 0;) {
      if (a.limbs_[i] != b.limbs_[i]) return a.limbs_[i] < b.limbs_[i] ? -1 : 1;
    }
    return 0;
  }
  static cpp_int add_abs(const cpp_int& a, const cpp_int& b) {
    cpp_int out;
    size_t size = std::max(a.limbs_.size(), b.limbs_.size());
    out.limbs_.resize(size);
    uint64_t carry = 0;
    for (size_t i = 0; i < size; ++i) {
      uint64_t av = i < a.limbs_.size() ? a.limbs_[i] : 0;
      uint64_t bv = i < b.limbs_.size() ? b.limbs_[i] : 0;
      uint64_t value = av + bv + carry;
      out.limbs_[i] = uint32_t(value);
      carry = value >> 32;
    }
    if (carry) out.limbs_.push_back(uint32_t(carry));
    return out;
  }
  static cpp_int sub_abs(const cpp_int& larger, const cpp_int& smaller) {
    cpp_int out;
    out.limbs_.resize(larger.limbs_.size());
    uint64_t borrow = 0;
    for (size_t i = 0; i < larger.limbs_.size(); ++i) {
      uint64_t av = larger.limbs_[i];
      uint64_t bv = (i < smaller.limbs_.size() ? smaller.limbs_[i] : 0) + borrow;
      out.limbs_[i] = uint32_t(av - bv);
      borrow = av < bv;
    }
    out.normalize();
    return out;
  }
  size_t bit_length() const {
    if (is_zero()) return 0;
    uint32_t high = limbs_.back();
    size_t bits = 32 * (limbs_.size() - 1);
    while (high) { ++bits; high >>= 1; }
    return bits;
  }
  bool bit(size_t index) const {
    size_t limb = index / 32;
    return limb < limbs_.size() && ((limbs_[limb] >> (index % 32)) & 1u);
  }
  void set_bit(size_t index) {
    size_t limb = index / 32;
    if (limbs_.size() <= limb) limbs_.resize(limb + 1);
    limbs_[limb] |= uint32_t(1u << (index % 32));
  }
  void shift_left_one() {
    uint64_t carry = 0;
    for (uint32_t& limb : limbs_) {
      uint64_t value = (uint64_t(limb) << 1) | carry;
      limb = uint32_t(value);
      carry = value >> 32;
    }
    if (carry) limbs_.push_back(uint32_t(carry));
  }
  static std::pair<cpp_int, cpp_int> divmod(const cpp_int& dividend,
                                            const cpp_int& divisor) {
    if (divisor.is_zero()) throw std::domain_error("integer division by zero");
    cpp_int numerator = abs(dividend), denominator = abs(divisor), quotient, remainder;
    uint64_t numerator_u64=0,denominator_u64=0;
    if(numerator.magnitude_u64(numerator_u64)&&denominator.magnitude_u64(denominator_u64)){
      quotient=from_u64(numerator_u64/denominator_u64);
      remainder=from_u64(numerator_u64%denominator_u64);
      quotient.negative_=(dividend.negative_!=divisor.negative_)&&!quotient.is_zero();
      remainder.negative_=dividend.negative_&&!remainder.is_zero();
      return {quotient,remainder};
    }
    if (compare_abs(numerator, denominator) >= 0) {
      for (size_t bit_index = numerator.bit_length(); bit_index-- > 0;) {
        remainder.shift_left_one();
        if (numerator.bit(bit_index)) remainder = remainder + cpp_int(1);
        if (compare_abs(remainder, denominator) >= 0) {
          remainder = sub_abs(remainder, denominator);
          quotient.set_bit(bit_index);
        }
      }
    } else {
      remainder = numerator;
    }
    quotient.negative_ = (dividend.negative_ != divisor.negative_) && !quotient.is_zero();
    remainder.negative_ = dividend.negative_ && !remainder.is_zero();
    quotient.normalize(); remainder.normalize();
    return {quotient, remainder};
  }
  static cpp_int from_u64(uint64_t value) {
    cpp_int out;
    if(value){out.limbs_.push_back(uint32_t(value));if(value>>32)out.limbs_.push_back(uint32_t(value>>32));}
    return out;
  }
  void mul_small(uint32_t value) { *this = *this * cpp_int(int64_t(value)); }
  void add_small(uint32_t value) { *this += cpp_int(int64_t(value)); }
  uint32_t div_small(uint32_t divisor) {
    uint64_t remainder = 0;
    for (size_t i = limbs_.size(); i-- > 0;) {
      uint64_t value = (remainder << 32) | limbs_[i];
      limbs_[i] = uint32_t(value / divisor);
      remainder = value % divisor;
    }
    normalize();
    return uint32_t(remainder);
  }
  void parse(const std::string& decimal) {
    if (decimal.empty()) throw std::invalid_argument("empty integer");
    size_t index = 0;
    bool requested_negative = false;
    if (decimal[index] == '-' || decimal[index] == '+') {
      requested_negative = decimal[index] == '-';
      if (++index == decimal.size()) throw std::invalid_argument("sign-only integer");
    }
    for (; index < decimal.size(); ++index) {
      char ch = decimal[index];
      if (ch < '0' || ch > '9') throw std::invalid_argument("non-decimal integer");
      mul_small(10); add_small(uint32_t(ch - '0'));
    }
    negative_ = requested_negative && !is_zero();
  }
};

constexpr uint32_t M0=0xD2511F53u, M1=0xCD9E8D57u;
constexpr uint32_t W0=0x9E3779B9u, W1=0xBB67AE85u;
constexpr uint64_t MAX_REJECTION_RHO=(uint64_t(1)<<34)-1;
constexpr int ABI=3;
constexpr const char* REV="VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-03";
constexpr const char* CARD_SHA256="df9bd52df6c873e79c315b1d134019df8721d5ec73b4b6a5566be1663305626e";

cpp_int abs_i(const cpp_int& x) { return abs(x); }
cpp_int gcd_i(cpp_int a, cpp_int b) {
  a=abs_i(a); b=abs_i(b);
  while (b != cpp_int(0)) { cpp_int r=a%b; a=b; b=r; }
  return a;
}
struct Rat {
  cpp_int n, d;
  Rat(cpp_int nn=0, cpp_int dd=1):n(nn),d(dd) {
    if (d==cpp_int(0)) throw std::domain_error("zero denominator");
    if (d<cpp_int(0)) { n=-n; d=-d; }
    cpp_int g=gcd_i(n,d); if(g!=cpp_int(0)){n/=g;d/=g;}
  }
  std::string s() const { return n.str()+"/"+d.str(); }
  bool fixed64_eligible() const { uint64_t a=0,b=0; return n.magnitude_u64(a)&&d.magnitude_u64(b); }
  size_t max_bits() const { return std::max(n.public_bit_length(),d.public_bit_length()); }
};
enum class StageKernel:uint32_t{Host=0,Controls=1,Candidate=2,Reducer=3,Count=4};
struct StageKernelStats {
  uint64_t operations=0,operands=0,fixed_hits=0,slow_paths=0,max_bits=0;
  std::array<uint64_t,5> bit_bands{};
};
struct StageStats { std::array<StageKernelStats,size_t(StageKernel::Count)> kernel{}; };
thread_local StageStats* active_stage_stats=nullptr;
thread_local StageKernel active_stage_kernel=StageKernel::Host;
struct StageScope {
  StageStats* prior_stats;StageKernel prior_kernel;
  StageScope(StageStats&stats,StageKernel kernel):prior_stats(active_stage_stats),prior_kernel(active_stage_kernel){active_stage_stats=&stats;active_stage_kernel=kernel;}
  ~StageScope(){active_stage_stats=prior_stats;active_stage_kernel=prior_kernel;}
};
void stage_observe_bits(StageKernelStats&stats,size_t bits,bool fixed){
  ++stats.operands;stats.max_bits=std::max<uint64_t>(stats.max_bits,bits);
  size_t band=bits<=32?0:bits<=64?1:bits<=128?2:bits<=256?3:4;++stats.bit_bands[band];
  if(fixed)++stats.fixed_hits;else ++stats.slow_paths;
}
void stage_observe_rat_operation(const Rat&a,const Rat&b){
  if(!active_stage_stats)return;auto&stats=active_stage_stats->kernel[size_t(active_stage_kernel)];++stats.operations;
  stage_observe_bits(stats,a.max_bits(),a.fixed64_eligible());stage_observe_bits(stats,b.max_bits(),b.fixed64_eligible());
}
void stage_observe_int_operation(const cpp_int&a,const cpp_int&b){
  if(!active_stage_stats)return;auto&stats=active_stage_stats->kernel[size_t(active_stage_kernel)];++stats.operations;
  uint64_t ignored=0;stage_observe_bits(stats,a.public_bit_length(),a.magnitude_u64(ignored));stage_observe_bits(stats,b.public_bit_length(),b.magnitude_u64(ignored));
}
size_t stage_i64_bits(int64_t value){uint64_t magnitude=value<0?uint64_t(-(value+1))+1:uint64_t(value);size_t bits=0;while(magnitude){++bits;magnitude>>=1;}return bits;}
void stage_observe_i64_operation(int64_t a,int64_t b){
  if(!active_stage_stats)return;auto&stats=active_stage_stats->kernel[size_t(active_stage_kernel)];++stats.operations;
  stage_observe_bits(stats,stage_i64_bits(a),true);stage_observe_bits(stats,stage_i64_bits(b),true);
}
void stage_merge_stats(StageStats&target,const StageStats&source){
  for(size_t k=0;k<size_t(StageKernel::Count);++k){auto&t=target.kernel[k];const auto&s=source.kernel[k];t.operations+=s.operations;t.operands+=s.operands;t.fixed_hits+=s.fixed_hits;t.slow_paths+=s.slow_paths;t.max_bits=std::max(t.max_bits,s.max_bits);for(size_t b=0;b<5;++b)t.bit_bands[b]+=s.bit_bands[b];}
}
Rat operator+(const Rat&a,const Rat&b){stage_observe_rat_operation(a,b);cpp_int g=gcd_i(a.d,b.d),ad=a.d/g,bd=b.d/g;return Rat(a.n*bd+b.n*ad,ad*b.d);}
Rat operator-(const Rat&a,const Rat&b){stage_observe_rat_operation(a,b);return Rat(a.n*b.d-b.n*a.d,a.d*b.d);}
Rat operator*(const Rat&a,const Rat&b){stage_observe_rat_operation(a,b);cpp_int g1=gcd_i(a.n,b.d),g2=gcd_i(b.n,a.d);return Rat((a.n/g1)*(b.n/g2),(a.d/g2)*(b.d/g1));}
Rat operator/(const Rat&a,const Rat&b){stage_observe_rat_operation(a,b);if(b.n==cpp_int(0))throw std::domain_error("rational division by zero");cpp_int g1=gcd_i(a.n,b.n),g2=gcd_i(b.d,a.d);return Rat((a.n/g1)*(b.d/g2),(a.d/g2)*(b.n/g1));}
bool operator<(const Rat&a,const Rat&b){stage_observe_rat_operation(a,b);cpp_int g=gcd_i(a.d,b.d);return a.n*(b.d/g)<b.n*(a.d/g);}
bool operator==(const Rat&a,const Rat&b){stage_observe_rat_operation(a,b);return a.n==b.n&&a.d==b.d;}
Rat sq(const Rat&x){return x*x;}

std::array<uint32_t,4> philox(uint64_t root,std::array<uint32_t,4> x){
  uint32_t k0=uint32_t(root), k1=uint32_t(root>>32);
  std::array<uint32_t,4> y{};
  for(int r=0;r<10;++r){
    uint64_t p0=uint64_t(M0)*x[0], p1=uint64_t(M1)*x[2];
    y={uint32_t(p1>>32)^x[1]^k0,uint32_t(p1),uint32_t(p0>>32)^x[3]^k1,uint32_t(p0)};
    x=y; if(r<9){k0+=W0;k1+=W1;}
  }
  return y;
}

bool uniform(uint64_t root,uint32_t c1,uint32_t c2,uint32_t c3,uint32_t m,
             uint64_t max_rho,uint32_t&value,uint64_t&rho_used){
  if(m==0||max_rho>MAX_REJECTION_RHO) return false;
  uint64_t span=uint64_t(1)<<32;
  uint64_t limit=span-(span%m);
  for(uint64_t rho=0;rho<=max_rho;++rho){
    auto w=philox(root,{uint32_t(rho/4),c1,c2,c3}); uint32_t u=w[rho%4];
    if(uint64_t(u)<limit){value=u%m;rho_used=rho;return true;}
    if(rho==std::numeric_limits<uint64_t>::max()) break;
  }
  return false;
}

bool uniform_full(uint64_t root,uint32_t c1,uint32_t c2,uint32_t c3,uint32_t m,
                  uint32_t&value,uint64_t&rho_used){
  return uniform(root,c1,c2,c3,m,MAX_REJECTION_RHO,value,rho_used);
}

enum class Family:uint32_t{Treatment=0,Free=1,DevGeometry=2,DevMarkov=3,
  ValGeometry=4,ValMarkov=5,EvalGeometry=6,EvalMarkov=7,BootBlock=8,BootEpisode=9};
struct Address{uint64_t root=0;uint32_t c1=0,c2=0,c3=0,m=0;};
bool roster_code(uint32_t N,uint32_t&code){
  switch(N){case 4:code=0;return true;case 6:code=1;return true;case 8:code=2;return true;case 12:code=3;return true;default:return false;}
}
bool encode_address(Family family,uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3,uint32_t p4,Address&out){
  switch(family){
    case Family::Treatment:
      if(p0<1||p0>2047||p1>3)return false;
      out={202608230200ULL,p0,p1,0x01000000u,129};return true;
    case Family::Free:
      if(p0<1||p0>2047||p1>3)return false;
      out={202608230201ULL,p0,p1,0x02000000u,129};return true;
    case Family::DevGeometry:
      if(p0>11||(p1!=4&&p1!=8)||p2>31||p4>=p1)return false;
      out={202608231000ULL+100*p0+p1,p2,p3,0x10000000u+p4,5};return true;
    case Family::DevMarkov:
      if(p0>11||(p1!=4&&p1!=8)||p2>31||p3<1||p3>31)return false;
      out={202608231000ULL+100*p0+p1,p2,p3,0x11000000u,10};return true;
    case Family::ValGeometry:
      if(p0>11||(p1!=4&&p1!=8)||p2>127||p4>=p1)return false;
      out={202608232000ULL+100*p0+p1,p2,p3,0x20000000u+p4,5};return true;
    case Family::ValMarkov:
      if(p0>11||(p1!=4&&p1!=8)||p2>127||p3<1||p3>31)return false;
      out={202608232000ULL+100*p0+p1,p2,p3,0x21000000u,10};return true;
    case Family::EvalGeometry:
      {uint32_t ignored;if(p0>11||!roster_code(p1,ignored)||p2>511||p4>=p1)return false;}
      out={202608239000ULL+100*p0+p1,p2,p3,0x30000000u+p4,5};return true;
    case Family::EvalMarkov:
      {uint32_t ignored;if(p0>11||!roster_code(p1,ignored)||p2>511||p3<1||p3>31)return false;}
      out={202608239000ULL+100*p0+p1,p2,p3,0x31000000u,10};return true;
    case Family::BootBlock:
      if(p0>19999||p1>11)return false;
      out={202608239999ULL,p0,p1,0x40000000u,12};return true;
    case Family::BootEpisode:{
      uint32_t nidx;if(p0>19999||p1>11||!roster_code(p2,nidx)||p3>5||p4>0x00ffffffu)return false;
      out={202608239999ULL,p0,p1+12*nidx+48*p3,0x41000000u+p4,0};return true;
    }
  }
  return false;
}

uint32_t markov_next(uint32_t current,uint32_t draw){
  if(current>5||draw>9)throw std::invalid_argument("invalid Markov input");
  if(draw<5)return current;
  uint32_t other=draw-5;
  return other>=current?other+1:other;
}

uint32_t resample_position(uint32_t p,uint32_t h,const std::array<uint32_t,6>&counts){
  if(h>5||p>=counts[h])throw std::invalid_argument("invalid resample position");
  uint64_t value=p;for(uint32_t h0=0;h0<h;++h0)value+=counts[h0];
  if(value>std::numeric_limits<uint32_t>::max())throw std::overflow_error("resample position overflow");
  return uint32_t(value);
}

enum class GeometryPurpose:uint32_t{Development=0,Validation=1,Evaluation=2};
bool geometry_family(GeometryPurpose purpose,Family&family){
  switch(purpose){case GeometryPurpose::Development:family=Family::DevGeometry;return true;
    case GeometryPurpose::Validation:family=Family::ValGeometry;return true;
    case GeometryPurpose::Evaluation:family=Family::EvalGeometry;return true;}
  return false;
}

struct Geometry {
  int N; std::vector<int> s; std::vector<Rat> x,left,right,v;
};
Geometry geometry_from_offsets(const std::vector<int>& offsets){
  int N=int(offsets.size()); Geometry g; g.N=N; g.s=offsets;
  for(int j=0;j<N;++j) g.x.emplace_back(cpp_int(192*(2*(j+1)-1)+offsets[j]),cpp_int(384*N));
  for(int j=0;j<N;++j){
    Rat l=j==0?Rat(0):(g.x[j-1]+g.x[j])/Rat(2);
    Rat r=j==N-1?Rat(1):(g.x[j]+g.x[j+1])/Rat(2);
    g.left.push_back(l);g.right.push_back(r);g.v.push_back(r-l);
  }
  return g;
}
bool heterogeneous(const Geometry&geometry){
  auto bounds=std::minmax_element(geometry.v.begin(),geometry.v.end(),[](const Rat&a,const Rat&b){return a<b;});
  return !( (*bounds.second-*bounds.first) < Rat(1,64*geometry.N) );
}
bool generate_geometry(GeometryPurpose purpose,uint32_t block,uint32_t N,uint32_t episode,
                       uint32_t max_g,Geometry&accepted,uint32_t&accepted_g,
                       bool force_scalar_exhaustion=false,bool force_homogeneous=false){
  Family family;if(!geometry_family(purpose,family))return false;
  for(uint64_t outer=0;outer<=max_g;++outer){
    std::vector<int> offsets;offsets.reserve(N);
    for(uint32_t i0=0;i0<N;++i0){
      Address address;if(!encode_address(family,block,N,episode,uint32_t(outer),i0,address))return false;
      if(force_scalar_exhaustion)return false;
      uint32_t value=0;uint64_t rho=0;
      if(!uniform_full(address.root,address.c1,address.c2,address.c3,address.m,value,rho))return false;
      offsets.push_back(force_homogeneous?0:-48+24*int(value));
    }
    Geometry candidate=geometry_from_offsets(offsets);
    if(heterogeneous(candidate)){accepted=std::move(candidate);accepted_g=uint32_t(outer);return true;}
    if(outer==std::numeric_limits<uint32_t>::max())break;
  }
  return false;
}
Rat anti(const Rat&x,const Rat&beta,const Rat&gamma){
  return x + beta*(sq(x)-x) + gamma*(Rat(3)*sq(x)-Rat(2)*sq(x)*x-x);
}
std::vector<Rat> masses(const Geometry&g,const Rat&beta,const Rat&gamma){
  std::vector<Rat> out; for(int i=0;i<g.N;++i)out.push_back(anti(g.right[i],beta,gamma)-anti(g.left[i],beta,gamma)); return out;
}
std::vector<int> lr(const std::vector<Rat>&w,int Q=120){
  Rat total; for(auto&a:w)total=total+a;
  std::vector<int> n(w.size()); std::vector<std::pair<Rat,int>> rem;
  int used=0;
  for(size_t i=0;i<w.size();++i){Rat q=Rat(Q)*w[i]/total; cpp_int z=q.n/q.d; n[i]=z.to_int_checked();used+=n[i];rem.push_back({q-Rat(z),int(i)});}
  std::sort(rem.begin(),rem.end(),[](auto&a,auto&b){if(a.first==b.first)return a.second<b.second;return b.first<a.first;});
  for(int k=0;k<Q-used;++k)++n[rem[k].second]; return n;
}
std::vector<Rat> treatment_weights(const Geometry&g,const std::vector<Rat>&d,const Rat&db,const std::array<Rat,4>&th){
  std::vector<Rat>w;for(int i=0;i<g.N;++i){Rat q=th[0]+th[1]*d[i]+th[2]*db+th[3]*sq(d[i]-db);w.push_back(g.v[i]*(Rat(1)+sq(q)));}return w;
}
Rat clip_half(const Rat&x){if(x<Rat(-1,2))return Rat(-1,2);if(Rat(1,2)<x)return Rat(1,2);return x;}
std::vector<Rat> free_weights(const Geometry&g,const std::vector<Rat>&d,const Rat&db,const std::array<Rat,4>&th,const std::array<Rat,4>&ph){
  auto base=treatment_weights(g,d,db,th);std::vector<Rat>w;
  for(int i=0;i<g.N;++i){Rat z=Rat(g.N)*g.v[i]-Rat(1);Rat r=clip_half(ph[0]+ph[1]*(d[i]-db)+ph[2]*z+ph[3]*(d[i]-db)*z);w.push_back(base[i]*sq(Rat(1)+r));}return w;
}
Rat rat_from_parts(const char* numerator,const char* denominator){
  if(!numerator||!denominator)throw std::invalid_argument("null rational part");
  return Rat(cpp_int(std::string(numerator)),cpp_int(std::string(denominator)));
}
std::string rational_binary(const char* an,const char* ad,const char* bn,const char* bd,uint32_t operation){
  Rat a=rat_from_parts(an,ad),b=rat_from_parts(bn,bd);
  switch(operation){
    case 0:return (a+b).s();
    case 1:return (a-b).s();
    case 2:return (a*b).s();
    case 3:return (a/b).s();
    case 4:return a<b?"1":"0";
    case 5:return a==b?"1":"0";
    default:throw std::invalid_argument("unregistered rational operation");
  }
}
std::string join_i(const std::vector<int>&x){std::ostringstream o;for(size_t i=0;i<x.size();++i){if(i)o<<',';o<<x[i];}return o.str();}
std::string fixture_audit(){
  std::ostringstream o;
  for(auto root:{uint64_t(0),uint64_t(202608230200),uint64_t(202608232004)}){auto w=philox(root,{0,1,2,0x10000003u});o<<"P|"<<root<<'|'<<w[0]<<','<<w[1]<<','<<w[2]<<','<<w[3]<<'\n';}
  uint32_t u=0;uint64_t rho=0;uniform(202608230200,1,2,0x01000000u,129,64,u,rho);o<<"U|"<<u<<'|'<<rho<<'\n';
  auto g=geometry_from_offsets({-48,24,0,48});
  for(int h=0;h<6;++h){Rat beta((h/2)-1,4),gamma(h%2,4);auto m=masses(g,beta,gamma);std::vector<Rat>d;Rat db;for(int i=0;i<g.N;++i){d.push_back(m[i]/g.v[i]);db=db+d.back();}db=db/Rat(g.N);
    std::array<Rat,4> th={Rat(1,2),Rat(-1,4),Rat(0),Rat(1,16)},ph={Rat(0),Rat(1,8),Rat(-1,16),Rat(1,32)};
    auto nt=lr(treatment_weights(g,d,db,th));auto nf=lr(free_weights(g,d,db,th,ph));std::array<Rat,4> zero={Rat(),Rat(),Rat(),Rat()};auto ne=lr(free_weights(g,d,db,th,zero));
    o<<"H|"<<h<<'|'<<join_i(nt)<<'|'<<join_i(nf)<<'|'<<join_i(ne)<<'|'<<(nt==ne)<<'\n';
  }
  std::vector<std::tuple<Rat,std::array<int,4>,int>> rows={
    {Rat(1,3),{0,0,0,0},0},{Rat(1,2),{1,0,0,0},2},{Rat(1,2),{0,1,0,0},1},{Rat(1,2),{0,1,0,0},3}};
  std::sort(rows.begin(),rows.end(),[](auto&a,auto&b){if(std::get<0>(a)==std::get<0>(b)){if(std::get<1>(a)==std::get<1>(b))return std::get<2>(a)<std::get<2>(b);return std::get<1>(a)<std::get<1>(b);}return std::get<0>(b)<std::get<0>(a);});
  o<<"ORDER";for(auto&r:rows)o<<'|'<<std::get<2>(r);o<<'\n';
  const char* an="6277101735386680763835789423207666416102355444464034512895";
  const char* ad="340282366920938463463374607431768211455";
  const char* bn="-1606938044258990275541962092341162602522202993782792835301499";
  const char* bd="1361129467683753853853498429727072845829";
  o<<"BIG|"<<rational_binary(an,ad,bn,bd,0)<<'|'<<rational_binary(an,ad,bn,bd,2)
   <<'|'<<rational_binary(an,ad,bn,bd,4)<<'\n';
  o<<"COUNTS|2048|2048|32|768|3072|24576|10|20000|491520000\n";
  return o.str();
}

// Result-blind production-form cost-collapse slice.  The namespace below is
// deliberately synthetic: it uses no registered r03 root key, frozen episode,
// coefficient, score, panel, or terminal.  Work identities are integer ranges;
// worker count and tile width therefore cannot enter any generated byte.
struct StageHost {
  uint32_t roster=0,index=0;
  Geometry geometry;
  std::array<uint32_t,6> state_counts{};
  std::array<uint8_t,32> state_tape{};
  std::array<std::vector<Rat>,6> mass{},density{};
  std::array<Rat,6> dbar{},control_u{};
};
struct StageCandidate {
  Rat aggregate;
  std::array<int,4> coefficient{};
  StageStats stats;
};
struct StageDraw { std::array<Rat,12> composite{}; StageStats stats; };

template<class Function>
void stage_parallel(uint32_t total,uint32_t workers,Function function){
  std::vector<std::thread> lanes;
  lanes.reserve(workers);
  for(uint32_t lane=0;lane<workers;++lane){
    uint32_t begin=uint32_t((uint64_t(total)*lane)/workers);
    uint32_t end=uint32_t((uint64_t(total)*(lane+1))/workers);
    lanes.emplace_back([=,&function](){for(uint32_t index=begin;index<end;++index)function(index);});
  }
  for(auto&lane:lanes)lane.join();
}

std::vector<int> stage_oracle(const Geometry&g,const std::vector<Rat>&m){
  std::vector<std::tuple<Rat,int,int>> records;
  records.reserve(size_t(g.N)*120);
  for(int i=0;i<g.N;++i)for(int k=0;k<120;++k){
    Rat delta=m[i]*g.v[i]/(g.v[i]+Rat(k,600))-m[i]*g.v[i]/(g.v[i]+Rat(k+1,600));
    records.push_back({delta,i,k});
  }
  std::sort(records.begin(),records.end(),[](const auto&a,const auto&b){
    if(std::get<0>(a)==std::get<0>(b)){
      if(std::get<1>(a)==std::get<1>(b))return std::get<2>(a)<std::get<2>(b);
      return std::get<1>(a)<std::get<1>(b);
    }
    return std::get<0>(b)<std::get<0>(a);
  });
  std::vector<int> n(g.N);for(int j=0;j<120;++j)++n[std::get<1>(records[j])];return n;
}
Rat stage_endpoint(const Geometry&g,const std::vector<Rat>&m,const std::vector<int>&n){
  Rat out;for(int i=0;i<g.N;++i)out=out+m[i]*g.v[i]/(g.v[i]+Rat(n[i],600));return out;
}
std::array<int,4> stage_coeff(uint32_t candidate){
  return {int(candidate%17)-8,int((candidate*3+1)%19)-9,int((candidate*5+2)%23)-11,int((candidate*7+3)%29)-14};
}
std::array<Rat,4> stage_coeff_rat(const std::array<int,4>&value){
  return {Rat(value[0],16),Rat(value[1],16),Rat(value[2],16),Rat(value[3],16)};
}
std::vector<StageHost> stage_hosts(uint32_t episodes,StageStats&stats){
  StageScope scope(stats,StageKernel::Host);
  static constexpr std::array<uint32_t,4> rosters={4,6,8,12};
  std::vector<StageHost> out;out.reserve(episodes);
  for(uint32_t e=0;e<episodes;++e){
    uint32_t N=rosters[e%4];std::vector<int> offsets(N);
    for(uint32_t i=0;i<N;++i){int selector=int((e*11+i*7+3)%5);offsets[i]=-48+24*selector;}
    // Force non-degenerate heterogeneity without rejection or a registered RNG.
    offsets.front()=-48;offsets.back()=48;
    StageHost host;host.roster=N;host.index=e;host.geometry=geometry_from_offsets(offsets);
    uint32_t state=e%6;
    for(uint32_t t=0;t<32;++t){host.state_tape[t]=uint8_t(state);++host.state_counts[state];uint32_t draw=(e*13+t*7+3)%10;state=markov_next(state,draw);}
    {
      StageScope controls(stats,StageKernel::Controls);
      for(int h=0;h<6;++h){
      Rat beta((h/2)-1,4),gamma(h%2,4);host.mass[h]=masses(host.geometry,beta,gamma);
      for(uint32_t i=0;i<N;++i){host.density[h].push_back(host.mass[h][i]/host.geometry.v[i]);host.dbar[h]=host.dbar[h]+host.density[h].back();}
      host.dbar[h]=host.dbar[h]/Rat(int(N));
      auto nd=lr(host.density[h]),nm=lr(host.mass[h]);std::vector<Rat>marg;
      for(uint32_t i=0;i<N;++i)marg.push_back(host.mass[h][i]/(Rat(600)*host.geometry.v[i]+Rat(1)));
      auto nmar=lr(marg),no=stage_oracle(host.geometry,host.mass[h]);
      host.control_u[h]=stage_endpoint(host.geometry,host.mass[h],nd)+stage_endpoint(host.geometry,host.mass[h],nm)+stage_endpoint(host.geometry,host.mass[h],nmar)+stage_endpoint(host.geometry,host.mass[h],no);
      }
    }
    out.push_back(std::move(host));
  }
  return out;
}
StageCandidate stage_candidate(uint32_t id,const std::vector<StageHost>&hosts){
  StageCandidate row;row.coefficient=stage_coeff(id);auto theta=stage_coeff_rat(row.coefficient);
  auto phi=stage_coeff_rat(stage_coeff(id+37));
  for(const auto&host:hosts){
    for(int h=0;h<6;++h){if(!host.state_counts[h])continue;
      std::vector<int>nt,nf;Rat u;
      {
        StageScope controls(row.stats,StageKernel::Controls);
        nt=lr(treatment_weights(host.geometry,host.density[h],host.dbar[h],theta));
        nf=lr(free_weights(host.geometry,host.density[h],host.dbar[h],theta,phi));
      // Exact U/Z production primitives are exercised; no synthetic value is
      // published.  Counts fold the cached 32-state tape exactly.
        u=stage_endpoint(host.geometry,host.mass[h],nt)+stage_endpoint(host.geometry,host.mass[h],nf)+host.control_u[h];
      }
      {
        StageScope aggregate(row.stats,StageKernel::Candidate);
        Rat z=Rat(6)-u;Rat weighted=z*Rat(int(host.state_counts[h]));row.aggregate=row.aggregate+weighted;
      }
    }
  }
  return row;
}

int64_t stage_score(uint32_t arm,uint32_t roster,uint32_t block,uint32_t episode){
  return int64_t((arm*97+roster*31+block*17+episode*13+(arm+1)*(episode%7))%1009)-504;
}
StageDraw stage_draw(uint32_t q){
  StageDraw out;static constexpr std::array<uint32_t,2> rosters={6,12};
  StageScope reducer(out.stats,StageKernel::Reducer);
  std::array<std::array<Rat,2>,10> jrJ{},jrR{};
  for(uint32_t ni=0;ni<2;++ni)for(uint32_t arm=0;arm<10;++arm){
    int64_t sumJ=0,sumR=0;
    for(uint32_t occurrence=0;occurrence<12;++occurrence){
      uint32_t source=(q*29+occurrence*7+11)%12;std::vector<std::tuple<int64_t,uint32_t,uint32_t>> sampled;sampled.reserve(72);
      int64_t occurrence_sum=0;
      for(uint32_t h=0;h<6;++h)for(uint32_t p=0;p<12;++p){
        uint32_t source_episode=h+6*((q*43+occurrence*19+ni*5+p*11)%12);
        int64_t value=stage_score(arm,rosters[ni],source,source_episode);
        stage_observe_i64_operation(occurrence_sum,value);occurrence_sum+=value;sampled.push_back({value,source_episode,p+12*h});
      }
      std::sort(sampled.begin(),sampled.end(),[](const auto&a,const auto&b){stage_observe_i64_operation(std::get<0>(a),std::get<0>(b));return a<b;});
      int64_t lower=0;for(uint32_t k=0;k<18;++k){stage_observe_i64_operation(lower,std::get<0>(sampled[k]));lower+=std::get<0>(sampled[k]);}
      stage_observe_i64_operation(sumJ,occurrence_sum);sumJ+=occurrence_sum;stage_observe_i64_operation(sumR,lower);sumR+=lower;
    }
    stage_observe_i64_operation(sumJ,12*72);stage_observe_i64_operation(sumR,12*18);jrJ[arm][ni]=Rat(cpp_int(sumJ),cpp_int(12*72));jrR[arm][ni]=Rat(cpp_int(sumR),cpp_int(12*18));
  }
  auto fill=[&](const auto&v,size_t offset){
    Rat V=v[0][0]-v[4][0];for(uint32_t base=4;base<=7;++base)for(uint32_t ni=0;ni<2;++ni)if(v[0][ni]-v[base][ni]<V)V=v[0][ni]-v[base][ni];
    Rat F=v[0][0]-v[1][0],A=v[0][0]-v[2][0],P=v[1][0]-v[0][0],G=v[4][0]-v[0][0],H=v[8][0]-v[4][0];
    if(v[4][1]-v[0][1]<G)G=v[4][1]-v[0][1];
    for(uint32_t ni=1;ni<2;++ni){if(v[0][ni]-v[1][ni]<F)F=v[0][ni]-v[1][ni];if(v[0][ni]-v[2][ni]<A)A=v[0][ni]-v[2][ni];if(v[1][ni]-v[0][ni]<P)P=v[1][ni]-v[0][ni];if(v[8][ni]-v[4][ni]<H)H=v[8][ni]-v[4][ni];}
    for(uint32_t base=4;base<=7;++base){Rat candidate=v[base][0]-v[0][0];for(uint32_t ni=1;ni<2;++ni)if(v[base][ni]-v[0][ni]<candidate)candidate=v[base][ni]-v[0][ni];if(G<candidate)G=candidate;}
    out.composite[offset+0]=V;out.composite[offset+1]=F;out.composite[offset+2]=A;out.composite[offset+3]=P;out.composite[offset+4]=G;out.composite[offset+5]=H;
  };
  fill(jrJ,0);fill(jrR,6);return out;
}

std::string stage_slice_audit(uint32_t width,uint32_t host_episodes,uint32_t candidates,uint32_t draws,uint32_t workers,uint64_t*metrics){
  if((width!=8&&width!=32&&width!=64)||host_episodes==0||host_episodes>4096||candidates==0||candidates>512||draws==0||draws>4096||(workers!=1&&workers!=2&&workers!=4&&workers!=8)||uint64_t(host_episodes)*candidates>245760)throw std::invalid_argument("stage cap exceeded");
  StageStats total_stats;auto hosts=stage_hosts(host_episodes,total_stats);std::vector<StageCandidate> rows(candidates);
  for(uint32_t tile=0;tile<candidates;tile+=width){uint32_t stop=std::min(candidates,tile+width);stage_parallel(stop-tile,std::min(workers,stop-tile),[&](uint32_t local){uint32_t id=tile+local;rows[id]=stage_candidate(id,hosts);});}
  for(const auto&row:rows)stage_merge_stats(total_stats,row.stats);
  std::vector<uint32_t> order(candidates);std::iota(order.begin(),order.end(),0);
  uint64_t ties=0;{
    StageScope merge(total_stats,StageKernel::Candidate);
    std::sort(order.begin(),order.end(),[&](uint32_t a,uint32_t b){if(rows[a].aggregate==rows[b].aggregate){if(rows[a].coefficient==rows[b].coefficient)return a<b;return rows[a].coefficient<rows[b].coefficient;}return rows[b].aggregate<rows[a].aggregate;});
    for(uint32_t index=1;index<candidates;++index)if(rows[order[index-1]].aggregate==rows[order[index]].aggregate)++ties;
  }
  std::vector<StageDraw> reducers(draws);stage_parallel(draws,std::min(workers,draws),[&](uint32_t q){reducers[q]=stage_draw(q);});
  for(const auto&draw:reducers)stage_merge_stats(total_stats,draw.stats);
  std::ostringstream out;out<<"VQFP-VNPA-R03-STAGE-R01-SYNTHETIC-V1\n";
  std::array<uint64_t,6> roster_count{};for(const auto&host:hosts){++roster_count[host.roster==4?0:host.roster==6?1:host.roster==8?2:3];out<<"H|"<<host.index<<'|'<<host.roster<<'|'<<join_i(host.geometry.s)<<'|';for(int h=0;h<6;++h){if(h)out<<',';out<<host.state_counts[h];}out<<'|';for(size_t t=0;t<host.state_tape.size();++t){if(t)out<<',';out<<int(host.state_tape[t]);}out<<'\n';}
  for(uint32_t id=0;id<candidates;++id){auto&r=rows[id];out<<"C|"<<id<<'|'<<r.coefficient[0]<<','<<r.coefficient[1]<<','<<r.coefficient[2]<<','<<r.coefficient[3]<<'|'<<r.aggregate.s()<<'\n';}
  out<<"ORDER";for(auto id:order)out<<'|'<<id;out<<'\n';
  uint32_t lo=draws/40,hi=draws-1-draws/40;{
    StageScope rank(total_stats,StageKernel::Reducer);
    for(uint32_t x=0;x<12;++x){std::vector<std::pair<Rat,uint32_t>> values;values.reserve(draws);for(uint32_t q=0;q<draws;++q)values.push_back({reducers[q].composite[x],q});std::sort(values.begin(),values.end(),[](const auto&a,const auto&b){if(a.first==b.first)return a.second<b.second;return a.first<b.first;});out<<"R|"<<x<<'|'<<values[lo].first.s()<<'|'<<values[hi].first.s()<<'\n';}
  }
  std::string payload=out.str();if(metrics){uint64_t exact_ops=0,fixed=0,slow=0,max_bits=0;for(const auto&kernel:total_stats.kernel){exact_ops+=kernel.operations;fixed+=kernel.fixed_hits;slow+=kernel.slow_paths;max_bits=std::max(max_bits,kernel.max_bits);}metrics[0]=host_episodes;metrics[1]=uint64_t(host_episodes)*32;metrics[2]=uint64_t(host_episodes)*candidates;metrics[3]=uint64_t(draws)*12*2*72;metrics[4]=exact_ops;metrics[5]=fixed;metrics[6]=slow;metrics[7]=max_bits;metrics[8]=candidates;metrics[9]=ties;metrics[10]=uint64_t(draws)*10*2*12;metrics[11]=metrics[10];metrics[12]=payload.size();metrics[13]=workers;metrics[14]=width;metrics[15]=uint64_t(draws)*12;for(size_t k=0;k<size_t(StageKernel::Count);++k){const auto&s=total_stats.kernel[k];size_t base=16+10*k;metrics[base]=s.operations;metrics[base+1]=s.operands;metrics[base+2]=s.fixed_hits;metrics[base+3]=s.slow_paths;metrics[base+4]=s.max_bits;for(size_t b=0;b<5;++b)metrics[base+5+b]=s.bit_bands[b];}}
  return payload;
}
int copy_out(const std::string&s,char*out,uint64_t cap){if(!out||cap<=s.size())return -int(s.size()+1);std::memcpy(out,s.c_str(),s.size()+1);return int(s.size());}
}

VQFP_EXPORT int vqfp_vnpa_r03_abi(){return ABI;}
VQFP_EXPORT const char* vqfp_vnpa_r03_revision(){return REV;}
VQFP_EXPORT const char* vqfp_vnpa_r03_science_card_sha256(){return CARD_SHA256;}
VQFP_EXPORT int vqfp_vnpa_r03_philox(uint64_t root,uint32_t x0,uint32_t x1,uint32_t x2,uint32_t x3,uint32_t*out){if(!out)return 2;auto w=philox(root,{x0,x1,x2,x3});for(int i=0;i<4;++i)out[i]=w[i];return 0;}
VQFP_EXPORT int vqfp_vnpa_r03_uniform(uint64_t root,uint32_t c1,uint32_t c2,uint32_t c3,uint32_t m,uint64_t max_rho,uint32_t*out_value,uint64_t*out_rho){if(!out_value||!out_rho||m==0||max_rho>MAX_REJECTION_RHO)return 2;uint32_t v;uint64_t r;if(!uniform(root,c1,c2,c3,m,max_rho,v,r))return 3;*out_value=v;*out_rho=r;return 0;}
VQFP_EXPORT int vqfp_vnpa_r03_uniform_full(uint64_t root,uint32_t c1,uint32_t c2,uint32_t c3,uint32_t m,uint32_t*out_value,uint64_t*out_rho){if(!out_value||!out_rho||m==0)return 2;uint32_t v;uint64_t r;if(!uniform_full(root,c1,c2,c3,m,v,r))return 3;*out_value=v;*out_rho=r;return 0;}
VQFP_EXPORT int vqfp_vnpa_r03_encode_address(uint32_t family,uint32_t p0,uint32_t p1,uint32_t p2,uint32_t p3,uint32_t p4,uint64_t*out_root,uint32_t*out_words){if(!out_root||!out_words||family>9)return 2;Address a;if(!encode_address(Family(family),p0,p1,p2,p3,p4,a))return 2;*out_root=a.root;out_words[0]=a.c1;out_words[1]=a.c2;out_words[2]=a.c3;out_words[3]=a.m;return 0;}
VQFP_EXPORT int vqfp_vnpa_r03_markov_next(uint32_t current,uint32_t draw,uint32_t*out){if(!out||current>5||draw>9)return 2;*out=markov_next(current,draw);return 0;}
VQFP_EXPORT int vqfp_vnpa_r03_resample_position(uint32_t p,uint32_t h,const uint32_t*counts,uint32_t*out){if(!counts||!out||h>5)return 2;try{std::array<uint32_t,6>c{};for(int i=0;i<6;++i)c[i]=counts[i];*out=resample_position(p,h,c);return 0;}catch(...){return 2;}}
VQFP_EXPORT int vqfp_vnpa_r03_u32_little_endian(uint32_t word,uint8_t*out){if(!out)return 2;out[0]=uint8_t(word);out[1]=uint8_t(word>>8);out[2]=uint8_t(word>>16);out[3]=uint8_t(word>>24);return 0;}
VQFP_EXPORT int vqfp_vnpa_r03_test_rejection_injected(uint32_t m,uint64_t max_rho,uint64_t forced_rejections,uint32_t accepted_word,uint64_t*out_rho,uint32_t*out_c0,uint32_t*out_lane){if(!m||max_rho>MAX_REJECTION_RHO||!out_rho||!out_c0||!out_lane)return 2;uint64_t span=uint64_t(1)<<32,limit=span-(span%m);if(forced_rejections>max_rho||uint64_t(accepted_word)>=limit)return 3;*out_rho=forced_rejections;*out_c0=uint32_t(forced_rejections/4);*out_lane=uint32_t(forced_rejections%4);return 0;}
VQFP_EXPORT int vqfp_vnpa_r03_geometry(uint32_t purpose,uint32_t block,uint32_t N,uint32_t episode,uint32_t max_g,uint32_t test_flags,int32_t*out_offsets,uint32_t*out_g){if(!out_offsets||!out_g||purpose>2||N>12)return 2;try{Geometry accepted;uint32_t g=0;bool ok=generate_geometry(GeometryPurpose(purpose),block,N,episode,max_g,accepted,g,(test_flags&1)!=0,(test_flags&2)!=0);if(!ok)return 3;for(uint32_t i=0;i<N;++i)out_offsets[i]=accepted.s[i];*out_g=g;return 0;}catch(...){return 2;}}
VQFP_EXPORT int vqfp_vnpa_r03_geometry_full(uint32_t purpose,uint32_t block,uint32_t N,uint32_t episode,int32_t*out_offsets,uint32_t*out_g){if(!out_offsets||!out_g||purpose>2||N>12)return 2;try{Geometry accepted;uint32_t g=0;if(!generate_geometry(GeometryPurpose(purpose),block,N,episode,std::numeric_limits<uint32_t>::max(),accepted,g))return 3;for(uint32_t i=0;i<N;++i)out_offsets[i]=accepted.s[i];*out_g=g;return 0;}catch(...){return 2;}}
VQFP_EXPORT int vqfp_vnpa_r03_exact_rational_binary(const char*an,const char*ad,const char*bn,const char*bd,uint32_t operation,char*out,uint64_t cap){try{return copy_out(rational_binary(an,ad,bn,bd,operation),out,cap);}catch(...){return -1;}}
VQFP_EXPORT int vqfp_vnpa_r03_fixture_audit(char*out,uint64_t cap){try{return copy_out(fixture_audit(),out,cap);}catch(...){return -1;}}
VQFP_EXPORT int vqfp_vnpa_r03_chain_benchmark(uint32_t width,uint32_t candidates,uint32_t episodes,uint32_t draws,uint64_t*out){
  if(!out||width==0||candidates==0||candidates>64||episodes==0||episodes>128||draws==0||draws>256)return 2;
  uint64_t checksum=0,words=0,policy=0,resamples=0;
  auto g=geometry_from_offsets({-48,24,0,48});
  // Handcrafted, non-frozen fixture coordinates exercise the actual exact
  // host/policy/LR path.  Width changes only native tiling, never an address.
  for(uint32_t tile=0;tile<candidates;tile+=width){
    uint32_t tile_stop=std::min(candidates,tile+width);
    for(uint32_t c=tile;c<tile_stop;++c)for(uint32_t e=0;e<episodes;++e){
      std::array<Rat,4> th={Rat(int(c%17)-8,16),Rat(int(e%13)-6,16),Rat(int((c+e)%11)-5,16),Rat(int(c%7)-3,16)};
      std::array<Rat,4> ph={Rat(int(e%9)-4,32),Rat(int(c%5)-2,32),Rat(int((2*c+e)%7)-3,32),Rat(int((c+3*e)%9)-4,32)};
      for(int h=0;h<6;++h){
        Rat beta((h/2)-1,4),gamma(h%2,4);auto m=masses(g,beta,gamma);std::vector<Rat>d;Rat db;
        for(int i=0;i<g.N;++i){d.push_back(m[i]/g.v[i]);db=db+d.back();}db=db/Rat(g.N);
        auto nt=lr(treatment_weights(g,d,db,th));auto nf=lr(free_weights(g,d,db,th,ph));
        for(int value:nt)checksum=checksum*1315423911u+uint64_t(value);
        for(int value:nf)checksum=checksum*2654435761u+uint64_t(value);
        policy+=8;
      }
    }
  }
  for(uint32_t q=0;q<draws;++q)for(uint32_t j=0;j<12;++j){uint32_t v;uint64_t r;
    if(!uniform(202608239999ULL,q,j,0x40000000u,12,64,v,r))return 3;
    auto addressed=philox(202608239999ULL,{uint32_t(r/4),q,j,0x40000000u});
    checksum^=(uint64_t(addressed[r%4])<<32)|v;words+=4;resamples+=1;}
  out[0]=checksum;out[1]=words;out[2]=policy;out[3]=resamples;out[4]=width;return 0;
}
VQFP_EXPORT int vqfp_vnpa_r03_stage_slice(uint32_t width,uint32_t host_episodes,uint32_t candidates,uint32_t draws,uint32_t workers,uint64_t*metrics,char*out,uint64_t cap){try{return copy_out(stage_slice_audit(width,host_episodes,candidates,draws,workers,metrics),out,cap);}catch(...){return -1;}}
VQFP_EXPORT int vqfp_vnpa_r03_production_execute_guard(){return 77;}
