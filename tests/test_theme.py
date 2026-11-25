import copy
import unittest
from pathlib import Path
import theme
import style


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path('test-state')
        self.cfg = style.cfg_extra(dict(theme='purple', opacity=50, acrylic=True,
                                        custom_colors={}, set_default_terminal=True))
        self.original = {'profiles': {'defaults': {'opacity': 90, 'font': {'size': 14}},
            'list': [{'guid': style.CMD_GUID, 'name': 'Command Prompt', 'tabColor': '#123456'},
                     {'guid': '{sample}', 'name': 'PowerShell', 'opacity': 80}]},
            'schemes': [], 'theme': 'dark', 'defaultProfile': style.CMD_GUID}

    def test_palettes_and_glass(self):
        for name in theme.PALETTES:
            with self.subTest(name=name):
                cfg = dict(self.cfg, theme=name)
                result = theme.apply_doc(copy.deepcopy(self.original), cfg, self.root)
                defaults, items = theme.profiles(result)
                for profile in [defaults, *items]:
                    self.assertEqual(profile['opacity'], 50)
                    self.assertTrue(profile['useAcrylic'])
                    self.assertEqual(profile['background'], theme.PALETTES[name][0])
                self.assertEqual(result['themes'][0]['tabRow']['background'], '#00000000')
                self.assertEqual(defaults['font']['size'], 14)

    def test_restore_existing_profiles(self):
        result = theme.apply_doc(copy.deepcopy(self.original), self.cfg, self.root)
        result['alwaysOnTop'] = True
        restored = theme.restore_doc(result, self.original, self.root)
        self.assertEqual(restored['profiles'], self.original['profiles'])
        self.assertEqual(restored['theme'], 'dark')
        self.assertTrue(restored['alwaysOnTop'])
        self.assertEqual(restored['schemes'], [])

    def test_custom_launch_preserved(self):
        original = copy.deepcopy(self.original)
        original['profiles']['list'][0]['commandline'] = 'cmd.exe /k custom.cmd'
        result = theme.apply_doc(original, self.cfg, self.root)
        self.assertEqual(result['profiles']['list'][0]['commandline'], 'cmd.exe /k custom.cmd')

    def test_jsonc(self):
        self.assertEqual(theme.read_jsonc(b'{// comment\n "url":"https://example.com", /* block */ "x":[1,],}'),
                         {'url':'https://example.com', 'x':[1]})

    def test_prompt_tokens_and_profile_marker(self):
        cmd = style.prompt_cmd(self.cfg)
        for token in ('$P', '$T', '$E', '$_'):
            self.assertIn(token, cmd)
        self.assertIn('function global:prompt', style.ps_source(self.cfg, self.root))
        self.assertEqual(style.ps_block_removed('existing\n'+style.MARK+'\nmanaged\n'+style.END+'\n'), 'existing\n')

    def test_custom_colors(self):
        cfg = dict(self.cfg, custom_colors={'background': '#112233'})
        self.assertEqual(theme.scheme(cfg)['background'], '#112233')


if __name__ == '__main__':
    unittest.main()
