// The in-game menu in Korean (MENU-LANG-01), every string of text_es (ui_text_es.inc).
// Included by ui_text.c in place of the keyboard-only Korean row.
static const char *const text_ko[UI_TEXT_COUNT] = {
    SWKBD("문자 입력", "이름을 입력하세요", "말", "확인", "취소", "컨트롤러: A 확인, B 취소"),

    [UI_MENU_TITLE] = "설정",
    [UI_MENU_TAB_SCREEN] = "화면", [UI_MENU_TAB_GAME] = "게임", [UI_MENU_TAB_MODS] = "모드", [UI_MENU_TAB_SOUND] = "사운드",
    [UI_MENU_TAB_CONTROLS] = "조작", [UI_MENU_TAB_MENU] = "메뉴", [UI_MENU_TAB_ADVANCED] = "고급",
    [UI_MENU_CONTINUE] = "계속하기", [UI_MENU_QUIT] = "게임 종료",
    [UI_MENU_ON] = "켬", [UI_MENU_OFF] = "끔", [UI_MENU_AUTO] = "자동",
    [UI_MENU_DEFAULT_MARK] = "기본값",
    [UI_MENU_AFTER_RESTART] = "재시작 후", [UI_MENU_SET_BY_ENV] = "환경 변수로 고정됨",
    [UI_MENU_SAVE_FAILED] = "설정을 저장하지 못했습니다",
    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",

    [UI_MENU_FULLSCREEN] = "전체 화면",
    [UI_MENU_FULLSCREEN_DESC] = "게임이 화면 전체를 사용합니다. F11로 전환합니다.",
    [UI_MENU_WINDOW_SIZE] = "창 크기",
    [UI_MENU_WINDOW_SIZE_DESC] = "전체 화면이 아닐 때의 게임 창 크기입니다.",
    [UI_MENU_WINDOW_SIZE_CUSTOM] = "사용자 지정",
    [UI_MENU_PRESENT] = "화면 출력 방식", [UI_MENU_PRESENT_DESC] = "완성된 프레임을 화면에 내보내는 방식입니다.",
    [UI_MENU_PRESENT_MAILBOX] = "Mailbox", [UI_MENU_PRESENT_VSYNC] = "VSync", [UI_MENU_PRESENT_IMMEDIATE] = "즉시",
    [UI_MENU_PRESENT_IN_USE] = "사용 중: %s",
    [UI_MENU_GPU] = "그래픽 카드", [UI_MENU_GPU_DESC] = "게임을 그리는 Vulkan 장치입니다.",
    [UI_MENU_GPU_AUTO] = "자동",
    [UI_MENU_PERF_OVERLAY] = "성능 정보",
    [UI_MENU_PERF_OVERLAY_DESC] = "오른쪽 위에 FPS를 표시합니다. '전체'는 프레임 시간 그래프, CPU·GPU·메모리 사용량, "
                                  "온도, 렌더 스레드 대기 시간을 추가로 표시합니다. F10으로 모드를 바꿉니다.",
    [UI_MENU_PERF_OFF] = "숨김", [UI_MENU_PERF_FPS] = "FPS", [UI_MENU_PERF_FULL] = "전체",
    [UI_PERF_LINE_FPS] = "%.0f fps",
    [UI_MENU_GRAPHICS] = "영상",
    [UI_MENU_OUTPUT_RES] = "게임 해상도",
    [UI_MENU_OUTPUT_RES_DESC] = "게임이 영상과 인터페이스를 그리는 크기입니다. 1280 x 720이 가장 가벼워 사양이 낮은 GPU에 "
                                "알맞습니다. 1920 x 1080을 넘으면 메모리(2560 x 1440에서 약 240 MB, 3840 x 2160에서 "
                                "790 MB 추가)와 GPU 시간이 더 필요합니다. 재시작 후 적용됩니다. '자동'은 화면 크기를 "
                                "따릅니다. 최대 1920 x 1080이며, 스케일러가 켜져 있으면 최대 3840 x 2160입니다.",
    [UI_MENU_UPSCALER] = "창 크기에 맞춘 스케일링",
    [UI_MENU_UPSCALER_DESC] = "영상을 창 크기에 맞추는 방식입니다. FSR은 바이리니어보다 윤곽과 디테일을 선명하게 유지하며, "
                              "영상이 이미 창에 맞는 크기여도 선명하게 다듬습니다.",
    [UI_MENU_UPSCALER_FSR] = "AMD FSR 1", [UI_MENU_UPSCALER_BILINEAR] = "바이리니어",
    [UI_MENU_FOV] = "시야각",
    [UI_MENU_FOV_DESC] = "카메라가 보여 주는 범위를 게임 원래 값(플레이 중 세로 50도)에 대한 백분율로 정합니다. "
                         "컷신은 게임 원래의 구도를 유지합니다.",
    [UI_MENU_ANISO] = "텍스처 필터링",
    [UI_MENU_ANISO_DESC] = "이방성 필터링: 비스듬히 보이는 바닥, 길, 벽이 멀리서도 흐려지지 않고 선명하게 보입니다. "
                           "게임: Switch와 같이 게임이 요청하는 수준입니다. 자동: 3D 스케일 1440p에서는 16x, "
                           "2160p에서는 게임 수준의 두 배, 그 밖에는 게임 수준을 사용합니다.",
    [UI_MENU_ANISO_GAME] = "게임",
    [UI_MENU_ANISO_AUTO] = "자동",
    [UI_MENU_SHARPNESS] = "FSR 선명도",
    [UI_MENU_SHARPNESS_DESC] = "FSR 스케일링 후의 선명화입니다. 0이면 끕니다.",
    [UI_MENU_COLOR] = "색상",
    [UI_MENU_COLOR_PRESET] = "색상 프로필",
    [UI_MENU_COLOR_PRESET_DESC] = "아래 네 가지 값을 설정합니다. 선명: 대비와 채도를 높이고 어두운 부분을 조금 밝게 합니다"
                                  "(OLED용). 또렷함: 대비, 채도, 밝기를 조금 높입니다. 값을 직접 바꾸면 프로필이 "
                                  "사용자 지정이 됩니다. HUD는 영상과 함께 바뀌지만 이 메뉴는 바뀌지 않습니다.",
    [UI_MENU_COLOR_DEFAULT] = "게임 기본", [UI_MENU_COLOR_VIVID] = "선명 (OLED)", [UI_MENU_COLOR_CLARITY] = "또렷함",
    [UI_MENU_COLOR_CUSTOM] = "사용자 지정",
    [UI_MENU_COLOR_BRIGHTNESS] = "밝기", [UI_MENU_COLOR_BRIGHTNESS_DESC] = "모든 색에 더해집니다. 0이면 그대로입니다.",
    [UI_MENU_COLOR_CONTRAST] = "대비",
    [UI_MENU_COLOR_CONTRAST_DESC] = "색을 중간 회색에서 멀어지게(100 % 초과) 하거나 가까워지게 합니다. 100 %이면 그대로입니다.",
    [UI_MENU_COLOR_SATURATION] = "채도",
    [UI_MENU_COLOR_SATURATION_DESC] = "회색 대비 색의 진하기입니다. 100 %이면 그대로입니다.",
    [UI_MENU_COLOR_GAMMA] = "감마",
    [UI_MENU_COLOR_GAMMA_DESC] = "1보다 낮으면 어두운 톤과 중간 톤이 밝아지고, 높으면 어두워집니다. 1이면 그대로입니다.",
    [UI_MENU_HDR_GROUP] = "HDR",
    [UI_MENU_HDR] = "HDR 출력",
    [UI_MENU_HDR_DESC] = "HDR 화면에서 강한 빛을 밝게 표현합니다. Windows에서 HDR을 켜거나('HDR 사용') 색 관리를 지원하는 "
                         "Wayland 컴포지터가 필요합니다. 없으면 영상은 SDR로 유지됩니다. 재시작 후 적용됩니다. "
                         "위의 색상 프로필은 SDR용이며 HDR에서는 사용되지 않습니다.",
    [UI_MENU_HDR_PEAK] = "최대 밝기",
    [UI_MENU_HDR_PEAK_DESC] = "화면의 최대 밝기(니트)입니다. 가장 강한 빛도 이 값을 넘지 않습니다.",
    [UI_MENU_HDR_GAME] = "게임 밝기",
    [UI_MENU_HDR_GAME_DESC] = "영상의 흰색(페이퍼 화이트) 밝기(니트)입니다. 203이 HDR 기준값이며, 밝은 방에서는 "
                              "높이세요.",
    [UI_MENU_HDR_UI] = "HUD 및 메뉴 밝기",
    [UI_MENU_HDR_UI_DESC] = "HUD와 이 메뉴의 흰색 밝기(니트)입니다.",
    [UI_MENU_HDR_HUE] = "하이라이트 색조 보정",
    [UI_MENU_HDR_HUE_DESC] = "불이나 불꽃 같은 강렬한 색이 게임의 SDR 영상처럼, 그리고 그 빛이 비추는 색과 같이 "
                             "흰색에 가까워집니다. 0이면 채도를 그대로 유지합니다.",
    [UI_MENU_SHADOW_SCALE] = "그림자 해상도",
    [UI_MENU_SHADOW_SCALE_DESC] = "태양 그림자 맵을 게임의 2048x2048보다 한 변당 지정한 배수만큼 크게 그립니다. "
                                  "그림자 윤곽과 나뭇잎 그림자가 선명해지지만 비디오 메모리를 더 사용합니다"
                                  "(2x에서 약 85~130 MiB, 4x에서 340~520 MiB). 다음 실행 시 적용됩니다.",
    [UI_MENU_AO] = "앰비언트 오클루전",
    [UI_MENU_AO_DESC] = "주변 빛이 잘 닿지 않는 주름, 모서리, 캐릭터와 물체 아래의 바닥을 어둡게 합니다. "
                        "월드에 조명을 적용한 뒤 화면에서 계산하며, 게임 자체에는 이 기능이 없습니다. '높음'은 "
                        "'낮음'보다 GPU 시간을 더 사용합니다. 즉시 적용됩니다.",
    [UI_MENU_AO_OFF] = "끔",
    [UI_MENU_AO_LOW] = "낮음",
    [UI_MENU_AO_HIGH] = "높음",
    [UI_MENU_UPSCALING] = "스케일러 (FSR / DLSS)",
    [UI_MENU_UPSCALING_DESC] = "게임의 안티앨리어싱 대신 시간적 스케일러를 사용합니다. 윤곽이 부드러워지고 깜빡임이 "
                               "줄며, 네이티브보다 낮은 모드에서는 FPS가 올라갑니다. NVIDIA DLSS는 NVIDIA RTX GPU와 "
                               "newsnap.exe 옆의 nvngx_dlss.dll이, Intel XeSS는 최신 GPU와 newsnap.exe 옆의 "
                               "libxess.dll이 필요합니다. AMD FSR은 모든 GPU에서 작동합니다. '자동'은 가능하면 DLSS를, "
                               "그 밖에는 FSR을 사용합니다. 여기서 선택한 DLSS와 XeSS는 재시작 후 적용됩니다. HUD는 바뀌지 않습니다.",
    [UI_MENU_UPSCALING_DESC_OTHER] = "게임의 안티앨리어싱 대신 시간적 스케일러를 사용합니다. 윤곽이 부드러워지고 깜빡임이 "
                                     "줄며, 네이티브보다 낮은 모드에서는 FPS가 올라갑니다. AMD FSR은 모든 GPU에서 "
                                     "작동합니다. 여기서 '자동'은 FSR입니다(NVIDIA DLSS와 Intel XeSS는 Windows 전용). "
                                     "HUD는 바뀌지 않습니다.",
    [UI_MENU_UPSCALING_OFF] = "끔", [UI_MENU_UPSCALING_AUTO] = "자동",
    [UI_MENU_UPSCALING_UNAVAILABLE] = "여기서는 사용할 수 없음",
    [UI_MENU_UPSCALING_UNTIL] = "재시작 전까지 %s",
    [UI_MENU_UPSCALING_QUALITY] = "성능 스케일링",
    [UI_MENU_UPSCALING_QUALITY_DESC] = "스케일러가 게임 해상도로 올리기 전에 3D 장면을 그리는 크기입니다"
                                       "(값 아래에 표시됩니다). 네이티브는 전체 크기로 그려 가장 선명합니다"
                                       "(DLSS에서는 DLAA). 품질, 균형, 성능, 울트라 성능은 약 67, 58, 50, 33 % 크기로 "
                                       "그려 FPS를 높입니다. 울트라 성능은 "
                                       "3840 x 2160용입니다. 재시작 후 적용됩니다.",
    [UI_MENU_UPSCALING_NATIVE] = "끔 (전체 해상도)", [UI_MENU_DLSS_QUALITY] = "품질", [UI_MENU_DLSS_BALANCED] = "균형",
    [UI_MENU_DLSS_PERFORMANCE] = "성능", [UI_MENU_UPSCALING_ULTRA] = "울트라 성능",
    [UI_MENU_UPSCALING_MODE_OFF] = "스케일러 없음",
    [UI_MENU_AA] = "안티앨리어싱 (SMAA)",
    [UI_MENU_AA_DESC] = "SMAA는 HUD를 그리기 전에 계단 현상이 있는 윤곽을 부드럽게 합니다. 높음이 기본값이며, 울트라는 "
                        "GPU를 조금 더 써서 더 많은 윤곽을 찾습니다. 스케일러가 작동하는 동안에는 사용되지 않습니다.",
    [UI_SNAP_SMAA_LOW] = "낮음", [UI_SNAP_SMAA_MEDIUM] = "중간", [UI_SNAP_SMAA_HIGH] = "높음",
    [UI_MENU_AA_OFF] = "끔",
    [UI_MENU_AA_BY_UPSCALER] = "스케일러가 윤곽을 부드럽게 합니다",
    [UI_SNAP_RES] = "게임 내부 해상도",
    [UI_SNAP_RES_DESC] = "3D 장면을 그리는 해상도입니다. 100 %는 게임 원래의 1920 x 1080입니다. 낮추면 영상이 "
                         "가벼워지고, 높이면(슈퍼샘플링) GPU 시간을 더 쓰는 대신 선명해집니다. '화면에 맞춤'은 "
                         "화면 또는 창의 높이에 맞춥니다. 안티앨리어싱과 함께 작동합니다. "
                         "재시작 후 적용됩니다.",
    [UI_SNAP_RES_UPSCALER] = "100 % 초과: 성능 스케일링을 끔으로 설정하세요",
    [UI_SNAP_FG] = "프레임 생성",
    [UI_SNAP_FG_DESC] = "AMD FSR 프레임 생성: 실제 프레임 두 장 사이마다 생성된 프레임을 한 장 넣습니다. 인터페이스는 "
                        "보간에서 제외됩니다. 게임이 모니터 주사율의 절반보다 빠르게 실행되는 동안에는 자동으로 "
                        "일시 정지됩니다. 성능 정보에 실제 FPS와 생성된 FPS가 표시됩니다. "
                        "재시작 후 적용됩니다.",
    [UI_SNAP_FG_NEEDS] = "스케일러로 AMD FSR 3.1 또는 FSR 4, NVIDIA DLSS가 필요합니다",
    [UI_SNAP_HDPH] = "HD 사진 썸네일",
    [UI_SNAP_HDPH_DESC] = "사진을 찍은 뒤의 미리 보기와 폴더 및 선택 화면의 사진에 게임의 360 x 240 썸네일 대신 "
                          "1080 x 720 사진을 사용합니다. 저장된 사진과 점수는 "
                          "바뀌지 않습니다.",
    [UI_SNAP_SHADOW] = "그림자 해상도",
    [UI_SNAP_SHADOW_DESC] = "게임의 모든 그림자 맵을 확대합니다. 자동은 3D 해상도를 따릅니다: 1080p에서 2x, "
                            "125-150 %에서 3x, 200 %부터 4x. 배경에 그려진 그림자는 바뀌지 않습니다. "
                            "재시작 후 적용됩니다.",
    [UI_SNAP_TEXPACK] = "HD 텍스처 팩",
    [UI_SNAP_TEXPACK_DESC] = "게임 옆 texpack 폴더의 HD 텍스처를 사용합니다. 이 텍스처는 이 PC에서 사용자 본인의 "
                             "게임으로 만든 것입니다. 재시작 후 적용됩니다.",
    [UI_SNAP_TEXPACK_NONE] = "texpack 폴더에 팩이 없습니다",
    [UI_SNAP_HDSH] = "HD 그림자 모드 (실험적)",
    [UI_SNAP_HDSH_DESC] = "식물, 바위, 계단, 배경의 그림자는 각 스테이지의 텍스처에 그려져 있습니다. "
                          "켬: 런처가 사용자 본인의 게임에서 이를 읽어 이 PC에서 모든 스테이지용으로 "
                          "확대합니다('HD 그림자 생성', 런처를 열면 자동으로 시작됩니다). 완료되면 표시됩니다. "
                          "실시간 그림자도 가장 큰 맵을 사용합니다(끄면 내부 해상도를 "
                          "따릅니다). 재시작 후 적용됩니다.",
    [UI_SNAP_UIMOTION] = "부드러운 메뉴와 인터페이스 (실험적)",
    [UI_SNAP_UIMOTION_DESC] = "60 FPS를 넘으면 메뉴와 인터페이스 요소의 움직임을 초당 60단계가 아니라 표시되는 모든 프레임에 그립니다. 게임 로직은 바뀌지 않습니다. 메뉴가 겹쳐 보이거나 깜박이면 "
                              "끄세요. 다시 시작한 뒤 적용됩니다.",
    [UI_SNAP_TAB] = "개선",
    [UI_SNAP_ENH] = "NewSnap 개선 기능 (게임 로직은 바꾸지 않습니다)",
    [UI_SNAP_ASPECT] = "화면 비율",
    [UI_SNAP_ASPECT_DESC] = "16:9 유지는 더 넓은 화면에서 양옆에 여백을 넣습니다. 늘리기는 창을 가득 채웁니다. Ultrawide는 "
                            "게임의 비율을 유지한 채 3D 시야를 창 크기로 넓히고, 인터페이스는 가운데에 두며, "
                            "사진은 기존의 16:9 시야로 찍습니다(실험적).",
    [UI_SNAP_TAB_SYS] = "시스템",
    [UI_SNAP_SYS_CONT] = "게임으로 돌아가기",
    [UI_SNAP_SYS_CONT_DESC] = "이 메뉴를 닫고 게임을 계속합니다.",
    [UI_SNAP_SYS_RESTART] = "게임 재시작",
    [UI_SNAP_SYS_RESTART_DESC] = "재시작 후 적용되는 설정을 위해 게임을 닫고 다시 엽니다. "
                                 "마지막으로 저장한 이후의 진행 상황은 사라집니다.",
    [UI_SNAP_SYS_QUIT] = "바탕 화면으로 나가기",
    [UI_SNAP_SYS_QUIT_DESC] = "게임을 닫습니다. 마지막으로 저장한 이후의 진행 상황은 사라집니다. 게임은 "
                              "조사를 마칠 때마다 자동으로 저장합니다.",
    [UI_MENU_OUTPUT_RES_AUTO] = "자동",
    [UI_MENU_OUTPUT_RES_NEXT] = ", 재시작 후 %s",

    [UI_MENU_FPS_LIMIT] = "FPS 제한",
    [UI_MENU_FPS_LIMIT_DESC] = "프레임 제한: 30, 60(기본값), 90, 120, 144 FPS 또는 VRR(모니터 주사율 바로 "
                               "아래). 원래 더 느린 장면은 그 속도를 유지합니다. 즉시 "
                               "적용됩니다. 실제 FPS는 GPU와 화면 모드에 따라 달라집니다.",
    [UI_MENU_FPS_30] = "30 FPS", [UI_MENU_FPS_60] = "60 FPS",
    [UI_MENU_REALTIME] = "실제 시간 기준 게임 속도",
    [UI_MENU_REALTIME_DESC] = "게임을 실제 시간에 맞춰 진행하여, 느린 프레임 때문에 게임이 느려지지 않게 합니다.",
    [UI_MENU_CLOTH_REALTIME] = "실제 시간 기준 천 움직임",
    [UI_MENU_CLOTH_REALTIME_DESC] = "천과 털도 실제 시간에 맞춰 움직입니다.",
    [UI_MENU_HIGHFPS_FIX] = "높은 FPS용 수정",
    [UI_MENU_HIGHFPS_FIX_DESC] = "30 FPS를 넘으면 잘못 작동하는 물리 효과와, 60을 넘으면 투명해지거나 "
                                 "보이지 않게 되는 물체를 수정합니다.",
    [UI_MENU_GAME_LANG] = "게임 언어", [UI_MENU_GAME_LANG_DESC] = "게임의 텍스트와 음성 언어입니다.",
    [UI_MENU_GAME_LANG_AUTO] = "자동",
    [UI_MENU_OPERATION_MODE] = "본체 모드",
    [UI_MENU_OPERATION_MODE_DESC] = "게임이 독(TV)에 연결된 것으로 인식할지 휴대 모드로 인식할지 정합니다.",
    [UI_MENU_MODE_DOCKED] = "TV (독)", [UI_MENU_MODE_HANDHELD] = "휴대 모드",
    [UI_MENU_HUD] = "HUD",
    [UI_MENU_HUD_DESC] = "끄면 플레이 중 게임의 HUD를 그리지 않습니다. 메뉴는 그대로 표시됩니다. F12로 전환합니다.",
    [UI_MENU_ASSUME_FOCUS] = "비활성 창에서도 계속 실행",
    [UI_MENU_ASSUME_FOCUS_DESC] = "켬(기본값): 다른 창을 사용하는 동안에도 게임이 계속 실행되며, 창이 다시 앞으로 올 "
                                  "때까지 키보드는 작동하지 않습니다. 끔: Switch에서 HOME 버튼을 누를 때처럼 창이 "
                                  "포커스를 잃으면 일시 정지됩니다. 이렇게 중단된 로딩은 멈춘 채로 "
                                  "남을 수 있습니다.",

    [UI_MENU_MODS_INSTALLED] = "설치된 모드",
    [UI_MENU_MODS_NONE] = "아직 모드가 없습니다. mods 폴더에 모드의 압축을 풀고(모드마다 폴더 하나, 그 안에 romfs "
                          "폴더) 게임을 재시작하세요.",
    [UI_MENU_MODS_OPEN] = "모드 폴더 열기",
    [UI_MENU_MODS_OPEN_DESC] = "게임이 모드를 불러오는 폴더를 표시합니다. 폴더가 없으면 만듭니다.",
    [UI_MENU_MODS_ROW_DESC] = "교체하는 게임 파일: %u개. 새로 추가하는 파일: %u개.",
    [UI_MENU_MODS_OVERRIDDEN] = "파일 %u개는 목록에서 더 위에 있는 %s의 것이 사용됩니다.",
    [UI_MENU_MODS_MOVE_HINT] = "위쪽 버튼 또는 Ctrl+위쪽 화살표로 올리고, 왼쪽 버튼 또는 Ctrl+아래쪽 화살표로 내립니다. 두 "
                               "모드가 같은 파일을 바꾸면 더 위에 있는 모드가 우선합니다. 변경 사항은 재시작 후 적용됩니다.",
    [UI_MENU_MODS_EMPTY] = "이 폴더에는 romfs, exefs, cheats 파일이 없습니다.",
    [UI_MENU_MODS_SUBSDK] = "이 모드에는 자체 게임 코드(subsdk 플러그인 또는 교체된 main)가 들어 있습니다. 이 포트는 "
                            "코드 모듈을 불러올 수 없으므로 모드 전체가 비활성화됩니다.",
    [UI_MENU_MODS_EXEFS_LATER] = "이 모드는 게임 코드(exefs)를 패치합니다. 게임이 다음 실행 시 패치를 "
                                 "통합합니다(몇 분 걸리는 재빌드). 그때까지 모드 전체가 비활성화됩니다.",
    [UI_MENU_MODS_CHEATS] = "치트: %d개.",
    [UI_MENU_MODS_CHEATS_FILE] = "이 게임 버전의 치트는 시작할 때 이 모드의 cheats\\%s에서 읽습니다.",
    [UI_MENU_MODS_BAD_NAME] = "폴더 이름에 모드 목록이 이름 구분에 사용하는 | 문자가 있습니다. 폴더 이름을 "
                              "바꾸세요.",
    [UI_MENU_MODS_OTHER_VERSION] = "파일 %u개는 다른 게임 버전용이라 건너뜁니다. 사용 중인 게임 버전에 맞게 "
                                   "만들어진 이 모드의 버전을 찾아보세요.",
    [UI_MENU_MODS_UNUSED] = "사용 안 함",

    [UI_MENU_VOLUME] = "음량", [UI_MENU_VOLUME_DESC] = "게임 전체 음량입니다.",

    [UI_MENU_MOTION] = "모션 컨트롤", [UI_MENU_MOTION_DESC] = "컨트롤러의 자이로 센서로 조준합니다.",
    [UI_MENU_RUMBLE_STRENGTH] = "진동 세기",
    [UI_MENU_RUMBLE_STRENGTH_DESC] = "컨트롤러가 진동하는 세기입니다.",
    [UI_MENU_RUMBLE_CURVE] = "진동 곡선",
    [UI_MENU_RUMBLE_CURVE_DESC] = "값이 낮을수록 약한 진동이 강해집니다.",
    [UI_MENU_RUMBLE_TRIGGERS] = "트리거 진동 (Xbox)",
    [UI_MENU_RUMBLE_TRIGGERS_DESC] = "Xbox 컨트롤러의 트리거도 진동시킵니다.",
    [UI_MENU_PAD_LAYOUT] = "버튼 배치",
    [UI_MENU_PAD_LAYOUT_DESC] = "어느 버튼이 A인지 정합니다. Nintendo: Switch처럼 오른쪽 버튼. Xbox: Xbox 컨트롤러처럼 "
                                "아래쪽 버튼. PlayStation: 아래쪽 버튼(크로스)이며 나머지는 위치에 따릅니다(PlayStation "
                                "버튼 모드용). '자동'은 Nintendo 표기 컨트롤러에는 Nintendo, "
                                "PlayStation 컨트롤러에는 PlayStation, 그 밖에는 Xbox를 선택합니다. 게임의 버튼 안내에 "
                                "표시할 컨트롤러는 버튼 표시에서 선택합니다.",
    [UI_MENU_PAD_LAYOUT_AUTO] = "자동", [UI_MENU_PAD_LAYOUT_NINTENDO] = "Nintendo (A가 오른쪽)",
    [UI_MENU_PAD_LAYOUT_XBOX] = "Xbox (A가 아래쪽)", [UI_MENU_PAD_LAYOUT_PLAYSTATION] = "PlayStation (A가 아래쪽)",
    [UI_MENU_PAD_LAYOUT_IN_USE] = "사용 중: %s",
    [UI_MENU_PROMPTS] = "버튼 표시",
    [UI_MENU_PROMPTS_DESC] = "게임의 버튼 안내에 어느 컨트롤러의 버튼을 표시할지 정합니다. '자동'은 사용 중인 컨트롤러를 따릅니다. "
                             "Nintendo: 게임 원래의 버튼. Xbox와 PlayStation: 각 배치에 맞게 그린 버튼 모드. "
                             "게임은 시작할 때 버튼 안내를 읽으므로 재시작 후에 바뀝니다.",
    [UI_MENU_PROMPTS_AUTO] = "자동", [UI_MENU_PROMPTS_NINTENDO] = "Nintendo", [UI_MENU_PROMPTS_XBOX] = "Xbox",
    [UI_MENU_PROMPTS_PLAYSTATION] = "PlayStation",
    [UI_MENU_PROMPTS_MISSING] = "버튼 표시 파일이 없습니다: 설치를 다시 실행하세요",
    [UI_MENU_PROMPTS_FAILED] = "버튼 표시 파일이 손상되었습니다: 설치를 다시 실행하세요",
    [UI_MENU_PROMPTS_RESTART] = "버튼 표시는 재시작 후 바뀝니다",
    [UI_MENU_PROMPTS_OFF_SHAPE] = "게임 해상도가 16:9가 아니어서 꺼짐",
    [UI_MENU_PROMPTS_OFF_MODS] = "꺼짐: RomFS 모드가 해당 파일을 교체함",
    [UI_MENU_PROMPTS_OFF_PATCHES] = "AC_ROMFS_PATCHES가 설정되어 있는 동안 꺼짐",
    [UI_MENU_RESTART] = "지금 재시작",
    [UI_MENU_RESTART_DESC] = "게임을 닫고 새 버튼 표시로 다시 엽니다. 마지막으로 저장한 이후의 "
                             "진행 상황은 사라집니다.",
    [UI_MENU_RESTART_CONFIRM] = "지금 게임을 재시작하시겠습니까? 마지막으로 저장한 이후의 진행 상황은 사라집니다.",
    [UI_MENU_RESTART_YES] = "재시작",
    [UI_MENU_RESTART_SAVING] = "게임이 저장 중입니다. 잠시 후 재시작할 수 있습니다.",
    [UI_MENU_LSTICK_DEADZONE] = "왼쪽 스틱 데드존", [UI_MENU_RSTICK_DEADZONE] = "오른쪽 스틱 데드존",
    [UI_MENU_STICK_DEADZONE_DESC] = "스틱을 얼마나 움직여야 게임이 인식하는지 정합니다. 캐릭터나 카메라가 저절로 "
                                    "움직이면 높이세요. 스틱에서 손을 떼고 '현재 스틱' 값을 본 뒤 데드존을 그보다 "
                                    "몇 포인트 높게 설정하세요.",
    [UI_MENU_STICK_DEADZONE_NOW] = "현재 스틱: %.0f %%",
    [UI_MENU_MOUSE_SENS] = "마우스 감도",
    [UI_MENU_MOUSE_SENS_DESC] = "마우스로 카메라가 회전하는 속도입니다.",
    [UI_MENU_WALK_KEY] = "걷기 키",
    [UI_MENU_WALK_KEY_DESC] = "누르고 있는 동안 키보드 스틱이 일부만 기울어져 달리지 않고 걷습니다. "
                              "기울기는 걷기 배율로 정합니다. 컨트롤러와 마우스에는 영향을 주지 않습니다.",
    [UI_MENU_WALK_KEY_TAKEN] = "%s에도 사용 중",
    [UI_MENU_WALK_SCALE] = "걷기 배율",
    [UI_MENU_WALK_SCALE_DESC] = "걷기 키를 누를 때 키보드 스틱의 기울기입니다. 절반이면 걷기, "
                                "최대이면 달리기입니다.",
    [UI_MENU_STICK_SENS] = "스틱 카메라 속도",
    [UI_MENU_STICK_SENS_DESC] = "게임의 다섯 가지 감도 각각에서 오른쪽 스틱의 카메라 속도(최고 속도 포함)에 "
                                "곱해집니다. 마우스는 별도의 설정이 있습니다.",

    [UI_BINDS_HELP] = "칸을 선택하고 A 또는 Enter를 누른 다음 키, 마우스 버튼 또는 컨트롤러 버튼을 누르세요. Delete 또는 X로 "
                      "칸을 비웁니다. 이미 사용 중인 키는 이 칸으로 옮겨지고, 컨트롤러 버튼은 대체되는 버튼과 "
                      "서로 바뀝니다.",
    [UI_BINDS_COL_KEY1] = "키 1", [UI_BINDS_COL_KEY2] = "키 2", [UI_BINDS_COL_PAD] = "컨트롤러",
    [UI_BINDS_GROUP_BUTTONS] = "버튼", [UI_BINDS_GROUP_MOVE] = "이동", [UI_BINDS_GROUP_CAMERA] = "카메라",
    [UI_BINDS_PRESS_KEY] = "%s: 키 또는 마우스 버튼을 누르세요",
    [UI_BINDS_PRESS_PAD] = "%s: 컨트롤러 버튼을 누르세요",
    [UI_BINDS_CANCEL_HINT] = "Esc로 취소, 또는 %d초 대기",
    [UI_BINDS_TAKEN] = "%s: %s에서 해제됨", [UI_BINDS_SWAPPED] = "%s 및 %s 서로 교체됨",
    [UI_BINDS_RESET] = "모든 버튼 초기화",
    [UI_BINDS_RESET_DESC] = "키와 버튼을 기본값으로 되돌립니다. 위의 버튼 배치가 다시 적용됩니다. 다시 지정한 "
                            "컨트롤러 버튼은 이 초기화를 하기 전까지 지정한 자리에 그대로 남습니다.",
    [UI_BIND_A] = "A", [UI_BIND_B] = "B", [UI_BIND_X] = "X", [UI_BIND_Y] = "Y",
    [UI_BIND_LCLICK] = "왼쪽 스틱 누르기", [UI_BIND_RCLICK] = "오른쪽 스틱 누르기", [UI_BIND_L] = "L",
    [UI_BIND_R] = "R", [UI_BIND_ZL] = "ZL", [UI_BIND_ZR] = "ZR", [UI_BIND_PLUS] = "플러스 (+)", [UI_BIND_MINUS] = "마이너스 (-)",
    [UI_BIND_LEFT] = "십자 버튼 왼쪽", [UI_BIND_UP] = "십자 버튼 위", [UI_BIND_RIGHT] = "십자 버튼 오른쪽",
    [UI_BIND_DOWN] = "십자 버튼 아래",
    [UI_BIND_LSTICK_LEFT] = "왼쪽으로 이동", [UI_BIND_LSTICK_UP] = "앞으로 이동",
    [UI_BIND_LSTICK_RIGHT] = "오른쪽으로 이동", [UI_BIND_LSTICK_DOWN] = "뒤로 이동",
    [UI_BIND_RSTICK_LEFT] = "카메라 왼쪽", [UI_BIND_RSTICK_UP] = "카메라 위",
    [UI_BIND_RSTICK_RIGHT] = "카메라 오른쪽", [UI_BIND_RSTICK_DOWN] = "카메라 아래",
    [UI_BIND_DESC_A] = "상호작용, 줍기, 말하기.", [UI_BIND_DESC_B] = "달리기, 취소, 돌아가기.",
    [UI_BIND_DESC_X] = "점프.", [UI_BIND_DESC_Y] = "공격.", [UI_BIND_DESC_LCLICK] = "웅크리기.",
    [UI_BIND_DESC_RCLICK] = "1인칭 시점.", [UI_BIND_DESC_L] = "능력.",
    [UI_BIND_DESC_R] = "던지기.", [UI_BIND_DESC_ZL] = "방패, 주목.", [UI_BIND_DESC_ZR] = "활.",
    [UI_BIND_DESC_PLUS] = "메뉴, 소지품.", [UI_BIND_DESC_MINUS] = "지도.",
    [UI_BIND_DESC_DPAD] = "빠른 선택.",
    [UI_BIND_DESC_MOVE] = "왼쪽 스틱처럼 이동합니다. 컨트롤러의 왼쪽 스틱도 항상 작동합니다.",
    [UI_BIND_DESC_CAMERA] = "오른쪽 스틱처럼 카메라를 돌립니다. 마우스와 컨트롤러의 오른쪽 스틱도 항상 "
                            "작동합니다.",
    [UI_KEY_SPACE] = "스페이스", [UI_KEY_TAB] = "Tab", [UI_KEY_LSHIFT] = "왼쪽 Shift", [UI_KEY_LCTRL] = "왼쪽 Ctrl",
    [UI_KEY_UP] = "위쪽 화살표", [UI_KEY_DOWN] = "아래쪽 화살표", [UI_KEY_LEFT] = "왼쪽 화살표",
    [UI_KEY_RIGHT] = "오른쪽 화살표",
    [UI_KEY_MOUSE_L] = "마우스 왼쪽 버튼", [UI_KEY_MOUSE_R] = "마우스 오른쪽 버튼", [UI_KEY_MOUSE_M] = "마우스 가운데 버튼",
    [UI_KEY_MOUSE_X1] = "마우스 4", [UI_KEY_MOUSE_X2] = "마우스 5",
    [UI_KEY_ENTER] = "Enter", [UI_KEY_BACKSPACE] = "Backspace", [UI_KEY_RSHIFT] = "오른쪽 Shift",
    [UI_KEY_RCTRL] = "오른쪽 Ctrl", [UI_KEY_LALT] = "Alt", [UI_KEY_CAPSLOCK] = "Caps Lock", [UI_KEY_INSERT] = "Insert",
    [UI_KEY_DELETE] = "Delete", [UI_KEY_HOME] = "Home", [UI_KEY_END] = "End", [UI_KEY_PAGEUP] = "Page Up",
    [UI_KEY_PAGEDOWN] = "Page Down", [UI_KEY_NUM_FMT] = "숫자 패드 %s",
    [UI_PAD_SOUTH] = "아래쪽 버튼", [UI_PAD_EAST] = "오른쪽 버튼", [UI_PAD_WEST] = "왼쪽 버튼",
    [UI_PAD_NORTH] = "위쪽 버튼", [UI_PAD_LSTICK] = "왼쪽 스틱", [UI_PAD_RSTICK] = "오른쪽 스틱",
    [UI_PAD_L] = "왼쪽 범퍼", [UI_PAD_R] = "오른쪽 범퍼", [UI_PAD_START] = "Start",
    [UI_PAD_BACK] = "Back",
    [UI_PAD_DPAD_LEFT] = "십자 버튼 왼쪽", [UI_PAD_DPAD_UP] = "십자 버튼 위", [UI_PAD_DPAD_RIGHT] = "십자 버튼 오른쪽",
    [UI_PAD_DPAD_DOWN] = "십자 버튼 아래", [UI_PAD_ZL] = "왼쪽 트리거", [UI_PAD_ZR] = "오른쪽 트리거",
    [UI_PAD_LPADDLE1] = "왼쪽 후면 버튼", [UI_PAD_RPADDLE1] = "오른쪽 후면 버튼",
    [UI_PAD_LPADDLE2] = "왼쪽 후면 버튼 2", [UI_PAD_RPADDLE2] = "오른쪽 후면 버튼 2",
    [UI_PAD_CROSS] = "크로스", [UI_PAD_CIRCLE] = "서클", [UI_PAD_SQUARE] = "스퀘어", [UI_PAD_TRIANGLE] = "트라이앵글",

    [UI_MENU_MENU_LANG] = "메뉴 언어", [UI_MENU_MENU_LANG_DESC] = "이 메뉴와 화면에 표시되는 정보의 언어입니다.",
    [UI_MENU_MENU_LANG_AUTO] = "자동 (Windows 설정)",

    [UI_MENU_ADV_WARNING] = "이 설정들은 테스트와 문제 해결을 위한 것입니다. 이유를 알고 있을 때만 변경하세요.",
    [UI_MENU_GROUP_SCHED] = "스케줄링", [UI_MENU_GROUP_SHADERS] = "셰이더 및 파이프라인",
    [UI_MENU_GROUP_TEXMEM] = "텍스처 및 메모리", [UI_MENU_GROUP_FIXES] = "렌더링 수정",
    [UI_MENU_GROUP_VULKAN] = "Vulkan", [UI_MENU_GROUP_DIAG] = "진단",
    [UI_MENU_ASYNC_PREEMPT] = "가상 코어 선점",
    [UI_MENU_ASYNC_PREEMPT_DESC] = "같은 가상 코어에서 게임 스레드가 다른 스레드를 중단시킬 수 있게 합니다.",
    [UI_MENU_PREEMPT_OFF] = "끔", [UI_MENU_PREEMPT_ON] = "켬", [UI_MENU_PREEMPT_INHERIT] = "상속만",
    [UI_MENU_REPLAY_ASYNC] = "별도 스레드에서 프레임 준비",
    [UI_MENU_REPLAY_ASYNC_DESC] = "GPU에 보낼 프레임을 게임 스레드가 아닌 별도 스레드에서 준비합니다. "
                                  "지연이 최대 한 프레임 늘어납니다.",
    [UI_MENU_TIMER_1MS] = "Windows 1 ms 타이머",
    [UI_MENU_TIMER_1MS_DESC] = "시스템 타이머 해상도를 1 ms로 높여 프레임 간격을 더 안정적으로 만듭니다.",
    [UI_MENU_PIPE_WAIT] = "대기 중인 드로우 처리",
    [UI_MENU_PIPE_WAIT_DESC] = "기본값은 대기 중인 드로우 전용 워커를 두는 현재의 스케줄링을 유지합니다. "
                               "이전 방식(드로우)은 예전 스케줄링을 사용합니다.",
    [UI_MENU_PIPE_WAIT_DEFAULT] = "기본값", [UI_MENU_PIPE_WAIT_DRAW] = "이전 방식 (드로우)",
    [UI_MENU_PIPE_SKIP] = "파이프라인 생성 중 건너뛰는 드로우",
    [UI_MENU_PIPE_SKIP_DESC] = "파이프라인을 기다리지 않고 버리는 드로우를 정합니다.",
    [UI_MENU_PIPE_SKIP_STRICT] = "엄격", [UI_MENU_PIPE_SKIP_ANY] = "모두",
    [UI_MENU_PIPE_SKIP_FULLSCREEN] = "전체 화면 패스",
    [UI_MENU_LIB_PREBUILD] = "스테이지 라이브러리 사전 컴파일",
    [UI_MENU_LIB_PREBUILD_DESC] = "셰이더 스테이지 라이브러리를 백그라운드에서 미리 컴파일합니다.",
    [UI_MENU_LIB_PREBUILD_THREADS] = "라이브러리 사전 컴파일 스레드",
    [UI_MENU_LIB_PREBUILD_THREADS_DESC] = "사전 컴파일에 사용하는 스레드 수입니다. '자동'은 CPU에 맞춰 정합니다.",
    [UI_MENU_PIPE_PREBUILD] = "파이프라인 사전 컴파일",
    [UI_MENU_PIPE_PREBUILD_DESC] = "알려진 파이프라인을 미리 컴파일합니다.",
    [UI_MENU_PREWARM_XLATE] = "변환기 예열",
    [UI_MENU_PREWARM_XLATE_DESC] = "시작할 때 알려진 셰이더를 변환하는 스레드 수입니다. '자동'은 CPU 스레드의 "
                                   "절반, 최대 16개를 사용합니다.",
    [UI_MENU_GPL] = "그래픽 파이프라인 라이브러리",
    [UI_MENU_GPL_DESC] = "Vulkan의 파이프라인 라이브러리 확장을 사용합니다. 드라이버에서 문제가 생기면 끄세요.",
    [UI_MENU_ASTC] = "ASTC 텍스처 디코딩",
    [UI_MENU_ASTC_DESC] = "ASTC 압축 텍스처를 디코딩하는 위치입니다.",
    [UI_MENU_ASTC_AUTO] = "자동", [UI_MENU_ASTC_GPU] = "GPU 셰이더", [UI_MENU_ASTC_NATIVE] = "네이티브",
    [UI_MENU_ASTC_CPU] = "CPU",
    [UI_MENU_MEMORY] = "GPU 메모리 모드",
    [UI_MENU_MEMORY_DESC] = "게임 메모리를 GPU와 공유하는 방식입니다.",
    [UI_MENU_MEMORY_AUTO] = "자동", [UI_MENU_MEMORY_IMPORT] = "가져오기", [UI_MENU_MEMORY_MIRROR] = "미러",
    [UI_MENU_MEMORY_VERIFY] = "검증",
    [UI_MENU_TEX_ALIAS] = "텍스처 별칭",
    [UI_MENU_TEX_ALIAS_DESC] = "사용 중인 다른 텍스처의 메모리 위에 만들어진 새 텍스처가 빈 상태가 아니라 그 내용으로 "
                               "시작합니다.",
    [UI_MENU_TEX_VRAM_PRESSURE] = "텍스처 메모리 한도",
    [UI_MENU_TEX_VRAM_PRESSURE_DESC] = "게임이 해제한 텍스처를 버리기 시작하는 비디오 메모리 사용률입니다"
                                       "(다시 사용될 때 저장 장치에서 불러옵니다). 0이면 유지합니다.",
    [UI_MENU_ASTC_BC] = "ASTC를 BC로 압축",
    [UI_MENU_ASTC_BC_DESC] = "GPU 디코더 사용 시: 디코딩한 ASTC 텍스처를 불투명하면 BC1로, 아니면 BC3로 다시 "
                             "인코딩하여 비디오 메모리를 4분의 1에서 8분의 1로 줄입니다. 4 GB 이하 GPU용이며, "
                             "텍스처에 블록이 조금 더 보입니다.",
    [UI_MENU_LOD_GUARD] = "LOD 보호",
    [UI_MENU_LOD_GUARD_DESC] = "GPU가 읽기 전에 게임이 디테일 수준을 다시 쓰는 작업을 마칠 때까지 기다려, 물체가 "
                               "엉뚱한 위치에서 깜빡이거나 먼 배경이 한 프레임 동안 밋밋하게 보이는 현상을 "
                               "막습니다.",
    [UI_MENU_FIX_C0] = "상수 버퍼 수정",
    [UI_MENU_FIX_C0_DESC] = "드라이버용으로 예약된 상수 뱅크 c0(스토리지 크기, 디스패치 크기, 포인트 크기, "
                            "베이스 인스턴스)을 0으로 읽지 않고 채웁니다.",
    [UI_MENU_FIX_ZERO] = "새 GPU 메모리를 0으로 초기화",
    [UI_MENU_FIX_ZERO_DESC] = "새 GPU 메모리 풀이 Switch의 메모리처럼 0으로 시작합니다.",
    [UI_MENU_BIND_SKIP] = "반복되는 바인딩 건너뛰기",
    [UI_MENU_BIND_SKIP_DESC] = "최적화: 바뀌지 않은 바인딩을 건너뜁니다.",
    [UI_MENU_SHADER_MEMO] = "셰이더 메모", [UI_MENU_SHADER_MEMO_DESC] = "최적화: 셰이더 조회 결과를 기억합니다.",
    [UI_MENU_PIPE_MEMO] = "파이프라인 메모",
    [UI_MENU_PIPE_MEMO_DESC] = "최적화: 상태가 같으면 이전 드로우의 파이프라인을 재사용합니다.",
    [UI_MENU_TEX_MEMO] = "텍스처 바인딩 메모",
    [UI_MENU_TEX_MEMO_DESC] = "최적화: 드로우 사이에 텍스처 디스크립터를 기억합니다.",
    [UI_MENU_DESC_TEMPLATE] = "디스크립터 템플릿",
    [UI_MENU_DESC_TEMPLATE_DESC] = "최적화: 디스크립터를 한꺼번에 갱신합니다.",
    [UI_MENU_PUSH_SKIP] = "반복되는 푸시 상수 건너뛰기",
    [UI_MENU_PUSH_SKIP_DESC] = "최적화: 바뀌지 않은 푸시 상수를 건너뜁니다.",
    [UI_MENU_SPLIT_DRAWS] = "GPU에 미리 제출",
    [UI_MENU_SPLIT_DRAWS_DESC] = "패스 사이에서 드로우 N개마다 GPU 작업을 나누어 제출해 GPU가 더 일찍 "
                                 "시작하게 합니다. 0이면 끕니다.",
    [UI_MENU_VK_VALIDATION] = "검증 레이어",
    [UI_MENU_VK_VALIDATION_DESC] = "모든 Vulkan 호출을 검사하며 게임이 매우 느려집니다.",
    [UI_MENU_VK_VALIDATION_MISSING] = "검증 레이어가 설치되어 있지 않습니다.",
    [UI_MENU_VK_DYN_VERTEX] = "동적 버텍스 상태",
    [UI_MENU_VK_DYN_VERTEX_DESC] = "동적 버텍스 입력을 강제로 켜거나 끕니다. 기본값은 GPU에 따라 "
                                   "다릅니다.",
    [UI_MENU_VK_DYN_A2C] = "동적 Alpha to coverage",
    [UI_MENU_VK_DYN_A2C_DESC] = "동적 alpha to coverage를 강제로 켜거나 끕니다. 기본값: RDNA 2 이하의 AMD "
                                "드라이버에서는 끔(켜면 캐릭터가 검게 그려집니다), "
                                "그 밖에는 켬.",
    [UI_MENU_VK_SUBGROUP_PIN] = "서브그룹 크기 고정",
    [UI_MENU_VK_SUBGROUP_PIN_DESC] = "셰이더의 서브그룹 크기를 고정합니다.",
    [UI_MENU_TRACE] = "성능 로그", [UI_MENU_TRACE_DESC] = "프레임 시간을 파일에 기록합니다.",
    [UI_MENU_FLIGHT] = "플라이트 레코더",
    [UI_MENU_FLIGHT_DESC] = "짧은 기록을 보관하다가 프레임이 멈추면 파일에 기록합니다.",
    [UI_MENU_FLIGHT_SPIKE_MS] = "멈춤 임계값 (ms)",
    [UI_MENU_FLIGHT_SPIKE_MS_DESC] = "멈춤으로 간주하는 프레임 시간입니다.",
    [UI_MENU_INPUT_RECORD] = "입력 기록",
    [UI_MENU_INPUT_RECORD_DESC] = "오류 보고를 위해 입력을 파일에 기록합니다.",
    [UI_MENU_OPEN_LOG] = "로그 폴더 열기", [UI_MENU_OPEN_LOG_DESC] = "로그가 있는 폴더를 표시합니다.",
    [UI_MENU_COPY_INFO] = "시스템 정보 복사",
    [UI_MENU_COPY_INFO_DESC] = "GPU, 드라이버, CPU, RAM, 변경한 설정을 클립보드에 복사합니다.",
    [UI_MENU_COPY_INFO_DONE] = "복사됨", [UI_MENU_ACTION_FAILED] = "실패했습니다",
    [UI_MENU_RESET] = "모든 설정 초기화", [UI_MENU_RESET_DESC] = "모든 탭에 적용됩니다.",
    [UI_MENU_RESET_CONFIRM] = "모든 설정을 기본값으로 초기화하시겠습니까?",
    [UI_MENU_RESET_YES] = "초기화",
    [UI_MENU_RESET_NO] = "취소",

    [UI_MENU_OV_FPS] = "%.0f FPS", [UI_MENU_OV_FRAME_MS] = "%.1f ms", [UI_MENU_OV_GAME_PCT] = "게임 %.0f%%",
    [UI_MENU_OV_MAX_MS] = "최대 %.1f ms",
    [UI_MENU_OV_GPU] = "GPU", [UI_MENU_OV_CPU] = "CPU", [UI_MENU_OV_RAM] = "RAM", [UI_MENU_OV_VRAM] = "VRAM",
    [UI_MENU_OV_TEMP] = "온도", [UI_MENU_OV_POWER] = "전력", [UI_MENU_OV_CLOCK] = "클럭",
    [UI_MENU_OV_NONE] = "-",
    [UI_MENU_OV_REPLAY] = "프레임 준비", [UI_MENU_OV_GPU_TIME] = "프레임당 GPU 사용 시간",
    [UI_MENU_OV_PIPE_WAIT] = "파이프라인 대기",
    [UI_MENU_OV_SHADER_WAIT] = "셰이더 대기", [UI_MENU_OV_TEX_UPLOADS] = "텍스처 업로드",
    [UI_MENU_OV_FMT_PCT] = "%.0f%%", [UI_MENU_OV_FMT_TEMP] = "%.0f °C", [UI_MENU_OV_FMT_POWER] = "%.0f W",
    [UI_MENU_OV_FMT_MHZ] = "%.0f MHz", [UI_MENU_OV_FMT_GB] = "%.1f GB", [UI_MENU_OV_FMT_GB_OF] = "/ %.1f GB",
    [UI_MENU_OV_GAME_GB] = "게임 %.1f GB", [UI_MENU_OV_FMT_MS] = "%.2f ms", [UI_MENU_OV_PER_FRAME] = "프레임당 %.1f",
    [UI_MENU_OV_WINDOW] = "창", [UI_MENU_OV_OUTPUT] = "게임 영상", [UI_MENU_OV_SCENE] = "3D 장면",
    [UI_MENU_OV_SCALING] = "스케일링", [UI_MENU_OV_LIMIT] = "FPS 제한", [UI_MENU_OV_PRESENT] = "화면 출력",
    [UI_MENU_OV_TEX] = "텍스처 압축", [UI_MENU_OV_OS] = "시스템",
    [UI_MENU_OV_FMT_SIZE] = "%ux%u", [UI_MENU_OV_FMT_SCENE] = "%ux%u, %.0f%%",
    [UI_MENU_OV_FMT_FSR] = "AMD FSR 1, 선명도 %d%%", [UI_MENU_OV_SCALE_NONE] = "없음 (1:1)",
    [UI_MENU_OV_SCALE_BILINEAR] = "바이리니어",
    [UI_MENU_OV_FMT_AREA] = "영역 평균, 선명도 %d%%",
    [UI_MENU_OV_FMT_PRESHARP] = "HUD 이전 RCAS, 선명도 %d%%",
    [UI_MENU_TAB_CHEATS] = "치트",
    [UI_MENU_CHEATS_NONE] = "이 게임 버전용 치트가 없습니다. 모드의 치트는 그 모드의 cheats 폴더에 있는 Atmosphere "
                            "치트 파일이며, 파일 이름은 게임 빌드 이름입니다: mods\\<mod>\\cheats\\%s. "
                            "치트를 읽으려면 게임을 재시작하세요. 게임 코드를 바꾸는 치트의 경우 게임이 "
                            "시작할 때 재빌드됩니다(몇 분).",
    [UI_MENU_CHEATS_MOD] = "%s: 치트 %d개",
    [UI_MENU_CHEAT_CODE_DESC] = "게임 코드를 변경합니다. 즉시 적용됩니다.",
    [UI_MENU_CHEAT_KEY_DESC] = "%s 입력을 누르고 있는 동안 게임 코드를 변경합니다. 즉시 적용됩니다.",
    [UI_MENU_CHEAT_DATA_DESC] = "켜져 있는 동안 매 프레임 게임 메모리에 값을 씁니다.",
    [UI_MENU_CHEAT_MASTER] = "항상 켜짐",
    [UI_MENU_CHEAT_MASTER_DESC] = "파일의 마스터 코드입니다. 항상 켜져 있습니다.",
    [UI_MENU_CHEAT_RESTORE] = "필요 없음",
    [UI_MENU_CHEAT_RESTORE_DESC] = "게임의 원래 코드를 다시 쓰기만 합니다. 치트를 끄면 이미 그렇게 됩니다.",
    [UI_MENU_CHEAT_REBUILD] = "재빌드 후",
    [UI_MENU_CHEAT_REBUILD_DESC] = "이 치트는 게임 코드를 바꾸며, 게임을 빌드한 뒤에 새로 추가되었거나 "
                                   "수정되었습니다. 게임이 다음 실행 시 통합하며(몇 분), 또는 지금 게임 재빌드를 "
                                   "사용하세요.",
    [UI_MENU_CHEAT_UNSUPPORTED] = "지원되지 않음",
    [UI_MENU_CHEAT_UNSUPPORTED_DESC] = "이 치트는 이 게임 버전에서 사용할 수 없습니다:",
    [UI_MENU_CHEATS_REBUILD] = "지금 게임 재빌드",
    [UI_MENU_CHEATS_REBUILD_DESC] = "일부 치트는 게임 코드를 바꾸는데 아직 통합되지 않았습니다. 새로 추가되었거나 "
                                    "수정되었거나, 마지막 재빌드가 실패 또는 취소되었습니다. 게임을 닫으면 설치 프로그램이 "
                                    "치트를 통합하고(몇 분) 게임을 다시 엽니다. 마지막으로 저장한 이후의 "
                                    "진행 상황은 사라집니다.",
    [UI_MENU_MODS_EXEFS_UNSUPPORTED] = "이 모드는 이 포트가 적용할 수 없는 방식으로 게임 코드(exefs)를 "
                                       "패치하므로 모드 전체가 비활성화됩니다. %s",
    [UI_MENU_MODS_EXEFS_OTHER] = "코드 패치(exefs)가 다른 게임 버전용입니다.",
    [UI_MENU_MODS_EXEFS_ON] = "사용 중인 코드 패치: 파일 %d개.",
    [UI_MENU_MODS_REPLACES_BUILTIN] = "사용 중인 코드 패치: 파일 %d개. 포트 자체 패치(%s)를 대체하며, "
                                      "이 모드가 켜져 있는 동안 해당 패치는 꺼집니다.",
};
