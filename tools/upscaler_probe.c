/* Standalone provider enumeration only; no scene resources or temporal dispatch.
 * Compile with snap_fsr_sdk.c and NEWSNAP_FSR_SDK=1; place the executable beside upscalers/.
 * The game uses the same query with its existing Vulkan device, never this new device. */
#include "snap_fsr_sdk.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int dispatch_probe(SnapFsrSdk *sdk, const SnapFsrDevice *d, uint32_t family, uint64_t provider) {
    SnapFsrConfig config={.render_width=64,.render_height=64,.output_width=96,.output_height=96,
        .generation=1,.hdr=1,.inverted_depth=1,.infinite_depth=1,.auto_exposure=1,.device_contract_verified=1};
    if(!snap_fsr_sdk_create(sdk,d,&config,provider)) { puts("Context creation failed"); snap_fsr_sdk_close(sdk); return 4; }
    uint64_t total,aliasable;
    if(snap_fsr_sdk_memory_usage(sdk,&total,&aliasable))
        printf("SDK context memory query: total=%llu bytes aliasable=%llu bytes\n",(unsigned long long)total,(unsigned long long)aliasable);
    else puts("SDK context memory query: unknown (query unavailable)");
    VkImage images[4]={0}; VkDeviceMemory memory[4]={0}; VkCommandPool pool=0;
    SnapFsrFrame frame={.scene_contract_verified=1,.reset=1,.delta_ms=16.67f,.pre_exposure=1,
        .camera_near=.01f,.camera_far=1000000,.vertical_fov=1,.meters_factor=1,.motion_scale_x=1,.motion_scale_y=1};
    SnapFsrImage *resources[]={&frame.color,&frame.depth,&frame.motion,&frame.output};
    VkFormat formats[]={VK_FORMAT_R16G16B16A16_SFLOAT,VK_FORMAT_R32_SFLOAT,VK_FORMAT_R16G16_SFLOAT,VK_FORMAT_R16G16B16A16_SFLOAT};
    VkPhysicalDeviceMemoryProperties mp; vkGetPhysicalDeviceMemoryProperties(d->physical_device,&mp);
    int result=4;
    for(unsigned i=0;i<4;i++) {
        uint32_t size=i==3?96:64;
        VkImageUsageFlags usage=VK_IMAGE_USAGE_TRANSFER_DST_BIT | (i==3?VK_IMAGE_USAGE_STORAGE_BIT:VK_IMAGE_USAGE_SAMPLED_BIT);
        VkImageCreateInfo ci={.sType=VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,.imageType=VK_IMAGE_TYPE_2D,.format=formats[i],
            .extent={size,size,1},.mipLevels=1,.arrayLayers=1,.samples=VK_SAMPLE_COUNT_1_BIT,.tiling=VK_IMAGE_TILING_OPTIMAL,.usage=usage};
        if(vkCreateImage(d->device,&ci,NULL,&images[i])!=VK_SUCCESS) goto done;
        VkMemoryRequirements req; vkGetImageMemoryRequirements(d->device,images[i],&req);
        uint32_t type=0; while(type<mp.memoryTypeCount && !(req.memoryTypeBits&(1u<<type))) type++;
        if(type==mp.memoryTypeCount) goto done;
        VkMemoryAllocateInfo ai={.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,.allocationSize=req.size,.memoryTypeIndex=type};
        if(vkAllocateMemory(d->device,&ai,NULL,&memory[i])!=VK_SUCCESS || vkBindImageMemory(d->device,images[i],memory[i],0)!=VK_SUCCESS) goto done;
        *resources[i]=(SnapFsrImage){.image=images[i],.format=formats[i],.width=size,.height=size,.samples=1,.layers=1,.mips=1,.generation=1,
            .usage=usage,.layout=i==3?VK_IMAGE_LAYOUT_GENERAL:VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
    }
    VkCommandPoolCreateInfo pi={.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,.queueFamilyIndex=family};
    if(vkCreateCommandPool(d->device,&pi,NULL,&pool)!=VK_SUCCESS) goto done;
    VkCommandBufferAllocateInfo cai={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,.commandPool=pool,.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY,.commandBufferCount=1};
    if(vkAllocateCommandBuffers(d->device,&cai,&frame.command_buffer)!=VK_SUCCESS) goto done;
    VkCommandBufferBeginInfo bi={.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    if(vkBeginCommandBuffer(frame.command_buffer,&bi)!=VK_SUCCESS) goto done;
    for(unsigned i=0;i<4;i++) {
        VkImageMemoryBarrier b={.sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,.oldLayout=VK_IMAGE_LAYOUT_UNDEFINED,
            .newLayout=VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,.dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT,
            .srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,.image=images[i],
            .subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1}};
        vkCmdPipelineBarrier(frame.command_buffer,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,NULL,0,NULL,1,&b);
        VkClearColorValue value={{0,0,0,0}};
        if(i==0) value=(VkClearColorValue){{.25f,.5f,.75f,1}};
        if(i==1) value=(VkClearColorValue){{.5f,0,0,0}};
        vkCmdClearColorImage(frame.command_buffer,images[i],VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,&value,1,&b.subresourceRange);
        b.oldLayout=b.newLayout; b.newLayout=resources[i]->layout;b.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
        b.dstAccessMask=i==3?VK_ACCESS_SHADER_WRITE_BIT:VK_ACCESS_SHADER_READ_BIT;
        vkCmdPipelineBarrier(frame.command_buffer,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,0,NULL,0,NULL,1,&b);
    }
    if(!snap_fsr_sdk_dispatch(sdk,&frame)) { puts("Dispatch recording failed"); goto done; }
    if(vkEndCommandBuffer(frame.command_buffer)!=VK_SUCCESS) goto done;
    VkQueue queue; vkGetDeviceQueue(d->device,family,0,&queue);
    VkSubmitInfo si={.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO,.commandBufferCount=1,.pCommandBuffers=&frame.command_buffer};
    if(vkQueueSubmit(queue,1,&si,VK_NULL_HANDLE)!=VK_SUCCESS || vkQueueWaitIdle(queue)!=VK_SUCCESS) goto done;
    puts("Official SDK FSR3 synthetic HDR reverse-infinite-Z dispatch submitted and completed; no Snap scene quality claim."); result=0;
done:
    vkDeviceWaitIdle(d->device);
    /* SDK owns registered views; destroy its context before the input images. */
    snap_fsr_sdk_close(sdk);
    if(pool) vkDestroyCommandPool(d->device,pool,NULL);
    for(unsigned i=0;i<4;i++) { if(images[i]) vkDestroyImage(d->device,images[i],NULL); if(memory[i]) vkFreeMemory(d->device,memory[i],NULL); }
    return result;
}

