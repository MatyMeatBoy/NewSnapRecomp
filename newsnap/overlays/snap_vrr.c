/* Optional status-only query of the game's real swapchain. No timing queues or scheduling. */
#include "snap_vrr.h"
#include "snap_vrr_writer.h"
#include "platform/platform.h"
#include <stdio.h>
#include <string.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
extern HWND gfx_window_handle(void);
#endif

static struct {
    SnapVrrStatus status;
    VkDevice device;
    VkSwapchainKHR swapchain;
    uint64_t generation, last_poll_ns;
    uintptr_t monitor_token;
#ifdef VK_EXT_present_timing
    PFN_vkGetSwapchainTimingPropertiesEXT query;
#endif
} V;

static void publish(void) {
    snap_vrr_writer_publish(&V.status);
}

static void monitor(char *id,size_t id_cap,char *name,size_t name_cap,uintptr_t *token) {
    id[0]=name[0]=0;*token=0;
#ifdef _WIN32
    HWND hwnd=gfx_window_handle();
    HMONITOR mon=hwnd?MonitorFromWindow(hwnd,MONITOR_DEFAULTTONULL):NULL;
    MONITORINFOEXW info={0};info.cbSize=sizeof info;
    if(!mon || !GetMonitorInfoW(mon,(MONITORINFO *)&info))return;
    *token=(uintptr_t)mon;
    if(!WideCharToMultiByte(CP_UTF8,0,info.szDevice,-1,id,(int)id_cap,NULL,NULL))id[0]=0;
    DISPLAY_DEVICEW display={0};display.cb=sizeof display;
    if((uintptr_t)mon==V.monitor_token && !strcmp(id,V.status.monitor_id))
        snprintf(name,name_cap,"%s",V.status.monitor_name);
    else if(EnumDisplayDevicesW(info.szDevice,0,&display,0))
        if(!WideCharToMultiByte(CP_UTF8,0,display.DeviceString,-1,name,(int)name_cap,NULL,NULL))name[0]=0;
#else
    (void)id_cap;(void)name_cap;
#endif
}

static void reset(const char *reason,uint64_t now) {
    char mode[24];memcpy(mode,V.status.present_mode,sizeof mode);
    snap_vrr_reset(&V.status,++V.generation,now,reason);
    memcpy(V.status.present_mode,mode,sizeof mode);
#ifdef VK_EXT_present_timing
    V.status.timing_api_available=V.query!=NULL;
#endif
    monitor(V.status.monitor_id,sizeof V.status.monitor_id,V.status.monitor_name,sizeof V.status.monitor_name,&V.monitor_token);
    V.last_poll_ns=0;
}

void snap_vrr_device_ready(VkDevice device,int enabled) {
    snap_vrr_writer_start();
    uint64_t generation=V.generation;
    memset(&V,0,sizeof V);V.generation=generation;V.device=device;
#ifdef VK_EXT_present_timing
    if(enabled)V.query=(PFN_vkGetSwapchainTimingPropertiesEXT)vkGetDeviceProcAddr(device,"vkGetSwapchainTimingPropertiesEXT");
#else
    (void)enabled;
#endif
    reset(enabled?"no_swapchain":"extension_unavailable",plat_now_ns());publish();
}

void snap_vrr_swapchain_changed(VkSwapchainKHR swapchain,const char *mode) {
    V.swapchain=swapchain;
    snprintf(V.status.present_mode,sizeof V.status.present_mode,"%s",mode?mode:"unknown");
    reset(V.status.timing_api_available?"not_observed":"extension_unavailable",plat_now_ns());publish();
}

void snap_vrr_after_present(VkDevice device,VkSwapchainKHR swapchain,VkResult present_result) {
    uint64_t now=plat_now_ns();
    char id[96],name[192];uintptr_t token;
    monitor(id,sizeof id,name,sizeof name,&token);
    if(token!=V.monitor_token || strcmp(id,V.status.monitor_id)) { reset("monitor_changed",now);publish(); }
    if(device!=V.device || swapchain!=V.swapchain || !swapchain) { reset("swapchain_mismatch",now);publish();return; }
    if(present_result!=VK_SUCCESS && present_result!=VK_SUBOPTIMAL_KHR) {
        snap_vrr_apply_result(&V.status,present_result,0,0,now);publish();return;
    }
    if(V.last_poll_ns && now-V.last_poll_ns<1000000000ull)return;
    V.last_poll_ns=now;
#ifdef VK_EXT_present_timing
    if(V.query) {
        VkSwapchainTimingPropertiesEXT timing={.sType=VK_STRUCTURE_TYPE_SWAPCHAIN_TIMING_PROPERTIES_EXT};
        uint64_t counter;
        VkResult result=V.query(device,swapchain,&timing,&counter);
        snap_vrr_apply_result(&V.status,result,timing.refreshDuration,timing.refreshInterval,now);
    } else
#endif
    {
        snap_vrr_apply_result(&V.status,VK_NOT_READY,0,0,now);
        snprintf(V.status.reason,sizeof V.status.reason,"%s","extension_unavailable");
    }
    publish();
}

void snap_vrr_shutdown(void) {
    V.swapchain=VK_NULL_HANDLE;
#ifdef VK_EXT_present_timing
    V.query=NULL;
#endif
    reset("stopped",plat_now_ns());publish();
    V.device=VK_NULL_HANDLE;
    snap_vrr_writer_stop();
}
