// Fresh exact native seam for RISP-ECR-R01.  No historical RISP/APFI source is used.

#include <gmpxx.h>

#include <array>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using cpp_int = mpz_class;

namespace {

cpp_int abs_int(cpp_int value) { return value < 0 ? -value : value; }

cpp_int gcd(cpp_int left, cpp_int right) {
  left = abs_int(left);
  right = abs_int(right);
  while (right != 0) {
    cpp_int remainder = left % right;
    left = right;
    right = remainder;
  }
  return left;
}

struct Rational {
  cpp_int numerator{0};
  cpp_int denominator{1};

  Rational() = default;
  Rational(cpp_int n) : numerator(std::move(n)) {}
  Rational(cpp_int n, cpp_int d) : numerator(std::move(n)), denominator(std::move(d)) {
    normalize();
  }

  void normalize() {
    if (denominator == 0) throw std::runtime_error("zero denominator");
    if (denominator < 0) {
      numerator = -numerator;
      denominator = -denominator;
    }
    cpp_int divisor = gcd(numerator, denominator);
    if (divisor != 0) {
      numerator /= divisor;
      denominator /= divisor;
    }
  }

  std::string wire() const {
    return numerator.get_str() + "/" + denominator.get_str();
  }
};

Rational operator+(const Rational& a, const Rational& b) {
  return Rational(a.numerator * b.denominator + b.numerator * a.denominator,
                  a.denominator * b.denominator);
}
Rational operator-(const Rational& a, const Rational& b) {
  return Rational(a.numerator * b.denominator - b.numerator * a.denominator,
                  a.denominator * b.denominator);
}
Rational operator*(const Rational& a, const Rational& b) {
  return Rational(a.numerator * b.numerator, a.denominator * b.denominator);
}
Rational operator/(const Rational& a, const Rational& b) {
  if (b.numerator == 0) throw std::runtime_error("division by zero");
  return Rational(a.numerator * b.denominator, a.denominator * b.numerator);
}
bool operator==(const Rational& a, const Rational& b) {
  return a.numerator == b.numerator && a.denominator == b.denominator;
}
bool operator<(const Rational& a, const Rational& b) {
  return a.numerator * b.denominator < b.numerator * a.denominator;
}

cpp_int ipow(cpp_int base, int exponent) {
  cpp_int result = 1;
  while (exponent-- > 0) result *= base;
  return result;
}

std::array<std::array<Rational, 3>, 3> transition(int duration) {
  if (duration != 4 && duration != 8 && duration != 12)
    throw std::runtime_error("unsupported duration");
  Rational persistence(ipow(15, duration), ipow(16, duration));
  Rational off = (Rational(1) - persistence) / Rational(3);
  Rational diagonal = off + persistence;
  std::array<std::array<Rational, 3>, 3> matrix{};
  for (int row = 0; row < 3; ++row)
    for (int column = 0; column < 3; ++column)
      matrix[row][column] = row == column ? diagonal : off;
  return matrix;
}

struct Event {
  int action;
  bool positive;
  int duration;
};

int parse_int(const std::string& text) {
  std::size_t used = 0;
  int value = std::stoi(text, &used);
  if (used != text.size()) throw std::runtime_error("invalid integer");
  return value;
}

std::vector<Event> parse_events(const std::string& text) {
  std::vector<Event> events;
  if (text.empty()) return events;
  std::stringstream stream(text);
  std::string token;
  while (std::getline(stream, token, ';')) {
    std::stringstream fields(token);
    std::string action_text, ack_text, duration_text, extra;
    if (!std::getline(fields, action_text, ',') || !std::getline(fields, ack_text, ',') ||
        !std::getline(fields, duration_text, ',') || std::getline(fields, extra, ','))
      throw std::runtime_error("invalid event encoding");
    int action = parse_int(action_text);
    int ack = parse_int(ack_text);
    int duration = parse_int(duration_text);
    if (action < 0 || action > 2 || (ack != 0 && ack != 1))
      throw std::runtime_error("invalid action or ACK");
    events.push_back({action, ack == 1, duration});
  }
  if (events.size() > 8) throw std::runtime_error("history exceeds native bound");
  return events;
}

std::string evaluate(const std::string& input) {
  const std::size_t separator = input.rfind('|');
  if (separator == std::string::npos) throw std::runtime_error("missing next duration");
  std::vector<Event> events = parse_events(input.substr(0, separator));
  int next_duration = parse_int(input.substr(separator + 1));
  auto belief = std::array<Rational, 3>{Rational(1, 3), Rational(1, 3), Rational(1, 3)};
  Rational history_mass(1);

  for (const Event& event : events) {
    auto matrix = transition(event.duration);
    std::array<Rational, 3> predicted{};
    std::array<Rational, 3> weights{};
    Rational evidence(0);
    for (int completion = 0; completion < 3; ++completion) {
      for (int previous = 0; previous < 3; ++previous)
        predicted[completion] = predicted[completion] + belief[previous] * matrix[previous][completion];
      Rational positive = completion == event.action ? Rational(4, 5) : Rational(1, 5);
      Rational likelihood = event.positive ? positive : Rational(1) - positive;
      weights[completion] = predicted[completion] * likelihood;
      evidence = evidence + weights[completion];
    }
    if (evidence.numerator <= 0) throw std::runtime_error("non-positive event mass");
    for (int sector = 0; sector < 3; ++sector) belief[sector] = weights[sector] / evidence;
    // Reachability is under the frozen full-support uniform reference-action
    // law.  RAW/FULL posteriors still condition on the supplied public action.
    history_mass = history_mass * evidence * Rational(1, 3);
  }

  auto next_matrix = transition(next_duration);
  std::array<Rational, 3> completion{};
  std::array<Rational, 3> q{};
  for (int sector = 0; sector < 3; ++sector) {
    for (int previous = 0; previous < 3; ++previous)
      completion[sector] = completion[sector] + belief[previous] * next_matrix[previous][sector];
    q[sector] = Rational(next_duration) * (Rational(-3, 5) + Rational(6, 5) * completion[sector]);
  }
  int chosen = 0;
  for (int action = 1; action < 3; ++action)
    if (q[chosen] < q[action]) chosen = action;  // strict: earlier printed action wins ties

  std::ostringstream output;
  output << history_mass.wire();
  for (const Rational& value : belief) output << ';' << value.wire();
  for (const Rational& value : q) output << ';' << value.wire();
  output << ';' << chosen << ';' << q[chosen].wire();
  return output.str();
}

thread_local std::string result_buffer;

}  // namespace

#ifdef _WIN32
#define RISP_ECR_EXPORT extern "C" __declspec(dllexport)
#else
#define RISP_ECR_EXPORT extern "C" __attribute__((visibility("default")))
#endif

RISP_ECR_EXPORT const char* risp_ecr_r01_registry_key() {
  return "RISP_ECR_R01_EXACT_EVENT_HOST_V1";
}

RISP_ECR_EXPORT const char* risp_ecr_r01_evaluate(const char* encoded) {
  try {
    if (encoded == nullptr) throw std::runtime_error("null input");
    result_buffer = evaluate(encoded);
  } catch (const std::exception& error) {
    result_buffer = std::string("ERROR:") + error.what();
  }
  return result_buffer.c_str();
}
