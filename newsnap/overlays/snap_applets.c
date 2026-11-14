// KEYBOARD-CRASH: system dialogs and online entry points Snap can reach that the
// host has no service for.
//
// The inherited runtime only answers a short list of IPC services (ipc.c).  An
// SDK function outside that list ends in rt_fatal("sm: service ... is not
// implemented") or runs against client state the host never initialised: the
// process exits and the player sees the game close.  Snap 2.0.1 imports such
// functions for its error dialogs, the network request, the Nintendo account
// link, the friend profile and the console album.
//
// Each override gives the answer an offline console gives after the player
// dismisses the system dialog, and logs what the game asked for.  Nothing here
// touches game state, progress, photographs or saves: the game's own handling
// of "dialog closed / no network / no linked account" runs unchanged.
// err::ShowError(Result) already works this way upstream (ov_system.c).
#include <stdint.h>
#include <string.h>

#include "host.h"
#include "platform/platform.h"

// Failure values.  The game only tests success, so the module is what matters
// for its own error text; descriptions are the SDK's as far as they are known.
#define SNAP_R_ACCOUNT_CANCELLED RT_RESULT(124, 0)      // 2124-0000: the player closed the account dialog
#define SNAP_R_ACCOUNT_NO_NSA RT_RESULT(124, 100)       // 2124-0100: no linked Nintendo Account
#define SNAP_R_NETWORK_UNRESOLVED RT_RESULT(110, 1)     // nifm: the request stays rejected (description not from SDK tables)
#define SNAP_R_ALBUM_UNAVAILABLE RT_RESULT(206, 1)      // capsrv: no console album on this host (description not from SDK tables)

// nn::err::ApplicationErrorArg as the SDK constructor fills it (sdk+0x15c6xx):
// number at +8, dialog text at +0x14, full-screen text at +0x814, each a
// NUL-terminated UTF-8 string of at most 0x800 bytes.
enum { APP_ERROR_NUMBER = 0x8, APP_ERROR_DIALOG = 0x14, APP_ERROR_FULLSCREEN = 0x814, APP_ERROR_TEXT = 0x800,
       APP_ERROR_SIZE = 0x1014 };

// A dialog the game repeats every frame must not bury the rest of the log.
static int snap_applet_log_budget(volatile int32_t *count) {
    return __atomic_fetch_add(count, 1, __ATOMIC_RELAXED) < 16;
}

// Bounded, printable copy of a guest string for the log.
static void snap_applet_text(const uint8_t *text, size_t limit, char *out, size_t cap) {
    size_t n = 0;
    for (size_t i = 0; i < limit && text[i] && n + 1 < cap; i++)
        out[n++] = text[i] < 0x20 || text[i] == 0x7f ? ' ' : (char)text[i];
    out[n] = 0;
}

static const char *snap_applet_caller(const Cpu *c, char *buf, int n) { return ldr_describe(c->x[30] - 4, buf, n); }

// void nn::err::ShowApplicationError(const ApplicationErrorArg &)
static void snap_show_application_error(Cpu *c) {
    static volatile int32_t shown;
    const uint8_t *arg = arg_p(c, 0);
    char from[96], dialog[241] = "", full[241] = "";
    uint32_t number = 0;
    if (arg && plat_mem_readable((uint64_t)(uintptr_t)arg, APP_ERROR_SIZE)) {
        memcpy(&number, arg + APP_ERROR_NUMBER, sizeof number);
        snap_applet_text(arg + APP_ERROR_DIALOG, APP_ERROR_TEXT, dialog, sizeof dialog);
        snap_applet_text(arg + APP_ERROR_FULLSCREEN, APP_ERROR_TEXT, full, sizeof full);
    }
    if (snap_applet_log_budget(&shown))
        rt_log("err: game application error dialog %u from %s: \"%s\" / \"%s\" (shown as dismissed; no system applet)",
               number, snap_applet_caller(c, from, sizeof from), dialog, full);
}
HOST_OVERRIDE("_ZN2nn3err20ShowApplicationErrorERKNS0_19ApplicationErrorArgE", snap_show_application_error);

// void nn::err::ShowError(const ErrorResultVariant &): a Result or an ErrorCode behind a tag
static void snap_show_error_variant(Cpu *c) {
    static volatile int32_t shown;
    const uint8_t *arg = arg_p(c, 0);
    char from[96];
    uint32_t words[4] = {0};
    if (arg && plat_mem_readable((uint64_t)(uintptr_t)arg, sizeof words)) memcpy(words, arg, sizeof words);
    if (snap_applet_log_budget(&shown))
        rt_log("err: game error dialog (variant %08x %08x %08x %08x) from %s (shown as dismissed; no system applet)",
               words[0], words[1], words[2], words[3], snap_applet_caller(c, from, sizeof from));
}
HOST_OVERRIDE("_ZN2nn3err9ShowErrorERKNS0_18ErrorResultVariantE", snap_show_error_variant);

// ---- network: the host exposes no connection (snap_host.c answers IsNetworkAvailable with false)
// void nn::nifm::SubmitNetworkRequestAndWait(): the request is made and rejected
static void snap_network_request(Cpu *c) {
    static volatile int32_t asked;
    char from[96];
    if (snap_applet_log_budget(&asked))
        rt_log("nifm: network request from %s: rejected, the host is offline", snap_applet_caller(c, from, sizeof from));
}
HOST_OVERRIDE("_ZN2nn4nifm27SubmitNetworkRequestAndWaitEv", snap_network_request);

