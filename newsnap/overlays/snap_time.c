// Snap's explicit device-time-zone APIs. The host owns nn::time initialization;
// its clock/calendar implementation must also own the opaque rule's consumer.
// Rule storage sizes follow libnx time.h (layout reference only).
#include <stdint.h>
#include <string.h>
#include "host.h"

extern void ov_time_location(char out[0x24]);
extern void ov_time_calendar(Cpu *c);
#define SNAP_TIME_INVALID 0x74u
#define SNAP_RULE_SIZE 0x4000
#define SNAP_RULE_MAGIC UINT64_C(0x534e4150545a3031)
typedef struct { uint64_t magic; char location[0x24]; } SnapTimeRule;

static void snap_device_location(Cpu *c) {
    char *out = arg_p(c, 0);
    if (!out) rt_fatal("time GetDeviceLocationName: null output");
    ov_time_location(out);
    c->x[0] = 0;
}

static void snap_load_time_rule(Cpu *c) {
    void *out = arg_p(c, 0);
    const char *location = arg_p(c, 1);
    SnapTimeRule rule = {.magic = SNAP_RULE_MAGIC};
    ov_time_location(rule.location);
    // Device-zone conversion only. Arbitrary IANA zones and Nintendo's binary
    // tzdata format are not supported, and must not be silently accepted.
    if (!out || !location || memcmp(location, rule.location, 0x24)) {
        c->x[0] = SNAP_TIME_INVALID;
        return;
    }
    memset(out, 0, SNAP_RULE_SIZE);
    memcpy(out, &rule, sizeof rule);
    c->x[0] = 0;
}

static void snap_to_calendar_rule(Cpu *c) {
    const void *source = arg_p(c, 3);
    SnapTimeRule rule;
    char current[0x24];
    if (!source) { c->x[0] = SNAP_TIME_INVALID; return; }
    memcpy(&rule, source, sizeof rule);
    ov_time_location(current);
    if (rule.magic != SNAP_RULE_MAGIC || memcmp(rule.location, current, sizeof current)) {
        c->x[0] = SNAP_TIME_INVALID;
        return;
    }
    // Uses the OS's calendar and DST rules for the supplied POSIX timestamp,
    // exactly as the existing host ToCalendarTime and ClockSnapshot do.
    ov_time_calendar(c);
}

// There is no Nintendo network-clock service in this offline host. System time
// is available, but must not be advertised as a verified network clock.
static void snap_network_accuracy(Cpu *c) { c->x[0] = 0; }

HOST_OVERRIDE("_ZN2nn4time21GetDeviceLocationNameEPNS0_12LocationNameE", snap_device_location);
HOST_OVERRIDE("_ZN2nn4time16LoadTimeZoneRuleEPNS0_12TimeZoneRuleERKNS0_12LocationNameE", snap_load_time_rule);
HOST_OVERRIDE("_ZN2nn4time26StandardNetworkSystemClock20IsAccuracySufficientEv", snap_network_accuracy);
HOST_OVERRIDE("_ZN2nn4time14ToCalendarTimeEPNS0_12CalendarTimeEPNS0_22CalendarAdditionalInfoERKNS0_9PosixTimeERKNS0_12TimeZoneRuleE", snap_to_calendar_rule);
