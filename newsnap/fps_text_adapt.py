"""FPS-TXT-01: the in-game frame limit text no longer describes Astral Chain's 60 fps patch.

The donor menu said "60 FPS runs the game's 60 fps patch; 30 FPS switches it off".
Snap has no inherited timing patch: it presents at 60 by itself and the setting is a
presentation cap (measured on the owner's RX 6900 XT: AC_FPS=30 gives 1801 presents
a minute, 60 gives 3600). The log line was already adapted in adapt.py.
"""

TEXTS = [
    ('"60 FPS runs the game\'s 60 fps patch; 30 FPS switches it off. Read live."',
     '"Frame limit: 30, 60 (default), 90, 120 or 144 FPS. Slower native scenes keep their cadence. Read live; achieved FPS depends on the GPU and display mode."'),
    ('"60 FPS включает патч игры на 60 кадров; 30 FPS отключает его. Читается на лету."',
     '"Лимит: 30, 60 (по умолчанию), 90, 120 или 144 FPS. Медленные сцены сохраняют свой темп. Изменяется сразу; результат зависит от GPU и режима вывода."'),
    ('"60 FPS usa o patch de 60 fps do jogo; 30 FPS o desliga. Lido na hora."',
     '"Limite: 30, 60 (padrão), 90, 120 ou 144 FPS. Cenas mais lentas mantêm sua cadência. Muda ao vivo; o resultado depende da GPU e do modo de apresentação."'),
    ('"60 FPS 启用游戏的 60 帧补丁；30 FPS 关闭它。即时生效。"',
     '"帧率上限：30、60（默认）、90、120 或 144 FPS。较慢场景保留原有节奏。即时生效；实际帧率取决于 GPU 和显示模式。"'),
]


def edits():
    return {'runtime/ui_text.c': list(TEXTS)}
