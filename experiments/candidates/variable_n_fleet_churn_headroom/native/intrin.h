#pragma once

// GCC equivalents for the two exact unsigned-integer primitives used by the
// unchanged R09 translation unit included by headroom_backend.cpp.  The Linux
// build alone adds this owned directory to the angle-include search path.
#if !defined(_WIN32)
#include <cstdint>

inline unsigned char _addcarry_u64(
    unsigned char carry, std::uint64_t left, std::uint64_t right,
    std::uint64_t* output
) {
    const auto sum = static_cast<unsigned __int128>(left)
        + static_cast<unsigned __int128>(right)
        + static_cast<unsigned __int128>(carry);
    *output = static_cast<std::uint64_t>(sum);
    return static_cast<unsigned char>(sum >> 64);
}

inline std::uint64_t _umul128(
    std::uint64_t left, std::uint64_t right, std::uint64_t* high
) {
    const auto product = static_cast<unsigned __int128>(left)
        * static_cast<unsigned __int128>(right);
    *high = static_cast<std::uint64_t>(product >> 64);
    return static_cast<std::uint64_t>(product);
}
#endif
