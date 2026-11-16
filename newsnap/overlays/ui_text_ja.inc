// The in-game menu in Japanese (MENU-LANG-01), every string of text_es (ui_text_es.inc).
// Included by ui_text.c in place of the keyboard-only Japanese row.
static const char *const text_ja[UI_TEXT_COUNT] = {
    SWKBD("文字入力", "名前を入力してください", "ウマ", "OK", "キャンセル", "コントローラー: A = OK、B = キャンセル"),

    [UI_MENU_TITLE] = "設定",
    [UI_MENU_TAB_SCREEN] = "画面", [UI_MENU_TAB_GAME] = "ゲーム", [UI_MENU_TAB_MODS] = "Mod", [UI_MENU_TAB_SOUND] = "サウンド",
    [UI_MENU_TAB_CONTROLS] = "操作", [UI_MENU_TAB_MENU] = "メニュー", [UI_MENU_TAB_ADVANCED] = "詳細設定",
    [UI_MENU_CONTINUE] = "続ける", [UI_MENU_QUIT] = "ゲームを終了",
    [UI_MENU_ON] = "オン", [UI_MENU_OFF] = "オフ", [UI_MENU_AUTO] = "自動",
    [UI_MENU_DEFAULT_MARK] = "デフォルト",
    [UI_MENU_AFTER_RESTART] = "再起動後に反映", [UI_MENU_SET_BY_ENV] = "環境変数で固定されています",
    [UI_MENU_SAVE_FAILED] = "設定を保存できませんでした",
    [UI_MENU_VERSION] = "NewSnapRecomp %s、Snap %s",

    [UI_MENU_FULLSCREEN] = "フルスクリーン",
    [UI_MENU_FULLSCREEN_DESC] = "ゲームを画面全体に表示します。F11 で切り替えられます。",
    [UI_MENU_WINDOW_SIZE] = "ウィンドウサイズ",
    [UI_MENU_WINDOW_SIZE_DESC] = "フルスクリーンでないときのゲームウィンドウの大きさです。",
    [UI_MENU_WINDOW_SIZE_CUSTOM] = "カスタム",
    [UI_MENU_PRESENT] = "表示モード", [UI_MENU_PRESENT_DESC] = "完成したフレームを画面に送る方法です。",
    [UI_MENU_PRESENT_MAILBOX] = "Mailbox", [UI_MENU_PRESENT_VSYNC] = "VSync", [UI_MENU_PRESENT_IMMEDIATE] = "即時",
    [UI_MENU_PRESENT_IN_USE] = "使用中: %s",
    [UI_MENU_GPU] = "グラフィックカード", [UI_MENU_GPU_DESC] = "ゲームを描画する Vulkan デバイスです。",
    [UI_MENU_GPU_AUTO] = "自動",
    [UI_MENU_PERF_OVERLAY] = "パフォーマンス表示",
    [UI_MENU_PERF_OVERLAY_DESC] = "画面右上に FPS を表示します。「詳細」ではグラフ付きのフレーム時間、CPU・GPU・メモリの"
                                  "使用率、温度、描画スレッドの待ち時間も表示します。F10 でモードを切り替えられます。",
    [UI_MENU_PERF_OFF] = "非表示", [UI_MENU_PERF_FPS] = "FPS", [UI_MENU_PERF_FULL] = "詳細",
    [UI_PERF_LINE_FPS] = "%.0f fps",
    [UI_MENU_GRAPHICS] = "映像",
    [UI_MENU_OUTPUT_RES] = "ゲームの解像度",
    [UI_MENU_OUTPUT_RES_DESC] = "ゲームが映像と UI を描画する大きさです。1280 x 720 は最も軽く、性能の控えめな GPU "
                                "向けです。1920 x 1080 を超えると、より多くのメモリ（2560 x 1440 で約 240 MB、"
                                "3840 x 2160 で約 790 MB の増加）と GPU 時間が必要になります。再起動後に反映されます。"
                                "「自動」は画面の大きさに合わせます。通常は 1920 x 1080 まで、アップスケーラーが"
                                "有効なときは 3840 x 2160 までです。",
    [UI_MENU_UPSCALER] = "ウィンドウへの拡大縮小",
    [UI_MENU_UPSCALER_DESC] = "映像をウィンドウの大きさに合わせる方法です。FSR はバイリニアよりも輪郭や細部を"
                              "くっきり保ち、映像がウィンドウと同じ大きさでもシャープにします。",
    [UI_MENU_UPSCALER_FSR] = "AMD FSR 1", [UI_MENU_UPSCALER_BILINEAR] = "バイリニア",
    [UI_MENU_FOV] = "視野角",
    [UI_MENU_FOV_DESC] = "カメラに映る範囲を、ゲーム本来の視野角（プレイ中は垂直 50 度）に対する割合で指定します。"
                         "ムービーシーンはゲーム本来の構図のままです。",
    [UI_MENU_ANISO] = "テクスチャフィルタリング",
    [UI_MENU_ANISO_DESC] = "異方性フィルタリング: 斜めから見た地面や道、壁が、遠くでもぼやけずくっきり見えます。"
                           "ゲーム: Switch と同じ、ゲームが指定するレベルです。オート: 3D スケールが 1440p のときは 16x、"
                           "2160p のときはゲームのレベルの 2 倍、それ以外はゲームのレベルです。",
    [UI_MENU_ANISO_GAME] = "ゲーム",
    [UI_MENU_ANISO_AUTO] = "オート",
    [UI_MENU_SHARPNESS] = "FSR のシャープネス",
    [UI_MENU_SHARPNESS_DESC] = "FSR による拡大後のシャープ化です。0 で無効になります。",
    [UI_MENU_COLOR] = "カラー",
    [UI_MENU_COLOR_PRESET] = "カラープロファイル",
    [UI_MENU_COLOR_PRESET_DESC] = "下の 4 つの値をまとめて設定します。ビビッド: コントラストと彩度を上げ、暗部を少し"
                                  "明るくします（OLED 向け）。クリア: コントラスト、彩度、明るさを少し上げます。値を"
                                  "動かすとプロファイルは「カスタム」になります。HUD は映像と一緒に変わりますが、"
                                  "このメニューは変わりません。",
    [UI_MENU_COLOR_DEFAULT] = "ゲーム本来", [UI_MENU_COLOR_VIVID] = "ビビッド（OLED）", [UI_MENU_COLOR_CLARITY] = "クリア",
    [UI_MENU_COLOR_CUSTOM] = "カスタム",
    [UI_MENU_COLOR_BRIGHTNESS] = "明るさ", [UI_MENU_COLOR_BRIGHTNESS_DESC] = "すべての色に加算します。0 で変化なしです。",
    [UI_MENU_COLOR_CONTRAST] = "コントラスト",
    [UI_MENU_COLOR_CONTRAST_DESC] = "色を中間のグレーから遠ざけます（100 % より上）、または近づけます。100 % で変化なしです。",
    [UI_MENU_COLOR_SATURATION] = "彩度",
    [UI_MENU_COLOR_SATURATION_DESC] = "グレーに対する色の鮮やかさです。100 % で変化なしです。",
    [UI_MENU_COLOR_GAMMA] = "ガンマ",
    [UI_MENU_COLOR_GAMMA_DESC] = "1 より下では暗部と中間調が明るくなり、1 より上では暗くなります。1 で変化なしです。",
    [UI_MENU_HDR_GROUP] = "HDR",
    [UI_MENU_HDR] = "HDR 出力",
    [UI_MENU_HDR_DESC] = "HDR 対応画面で強い輝きを表現します。Windows で HDR（「HDR を使用する」）を有効にするか、"
                         "カラーマネジメント対応の Wayland コンポジターが必要です。ない場合は SDR のままになります。"
                         "再起動後に反映されます。上のカラープロファイルは SDR 用で、HDR では使われません。",
    [UI_MENU_HDR_PEAK] = "最大輝度",
    [UI_MENU_HDR_PEAK_DESC] = "お使いの画面の最大輝度（nit）です。最も明るい部分はこの値で止まります。",
    [UI_MENU_HDR_GAME] = "ゲームの明るさ",
    [UI_MENU_HDR_GAME_DESC] = "映像の白（ペーパーホワイト）の輝度（nit）です。203 が HDR の基準値です。明るい部屋では"
                              "上げてください。",
    [UI_MENU_HDR_UI] = "HUD とメニューの明るさ",
    [UI_MENU_HDR_UI_DESC] = "HUD とこのメニューの白の輝度（nit）です。",
    [UI_MENU_HDR_HUE] = "ハイライトの色相補正",
    [UI_MENU_HDR_HUE_DESC] = "炎や火花などの強い色が、それらが放つ光と同じように、ゲームの SDR 映像のように白に"
                             "近づきます。0 では完全に飽和した色のままになります。",
    [UI_MENU_SHADOW_SCALE] = "影の解像度",
    [UI_MENU_SHADOW_SCALE_DESC] = "太陽のシャドウマップを、ゲーム本来の 2048x2048 に対して一辺あたり指定倍の大きさで"
                                  "描画します。影の輪郭や木の葉の影がくっきりしますが、ビデオメモリを使います"
                                  "（2x で約 85～130 MiB、4x で約 340～520 MiB）。次回の起動時に反映されます。",
    [UI_MENU_AO] = "アンビエントオクルージョン",
    [UI_MENU_AO_DESC] = "ひだや隅、キャラクターや物の下の地面など、環境光が届きにくい場所を暗くします。ワールドの"
                        "ライティング後に画面上で計算します。ゲーム自体にはこの機能はありません。「高」は「低」より "
                        "GPU 時間がかかります。すぐに反映されます。",
    [UI_MENU_AO_OFF] = "オフ",
    [UI_MENU_AO_LOW] = "低",
    [UI_MENU_AO_HIGH] = "高",
    [UI_MENU_UPSCALING] = "アップスケーラー（FSR / DLSS）",
    [UI_MENU_UPSCALING_DESC] = "ゲームのアンチエイリアスの代わりに使うテンポラルアップスケーラーです。輪郭がより"
                               "なめらかになり、ちらつきが減ります。ネイティブより下のモードでは FPS も上がります。"
                               "NVIDIA DLSS には NVIDIA RTX GPU と、newsnap.exe と同じ場所に nvngx_dlss.dll が必要です。"
                               "Intel XeSS には最近の GPU と、newsnap.exe と同じ場所に libxess.dll が必要です。AMD FSR は"
                               "どの GPU でも動作します。「自動」は使える場合は DLSS を、それ以外では FSR を使います。"
                               "ここで選んだ DLSS と XeSS は再起動後に反映されます。HUD は変わりません。",
    [UI_MENU_UPSCALING_DESC_OTHER] = "ゲームのアンチエイリアスの代わりに使うテンポラルアップスケーラーです。輪郭がより"
                                     "なめらかになり、ちらつきが減ります。ネイティブより下のモードでは FPS も上がります。"
                                     "AMD FSR はどの GPU でも動作します。ここでは「自動」は FSR です（NVIDIA DLSS と "
                                     "Intel XeSS は Windows 専用です）。HUD は変わりません。",
    [UI_MENU_UPSCALING_OFF] = "オフ", [UI_MENU_UPSCALING_AUTO] = "自動",
    [UI_MENU_UPSCALING_UNAVAILABLE] = "ここでは使用できません",
    [UI_MENU_UPSCALING_UNTIL] = "再起動するまで %s",
    [UI_MENU_UPSCALING_QUALITY] = "パフォーマンススケーリング",
    [UI_MENU_UPSCALING_QUALITY_DESC] = "アップスケーラーがゲームの解像度に拡大する前の、3D シーンの描画サイズです"
                                       "（値の下に表示されます）。ネイティブはフルサイズで描画し、最もくっきりします"
                                       "（DLSS では DLAA）。クオリティ、バランス、パフォーマンス、ウルトラパフォーマンスは"
                                       "約 67、58、50、33 % で描画して FPS を上げます。ウルトラパフォーマンスは "
                                       "3840 x 2160 向けです。再起動後に反映されます。",
    [UI_MENU_UPSCALING_NATIVE] = "オフ（フル解像度）", [UI_MENU_DLSS_QUALITY] = "クオリティ", [UI_MENU_DLSS_BALANCED] = "バランス",
    [UI_MENU_DLSS_PERFORMANCE] = "パフォーマンス", [UI_MENU_UPSCALING_ULTRA] = "ウルトラパフォーマンス",
    [UI_MENU_UPSCALING_MODE_OFF] = "アップスケーラーなし",
    [UI_MENU_AA] = "アンチエイリアス（SMAA）",
    [UI_MENU_AA_DESC] = "SMAA は HUD を描画する前に、輪郭のギザギザをなめらかにします。デフォルトは「高」です。"
                        "「ウルトラ」は GPU 負荷が少し増えますが、より多くの輪郭を検出します。アップスケーラーの"
                        "動作中は使われません。",
    [UI_SNAP_SMAA_LOW] = "低", [UI_SNAP_SMAA_MEDIUM] = "中", [UI_SNAP_SMAA_HIGH] = "高",
    [UI_MENU_AA_OFF] = "オフ",
    [UI_MENU_AA_BY_UPSCALER] = "アップスケーラーが輪郭をなめらかにします",
    [UI_SNAP_RES] = "ゲームの内部解像度",
    [UI_SNAP_RES_DESC] = "3D シーンを描画する解像度です。100 % はゲーム本来の 1920 x 1080 です。下げると軽くなり、"
                         "上げる（スーパーサンプリング）とよりくっきりしますが GPU 時間がかかります。「画面に合わせる」は"
                         "画面またはウィンドウの高さに合わせます。アンチエイリアスと併用できます。再起動後に"
                         "反映されます。",
    [UI_SNAP_RES_UPSCALER] = "100 % を超える場合: パフォーマンススケーリングを「オフ」にしてください",
    [UI_SNAP_FG] = "フレーム生成",
    [UI_SNAP_FG_DESC] = "AMD FSR フレーム生成: 実フレーム 2 枚の間に生成フレームを 1 枚はさみます。UI は補間の"
                        "対象外です。ゲームがモニターのリフレッシュレートの半分より速く動いている間は自動で"
                        "一時停止します。パフォーマンス表示には実 FPS と生成 FPS が表示されます。再起動後に"
                        "反映されます。",
    [UI_SNAP_FG_NEEDS] = "アップスケーラーに AMD FSR 3.1 または FSR 4、NVIDIA DLSS が必要です",
    [UI_SNAP_HDPH] = "写真サムネイルの HD 化",
    [UI_SNAP_HDPH_DESC] = "撮影後のプレビューと、フォルダーや選択画面の写真に、ゲームの 360 x 240 のサムネイルの"
                          "代わりに 1080 x 720 の写真を使います。保存される写真と評価は変わりません。",
    [UI_SNAP_SHADOW] = "影の解像度",
    [UI_SNAP_SHADOW_DESC] = "ゲームのすべてのシャドウマップを拡大します。オートは 3D 解像度に従います: 1080p で 2x、"
                            "125-150 % で 3x、200 % 以上で 4x。ステージに描き込まれた影は変わりません。再起動後に"
                            "反映されます。",
    [UI_SNAP_TEXPACK] = "HD テクスチャパック",
    [UI_SNAP_TEXPACK_DESC] = "ゲームと同じ場所の texpack フォルダーにある HD テクスチャを使います。これはお持ちの"
                             "ゲームをもとに、この PC で作成されたものです。再起動後に反映されます。",
    [UI_SNAP_TEXPACK_NONE] = "texpack フォルダーにパックがありません",
    [UI_SNAP_HDSH] = "HD シャドウモード（試験的）",
    [UI_SNAP_HDSH_DESC] = "植物、岩、階段、ステージの影は、各レベルのテクスチャに描き込まれています。オン: "
                          "ランチャーがお持ちのゲームからそれらを読み取り、この PC ですべてのレベル分を拡大します"
                          "（「HD シャドウを生成」。ランチャーを開くと自動で始まります）。完了すると表示されます。"
                          "リアルタイムの影も最大のシャドウマップを使います（オフのときは内部解像度に従います）。"
                          "再起動後に反映されます。",
    [UI_SNAP_UIMOTION] = "メニューとインターフェースを滑らかに（実験的）",
    [UI_SNAP_UIMOTION_DESC] = "60 FPS を超えるとき、メニューとインターフェースの動きを毎秒 60 "
                              "ステップではなく表示されるフレームごとに描画します。ゲームのロジックは変わりません。メニューが二重に見えたりちらついたりする場合はオフにしてください。再起動後に適用されます。",
    [UI_SNAP_TAB] = "拡張機能",
    [UI_SNAP_ENH] = "NewSnap の拡張機能（ゲームのロジックは変わりません）",
    [UI_SNAP_ASPECT] = "アスペクト比",
    [UI_SNAP_ASPECT_DESC] = "「16:9 を維持」は横長の画面で左右に帯を表示します。「引き伸ばし」はウィンドウ全体に"
                            "広げます。「ウルトラワイド」はゲームの比率のまま 3D ビューをウィンドウまで広げ、UI を"
                            "中央に置き、写真はこれまでどおり 16:9 のビューで撮影します（試験的）。",
    [UI_SNAP_TAB_SYS] = "システム",
    [UI_SNAP_SYS_CONT] = "ゲームに戻る",
    [UI_SNAP_SYS_CONT_DESC] = "このメニューを閉じてゲームを続けます。",
    [UI_SNAP_SYS_RESTART] = "ゲームを再起動",
    [UI_SNAP_SYS_RESTART_DESC] = "再起動後に反映される設定のために、ゲームを閉じてもう一度開きます。最後にセーブした"
                                 "後の進行状況は失われます。",
    [UI_SNAP_SYS_QUIT] = "デスクトップに戻る",
    [UI_SNAP_SYS_QUIT_DESC] = "ゲームを終了します。最後にセーブした後の進行状況は失われます。ゲームは調査が"
                              "終わるたびにだけセーブします。",
    [UI_MENU_OUTPUT_RES_AUTO] = "自動",
    [UI_MENU_OUTPUT_RES_NEXT] = "、再起動後は %s",

    [UI_MENU_FPS_LIMIT] = "FPS 上限",
    [UI_MENU_FPS_LIMIT_DESC] = "フレームレートの上限: 30、60（デフォルト）、90、120、144 FPS、または VRR（モニターの"
                               "リフレッシュレートのすぐ下）。もともと低いフレームレートのシーンは、そのテンポを"
                               "保ちます。すぐに反映されます。実際の FPS は GPU と表示モードによって変わります。",
    [UI_MENU_FPS_30] = "30 FPS", [UI_MENU_FPS_60] = "60 FPS",
    [UI_MENU_REALTIME] = "ゲーム速度を実時間に合わせる",
    [UI_MENU_REALTIME_DESC] = "ゲームを実時間に合わせて進め、遅いフレームがあってもゲームが遅くならないようにします。",
    [UI_MENU_CLOTH_REALTIME] = "布を実時間に合わせる",
    [UI_MENU_CLOTH_REALTIME_DESC] = "布や髪の動きも実時間に合わせて進めます。",
    [UI_MENU_HIGHFPS_FIX] = "高 FPS 向けの修正",
    [UI_MENU_HIGHFPS_FIX_DESC] = "30 FPS を超えると不具合が出る物理演算と、60 FPS を超えると透明になったり"
                                 "見えなくなったりするオブジェクトを修正します。",
    [UI_MENU_GAME_LANG] = "ゲームの言語", [UI_MENU_GAME_LANG_DESC] = "ゲームのテキストと音声の言語です。",
    [UI_MENU_GAME_LANG_AUTO] = "自動",
    [UI_MENU_OPERATION_MODE] = "本体モード",
    [UI_MENU_OPERATION_MODE_DESC] = "ゲームに、ドック接続（TV）と携帯モードのどちらで動作していると認識させるかです。",
    [UI_MENU_MODE_DOCKED] = "TV（ドック）", [UI_MENU_MODE_HANDHELD] = "携帯モード",
    [UI_MENU_HUD] = "HUD",
    [UI_MENU_HUD_DESC] = "オフにすると、プレイ中にゲームの HUD を表示しません。メニューは表示されます。F12 で"
                         "切り替えられます。",
    [UI_MENU_ASSUME_FOCUS] = "非アクティブでも続行",
    [UI_MENU_ASSUME_FOCUS_DESC] = "オン（デフォルト）では、ほかのウィンドウを使っている間もゲームが動き続け、"
                                  "ウィンドウが前面に戻るまでキーボード操作は効きません。オフでは、Switch で HOME を"
                                  "押したときのように、ウィンドウがフォーカスを失うと一時停止します。その場合、"
                                  "中断されたロードが止まったままになることがあります。",

    [UI_MENU_MODS_INSTALLED] = "インストール済みの Mod",
    [UI_MENU_MODS_NONE] = "まだ Mod がありません。Mod を mods フォルダーに展開し（Mod ごとに 1 つのフォルダー、"
                          "その中に romfs フォルダー）、ゲームを再起動してください。",
    [UI_MENU_MODS_OPEN] = "Mod フォルダーを開く",
    [UI_MENU_MODS_OPEN_DESC] = "ゲームが Mod を読み込むフォルダーを表示します。存在しない場合は作成されます。",
    [UI_MENU_MODS_ROW_DESC] = "置き換えるゲームファイル: %u。追加する新しいファイル: %u。",
    [UI_MENU_MODS_OVERRIDDEN] = "この Mod の %u 個のファイルは、リストでより上にある %s のものが使われます。",
    [UI_MENU_MODS_MOVE_HINT] = "上ボタンまたは Ctrl+上 で上へ、左ボタンまたは Ctrl+下 で下へ移動します。2 つの Mod が"
                               "同じファイルを変更する場合は、上にあるものが優先されます。変更は再起動後に"
                               "反映されます。",
    [UI_MENU_MODS_EMPTY] = "このフォルダーには romfs、exefs、cheats のファイルがありません。",
    [UI_MENU_MODS_SUBSDK] = "この Mod は独自のゲームコード（subsdk プラグインまたは置き換えられた main）を含んで"
                            "います。この移植版はコードモジュールを読み込めないため、Mod 全体が無効になります。",
    [UI_MENU_MODS_EXEFS_LATER] = "この Mod はゲームのコードにパッチを当てます（exefs）。パッチは次回の起動時に"
                                 "組み込まれます（数分かかる再ビルド）。それまで Mod 全体が無効になります。",
    [UI_MENU_MODS_CHEATS] = "チート: %d 個。",
    [UI_MENU_MODS_CHEATS_FILE] = "このゲームバージョン用のチートは、起動時にこの Mod の cheats\\%s から読み込まれます。",
    [UI_MENU_MODS_BAD_NAME] = "フォルダー名に | が含まれています。この文字は Mod リストで名前の区切りに使われます。"
                              "フォルダー名を変更してください。",
    [UI_MENU_MODS_OTHER_VERSION] = "この Mod の %u 個のファイルは別のゲームバージョン用のため、スキップされます。"
                                   "お使いのゲームバージョン向けに作られたこの Mod を探してください。",
    [UI_MENU_MODS_UNUSED] = "未使用",

    [UI_MENU_VOLUME] = "音量", [UI_MENU_VOLUME_DESC] = "ゲーム全体の音量です。",

    [UI_MENU_MOTION] = "モーション操作", [UI_MENU_MOTION_DESC] = "コントローラーのジャイロで狙いをつけます。",
    [UI_MENU_RUMBLE_STRENGTH] = "振動の強さ",
    [UI_MENU_RUMBLE_STRENGTH_DESC] = "コントローラーが振動する強さです。",
    [UI_MENU_RUMBLE_CURVE] = "振動カーブ",
    [UI_MENU_RUMBLE_CURVE_DESC] = "値を下げると、弱い振動が強調されます。",
    [UI_MENU_RUMBLE_TRIGGERS] = "トリガーの振動（Xbox）",
    [UI_MENU_RUMBLE_TRIGGERS_DESC] = "Xbox コントローラーのトリガーも振動させます。",
    [UI_MENU_PAD_LAYOUT] = "ボタン配置",
    [UI_MENU_PAD_LAYOUT_DESC] = "どのボタンを A にするかです。Nintendo: Switch と同じ右のボタン。Xbox: Xbox "
                                "コントローラーと同じ下のボタン。PlayStation: 下のボタン（×）で、残りは位置どおり。"
                                "PlayStation ボタン Mod 向けです。「自動」は Nintendo 表記のコントローラーでは "
                                "Nintendo、PlayStation コントローラーでは PlayStation、それ以外では Xbox を選びます。"
                                "ゲーム内のボタン表示にどのコントローラーを使うかは「ボタン表示」で選びます。",
    [UI_MENU_PAD_LAYOUT_AUTO] = "自動", [UI_MENU_PAD_LAYOUT_NINTENDO] = "Nintendo（A が右）",
    [UI_MENU_PAD_LAYOUT_XBOX] = "Xbox（A が下）", [UI_MENU_PAD_LAYOUT_PLAYSTATION] = "PlayStation（A が下）",
    [UI_MENU_PAD_LAYOUT_IN_USE] = "使用中: %s",
    [UI_MENU_PROMPTS] = "ボタン表示",
    [UI_MENU_PROMPTS_DESC] = "ゲーム内のボタン表示に、どのコントローラーのボタンを使うかです。「自動」は使用中の"
                             "コントローラーに合わせます。Nintendo: ゲーム本来の表示。Xbox と PlayStation: それぞれの"
                             "配置に合わせて描かれたボタン Mod。ゲームは起動時にボタン表示を読み込むため、変更は"
                             "再起動後に反映されます。",
    [UI_MENU_PROMPTS_AUTO] = "自動", [UI_MENU_PROMPTS_NINTENDO] = "Nintendo", [UI_MENU_PROMPTS_XBOX] = "Xbox",
    [UI_MENU_PROMPTS_PLAYSTATION] = "PlayStation",
    [UI_MENU_PROMPTS_MISSING] = "ボタン表示のファイルがありません: インストールをやり直してください",
    [UI_MENU_PROMPTS_FAILED] = "ボタン表示のファイルが壊れています: インストールをやり直してください",
    [UI_MENU_PROMPTS_RESTART] = "ボタン表示は再起動後に変わります",
    [UI_MENU_PROMPTS_OFF_SHAPE] = "ゲームの解像度が 16:9 でないため無効",
    [UI_MENU_PROMPTS_OFF_MODS] = "無効: RomFS の Mod がこのファイルを置き換えています",
    [UI_MENU_PROMPTS_OFF_PATCHES] = "AC_ROMFS_PATCHES が設定されている間は無効",
    [UI_MENU_RESTART] = "今すぐ再起動",
    [UI_MENU_RESTART_DESC] = "ゲームを閉じて、新しいボタン表示でもう一度開きます。最後にセーブした後の進行状況は"
                             "失われます。",
    [UI_MENU_RESTART_CONFIRM] = "今すぐゲームを再起動しますか？最後にセーブした後の進行状況は失われます。",
    [UI_MENU_RESTART_YES] = "再起動",
    [UI_MENU_RESTART_SAVING] = "ゲームがセーブ中です。まもなく再起動できるようになります。",
    [UI_MENU_LSTICK_DEADZONE] = "左スティックのデッドゾーン", [UI_MENU_RSTICK_DEADZONE] = "右スティックのデッドゾーン",
    [UI_MENU_STICK_DEADZONE_DESC] = "スティックをどれだけ動かすとゲームが反応するかです。キャラクターやカメラが"
                                    "勝手に動く場合は上げてください。スティックから指を離して「現在のスティック」を"
                                    "確認し、デッドゾーンをそれより数ポイント上に設定します。",
    [UI_MENU_STICK_DEADZONE_NOW] = "現在のスティック: %.0f %%",
    [UI_MENU_MOUSE_SENS] = "マウス感度",
    [UI_MENU_MOUSE_SENS_DESC] = "マウスでカメラが回る速さです。",
    [UI_MENU_WALK_KEY] = "歩行キー",
    [UI_MENU_WALK_KEY_DESC] = "押している間、キーボードのスティック入力が途中までしか倒れず、走らずに歩きます。"
                              "どこまで倒すかは「歩行スケール」で決まります。コントローラーとマウスには影響しません。",
    [UI_MENU_WALK_KEY_TAKEN] = "%s にも割り当て済み",
    [UI_MENU_WALK_SCALE] = "歩行スケール",
    [UI_MENU_WALK_SCALE_DESC] = "歩行キーを押しているときの、キーボードのスティック入力の倒し具合です。半分で歩き、"
                                "最大で走りになります。",
    [UI_MENU_STICK_SENS] = "スティックのカメラ速度",
    [UI_MENU_STICK_SENS_DESC] = "ゲームの 5 段階の感度それぞれで、右スティックのカメラ速度（最高速度を含む）に"
                                "倍率をかけます。マウスには専用の設定があります。",

    [UI_BINDS_HELP] = "マスを選んで A または Enter を押し、続けてキー、マウスボタン、コントローラーのボタンを"
                      "押してください。Delete または X でマスを空にします。使用中のキーはここへ移動し、コントローラーの"
                      "ボタンは置き換え先のボタンと入れ替わります。",
    [UI_BINDS_COL_KEY1] = "キー 1", [UI_BINDS_COL_KEY2] = "キー 2", [UI_BINDS_COL_PAD] = "コントローラー",
    [UI_BINDS_GROUP_BUTTONS] = "ボタン", [UI_BINDS_GROUP_MOVE] = "移動", [UI_BINDS_GROUP_CAMERA] = "カメラ",
    [UI_BINDS_PRESS_KEY] = "「%s」に割り当てるキーまたはマウスボタンを押してください",
    [UI_BINDS_PRESS_PAD] = "「%s」に割り当てるコントローラーのボタンを押してください",
    [UI_BINDS_CANCEL_HINT] = "Esc でキャンセル、または %d 秒待つ",
    [UI_BINDS_TAKEN] = "%s を「%s」から解除しました", [UI_BINDS_SWAPPED] = "%s を %s と入れ替えました",
    [UI_BINDS_RESET] = "すべてのボタンをリセット",
    [UI_BINDS_RESET_DESC] = "キーとボタンをデフォルトに戻します。上のボタン配置があらためて適用されます。割り当てを"
                            "変えたコントローラーのボタンは、このリセットまでは設定した位置のままです。",
    [UI_BIND_A] = "A", [UI_BIND_B] = "B", [UI_BIND_X] = "X", [UI_BIND_Y] = "Y",
    [UI_BIND_LCLICK] = "左スティック押し込み", [UI_BIND_RCLICK] = "右スティック押し込み", [UI_BIND_L] = "L",
    [UI_BIND_R] = "R", [UI_BIND_ZL] = "ZL", [UI_BIND_ZR] = "ZR", [UI_BIND_PLUS] = "プラス（+）", [UI_BIND_MINUS] = "マイナス（-）",
    [UI_BIND_LEFT] = "方向ボタン左", [UI_BIND_UP] = "方向ボタン上", [UI_BIND_RIGHT] = "方向ボタン右",
    [UI_BIND_DOWN] = "方向ボタン下",
    [UI_BIND_LSTICK_LEFT] = "左へ移動", [UI_BIND_LSTICK_UP] = "前へ移動",
    [UI_BIND_LSTICK_RIGHT] = "右へ移動", [UI_BIND_LSTICK_DOWN] = "後ろへ移動",
    [UI_BIND_RSTICK_LEFT] = "カメラ左", [UI_BIND_RSTICK_UP] = "カメラ上",
    [UI_BIND_RSTICK_RIGHT] = "カメラ右", [UI_BIND_RSTICK_DOWN] = "カメラ下",
    [UI_BIND_DESC_A] = "調べる、拾う、話す。", [UI_BIND_DESC_B] = "走る、キャンセル、戻る。",
    [UI_BIND_DESC_X] = "ジャンプ。", [UI_BIND_DESC_Y] = "攻撃。", [UI_BIND_DESC_LCLICK] = "しゃがむ。",
    [UI_BIND_DESC_RCLICK] = "一人称視点。", [UI_BIND_DESC_L] = "アビリティ。",
    [UI_BIND_DESC_R] = "投げる。", [UI_BIND_DESC_ZL] = "盾、注目。", [UI_BIND_DESC_ZR] = "弓。",
    [UI_BIND_DESC_PLUS] = "メニュー、持ち物。", [UI_BIND_DESC_MINUS] = "マップ。",
    [UI_BIND_DESC_DPAD] = "クイック選択。",
    [UI_BIND_DESC_MOVE] = "左スティックと同じように移動します。コントローラーの左スティックも常に使えます。",
    [UI_BIND_DESC_CAMERA] = "右スティックと同じようにカメラを回します。マウスとコントローラーの右スティックも常に"
                            "使えます。",
    [UI_KEY_SPACE] = "スペース", [UI_KEY_TAB] = "Tab", [UI_KEY_LSHIFT] = "左 Shift", [UI_KEY_LCTRL] = "左 Ctrl",
    [UI_KEY_UP] = "上矢印", [UI_KEY_DOWN] = "下矢印", [UI_KEY_LEFT] = "左矢印",
    [UI_KEY_RIGHT] = "右矢印",
    [UI_KEY_MOUSE_L] = "左クリック", [UI_KEY_MOUSE_R] = "右クリック", [UI_KEY_MOUSE_M] = "中クリック",
    [UI_KEY_MOUSE_X1] = "マウス 4", [UI_KEY_MOUSE_X2] = "マウス 5",
    [UI_KEY_ENTER] = "Enter", [UI_KEY_BACKSPACE] = "Backspace", [UI_KEY_RSHIFT] = "右 Shift",
    [UI_KEY_RCTRL] = "右 Ctrl", [UI_KEY_LALT] = "Alt", [UI_KEY_CAPSLOCK] = "Caps Lock", [UI_KEY_INSERT] = "Insert",
    [UI_KEY_DELETE] = "Delete", [UI_KEY_HOME] = "Home", [UI_KEY_END] = "End", [UI_KEY_PAGEUP] = "Page Up",
    [UI_KEY_PAGEDOWN] = "Page Down", [UI_KEY_NUM_FMT] = "テンキー %s",
    [UI_PAD_SOUTH] = "下ボタン", [UI_PAD_EAST] = "右ボタン", [UI_PAD_WEST] = "左ボタン",
    [UI_PAD_NORTH] = "上ボタン", [UI_PAD_LSTICK] = "左スティック", [UI_PAD_RSTICK] = "右スティック",
    [UI_PAD_L] = "左ショルダーボタン", [UI_PAD_R] = "右ショルダーボタン", [UI_PAD_START] = "Start",
    [UI_PAD_BACK] = "Back",
    [UI_PAD_DPAD_LEFT] = "方向ボタン左", [UI_PAD_DPAD_UP] = "方向ボタン上", [UI_PAD_DPAD_RIGHT] = "方向ボタン右",
    [UI_PAD_DPAD_DOWN] = "方向ボタン下", [UI_PAD_ZL] = "左トリガー", [UI_PAD_ZR] = "右トリガー",
    [UI_PAD_LPADDLE1] = "左背面ボタン", [UI_PAD_RPADDLE1] = "右背面ボタン",
    [UI_PAD_LPADDLE2] = "左背面ボタン 2", [UI_PAD_RPADDLE2] = "右背面ボタン 2",
    [UI_PAD_CROSS] = "×", [UI_PAD_CIRCLE] = "○", [UI_PAD_SQUARE] = "□", [UI_PAD_TRIANGLE] = "△",

    [UI_MENU_MENU_LANG] = "メニューの言語", [UI_MENU_MENU_LANG_DESC] = "このメニューと画面上の情報表示の言語です。",
    [UI_MENU_MENU_LANG_AUTO] = "自動（Windows の設定）",

    [UI_MENU_ADV_WARNING] = "これらの設定はテストと問題解決のためのものです。理由がわかっている場合にだけ変更してください。",
    [UI_MENU_GROUP_SCHED] = "スケジューリング", [UI_MENU_GROUP_SHADERS] = "シェーダーとパイプライン",
    [UI_MENU_GROUP_TEXMEM] = "テクスチャとメモリ", [UI_MENU_GROUP_FIXES] = "描画の修正",
    [UI_MENU_GROUP_VULKAN] = "Vulkan", [UI_MENU_GROUP_DIAG] = "診断",
    [UI_MENU_ASYNC_PREEMPT] = "仮想コアのプリエンプション",
    [UI_MENU_ASYNC_PREEMPT_DESC] = "同じ仮想コア上で、ゲームのスレッドが別のスレッドに割り込めるようにします。",
    [UI_MENU_PREEMPT_OFF] = "オフ", [UI_MENU_PREEMPT_ON] = "オン", [UI_MENU_PREEMPT_INHERIT] = "継承のみ",
    [UI_MENU_REPLAY_ASYNC] = "フレームを専用スレッドで準備",
    [UI_MENU_REPLAY_ASYNC_DESC] = "GPU 向けのフレームを、ゲームのスレッドではなく別のスレッドで準備します。最大で "
                                  "1 フレームの遅延が加わります。",
    [UI_MENU_TIMER_1MS] = "Windows の 1 ms タイマー",
    [UI_MENU_TIMER_1MS_DESC] = "システムタイマーの分解能を 1 ms に上げて、フレームのテンポを安定させます。",
    [UI_MENU_PIPE_WAIT] = "待機中の描画の扱い",
    [UI_MENU_PIPE_WAIT_DESC] = "「デフォルト」は、待機中の描画用にワーカーを 1 つ確保する現在のスケジューリングを"
                               "使います。「旧方式（描画）」は以前のスケジューリングを使います。",
    [UI_MENU_PIPE_WAIT_DEFAULT] = "デフォルト", [UI_MENU_PIPE_WAIT_DRAW] = "旧方式（描画）",
    [UI_MENU_PIPE_SKIP] = "パイプライン作成中にスキップする描画",
    [UI_MENU_PIPE_SKIP_DESC] = "パイプラインを待たずに破棄する描画の種類です。",
    [UI_MENU_PIPE_SKIP_STRICT] = "厳格", [UI_MENU_PIPE_SKIP_ANY] = "すべて",
    [UI_MENU_PIPE_SKIP_FULLSCREEN] = "フルスクリーンパス",
    [UI_MENU_LIB_PREBUILD] = "ステージライブラリを事前ビルド",
    [UI_MENU_LIB_PREBUILD_DESC] = "シェーダーステージのライブラリを、バックグラウンドであらかじめコンパイルします。",
    [UI_MENU_LIB_PREBUILD_THREADS] = "ライブラリ事前ビルドのスレッド数",
    [UI_MENU_LIB_PREBUILD_THREADS_DESC] = "事前ビルドに使うスレッド数です。「自動」は CPU に合わせた数を選びます。",
    [UI_MENU_PIPE_PREBUILD] = "パイプラインを事前ビルド",
    [UI_MENU_PIPE_PREBUILD_DESC] = "既知のパイプラインをあらかじめコンパイルします。",
    [UI_MENU_PREWARM_XLATE] = "トランスレーターのプリウォーム",
    [UI_MENU_PREWARM_XLATE_DESC] = "起動時に既知のシェーダーを変換するスレッド数です。「自動」は CPU スレッド数の半分、"
                                   "最大 16 を使います。",
    [UI_MENU_GPL] = "グラフィックスパイプラインライブラリ",
    [UI_MENU_GPL_DESC] = "Vulkan のパイプラインライブラリ拡張を使います。ドライバーで問題が起きる場合はオフに"
                         "してください。",
    [UI_MENU_ASTC] = "ASTC テクスチャのデコード",
    [UI_MENU_ASTC_DESC] = "ASTC 圧縮テクスチャをデコードする場所です。",
    [UI_MENU_ASTC_AUTO] = "自動", [UI_MENU_ASTC_GPU] = "GPU シェーダー", [UI_MENU_ASTC_NATIVE] = "ネイティブ",
    [UI_MENU_ASTC_CPU] = "CPU",
    [UI_MENU_MEMORY] = "GPU メモリモード",
    [UI_MENU_MEMORY_DESC] = "ゲームのメモリを GPU と共有する方法です。",
    [UI_MENU_MEMORY_AUTO] = "自動", [UI_MENU_MEMORY_IMPORT] = "インポート", [UI_MENU_MEMORY_MIRROR] = "ミラー",
    [UI_MENU_MEMORY_VERIFY] = "検証",
    [UI_MENU_TEX_ALIAS] = "テクスチャエイリアス",
    [UI_MENU_TEX_ALIAS_DESC] = "使用中の別のテクスチャのメモリ上に作られた新しいテクスチャが、空ではなくその内容から"
                               "始まります。",
    [UI_MENU_TEX_VRAM_PRESSURE] = "テクスチャメモリの上限",
    [UI_MENU_TEX_VRAM_PRESSURE_DESC] = "ビデオメモリの使用率がこの割合を超えると、ゲームが解放したテクスチャを"
                                       "破棄します（使うときにストレージから読み直します）。0 では保持します。",
    [UI_MENU_ASTC_BC] = "ASTC を BC に圧縮",
    [UI_MENU_ASTC_BC_DESC] = "GPU デコーダー使用時: デコードした ASTC テクスチャを、不透明なら BC1、それ以外は BC3 に"
                             "再エンコードします。ビデオメモリは 4 分の 1 から 8 分の 1 になります。4 GB 以下の GPU "
                             "向けです。テクスチャに少しブロックノイズが出ます。",
    [UI_MENU_LOD_GUARD] = "LOD ガード",
    [UI_MENU_LOD_GUARD_DESC] = "ゲームが LOD の書き換えを終えるまで GPU の読み取りを待たせることで、オブジェクトが"
                               "間違った場所で一瞬ちらついたり、遠景が 1 フレームだけ平坦になったりするのを防ぎます。",
    [UI_MENU_FIX_C0] = "定数バッファーの修正",
    [UI_MENU_FIX_C0_DESC] = "ドライバー予約の定数バンク c0（ストレージサイズ、ディスパッチサイズ、ポイントサイズ、"
                            "ベースインスタンス）を、ゼロを読む代わりに正しい値で埋めます。",
    [UI_MENU_FIX_ZERO] = "新しい GPU メモリをゼロで初期化",
    [UI_MENU_FIX_ZERO_DESC] = "新しい GPU メモリプールが、Switch のメモリと同じようにゼロから始まります。",
    [UI_MENU_BIND_SKIP] = "重複したバインドをスキップ",
    [UI_MENU_BIND_SKIP_DESC] = "最適化: 変更のないバインドをスキップします。",
    [UI_MENU_SHADER_MEMO] = "シェーダーメモ", [UI_MENU_SHADER_MEMO_DESC] = "最適化: シェーダーの検索結果を記憶します。",
    [UI_MENU_PIPE_MEMO] = "パイプラインメモ",
    [UI_MENU_PIPE_MEMO_DESC] = "最適化: 状態が同じ場合、前の描画のパイプラインを再利用します。",
    [UI_MENU_TEX_MEMO] = "テクスチャバインドメモ",
    [UI_MENU_TEX_MEMO_DESC] = "最適化: 描画間でテクスチャのディスクリプターを記憶します。",
    [UI_MENU_DESC_TEMPLATE] = "ディスクリプターテンプレート",
    [UI_MENU_DESC_TEMPLATE_DESC] = "最適化: ディスクリプターをまとめて更新します。",
    [UI_MENU_PUSH_SKIP] = "重複した push constants をスキップ",
    [UI_MENU_PUSH_SKIP_DESC] = "最適化: 変更のない push constants をスキップします。",
    [UI_MENU_SPLIT_DRAWS] = "GPU への早期送信",
    [UI_MENU_SPLIT_DRAWS_DESC] = "パスの合間に N 回の描画ごとに GPU の処理を分けて送り、GPU が早く処理を始められる"
                                 "ようにします。0 で無効になります。",
    [UI_MENU_VK_VALIDATION] = "検証レイヤー",
    [UI_MENU_VK_VALIDATION_DESC] = "Vulkan の呼び出しをすべて検査します。ゲームがかなり遅くなります。",
    [UI_MENU_VK_VALIDATION_MISSING] = "検証レイヤーがインストールされていません。",
    [UI_MENU_VK_DYN_VERTEX] = "動的な頂点ステート",
    [UI_MENU_VK_DYN_VERTEX_DESC] = "動的な頂点入力を強制的にオンまたはオフにします。デフォルトは GPU によって"
                                   "異なります。",
    [UI_MENU_VK_DYN_A2C] = "動的な alpha to coverage",
    [UI_MENU_VK_DYN_A2C_DESC] = "動的な alpha to coverage を強制的にオンまたはオフにします。デフォルト: RDNA 2 以前の "
                                "AMD ドライバーではオフ（オンにするとキャラクターが黒く描画されます）、それ以外では"
                                "オンです。",
    [UI_MENU_VK_SUBGROUP_PIN] = "サブグループサイズを固定",
    [UI_MENU_VK_SUBGROUP_PIN_DESC] = "シェーダーのサブグループサイズを固定します。",
    [UI_MENU_TRACE] = "パフォーマンスログ", [UI_MENU_TRACE_DESC] = "フレーム時間をファイルに書き出します。",
    [UI_MENU_FLIGHT] = "フライトレコーダー",
    [UI_MENU_FLIGHT_DESC] = "短い履歴を保持し、フレームが固まったときに書き出します。",
    [UI_MENU_FLIGHT_SPIKE_MS] = "フリーズのしきい値（ms）",
    [UI_MENU_FLIGHT_SPIKE_MS_DESC] = "フリーズとみなすフレーム時間です。",
    [UI_MENU_INPUT_RECORD] = "入力を記録",
    [UI_MENU_INPUT_RECORD_DESC] = "不具合報告のために、入力操作をファイルに書き出します。",
    [UI_MENU_OPEN_LOG] = "ログフォルダーを開く", [UI_MENU_OPEN_LOG_DESC] = "ログのあるフォルダーを表示します。",
    [UI_MENU_COPY_INFO] = "システム情報をコピー",
    [UI_MENU_COPY_INFO_DESC] = "GPU、ドライバー、CPU、RAM、変更した設定をクリップボードにコピーします。",
    [UI_MENU_COPY_INFO_DONE] = "コピーしました", [UI_MENU_ACTION_FAILED] = "失敗しました",
    [UI_MENU_RESET] = "すべての設定をリセット", [UI_MENU_RESET_DESC] = "すべてのタブに適用されます。",
    [UI_MENU_RESET_CONFIRM] = "すべての設定をデフォルトに戻しますか？",
    [UI_MENU_RESET_YES] = "リセット",
    [UI_MENU_RESET_NO] = "キャンセル",

    [UI_MENU_OV_FPS] = "%.0f FPS", [UI_MENU_OV_FRAME_MS] = "%.1f ms", [UI_MENU_OV_GAME_PCT] = "ゲーム %.0f%%",
    [UI_MENU_OV_MAX_MS] = "最大 %.1f ms",
    [UI_MENU_OV_GPU] = "GPU", [UI_MENU_OV_CPU] = "CPU", [UI_MENU_OV_RAM] = "RAM", [UI_MENU_OV_VRAM] = "VRAM",
    [UI_MENU_OV_TEMP] = "温度", [UI_MENU_OV_POWER] = "消費電力", [UI_MENU_OV_CLOCK] = "クロック",
    [UI_MENU_OV_NONE] = "-",
    [UI_MENU_OV_REPLAY] = "フレームの準備", [UI_MENU_OV_GPU_TIME] = "フレームあたりの GPU 使用時間",
    [UI_MENU_OV_PIPE_WAIT] = "パイプライン待ち",
    [UI_MENU_OV_SHADER_WAIT] = "シェーダー待ち", [UI_MENU_OV_TEX_UPLOADS] = "テクスチャのアップロード",
    [UI_MENU_OV_FMT_PCT] = "%.0f%%", [UI_MENU_OV_FMT_TEMP] = "%.0f °C", [UI_MENU_OV_FMT_POWER] = "%.0f W",
    [UI_MENU_OV_FMT_MHZ] = "%.0f MHz", [UI_MENU_OV_FMT_GB] = "%.1f GB", [UI_MENU_OV_FMT_GB_OF] = "/ %.1f GB",
    [UI_MENU_OV_GAME_GB] = "ゲーム %.1f GB", [UI_MENU_OV_FMT_MS] = "%.2f ms", [UI_MENU_OV_PER_FRAME] = "フレームあたり %.1f",
    [UI_MENU_OV_WINDOW] = "ウィンドウ", [UI_MENU_OV_OUTPUT] = "ゲームの映像", [UI_MENU_OV_SCENE] = "3D シーン",
    [UI_MENU_OV_SCALING] = "スケーリング", [UI_MENU_OV_LIMIT] = "FPS 上限", [UI_MENU_OV_PRESENT] = "表示モード",
    [UI_MENU_OV_TEX] = "テクスチャ圧縮", [UI_MENU_OV_OS] = "システム",
    [UI_MENU_OV_FMT_SIZE] = "%ux%u", [UI_MENU_OV_FMT_SCENE] = "%ux%u, %.0f%%",
    [UI_MENU_OV_FMT_FSR] = "AMD FSR 1、シャープネス %d%%", [UI_MENU_OV_SCALE_NONE] = "なし（1:1）",
    [UI_MENU_OV_SCALE_BILINEAR] = "バイリニア",
    [UI_MENU_OV_FMT_AREA] = "面積平均、シャープネス %d%%",
    [UI_MENU_OV_FMT_PRESHARP] = "HUD の前に RCAS、シャープネス %d%%",
    [UI_MENU_TAB_CHEATS] = "チート",
    [UI_MENU_CHEATS_NONE] = "このゲームバージョン用のチートがありません。Mod のチートは、その Mod の cheats "
                            "フォルダーに置く Atmosphere 形式のチートファイルで、ゲームのビルド名をファイル名に"
                            "します: mods\\<mod>\\cheats\\%s。読み込むにはゲームを再起動してください。ゲームの"
                            "コードを変更するチートの場合、起動時にゲームが再ビルドされます（数分）。",
    [UI_MENU_CHEATS_MOD] = "%s: チート %d 個",
    [UI_MENU_CHEAT_CODE_DESC] = "ゲームのコードを変更します。すぐに有効になります。",
    [UI_MENU_CHEAT_KEY_DESC] = "%s を押している間、ゲームのコードを変更します。すぐに有効になります。",
    [UI_MENU_CHEAT_DATA_DESC] = "オンの間、毎フレーム、ゲームのメモリに書き込みます。",
    [UI_MENU_CHEAT_MASTER] = "常にオン",
    [UI_MENU_CHEAT_MASTER_DESC] = "ファイルのマスターコードです。常にオンになっています。",
    [UI_MENU_CHEAT_RESTORE] = "不要",
    [UI_MENU_CHEAT_RESTORE_DESC] = "ゲーム本来のコードを書き戻すだけのものです。チートをオフにすれば同じことが"
                                   "行われます。",
    [UI_MENU_CHEAT_REBUILD] = "再ビルド後",
    [UI_MENU_CHEAT_REBUILD_DESC] = "このチートはゲームのコードを変更するもので、ゲームのビルド後に追加または編集"
                                   "されました。次回の起動時に組み込まれます（数分）。または「今すぐゲームを再ビルド」を"
                                   "使ってください。",
    [UI_MENU_CHEAT_UNSUPPORTED] = "非対応",
    [UI_MENU_CHEAT_UNSUPPORTED_DESC] = "このチートはこのゲームバージョンでは使えません:",
    [UI_MENU_CHEATS_REBUILD] = "今すぐゲームを再ビルド",
    [UI_MENU_CHEATS_REBUILD_DESC] = "ゲームのコードを変更するチートの一部が、まだ組み込まれていません。新しく追加"
                                    "または編集されたか、前回の再ビルドが失敗またはキャンセルされました。ゲームを"
                                    "閉じ、インストール処理がチートを組み込んで（数分）、ゲームをもう一度開きます。"
                                    "最後にセーブした後の進行状況は失われます。",
    [UI_MENU_MODS_EXEFS_UNSUPPORTED] = "この Mod はゲームのコード（exefs）に、この移植版では適用できない方法でパッチを"
                                       "当てるため、Mod 全体が無効になります。%s",
    [UI_MENU_MODS_EXEFS_OTHER] = "この Mod のコードパッチ（exefs）は別のゲームバージョン用です。",
    [UI_MENU_MODS_EXEFS_ON] = "使用中のコードパッチ: %d ファイル。",
    [UI_MENU_MODS_REPLACES_BUILTIN] = "使用中のコードパッチ: %d ファイル。移植版に内蔵のパッチ %s を置き換えます。"
                                      "内蔵パッチは、この Mod がオンの間は無効になります。",
};
