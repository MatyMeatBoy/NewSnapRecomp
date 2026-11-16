import io
import json
import struct
import tempfile
import unittest
from pathlib import Path

from newsnap import discord_presence as D


class FakePipe:
    """Answers READY to the handshake and echoes every command, as Discord's client does."""

    def __init__(self, ready=True):
        self.sent, self.answers, self.ready, self.closed = [], io.BytesIO(), ready, False

    def write(self, data):
        opcode, length = struct.unpack_from('<II', data)
        payload = json.loads(data[8:8 + length].decode('utf-8'))
        self.sent.append((opcode, payload))
        answer = ({'cmd': 'DISPATCH', 'evt': 'READY' if self.ready else 'ERROR'} if opcode == D.HANDSHAKE
                  else {'cmd': payload.get('cmd'), 'nonce': payload.get('nonce')})
        at = self.answers.tell()
        self.answers.seek(0, 2)
        self.answers.write(D.frame(D.FRAME, answer))
        self.answers.seek(at)

    def read(self, n):
        return self.answers.read(n)

    def close(self):
        self.closed = True


class Settings(unittest.TestCase):
    def test_application_id_from_the_settings_or_the_built_in_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(D.application_id(tmp), D.APPLICATION_ID)
            (Path(tmp) / 'launcher-settings.json').write_text(json.dumps({'discord_app_id': 'not a number'}))
            self.assertEqual(D.application_id(tmp), '')            # an id that is not one switches it off
            (Path(tmp) / 'launcher-settings.json').write_text(json.dumps({'discord_app_id': '123456789012345678'}))
            self.assertEqual(D.application_id(tmp), '123456789012345678')

    def test_choice_is_kept_beside_the_other_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'launcher-settings.json'
            path.write_text(json.dumps({'game_data_relative': 'GameData'}))
            self.assertTrue(D.enabled(tmp))
            D.set_enabled(tmp, False)
            self.assertFalse(D.enabled(tmp))
            self.assertEqual(json.loads(path.read_text())['game_data_relative'], 'GameData')
            D.set_enabled(tmp, True)
            self.assertTrue(D.enabled(tmp))
            path.write_text('{broken')
            self.assertTrue(D.enabled(tmp))   # an unreadable file reads as the default


class Protocol(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        (Path(self.tmp.name) / 'launcher-settings.json').write_text(json.dumps({'discord_app_id': '123456789012345678'}))

    def test_handshake_then_activity_then_clear(self):
        pipe = FakePipe()
        presence = D.Presence(self.tmp.name, opener=lambda: pipe, pid=4321)
        self.assertTrue(presence._start('123456789012345678', 1700000000.9))
        self.assertEqual(pipe.sent[0], (D.HANDSHAKE, {'v': 1, 'client_id': '123456789012345678'}))
        opcode, command = pipe.sent[1]
        self.assertEqual((opcode, command['cmd'], command['args']['pid']), (D.FRAME, 'SET_ACTIVITY', 4321))
        shown = command['args']['activity']
        self.assertEqual((shown['details'], shown['state'], shown['timestamps']), (D.DETAILS, D.STATE, {'start': 1700000000}))
        self.assertEqual(set(shown), {'details', 'state', 'timestamps', 'assets'})   # nothing about the player
        presence._stop()
        self.assertIsNone(pipe.sent[2][1]['args']['activity'])
        self.assertTrue(pipe.closed)
        presence._stop()                       # a second stop does nothing
        self.assertEqual(len(pipe.sent), 3)

    def test_discord_not_running_or_refusing_is_silent(self):
        self.assertFalse(D.Presence(self.tmp.name, opener=lambda: None)._start('123456789012345678', 1.0))
        pipe = FakePipe(ready=False)
        presence = D.Presence(self.tmp.name, opener=lambda: pipe)
        self.assertFalse(presence._start('123456789012345678', 1.0))
        self.assertTrue(pipe.closed)
        self.assertEqual(len(pipe.sent), 1)    # no activity after a refused handshake

    def test_start_does_nothing_when_switched_off_or_without_id(self):
        D.set_enabled(self.tmp.name, False)
        opened = []
        self.assertFalse(D.Presence(self.tmp.name, opener=lambda: opened.append(1)).start())
        saved, D.APPLICATION_ID = D.APPLICATION_ID, ''
        try:
            with tempfile.TemporaryDirectory() as empty:
                self.assertFalse(D.Presence(empty, opener=lambda: opened.append(1)).start())
        finally:
            D.APPLICATION_ID = saved
        self.assertEqual(opened, [])

    def test_the_application_id_is_set(self):
        self.assertTrue(D.APPLICATION_ID.isdigit())

if __name__ == '__main__':
    unittest.main()