// Result nn::nifm::HandleNetworkRequestErrorResult(): the console shows why the request failed; it stays failed
static void snap_network_error_dialog(Cpu *c) {
    static volatile int32_t shown;
    char from[96];
    if (snap_applet_log_budget(&shown))
        rt_log("nifm: network error dialog from %s (shown as dismissed, still offline)",
               snap_applet_caller(c, from, sizeof from));
    ret_x(c, SNAP_R_NETWORK_UNRESOLVED);
}
HOST_OVERRIDE("_ZN2nn4nifm31HandleNetworkRequestErrorResultEv", snap_network_error_dialog);

static void snap_network_cancel(Cpu *c) { (void)c; }
HOST_OVERRIDE("_ZN2nn4nifm20CancelNetworkRequestEv", snap_network_cancel);

// Result nn::nifm::GetCurrentPrimaryIpAddress(in_addr *)
static void snap_network_address(Cpu *c) {
    uint32_t *out = arg_p(c, 0);
    if (out) *out = 0;
    ret_x(c, SNAP_R_NETWORK_UNRESOLVED);
}
HOST_OVERRIDE("_ZN2nn4nifm26GetCurrentPrimaryIpAddressEP7in_addr", snap_network_address);

// Result nn::nifm::GetCurrentProxySetting(ProxySetting *): no connection, nothing written
static void snap_network_proxy(Cpu *c) { ret_x(c, SNAP_R_NETWORK_UNRESOLVED); }
HOST_OVERRIDE("_ZN2nn4nifm22GetCurrentProxySettingEPNS0_12ProxySettingE", snap_network_proxy);

// ---- Nintendo Account: the local account (ov_system.c account_uid) has none linked
// Result nn::account::IsNetworkServiceAccountAvailable(bool *, const UserHandle &)
static void snap_account_linked(Cpu *c) {
    uint8_t *out = arg_p(c, 0);
    if (!out) rt_fatal("account IsNetworkServiceAccountAvailable: null output");
    *out = 0;
    ret_x(c, 0);
}
HOST_OVERRIDE("_ZN2nn7account32IsNetworkServiceAccountAvailableEPbRKNS0_10UserHandleE", snap_account_linked);

// Result nn::account::EnsureNetworkServiceAccountAvailable(const UserHandle &): the console offers to link one
static void snap_account_ensure(Cpu *c) {
    static volatile int32_t shown;
    char from[96];
    if (snap_applet_log_budget(&shown))
        rt_log("account: Nintendo Account link dialog from %s (shown as cancelled; local account only)",
               snap_applet_caller(c, from, sizeof from));
    ret_x(c, SNAP_R_ACCOUNT_CANCELLED);
}
HOST_OVERRIDE("_ZN2nn7account36EnsureNetworkServiceAccountAvailableERKNS0_10UserHandleE", snap_account_ensure);

static void snap_account_unavailable(Cpu *c) { ret_x(c, SNAP_R_ACCOUNT_NO_NSA); }
HOST_OVERRIDE("_ZN2nn7account26GetNetworkServiceAccountIdEPNS0_23NetworkServiceAccountIdERKNS0_10UserHandleE",
              snap_account_unavailable);
HOST_OVERRIDE("_ZN2nn7account44EnsureNetworkServiceAccountIdTokenCacheAsyncEPNS0_12AsyncContextERKNS0_10UserHandleE",
              snap_account_unavailable);
HOST_OVERRIDE("_ZN2nn7account37LoadNetworkServiceAccountIdTokenCacheEPmPcmRKNS0_10UserHandleE",
              snap_account_unavailable);

// ---- friends: no friend service; the profile page is a system applet
static void snap_friends_initialize(Cpu *c) { (void)c; }
HOST_OVERRIDE("_ZN2nn7friends10InitializeEv", snap_friends_initialize);

// Result nn::friends::ShowUserDetailInfo(uid, account id, screen names)
static void snap_friends_profile(Cpu *c) {
    static volatile int32_t shown;
    char from[96];
    if (snap_applet_log_budget(&shown))
        rt_log("friends: user profile applet from %s (shown as closed; no friend service)",
               snap_applet_caller(c, from, sizeof from));
    ret_x(c, 0);
}
HOST_OVERRIDE("_ZN2nn7friends18ShowUserDetailInfoERKNS_7account3UidERKNS1_23NetworkServiceAccountIdERKNS0_15InAppScreenNameESA_",
              snap_friends_profile);

// ---- console album: not present on this host.  The launcher's album reads the
// game's own photo banks; nothing is written here.
static void snap_album_noop(Cpu *c) { (void)c; }
HOST_OVERRIDE("_ZN2nn5album10InitializeEv", snap_album_noop);
HOST_OVERRIDE("_ZN2nn5album8FinalizeEv", snap_album_noop);

// Result nn::album::SaveScreenshot(const void *, size_t, ImageSize, ImageOrientation, AlbumReportOption)
static void snap_album_save(Cpu *c) {
    static volatile int32_t asked;
    char from[96];
    if (snap_applet_log_budget(&asked))
        rt_log("album: SaveScreenshot of %llu bytes from %s: refused, no console album on this host",
               (unsigned long long)arg_x(c, 1), snap_applet_caller(c, from, sizeof from));
    ret_x(c, SNAP_R_ALBUM_UNAVAILABLE);
}
HOST_OVERRIDE("_ZN2nn5album14SaveScreenshotEPKvmNS0_9ImageSizeENS0_16ImageOrientationENS0_17AlbumReportOptionE",
              snap_album_save);
