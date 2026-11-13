/* Pure observation contract; no display settings or presentation policy changes. */
#include "snap_vrr.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

int snap_vrr_instance_capabilities;

void snap_vrr_reset(SnapVrrStatus *s, uint64_t generation, uint64_t now, const char *reason) {
    memset(s, 0, sizeof *s);
    s->generation=generation; s->observed_ns=now; s->result=VK_NOT_READY;
    snprintf(s->reason,sizeof s->reason,"%s",reason ? reason : "not_observed");
}

void snap_vrr_apply_result(SnapVrrStatus *s, VkResult result, uint64_t duration, uint64_t interval, uint64_t now) {
    s->observed_ns=now; s->result=result; s->presentation=SNAP_REFRESH_UNKNOWN;
    s->refresh_duration_ns=s->refresh_interval_ns=0;
    const char *reason="query_failed";
    if(result==VK_NOT_READY) reason="not_ready";
    else if(result==VK_SUCCESS) {
        if(!duration || !interval) reason="timing_unknown";
        else if(interval==UINT64_MAX) { s->presentation=SNAP_REFRESH_VARIABLE; reason="observed_variable"; }
        else if(interval==duration) { s->presentation=SNAP_REFRESH_FIXED; reason="observed_fixed"; }
        else reason="unclassified_timing";
        s->refresh_duration_ns=duration; s->refresh_interval_ns=interval;
    }
    snprintf(s->reason,sizeof s->reason,"%s",reason);
}

typedef struct { char *out; size_t capacity, length; int failed; } Json;
static void put(Json *j,const char *format,...) {
    if(j->failed)return;
    va_list args;va_start(args,format);
    int n=vsnprintf(j->out+j->length,j->capacity-j->length,format,args);
    va_end(args);
    if(n<0 || (size_t)n>=j->capacity-j->length)j->failed=1;
    else j->length+=(size_t)n;
}
static void quoted(Json *j,const char *value,size_t bound) {
    put(j,"\"");
    for(size_t i=0;i<bound && value[i];i++) {
        unsigned char c=(unsigned char)value[i];
        if(c=='\\' || c=='\"')put(j,"\\%c",c);
        else if(c<32)put(j,"\\u%04x",c);
        else put(j,"%c",c);
    }
    put(j,"\"");
}
size_t snap_vrr_json(const SnapVrrStatus *s,char *output,size_t capacity) {
    if(!s || !output || !capacity)return 0;
    Json j={output,capacity,0,0};
    const char *state=s->presentation==SNAP_REFRESH_FIXED?"fixed":s->presentation==SNAP_REFRESH_VARIABLE?"variable":"unknown";
    put(&j,"{\"format\":\"newsnap-display-status-v1\",\"version\":1,\"source\":\"%s\",\"presentation\":\"%s\",\"display_support\":\"unknown\",\"driver_enabled\":\"unknown\",\"timing_api_available\":%s,\"generation\":%llu,\"observed_monotonic_ns\":%llu,\"process_id\":%u,\"vk_result\":%d,\"refresh_duration_ns\":%llu,\"refresh_interval_ns\":%llu,\"reason\":",
        s->presentation==SNAP_REFRESH_UNKNOWN?"none":"vulkan_ext_present_timing",state,s->timing_api_available?"true":"false",(unsigned long long)s->generation,(unsigned long long)s->observed_ns,s->process_id,(int)s->result,
        (unsigned long long)s->refresh_duration_ns,(unsigned long long)s->refresh_interval_ns);
    quoted(&j,s->reason,sizeof s->reason); put(&j,",\"monitor_id\":");quoted(&j,s->monitor_id,sizeof s->monitor_id);
    put(&j,",\"monitor_name\":");quoted(&j,s->monitor_name,sizeof s->monitor_name);
    put(&j,",\"actual_present_mode\":");quoted(&j,s->present_mode,sizeof s->present_mode);put(&j,"}\n");
    if(j.failed) { output[0]=0;return 0; } return j.length;
}

int snap_vrr_append_extension(const char **names,uint32_t *count,uint32_t capacity,const char *name) {
    if(!names || !count || !name || *count>capacity)return 0;
    for(uint32_t i=0;i<*count;i++)if(!strcmp(names[i],name))return 1;
    if(*count==capacity)return 0;
    names[(*count)++]=name;return 1;
}
int snap_vrr_extension_bundle(const VkExtensionProperties *properties,uint32_t count) {
    const char *required[]={"VK_EXT_present_timing","VK_KHR_present_id2","VK_KHR_calibrated_timestamps","VK_KHR_swapchain"};
    if(!snap_vrr_instance_capabilities)return 0;
    for(unsigned i=0;i<sizeof required/sizeof *required;i++) {
        int found=0;
        for(uint32_t k=0;k<count;k++)if(!strcmp(properties[k].extensionName,required[i]))found=1;
        if(!found)return 0;
    }
    return 1;
}
