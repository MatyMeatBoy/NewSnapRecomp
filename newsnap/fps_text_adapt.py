"""FPS-TXT-01: the in-game frame limit text no longer describes Astral Chain's 60 fps patch.

The donor menu said "60 FPS runs the game's 60 fps patch; 30 FPS switches it off".
Snap has no inherited timing patch: it presents at 60 by itself and the setting is a
presentation cap (measured on the owner's RX 6900 XT: AC_FPS=30 gives 1801 presents
a minute, 60 gives 3600). The log line was already adapted in adapt.py.
"""

TEXTS = [
    ('"60 FPS runs the game\'s 60 fps patch; 30 FPS switches it off. Read live."',
     '"Frame limit. 60 FPS is Snap\'s own rate; 30 FPS caps presentation at 30 per second. Read live."'),
    ('"60 FPS включает патч игры на 60 кадров; 30 FPS отключает его. Читается на лету."',
     '"Ограничение кадров. 60 FPS — собственная частота Snap; 30 FPS ограничивает вывод 30 кадрами в секунду. Читается на лету."'),
    ('"60 FPS usa o patch de 60 fps do jogo; 30 FPS o desliga. Lido na hora."',
     '"Limite de quadros. 60 FPS é a taxa própria do Snap; 30 FPS limita a exibição a 30 por segundo. Lido na hora."'),
    ('"60 FPS 启用游戏的 60 帧补丁；30 FPS 关闭它。即时生效。"',
     '"帧率上限。60 FPS 是 Snap 自身的帧率；30 FPS 将画面输出限制为每秒 30 帧。即时生效。"'),
]


def edits():
    return {'runtime/ui_text.c': list(TEXTS)}
