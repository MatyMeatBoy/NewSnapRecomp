#include "snap_vrr_writer.h"
#include "platform/platform.h"
#include "host.h"
#include <string.h>

static struct {
    PlatMutex lock;
    PlatCond ready;
    PlatThread *thread;
    char path[PLAT_PATH_MAX], pending[2048];
    size_t length;
    int stop, failed;
} W;

static void writer(void *argument) {
    (void)argument;
    char json[2048];
    for(;;) {
        plat_mutex_lock(&W.lock);
        while(!W.length && !W.stop)plat_cond_wait(&W.ready,&W.lock);
        if(!W.length && W.stop) { plat_mutex_unlock(&W.lock);return; }
        size_t n=W.length;memcpy(json,W.pending,n);W.length=0;
        plat_mutex_unlock(&W.lock);
        if(!plat_file_write_atomic(W.path,json,n)) {
            plat_mutex_lock(&W.lock);int first=!W.failed;W.failed=1;W.length=0;plat_mutex_unlock(&W.lock);
            if(first)rt_log("display: status write failed; observation unavailable (further failures suppressed)");
        }
    }
}

void snap_vrr_writer_stop(void) {
    if(!W.thread)return;
    plat_mutex_lock(&W.lock);W.stop=1;plat_cond_signal(&W.ready);plat_mutex_unlock(&W.lock);
    /* Worker has no Vulkan/window references and needs no queue/present lock to complete. */
    plat_thread_join(W.thread);W.thread=NULL;
}

void snap_vrr_writer_start(void) {
    snap_vrr_writer_stop();
    W.path[0]=0;W.length=0;W.stop=W.failed=0;
    if(!plat_getenv("NEWSNAP_DISPLAY_STATUS",W.path,sizeof W.path))return;
#ifdef _WIN32
    if(!((W.path[0] && W.path[1]==':' && (W.path[2]=='\\' || W.path[2]=='/')) || (W.path[0]=='\\' && W.path[1]=='\\')))return;
#else
    if(W.path[0]!='/')return;
#endif
    W.thread=plat_thread_new(writer,NULL,"display-status");
    if(!W.thread) { W.failed=1;rt_log("display: status writer unavailable; no observation file will be published"); }
}

void snap_vrr_writer_publish(const SnapVrrStatus *status) {
    if(!W.thread)return;
    SnapVrrStatus copy=*status;
    copy.process_id=plat_process_id();
    plat_mutex_lock(&W.lock);
    if(W.failed) {
        snap_vrr_apply_result(&copy,VK_ERROR_UNKNOWN,0,0,copy.observed_ns);
        memcpy(copy.reason,"status_write_failed",sizeof "status_write_failed");
    }
    /* Serializing/copying bounded CPU data is the only work shared with the present thread. */
    size_t n=snap_vrr_json(&copy,W.pending,sizeof W.pending);
    if(n) { W.length=n;plat_cond_signal(&W.ready); }
    plat_mutex_unlock(&W.lock);
}
