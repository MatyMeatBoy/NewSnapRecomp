// The in-game menu in Traditional Chinese (MENU-LANG-01), every string of text_es (ui_text_es.inc).
// Included by ui_text.c in place of the keyboard-only Traditional Chinese row.
static const char *const text_zh_hant[UI_TEXT_COUNT] = {
    SWKBD("文字輸入", "請輸入名字", "馬兒", "確定", "取消", "手把：A 確定，B 取消"),

    [UI_MENU_TITLE] = "設定",
    [UI_MENU_TAB_SCREEN] = "螢幕", [UI_MENU_TAB_GAME] = "遊戲", [UI_MENU_TAB_MODS] = "模組", [UI_MENU_TAB_SOUND] = "音效",
    [UI_MENU_TAB_CONTROLS] = "操作", [UI_MENU_TAB_MENU] = "選單", [UI_MENU_TAB_ADVANCED] = "進階",
    [UI_MENU_CONTINUE] = "繼續", [UI_MENU_QUIT] = "離開遊戲",
    [UI_MENU_ON] = "開啟", [UI_MENU_OFF] = "關閉", [UI_MENU_AUTO] = "自動",
    [UI_MENU_DEFAULT_MARK] = "預設",
    [UI_MENU_AFTER_RESTART] = "重新啟動後", [UI_MENU_SET_BY_ENV] = "由環境變數指定",
    [UI_MENU_SAVE_FAILED] = "無法儲存設定",
    [UI_MENU_VERSION] = "NewSnapRecomp %s，Snap %s",

    [UI_MENU_FULLSCREEN] = "全螢幕",
    [UI_MENU_FULLSCREEN_DESC] = "遊戲佔滿整個螢幕；按 F11 切換。",
    [UI_MENU_WINDOW_SIZE] = "視窗大小",
    [UI_MENU_WINDOW_SIZE_DESC] = "非全螢幕時遊戲視窗的大小。",
    [UI_MENU_WINDOW_SIZE_CUSTOM] = "自訂",
    [UI_MENU_PRESENT] = "呈現模式", [UI_MENU_PRESENT_DESC] = "完成的影格如何送到螢幕上。",
    [UI_MENU_PRESENT_MAILBOX] = "Mailbox", [UI_MENU_PRESENT_VSYNC] = "VSync", [UI_MENU_PRESENT_IMMEDIATE] = "立即",
    [UI_MENU_PRESENT_IN_USE] = "使用中：%s",
    [UI_MENU_GPU] = "顯示卡", [UI_MENU_GPU_DESC] = "用來繪製遊戲的 Vulkan 裝置。",
    [UI_MENU_GPU_AUTO] = "自動",
    [UI_MENU_PERF_OVERLAY] = "效能資訊",
    [UI_MENU_PERF_OVERLAY_DESC] = "在右上角顯示 FPS。「完整」會再加上影格時間與圖表、"
                                  "CPU、GPU 與記憶體負載、溫度，以及算繪執行緒的等待。按 F10 切換模式。",
    [UI_MENU_PERF_OFF] = "隱藏", [UI_MENU_PERF_FPS] = "FPS", [UI_MENU_PERF_FULL] = "完整",
    [UI_PERF_LINE_FPS] = "%.0f fps",
    [UI_MENU_GRAPHICS] = "畫面",
    [UI_MENU_OUTPUT_RES] = "遊戲解析度",
    [UI_MENU_OUTPUT_RES_DESC] = "遊戲繪製畫面與介面的大小。1280 x 720 負擔最輕，適合效能普通的 GPU。"
                                "超過 1920 x 1080 時，遊戲需要更多記憶體（2560 x 1440 約多 240 MB，"
                                "3840 x 2160 約多 790 MB）與 GPU 時間。重新啟動後套用。「自動」"
                                "採用螢幕的大小：最高 1920 x 1080，啟用升頻器時最高 3840 x 2160。",
    [UI_MENU_UPSCALER] = "縮放至視窗",
    [UI_MENU_UPSCALER_DESC] = "畫面如何縮放至視窗。FSR 比雙線性更能保留銳利的邊緣與細節，"
                              "即使畫面本來就符合視窗大小，也會加以銳化。",
    [UI_MENU_UPSCALER_FSR] = "AMD FSR 1", [UI_MENU_UPSCALER_BILINEAR] = "雙線性",
    [UI_MENU_FOV] = "視野",
    [UI_MENU_FOV_DESC] = "攝影機能看到多少世界，以遊戲原本視野的百分比表示（遊玩時垂直 50 度）。"
                         "過場動畫保留遊戲原本的構圖。",
    [UI_MENU_ANISO] = "材質過濾",
    [UI_MENU_ANISO_DESC] = "非等向性過濾：從斜角看去的地面、道路與牆壁在遠處依然清晰，不會變得模糊。"
                           "遊戲：遊戲要求的等級，與 Switch 相同。Auto：3D 縮放為 1440p 時用 16x，"
                           "2160p 時用遊戲等級的兩倍，其他情況用遊戲的等級。",
    [UI_MENU_ANISO_GAME] = "遊戲",
    [UI_MENU_ANISO_AUTO] = "Auto",
    [UI_MENU_SHARPNESS] = "FSR 銳利度",
    [UI_MENU_SHARPNESS_DESC] = "FSR 縮放後的銳化；0 為關閉。",
    [UI_MENU_COLOR] = "色彩",
    [UI_MENU_COLOR_PRESET] = "色彩設定檔",
    [UI_MENU_COLOR_PRESET_DESC] = "調整下方的四個數值。鮮豔：更高的對比與飽和度，暗部稍微提亮"
                                  "（為 OLED 設計）。清晰：對比、飽和度與亮度略為提高。更動任何"
                                  "一個數值後，設定檔會變成「自訂」。HUD 會隨畫面改變；本選單不會。",
    [UI_MENU_COLOR_DEFAULT] = "遊戲原始", [UI_MENU_COLOR_VIVID] = "鮮豔（OLED）", [UI_MENU_COLOR_CLARITY] = "清晰",
    [UI_MENU_COLOR_CUSTOM] = "自訂",
    [UI_MENU_COLOR_BRIGHTNESS] = "亮度", [UI_MENU_COLOR_BRIGHTNESS_DESC] = "加到每個顏色上；0 為不變。",
    [UI_MENU_COLOR_CONTRAST] = "對比",
    [UI_MENU_COLOR_CONTRAST_DESC] = "讓顏色遠離中間灰（高於 100 %）或靠近中間灰；100 % 為不變。",
    [UI_MENU_COLOR_SATURATION] = "飽和度",
    [UI_MENU_COLOR_SATURATION_DESC] = "顏色相對於灰色的濃度；100 % 為不變。",
    [UI_MENU_COLOR_GAMMA] = "Gamma",
    [UI_MENU_COLOR_GAMMA_DESC] = "低於 1 會提亮暗部與中間調，高於 1 會使其變暗；1 為不變。",
    [UI_MENU_HDR_GROUP] = "HDR",
    [UI_MENU_HDR] = "HDR 輸出",
    [UI_MENU_HDR_DESC] = "在 HDR 螢幕上呈現強烈的高光。需要在 Windows 中開啟 HDR（「使用 HDR」），或使用"
                         "支援色彩管理的 Wayland 合成器；否則畫面仍為 SDR。重新啟動後套用。"
                         "上方的色彩設定檔是給 SDR 用的，HDR 時不會使用。",
    [UI_MENU_HDR_PEAK] = "最大亮度",
    [UI_MENU_HDR_PEAK_DESC] = "你的螢幕的最大亮度（nits）；最強的高光會止於此值。",
    [UI_MENU_HDR_GAME] = "遊戲亮度",
    [UI_MENU_HDR_GAME_DESC] = "畫面白色的亮度（nits，即紙白）。203 是 HDR 的參考值；在明亮的房間裡"
                              "可以調高。",
    [UI_MENU_HDR_UI] = "HUD 與選單亮度",
    [UI_MENU_HDR_UI_DESC] = "HUD 與本選單白色的亮度（nits）。",
    [UI_MENU_HDR_HUE] = "高光色調校正",
    [UI_MENU_HDR_HUE_DESC] = "火焰、火花等強烈的顏色會像遊戲的 SDR 畫面一樣趨向白色，"
                             "它們投射出的光也是如此；0 會讓它們保持完全飽和。",
    [UI_MENU_SHADOW_SCALE] = "陰影解析度",
    [UI_MENU_SHADOW_SCALE_DESC] = "以遊戲 2048x2048 的若干倍邊長繪製太陽的陰影貼圖："
                                  "陰影邊緣與樹葉的陰影更清晰，代價是視訊記憶體"
                                  "（2x 約 85 至 130 MiB，4x 約 340 至 520 MiB）。下次啟動時套用。",
    [UI_MENU_AO] = "環境光遮蔽",
    [UI_MENU_AO_DESC] = "讓皺摺、角落，以及角色與物體下方的地面等環境光較難到達的地方變暗。"
                        "在世界完成光照後於螢幕空間計算；遊戲本身沒有這項效果。「高」"
                        "比「低」耗用更多 GPU 時間。立即套用。",
    [UI_MENU_AO_OFF] = "關閉",
    [UI_MENU_AO_LOW] = "低",
    [UI_MENU_AO_HIGH] = "高",
    [UI_MENU_UPSCALING] = "升頻器（FSR / DLSS）",
    [UI_MENU_UPSCALING_DESC] = "以時間性升頻器取代遊戲的反鋸齒：邊緣更平滑、閃爍更少，"
                               "選用低於「原生」的模式還能提高 FPS。NVIDIA DLSS 需要 NVIDIA RTX GPU，"
                               "且 nvngx_dlss.dll 要放在 newsnap.exe 旁；Intel XeSS 需要較新的 GPU，且 libxess.dll 要放在 "
                               "newsnap.exe 旁；AMD FSR 可在任何 GPU 上運作。「自動」會在可用時使用 DLSS，"
                               "其他情況使用 FSR。在此選擇的 DLSS 與 XeSS 於重新啟動後套用。HUD 不受影響。",
    [UI_MENU_UPSCALING_DESC_OTHER] = "以時間性升頻器取代遊戲的反鋸齒：邊緣更平滑、閃爍更少，"
                                     "選用低於「原生」的模式還能提高 FPS。AMD FSR 可在任何 GPU 上"
                                     "運作；在這裡「自動」就是 FSR（NVIDIA DLSS 與 Intel XeSS 僅適用於 Windows）。"
                                     "HUD 不受影響。",
    [UI_MENU_UPSCALING_OFF] = "關閉", [UI_MENU_UPSCALING_AUTO] = "自動",
    [UI_MENU_UPSCALING_UNAVAILABLE] = "此處無法使用",
    [UI_MENU_UPSCALING_UNTIL] = "重新啟動前為 %s",
    [UI_MENU_UPSCALING_QUALITY] = "效能縮放",
    [UI_MENU_UPSCALING_QUALITY_DESC] = "升頻器將 3D 場景放大到遊戲解析度之前，場景的繪製大小"
                                       "（顯示在數值下方）。「原生」以完整大小繪製，最為清晰"
                                       "（使用 DLSS 時為 DLAA）。品質、平衡、效能與超高效能分別以"
                                       "約 67、58、50 與 33 % 繪製以提高 FPS；超高效能適用於 "
                                       "3840 x 2160。重新啟動後套用。",
    [UI_MENU_UPSCALING_NATIVE] = "關閉（完整解析度）", [UI_MENU_DLSS_QUALITY] = "品質", [UI_MENU_DLSS_BALANCED] = "平衡",
    [UI_MENU_DLSS_PERFORMANCE] = "效能", [UI_MENU_UPSCALING_ULTRA] = "超高效能",
    [UI_MENU_UPSCALING_MODE_OFF] = "未使用升頻器",
    [UI_MENU_AA] = "反鋸齒（SMAA）",
    [UI_MENU_AA_DESC] = "SMAA 會在繪製 HUD 之前撫平鋸齒狀的邊緣。預設為「高」；Ultra "
                        "能找出更多邊緣，但稍微多用一些 GPU。升頻器運作時不會使用。",
    [UI_SNAP_SMAA_LOW] = "低", [UI_SNAP_SMAA_MEDIUM] = "中", [UI_SNAP_SMAA_HIGH] = "高",
    [UI_MENU_AA_OFF] = "關閉",
    [UI_MENU_AA_BY_UPSCALER] = "由升頻器平滑邊緣",
    [UI_SNAP_RES] = "遊戲內部解析度",
    [UI_SNAP_RES_DESC] = "繪製 3D 場景的解析度。100 % 是遊戲原本的 1920 x 1080：調低可減輕"
                         "負擔，調高（超取樣）則畫面更清晰，但會耗用 GPU 時間。「依螢幕」"
                         "會配合螢幕或視窗的高度。可與反鋸齒一起使用。"
                         "重新啟動後套用。",
    [UI_SNAP_RES_UPSCALER] = "高於 100 % 時：請將效能縮放設為「關閉」",
    [UI_SNAP_FG] = "影格生成",
    [UI_SNAP_FG_DESC] = "AMD FSR 影格生成：每兩個真實影格之間插入一個生成的影格。介面"
                        "不參與插補。當遊戲的速度超過螢幕更新率的一半時會自動暫停。"
                        "效能資訊會顯示真實的 FPS 與生成的 FPS。"
                        "重新啟動後套用。",
    [UI_SNAP_FG_NEEDS] = "需要以 AMD FSR 3.1 或 FSR 4 作為升頻器",
    [UI_SNAP_HDPH] = "HD 相片縮圖",
    [UI_SNAP_HDPH_DESC] = "拍照後的預覽，以及資料夾與選擇畫面中的相片，會使用 "
                          "1080 x 720 的相片，而不是遊戲 360 x 240 的縮圖。儲存的相片與評分"
                          "不受影響。",
    [UI_SNAP_SHADOW] = "陰影解析度",
    [UI_SNAP_SHADOW_DESC] = "放大遊戲所有的陰影貼圖。Auto 會跟隨 3D 解析度：1080p 為 2x，"
                            "125-150 % 為 3x，200 % 以上為 4x。繪製在場景上的陰影不受影響。"
                            "重新啟動後套用。",
    [UI_SNAP_TEXPACK] = "HD 材質包",
    [UI_SNAP_TEXPACK_DESC] = "使用遊戲旁 texpack 資料夾中的 HD 材質，這些材質是在這台電腦上"
                             "以你自己的遊戲製作的。重新啟動後套用。",
    [UI_SNAP_TEXPACK_NONE] = "texpack 資料夾中沒有材質包",
    [UI_SNAP_HDSH] = "HD 陰影模式（實驗性）",
    [UI_SNAP_HDSH_DESC] = "植物、岩石、階梯與場景的陰影是繪製在各關卡的材質上的。"
                          "開啟：啟動器會從你自己的遊戲讀取它們，並在這台電腦上為所有關卡"
                          "放大（「產生 HD 陰影」；開啟啟動器時會自動開始）；完成後即可看到。"
                          "即時陰影也會使用最大的貼圖（關閉時則跟隨內部解析度）。"
                          "重新啟動後套用。",
    [UI_SNAP_TAB] = "強化",
    [UI_SNAP_ENH] = "NewSnap 的強化功能（不會改變遊戲邏輯）",
    [UI_SNAP_ASPECT] = "長寬比",
    [UI_SNAP_ASPECT_DESC] = "「維持 16:9」會在較寬的螢幕上加上黑邊；「延展」會填滿視窗；Ultrawide 會"
                            "以遊戲的比例將 3D 視野擴展至視窗，介面保持在中央，"
                            "相片則照常以 16:9 的視野拍攝（實驗性）。",
    [UI_SNAP_TAB_SYS] = "系統",
    [UI_SNAP_SYS_CONT] = "返回遊戲",
    [UI_SNAP_SYS_CONT_DESC] = "關閉本選單並繼續遊玩。",
    [UI_SNAP_SYS_RESTART] = "重新啟動遊戲",
    [UI_SNAP_SYS_RESTART_DESC] = "關閉遊戲後重新開啟，用於需要重新啟動才會套用的設定。"
                                 "上次存檔之後的進度將會遺失。",
    [UI_SNAP_SYS_QUIT] = "離開並回到桌面",
    [UI_SNAP_SYS_QUIT_DESC] = "關閉遊戲。上次存檔之後的進度將會遺失；遊戲只會在"
                              "每次探險結束後存檔。",
    [UI_MENU_OUTPUT_RES_AUTO] = "自動",
    [UI_MENU_OUTPUT_RES_NEXT] = "，重新啟動後為 %s",

    [UI_MENU_FPS_LIMIT] = "FPS 上限",
    [UI_MENU_FPS_LIMIT_DESC] = "影格率上限：30、60（預設）、90、120 或 144 FPS，或 VRR（略低於"
                               "螢幕更新率）。原本較慢的場景會保留其節奏。立即套用；"
                               "實際達到的 FPS 取決於 GPU 與顯示模式。",
    [UI_MENU_FPS_30] = "30 FPS", [UI_MENU_FPS_60] = "60 FPS",
    [UI_MENU_REALTIME] = "依時鐘決定遊戲速度",
    [UI_MENU_REALTIME_DESC] = "依實際時間推進遊戲，讓較慢的影格不會拖慢遊戲。",
    [UI_MENU_CLOTH_REALTIME] = "依時鐘推進布料",
    [UI_MENU_CLOTH_REALTIME_DESC] = "布料與毛髮也依實際時間推進。",
    [UI_MENU_HIGHFPS_FIX] = "高 FPS 修正",
    [UI_MENU_HIGHFPS_FIX_DESC] = "修正高於 30 FPS 時出錯的物理效果，以及高於 60 時變成透明或"
                                 "看不見的物體。",
    [UI_MENU_GAME_LANG] = "遊戲語言", [UI_MENU_GAME_LANG_DESC] = "遊戲文字與語音的語言。",
    [UI_MENU_GAME_LANG_AUTO] = "自動",
    [UI_MENU_OPERATION_MODE] = "主機模式",
    [UI_MENU_OPERATION_MODE_DESC] = "讓遊戲認為自己是在底座（TV）上還是手提模式。",
    [UI_MENU_MODE_DOCKED] = "TV（底座）", [UI_MENU_MODE_HANDHELD] = "手提",
    [UI_MENU_HUD] = "HUD",
    [UI_MENU_HUD_DESC] = "關閉時，遊玩中不會繪製遊戲的 HUD；選單照常顯示。按 F12 切換。",
    [UI_MENU_ASSUME_FOCUS] = "失去焦點時繼續執行",
    [UI_MENU_ASSUME_FOCUS_DESC] = "開啟（預設）時，你切換到其他視窗後遊戲仍會繼續，鍵盤則要等"
                                  "視窗回到前景才會作用。關閉時，遊戲視窗失去焦點就會暫停，"
                                  "就像在 Switch 上按下 Home 一樣；這樣被中斷的載入可能會"
                                  "卡住。",

    [UI_MENU_MODS_INSTALLED] = "已安裝的模組",
    [UI_MENU_MODS_NONE] = "目前還沒有模組。請將模組解壓縮到 mods 資料夾，每個模組一個資料夾，裡面要有它的 romfs "
                          "資料夾，然後重新啟動遊戲。",
    [UI_MENU_MODS_OPEN] = "開啟模組資料夾",
    [UI_MENU_MODS_OPEN_DESC] = "顯示遊戲載入模組的資料夾。若不存在則會建立。",
    [UI_MENU_MODS_ROW_DESC] = "取代的遊戲檔案：%u 個。新增的檔案：%u 個。",
    [UI_MENU_MODS_OVERRIDDEN] = "其中 %u 個檔案改由清單中位置較高的 %s 提供。",
    [UI_MENU_MODS_MOVE_HINT] = "上方按鈕或 Ctrl+上 可將它上移，左方按鈕或 Ctrl+下 可將它下移。當兩個"
                               "模組更動同一個檔案時，以位置較高者為準。變更於重新啟動後套用。",
    [UI_MENU_MODS_EMPTY] = "這個資料夾沒有 romfs、exefs 或 cheats 檔案。",
    [UI_MENU_MODS_SUBSDK] = "這個模組帶有自己的遊戲程式碼（subsdk 外掛或被取代的 main）。移植版"
                            "無法載入程式碼模組，因此整個模組都會停用。",
    [UI_MENU_MODS_EXEFS_LATER] = "這個模組會修補遊戲程式碼（exefs）。遊戲會在下次啟動時整合這些修補"
                                 "（需要幾分鐘的重建）；在那之前整個模組都會停用。",
    [UI_MENU_MODS_CHEATS] = "金手指：%d 個。",
    [UI_MENU_MODS_CHEATS_FILE] = "這個遊戲版本的金手指會在啟動時從此模組的 cheats\\%s 讀取。",
    [UI_MENU_MODS_BAD_NAME] = "資料夾名稱含有 |，而模組清單用它來分隔名稱。請重新命名"
                              "資料夾。",
    [UI_MENU_MODS_OTHER_VERSION] = "其中 %u 個檔案是給其他遊戲版本用的，已略過。請尋找"
                                   "為你的遊戲版本製作的這個模組。",
    [UI_MENU_MODS_UNUSED] = "未使用",

    [UI_MENU_VOLUME] = "音量", [UI_MENU_VOLUME_DESC] = "遊戲的整體音量。",

    [UI_MENU_MOTION] = "體感操作", [UI_MENU_MOTION_DESC] = "用手把的陀螺儀瞄準。",
    [UI_MENU_RUMBLE_STRENGTH] = "震動強度",
    [UI_MENU_RUMBLE_STRENGTH_DESC] = "手把震動的力道。",
    [UI_MENU_RUMBLE_CURVE] = "震動曲線",
    [UI_MENU_RUMBLE_CURVE_DESC] = "數值越低，輕微的震動越會被加強。",
    [UI_MENU_RUMBLE_TRIGGERS] = "扳機震動（Xbox）",
    [UI_MENU_RUMBLE_TRIGGERS_DESC] = "讓 Xbox 手把的扳機也一起震動。",
    [UI_MENU_PAD_LAYOUT] = "按鈕配置",
    [UI_MENU_PAD_LAYOUT_DESC] = "哪一顆按鈕是 A。Nintendo：右邊那顆，與 Switch 相同。Xbox：下面那顆，與 Xbox "
                                "手把相同。PlayStation：下面那顆（叉），其餘按位置對應，供 PlayStation "
                                "按鈕模組使用。「自動」會為印有 Nintendo 標示的手把選擇 Nintendo，"
                                "PlayStation 手把選擇 PlayStation，其他則選擇 Xbox。遊戲提示顯示哪一種手把，"
                                "請在「按鈕提示」中選擇。",
    [UI_MENU_PAD_LAYOUT_AUTO] = "自動", [UI_MENU_PAD_LAYOUT_NINTENDO] = "Nintendo（A 在右）",
    [UI_MENU_PAD_LAYOUT_XBOX] = "Xbox（A 在下）", [UI_MENU_PAD_LAYOUT_PLAYSTATION] = "PlayStation（A 在下）",
    [UI_MENU_PAD_LAYOUT_IN_USE] = "使用中：%s",
    [UI_MENU_PROMPTS] = "按鈕提示",
    [UI_MENU_PROMPTS_DESC] = "遊戲提示顯示哪一種手把的按鈕。「自動」會跟隨使用中的手把。"
                             "Nintendo：遊戲原本的圖示。Xbox 與 PlayStation：為各配置繪製的按鈕模組。"
                             "遊戲在啟動時讀取提示，因此重新啟動後才會改變。",
    [UI_MENU_PROMPTS_AUTO] = "自動", [UI_MENU_PROMPTS_NINTENDO] = "Nintendo", [UI_MENU_PROMPTS_XBOX] = "Xbox",
    [UI_MENU_PROMPTS_PLAYSTATION] = "PlayStation",
    [UI_MENU_PROMPTS_MISSING] = "缺少提示檔案：請重新執行安裝",
    [UI_MENU_PROMPTS_FAILED] = "提示檔案已損毀：請重新執行安裝",
    [UI_MENU_PROMPTS_RESTART] = "提示於重新啟動後改變",
    [UI_MENU_PROMPTS_OFF_SHAPE] = "遊戲解析度不是 16:9 時停用",
    [UI_MENU_PROMPTS_OFF_MODS] = "已停用：有 RomFS 模組取代了它的檔案",
    [UI_MENU_PROMPTS_OFF_PATCHES] = "設定了 AC_ROMFS_PATCHES 時停用",
    [UI_MENU_RESTART] = "立即重新啟動",
    [UI_MENU_RESTART_DESC] = "關閉遊戲後以新的提示重新開啟。上次存檔之後的進度"
                             "將會遺失。",
    [UI_MENU_RESTART_CONFIRM] = "要立即重新啟動遊戲嗎？上次存檔之後的進度將會遺失。",
    [UI_MENU_RESTART_YES] = "重新啟動",
    [UI_MENU_RESTART_SAVING] = "遊戲正在存檔：稍後即可重新啟動。",
    [UI_MENU_LSTICK_DEADZONE] = "左搖桿死區", [UI_MENU_RSTICK_DEADZONE] = "右搖桿死區",
    [UI_MENU_STICK_DEADZONE_DESC] = "搖桿要移動多少遊戲才會察覺。如果角色或攝影機會自己移動，"
                                    "請調高：放開搖桿，查看「搖桿目前」的數值，再把死區設得比它"
                                    "高幾個百分點。",
    [UI_MENU_STICK_DEADZONE_NOW] = "搖桿目前：%.0f %%",
    [UI_MENU_MOUSE_SENS] = "滑鼠靈敏度",
    [UI_MENU_MOUSE_SENS_DESC] = "用滑鼠轉動攝影機的速度。",
    [UI_MENU_WALK_KEY] = "步行鍵",
    [UI_MENU_WALK_KEY_DESC] = "按住時，鍵盤的搖桿只會傾斜一部分，變成步行而不是"
                              "奔跑。傾斜多少由步行幅度決定。不影響手把與滑鼠。",
    [UI_MENU_WALK_KEY_TAKEN] = "同時也是 %s",
    [UI_MENU_WALK_SCALE] = "步行幅度",
    [UI_MENU_WALK_SCALE_DESC] = "按住步行鍵時鍵盤搖桿的傾斜程度。一半是步行，"
                                "最大是奔跑。",
    [UI_MENU_STICK_SENS] = "搖桿攝影機速度",
    [UI_MENU_STICK_SENS_DESC] = "將遊戲右搖桿的攝影機速度（包含最高速度）乘上此倍率，套用於遊戲的"
                                "五種靈敏度。滑鼠有自己的設定。",

    [UI_BINDS_HELP] = "選擇一個欄位並按 A 或 Enter，再按下按鍵、滑鼠按鈕或手把按鈕。Delete 或 X "
                      "可清空欄位。已使用的按鍵會移到這裡；手把按鈕則會與被它取代的按鈕"
                      "互換。",
    [UI_BINDS_COL_KEY1] = "按鍵 1", [UI_BINDS_COL_KEY2] = "按鍵 2", [UI_BINDS_COL_PAD] = "手把",
    [UI_BINDS_GROUP_BUTTONS] = "按鈕", [UI_BINDS_GROUP_MOVE] = "移動", [UI_BINDS_GROUP_CAMERA] = "攝影機",
    [UI_BINDS_PRESS_KEY] = "請按下按鍵或滑鼠按鈕以設定 %s",
    [UI_BINDS_PRESS_PAD] = "請按下手把按鈕以設定 %s",
    [UI_BINDS_CANCEL_HINT] = "按 Esc 取消，或等待 %d 秒",
    [UI_BINDS_TAKEN] = "%s 已從 %s 移除", [UI_BINDS_SWAPPED] = "%s 已與 %s 互換",
    [UI_BINDS_RESET] = "重設所有按鈕",
    [UI_BINDS_RESET_DESC] = "恢復預設的按鍵與按鈕。上方的配置會重新套用："
                            "重新指定過的手把按鈕會留在你設定的位置，直到這次重設為止。",
    [UI_BIND_A] = "A", [UI_BIND_B] = "B", [UI_BIND_X] = "X", [UI_BIND_Y] = "Y",
    [UI_BIND_LCLICK] = "按下左搖桿", [UI_BIND_RCLICK] = "按下右搖桿", [UI_BIND_L] = "L",
    [UI_BIND_R] = "R", [UI_BIND_ZL] = "ZL", [UI_BIND_ZR] = "ZR", [UI_BIND_PLUS] = "加號（+）", [UI_BIND_MINUS] = "減號（-）",
    [UI_BIND_LEFT] = "十字鍵左", [UI_BIND_UP] = "十字鍵上", [UI_BIND_RIGHT] = "十字鍵右",
    [UI_BIND_DOWN] = "十字鍵下",
    [UI_BIND_LSTICK_LEFT] = "向左移動", [UI_BIND_LSTICK_UP] = "向前移動",
    [UI_BIND_LSTICK_RIGHT] = "向右移動", [UI_BIND_LSTICK_DOWN] = "向後移動",
    [UI_BIND_RSTICK_LEFT] = "攝影機向左", [UI_BIND_RSTICK_UP] = "攝影機向上",
    [UI_BIND_RSTICK_RIGHT] = "攝影機向右", [UI_BIND_RSTICK_DOWN] = "攝影機向下",
    [UI_BIND_DESC_A] = "互動、撿取、交談。", [UI_BIND_DESC_B] = "奔跑、取消、返回。",
    [UI_BIND_DESC_X] = "跳躍。", [UI_BIND_DESC_Y] = "攻擊。", [UI_BIND_DESC_LCLICK] = "蹲下。",
    [UI_BIND_DESC_RCLICK] = "第一人稱視角。", [UI_BIND_DESC_L] = "能力。",
    [UI_BIND_DESC_R] = "投擲。", [UI_BIND_DESC_ZL] = "盾牌、鎖定。", [UI_BIND_DESC_ZR] = "弓。",
    [UI_BIND_DESC_PLUS] = "選單、物品欄。", [UI_BIND_DESC_MINUS] = "地圖。",
    [UI_BIND_DESC_DPAD] = "快速選擇。",
    [UI_BIND_DESC_MOVE] = "與左搖桿一樣進行移動。手把的左搖桿也始終有效。",
    [UI_BIND_DESC_CAMERA] = "與右搖桿一樣轉動攝影機。滑鼠與手把的右搖桿也始終"
                            "有效。",
    [UI_KEY_SPACE] = "空白鍵", [UI_KEY_TAB] = "Tab", [UI_KEY_LSHIFT] = "左 Shift", [UI_KEY_LCTRL] = "左 Ctrl",
    [UI_KEY_UP] = "方向鍵上", [UI_KEY_DOWN] = "方向鍵下", [UI_KEY_LEFT] = "方向鍵左",
    [UI_KEY_RIGHT] = "方向鍵右",
    [UI_KEY_MOUSE_L] = "滑鼠左鍵", [UI_KEY_MOUSE_R] = "滑鼠右鍵", [UI_KEY_MOUSE_M] = "滑鼠中鍵",
    [UI_KEY_MOUSE_X1] = "滑鼠 4", [UI_KEY_MOUSE_X2] = "滑鼠 5",
    [UI_KEY_ENTER] = "Enter", [UI_KEY_BACKSPACE] = "Backspace", [UI_KEY_RSHIFT] = "右 Shift",
    [UI_KEY_RCTRL] = "右 Ctrl", [UI_KEY_LALT] = "Alt", [UI_KEY_CAPSLOCK] = "Caps Lock", [UI_KEY_INSERT] = "Insert",
    [UI_KEY_DELETE] = "Delete", [UI_KEY_HOME] = "Home", [UI_KEY_END] = "End", [UI_KEY_PAGEUP] = "Page Up",
    [UI_KEY_PAGEDOWN] = "Page Down", [UI_KEY_NUM_FMT] = "數字鍵 %s",
    [UI_PAD_SOUTH] = "下方按鈕", [UI_PAD_EAST] = "右方按鈕", [UI_PAD_WEST] = "左方按鈕",
    [UI_PAD_NORTH] = "上方按鈕", [UI_PAD_LSTICK] = "左搖桿", [UI_PAD_RSTICK] = "右搖桿",
    [UI_PAD_L] = "左肩鍵", [UI_PAD_R] = "右肩鍵", [UI_PAD_START] = "Start",
    [UI_PAD_BACK] = "Back",
    [UI_PAD_DPAD_LEFT] = "十字鍵左", [UI_PAD_DPAD_UP] = "十字鍵上", [UI_PAD_DPAD_RIGHT] = "十字鍵右",
    [UI_PAD_DPAD_DOWN] = "十字鍵下", [UI_PAD_ZL] = "左扳機", [UI_PAD_ZR] = "右扳機",
    [UI_PAD_LPADDLE1] = "左背鍵", [UI_PAD_RPADDLE1] = "右背鍵",
    [UI_PAD_LPADDLE2] = "左背鍵 2", [UI_PAD_RPADDLE2] = "右背鍵 2",
    [UI_PAD_CROSS] = "叉", [UI_PAD_CIRCLE] = "圓圈", [UI_PAD_SQUARE] = "方塊", [UI_PAD_TRIANGLE] = "三角",

    [UI_MENU_MENU_LANG] = "選單語言", [UI_MENU_MENU_LANG_DESC] = "本選單與螢幕上資訊的語言。",
    [UI_MENU_MENU_LANG_AUTO] = "自動（依 Windows）",

    [UI_MENU_ADV_WARNING] = "這些設定用於測試與排除問題。請在清楚原因的情況下才更動。",
    [UI_MENU_GROUP_SCHED] = "排程", [UI_MENU_GROUP_SHADERS] = "著色器與管線",
    [UI_MENU_GROUP_TEXMEM] = "材質與記憶體", [UI_MENU_GROUP_FIXES] = "算繪修正",
    [UI_MENU_GROUP_VULKAN] = "Vulkan", [UI_MENU_GROUP_DIAG] = "診斷",
    [UI_MENU_ASYNC_PREEMPT] = "虛擬核心搶佔",
    [UI_MENU_ASYNC_PREEMPT_DESC] = "允許遊戲的一個執行緒中斷同一虛擬核心上的另一個執行緒。",
    [UI_MENU_PREEMPT_OFF] = "關閉", [UI_MENU_PREEMPT_ON] = "開啟", [UI_MENU_PREEMPT_INHERIT] = "僅繼承",
    [UI_MENU_REPLAY_ASYNC] = "在獨立執行緒準備影格",
    [UI_MENU_REPLAY_ASYNC_DESC] = "在另一個執行緒而非遊戲執行緒為 GPU 準備影格。最多會增加"
                                  "一個影格的延遲。",
    [UI_MENU_TIMER_1MS] = "Windows 1 ms 計時器",
    [UI_MENU_TIMER_1MS_DESC] = "將系統計時器的解析度提高到 1 ms，讓影格節奏更穩定。",
    [UI_MENU_PIPE_WAIT] = "等待中繪製的處理方式",
    [UI_MENU_PIPE_WAIT_DESC] = "「預設」維持目前的排程，並保留一個工作執行緒給等待中的"
                               "繪製；「舊版（繪製）」使用先前的排程。",
    [UI_MENU_PIPE_WAIT_DEFAULT] = "預設", [UI_MENU_PIPE_WAIT_DRAW] = "舊版（繪製）",
    [UI_MENU_PIPE_SKIP] = "建立管線時略過的繪製",
    [UI_MENU_PIPE_SKIP_DESC] = "哪些繪製會被捨棄，而不是等待其管線。",
    [UI_MENU_PIPE_SKIP_STRICT] = "嚴格", [UI_MENU_PIPE_SKIP_ANY] = "任何",
    [UI_MENU_PIPE_SKIP_FULLSCREEN] = "全螢幕繪製階段",
    [UI_MENU_LIB_PREBUILD] = "預先編譯階段程式庫",
    [UI_MENU_LIB_PREBUILD_DESC] = "在背景預先編譯著色器階段程式庫。",
    [UI_MENU_LIB_PREBUILD_THREADS] = "程式庫預先編譯執行緒",
    [UI_MENU_LIB_PREBUILD_THREADS_DESC] = "用於預先編譯的執行緒；「自動」會依你的 CPU 選擇數量。",
    [UI_MENU_PIPE_PREBUILD] = "預先編譯管線",
    [UI_MENU_PIPE_PREBUILD_DESC] = "預先編譯已知的管線。",
    [UI_MENU_PREWARM_XLATE] = "預熱轉譯器",
    [UI_MENU_PREWARM_XLATE_DESC] = "啟動時轉譯已知著色器的執行緒；「自動」使用 CPU 執行緒數的"
                                   "一半，最多 16 個。",
    [UI_MENU_GPL] = "圖形管線程式庫",
    [UI_MENU_GPL_DESC] = "使用 Vulkan 的管線程式庫擴充功能；如果你的驅動程式因此出錯，請關閉。",
    [UI_MENU_ASTC] = "ASTC 材質解碼",
    [UI_MENU_ASTC_DESC] = "在哪裡解碼 ASTC 壓縮材質。",
    [UI_MENU_ASTC_AUTO] = "自動", [UI_MENU_ASTC_GPU] = "GPU 著色器", [UI_MENU_ASTC_NATIVE] = "原生",
    [UI_MENU_ASTC_CPU] = "CPU",
    [UI_MENU_MEMORY] = "GPU 記憶體模式",
    [UI_MENU_MEMORY_DESC] = "遊戲的記憶體如何與 GPU 共用。",
    [UI_MENU_MEMORY_AUTO] = "自動", [UI_MENU_MEMORY_IMPORT] = "匯入", [UI_MENU_MEMORY_MIRROR] = "鏡像",
    [UI_MENU_MEMORY_VERIFY] = "驗證",
    [UI_MENU_TEX_ALIAS] = "材質別名",
    [UI_MENU_TEX_ALIAS_DESC] = "在另一個使用中材質的記憶體上建立的新材質，會以該內容為起始，而不是"
                               "空白。",
    [UI_MENU_TEX_VRAM_PRESSURE] = "材質記憶體上限",
    [UI_MENU_TEX_VRAM_PRESSURE_DESC] = "視訊記憶體用量達到此百分比後，會捨棄遊戲已釋放的材質"
                                       "（使用時再從儲存裝置載回）。0 為全部保留。",
    [UI_MENU_ASTC_BC] = "將 ASTC 壓縮為 BC",
    [UI_MENU_ASTC_BC_DESC] = "搭配 GPU 解碼器：將解碼後的 ASTC 材質重新編碼，不透明者為 BC1，"
                             "其餘為 BC3，只佔四分之一到八分之一的視訊記憶體。適用於 4 GB 以下的 GPU；"
                             "材質看起來會稍微有塊狀感。",
    [UI_MENU_LOD_GUARD] = "LOD 保護",
    [UI_MENU_LOD_GUARD_DESC] = "等遊戲重寫完細節層級後才讓 GPU 讀取，避免物體在錯誤的位置"
                               "閃現，或遠方背景有一個影格變得"
                               "平板。",
    [UI_MENU_FIX_C0] = "常數緩衝區修正",
    [UI_MENU_FIX_C0_DESC] = "填入驅動程式保留的 c0 常數區（儲存大小、分派大小、"
                            "點大小、基底實例），而不是讀到零。",
    [UI_MENU_FIX_ZERO] = "將新的 GPU 記憶體清零",
    [UI_MENU_FIX_ZERO_DESC] = "新的 GPU 記憶體集區從零開始，與 Switch 的記憶體相同。",
    [UI_MENU_BIND_SKIP] = "略過重複的繫結",
    [UI_MENU_BIND_SKIP_DESC] = "最佳化：略過沒有變更的繫結。",
    [UI_MENU_SHADER_MEMO] = "著色器快取記憶", [UI_MENU_SHADER_MEMO_DESC] = "最佳化：記住著色器的查詢結果。",
    [UI_MENU_PIPE_MEMO] = "管線快取記憶",
    [UI_MENU_PIPE_MEMO_DESC] = "最佳化：狀態重複時重複使用上一次繪製的管線。",
    [UI_MENU_TEX_MEMO] = "材質繫結快取記憶",
    [UI_MENU_TEX_MEMO_DESC] = "最佳化：在各次繪製之間記住材質描述元。",
    [UI_MENU_DESC_TEMPLATE] = "描述元範本",
    [UI_MENU_DESC_TEMPLATE_DESC] = "最佳化：成批更新描述元。",
    [UI_MENU_PUSH_SKIP] = "略過重複的 push constants",
    [UI_MENU_PUSH_SKIP_DESC] = "最佳化：略過沒有變更的 push constants。",
    [UI_MENU_SPLIT_DRAWS] = "提早送交 GPU",
    [UI_MENU_SPLIT_DRAWS_DESC] = "在繪製階段之間每 N 次繪製就分批送出 GPU 工作，讓 GPU 提早"
                                 "開始；0 為關閉。",
    [UI_MENU_VK_VALIDATION] = "驗證層",
    [UI_MENU_VK_VALIDATION_DESC] = "檢查每一個 Vulkan 呼叫，會讓遊戲變得很慢。",
    [UI_MENU_VK_VALIDATION_MISSING] = "尚未安裝驗證層。",
    [UI_MENU_VK_DYN_VERTEX] = "動態頂點狀態",
    [UI_MENU_VK_DYN_VERTEX_DESC] = "強制開啟或關閉動態頂點輸入；預設值取決於"
                                   "GPU。",
    [UI_MENU_VK_DYN_A2C] = "動態 alpha to coverage",
    [UI_MENU_VK_DYN_A2C_DESC] = "強制開啟或關閉動態 alpha to coverage。預設：在 RDNA 2 及更早的 "
                                "AMD 驅動程式上關閉，因為開啟時角色會被畫成黑色；"
                                "其他情況開啟。",
    [UI_MENU_VK_SUBGROUP_PIN] = "固定子群組大小",
    [UI_MENU_VK_SUBGROUP_PIN_DESC] = "固定著色器的子群組大小。",
    [UI_MENU_TRACE] = "效能記錄", [UI_MENU_TRACE_DESC] = "將影格時間寫入檔案。",
    [UI_MENU_FLIGHT] = "飛行記錄器",
    [UI_MENU_FLIGHT_DESC] = "保留一小段歷程，並在影格凍結時寫入檔案。",
    [UI_MENU_FLIGHT_SPIKE_MS] = "凍結門檻（ms）",
    [UI_MENU_FLIGHT_SPIKE_MS_DESC] = "視為凍結的影格時間。",
    [UI_MENU_INPUT_RECORD] = "錄製輸入",
    [UI_MENU_INPUT_RECORD_DESC] = "將你的按鍵操作寫入檔案，以便回報錯誤。",
    [UI_MENU_OPEN_LOG] = "開啟記錄檔資料夾", [UI_MENU_OPEN_LOG_DESC] = "顯示存放記錄檔的資料夾。",
    [UI_MENU_COPY_INFO] = "複製系統資訊",
    [UI_MENU_COPY_INFO_DESC] = "將 GPU、驅動程式、CPU、RAM 與已變更的設定複製到剪貼簿。",
    [UI_MENU_COPY_INFO_DONE] = "已複製", [UI_MENU_ACTION_FAILED] = "未成功",
    [UI_MENU_RESET] = "重設所有設定", [UI_MENU_RESET_DESC] = "套用於所有分頁。",
    [UI_MENU_RESET_CONFIRM] = "要將所有設定重設為預設值嗎？",
    [UI_MENU_RESET_YES] = "重設",
    [UI_MENU_RESET_NO] = "取消",

    [UI_MENU_OV_FPS] = "%.0f FPS", [UI_MENU_OV_FRAME_MS] = "%.1f ms", [UI_MENU_OV_GAME_PCT] = "遊戲 %.0f%%",
    [UI_MENU_OV_MAX_MS] = "最大 %.1f ms",
    [UI_MENU_OV_GPU] = "GPU", [UI_MENU_OV_CPU] = "CPU", [UI_MENU_OV_RAM] = "RAM", [UI_MENU_OV_VRAM] = "VRAM",
    [UI_MENU_OV_TEMP] = "溫度", [UI_MENU_OV_POWER] = "耗電", [UI_MENU_OV_CLOCK] = "時脈",
    [UI_MENU_OV_NONE] = "-",
    [UI_MENU_OV_REPLAY] = "影格準備", [UI_MENU_OV_GPU_TIME] = "每影格 GPU 忙碌時間",
    [UI_MENU_OV_PIPE_WAIT] = "管線等待",
    [UI_MENU_OV_SHADER_WAIT] = "著色器等待", [UI_MENU_OV_TEX_UPLOADS] = "材質上傳",
    [UI_MENU_OV_FMT_PCT] = "%.0f%%", [UI_MENU_OV_FMT_TEMP] = "%.0f °C", [UI_MENU_OV_FMT_POWER] = "%.0f W",
    [UI_MENU_OV_FMT_MHZ] = "%.0f MHz", [UI_MENU_OV_FMT_GB] = "%.1f GB", [UI_MENU_OV_FMT_GB_OF] = "/ %.1f GB",
    [UI_MENU_OV_GAME_GB] = "遊戲 %.1f GB", [UI_MENU_OV_FMT_MS] = "%.2f ms", [UI_MENU_OV_PER_FRAME] = "每影格 %.1f",
    [UI_MENU_OV_WINDOW] = "視窗", [UI_MENU_OV_OUTPUT] = "遊戲畫面", [UI_MENU_OV_SCENE] = "3D 場景",
    [UI_MENU_OV_SCALING] = "縮放", [UI_MENU_OV_LIMIT] = "FPS 上限", [UI_MENU_OV_PRESENT] = "呈現模式",
    [UI_MENU_OV_TEX] = "材質壓縮", [UI_MENU_OV_OS] = "系統",
    [UI_MENU_OV_FMT_SIZE] = "%ux%u", [UI_MENU_OV_FMT_SCENE] = "%ux%u，%.0f%%",
    [UI_MENU_OV_FMT_FSR] = "AMD FSR 1，銳利度 %d%%", [UI_MENU_OV_SCALE_NONE] = "無（1:1）",
    [UI_MENU_OV_SCALE_BILINEAR] = "雙線性",
    [UI_MENU_OV_FMT_AREA] = "區域平均，銳利度 %d%%",
    [UI_MENU_OV_FMT_PRESHARP] = "HUD 之前的 RCAS，銳利度 %d%%",
    [UI_MENU_TAB_CHEATS] = "金手指",
    [UI_MENU_CHEATS_NONE] = "這個遊戲版本沒有金手指。模組的金手指是放在其 cheats 資料夾中的 "
                            "Atmosphere 金手指檔案，以遊戲的 build 名稱命名：mods\\<mod>\\cheats\\%s。"
                            "重新啟動遊戲即可讀取。若金手指會更動遊戲程式碼，遊戲會在啟動時"
                            "重建（需要幾分鐘）。",
    [UI_MENU_CHEATS_MOD] = "%s：%d 個金手指",
    [UI_MENU_CHEAT_CODE_DESC] = "更動遊戲程式碼。立即生效。",
    [UI_MENU_CHEAT_KEY_DESC] = "按住 %s 時更動遊戲程式碼。立即生效。",
    [UI_MENU_CHEAT_DATA_DESC] = "開啟期間，每個影格都會寫入遊戲的記憶體。",
    [UI_MENU_CHEAT_MASTER] = "一律開啟",
    [UI_MENU_CHEAT_MASTER_DESC] = "檔案中的主代碼：一律開啟。",
    [UI_MENU_CHEAT_RESTORE] = "不需要",
    [UI_MENU_CHEAT_RESTORE_DESC] = "只是把遊戲原本的程式碼寫回去。關閉金手指時就已經會這麼做。",
    [UI_MENU_CHEAT_REBUILD] = "重建後",
    [UI_MENU_CHEAT_REBUILD_DESC] = "這個金手指會更動遊戲程式碼，而且是在遊戲建置之後新增或編輯的。"
                                   "遊戲會在下次啟動時整合它（需要幾分鐘），或者使用「立即重建"
                                   "遊戲」。",
    [UI_MENU_CHEAT_UNSUPPORTED] = "不支援",
    [UI_MENU_CHEAT_UNSUPPORTED_DESC] = "這個金手指無法用於這個遊戲版本：",
    [UI_MENU_CHEATS_REBUILD] = "立即重建遊戲",
    [UI_MENU_CHEATS_REBUILD_DESC] = "有些金手指會更動遊戲程式碼但尚未整合：它們是新增或"
                                    "編輯過的，或是上次重建失敗或被取消。此操作會關閉遊戲；安裝程式"
                                    "會整合它們（需要幾分鐘）並重新開啟遊戲。上次存檔之後的進度"
                                    "將會遺失。",
    [UI_MENU_MODS_EXEFS_UNSUPPORTED] = "這個模組以移植版無法套用的方式修補遊戲程式碼（exefs），"
                                       "因此整個模組都會停用。%s",
    [UI_MENU_MODS_EXEFS_OTHER] = "它的程式碼修補（exefs）是給其他遊戲版本用的。",
    [UI_MENU_MODS_EXEFS_ON] = "使用中的程式碼修補：%d 個檔案。",
    [UI_MENU_MODS_REPLACES_BUILTIN] = "使用中的程式碼修補：%d 個檔案。它們取代了移植版內建的修補 %s，"
                                      "在這個模組啟用期間，該內建修補會停用。",
};
