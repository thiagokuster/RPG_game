import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"


class TestArena3D(unittest.TestCase):
    def test_three_js_vem_do_arquivo_local(self):
        html = (FRONTEND / "jogo.html").read_text(encoding="utf-8")
        self.assertIn("/js/vendor/three.module.min.js", html)
        self.assertIn("importmap", html)
        self.assertNotIn("cdnjs.cloudflare.com/ajax/libs/three.js", html)
        vendor = FRONTEND / "js" / "vendor" / "three.module.min.js"
        self.assertTrue(vendor.is_file())
        self.assertGreater(vendor.stat().st_size, 100_000)

    def test_arena_reaproveita_modelos_e_enfileira_eventos(self):
        fonte = (FRONTEND / "js" / "arena3d.js").read_text(encoding="utf-8")
        self.assertIn("disposeObject", fonte)
        self.assertIn("lastSeenId", fonte)
        self.assertIn("queue.push", fonte)
        self.assertIn("playNext", fonte)
        self.assertIn("window.addEventListener(\"resize\"", fonte)
        self.assertIn("if (visible)", fonte)
        self.assertIn("makeLabelTexture", fonte)
        self.assertIn("body.scale.set", fonte)
        self.assertIn("labelKey", fonte)
        self.assertIn("playDeath", fonte)
        self.assertIn("showWaveBanner", fonte)
        self.assertIn("shouldResetMatch", fonte)
        self.assertIn("animGen", fonte)
        self.assertIn("applyIdleEmissive", fonte)
        self.assertNotIn("group.scale.set", fonte)
        self.assertNotIn("figures.clear()", fonte)
        html = (FRONTEND / "jogo.html").read_text(encoding="utf-8")
        self.assertIn("ondaBanner", html)
        match = (FRONTEND / "js" / "arena3d_match.js").read_text(encoding="utf-8")
        self.assertIn("!player.npc", match)
        self.assertIn("if (!primed)", match)
        self.assertNotIn("room.status", match)

    def test_fingerprint_e_fila_no_node(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node indisponível")
        script = ROOT / "tests" / "test_arena3d_match.mjs"
        result = subprocess.run([node, str(script)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