int main(int argc, char **argv) {
    int dispatch=argc==2 && !strcmp(argv[1],"--dispatch");
    VkApplicationInfo app = {.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO,.pApplicationName="NewSnap SDK provider probe",.apiVersion=VK_API_VERSION_1_3};
    VkInstanceCreateInfo ci = {.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,.pApplicationInfo=&app};
    VkInstance instance = VK_NULL_HANDLE;
    if (vkCreateInstance(&ci,NULL,&instance)!=VK_SUCCESS) return 2;
    uint32_t count=0;
    if (vkEnumeratePhysicalDevices(instance,&count,NULL)!=VK_SUCCESS || !count) { vkDestroyInstance(instance,NULL); return 2; }
    VkPhysicalDevice *devices=calloc(count,sizeof *devices);
    if (!devices) { vkDestroyInstance(instance,NULL); return 2; }
    if (vkEnumeratePhysicalDevices(instance,&count,devices)!=VK_SUCCESS) { free(devices); vkDestroyInstance(instance,NULL); return 2; }
    SnapFsrSdk *sdk=snap_fsr_sdk_open();
    int result=sdk ? 0 : 3;
    if (!sdk) puts("FSR SDK unavailable: native/spatial fallback");
    for (uint32_t i=0;sdk && i<count;i++) {
        VkPhysicalDeviceProperties props; vkGetPhysicalDeviceProperties(devices[i],&props);
        uint32_t families=0; vkGetPhysicalDeviceQueueFamilyProperties(devices[i],&families,NULL);
        VkQueueFamilyProperties *queues=calloc(families,sizeof *queues);
        if (!queues) { result=2; break; }
        vkGetPhysicalDeviceQueueFamilyProperties(devices[i],&families,queues);
        uint32_t family=0;
        while(family<families && !(queues[family].queueFlags&VK_QUEUE_COMPUTE_BIT)) family++;
        free(queues); if(family==families) continue;
        float priority=1;
        VkDeviceQueueCreateInfo qi={.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,.queueFamilyIndex=family,.queueCount=1,.pQueuePriorities=&priority};
        VkPhysicalDeviceVulkan13Features f13={.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES};
        VkPhysicalDeviceVulkan12Features f12={.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES,.pNext=&f13};
        VkPhysicalDeviceVulkan11Features f11={.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES,.pNext=&f12};
        VkPhysicalDeviceFeatures2 f2={.sType=VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2,.pNext=&f11};
        vkGetPhysicalDeviceFeatures2(devices[i],&f2);
        VkDeviceCreateInfo di={.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,.pNext=&f2,.queueCreateInfoCount=1,.pQueueCreateInfos=&qi};
        VkDevice device;
        if(vkCreateDevice(devices[i],&di,NULL,&device)!=VK_SUCCESS) { result=2; continue; }
        SnapFsrDevice d={device,devices[i],vkGetDeviceProcAddr}; SnapFsrProvider providers[32];
        uint32_t n=snap_fsr_sdk_query(sdk,&d,providers,32);
        printf("GPU: %s; vendor=%04x; providers=%u\n",props.deviceName,props.vendorID,n);
        for(uint32_t j=0;j<n;j++) printf("  %016llx %s\n",(unsigned long long)providers[j].id,providers[j].name);
        puts("Enumeration only: device features and Snap temporal resource contract remain separate gates.");
        if(dispatch && n) {
            /* This consumes sdk; each invocation dispatches on one GPU only. */
            result=dispatch_probe(sdk,&d,family,providers[0].id); sdk=NULL;
        }
        vkDestroyDevice(device,NULL);
    }
    snap_fsr_sdk_close(sdk); free(devices); vkDestroyInstance(instance,NULL); return result;
}
