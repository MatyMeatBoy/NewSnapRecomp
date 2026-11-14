// Presentation policy for Snap: retain the game's own grading and tone mapping.
#pragma once
#include <string.h>
static inline const char *snap_neutral_value(const char *name) {
    char key[64]; unsigned i=0;
    if(!name)return 0;
    while(name[i] && i<sizeof key-1) { char c=name[i];key[i]=(c>='a'&&c<='z')?c-32:c;i++; }
    if(name[i])return 0;
    key[i]=0;
    const char *k=!strncmp(key,"AC_",3)?key+3:key;
    if(!strcmp(k,"COLOR_PRESET"))return "default";
    if(!strcmp(k,"COLOR_BRIGHTNESS")||!strcmp(k,"SHARPNESS")||!strcmp(k,"HDR")||
       !strcmp(k,"CONTACT_SHADOWS")||!strcmp(k,"PCSS"))return "0";
    if(!strcmp(k,"COLOR_CONTRAST")||!strcmp(k,"COLOR_SATURATION"))return "100";
    if(!strcmp(k,"COLOR_GAMMA"))return "1";   // SHADOW_SCALE is a resolution choice (SS-02), not grading
    if(!strcmp(k,"UPSCALER"))return "bilinear";
    if(!strcmp(k,"AO"))return "off";
    return 0;
}
