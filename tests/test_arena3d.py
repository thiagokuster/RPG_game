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
        self.assertIn("if (!primed)", fonte)
        self.assertIn("body.scale.set", fonte)
        self.assertIn("labelKey", fonte)
        self.assertIn("playDeath", fonte)
        self.assertIn("showWaveBanner", fonte)
        self.assertNotIn("group.scale.set", fonte)
        self.assertNotIn("figures.clear()", fonte)
        html = (FRONTEND / "jogo.html").read_text(encoding="utf-8")
        self.assertIn("ondaBanner", html)


if __name__ == "__main__":
    unittest.main()
