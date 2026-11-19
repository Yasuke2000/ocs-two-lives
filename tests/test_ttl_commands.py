"""tools/gen_ttl_commands.py: the parser of the /ttl command registration (fixtures), and a smoke test on the real source."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_ttl_commands as g  # noqa: E402

FIXTURE = """
ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event
  var op = src => src.hasPermission(2)
  var playerArg = () => Commands.argument('target', Arguments.PLAYER.create(event))
  var strArg = name => Commands.argument(name, Arguments.STRING.create(event))
  var expectTree = label => Commands.literal('expect')
    .then(playerArg().then(strArg('field').executes(ctx => 1)))
  // a comment with .then(Commands.literal('ghost'))
  var node = strArg('v')
  ;['a', 'b'].forEach(f => { node = node.then(Commands.literal(f).executes(ctx => 1)) })
  event.register(Commands.literal('ttl')
    .then(Commands.literal('hello').executes(ctx => 1))
    .then(Commands.literal('where').requires(src => src.hasPermission(0))
      .executes(ctx => 1)
      .then(strArg('id').executes(ctx => 1)))
    .then(Commands.literal('boss').requires(op)
      .then(Commands.literal('summon').then(strArg('id').executes(ctx => 1)))
      .then(expectTree('boss')))
    .then(Commands.literal('loop').then(node)))
  event.register(Commands.literal('locate')
    .then(Commands.literal('place').requires(op).then(strArg('id').executes(ctx => 1))))
})
"""


def parse(text, root="ttl"):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "commands.js"
        p.write_text(text, encoding="utf-8")
        return g.parse_file(p, root)


class ParserFixtures(unittest.TestCase):
    def test_tree_permissions_and_builders(self):
        root = parse(FIXTURE)
        tops = {c.name: c for c in root.children}
        self.assertEqual(sorted(tops), ["boss", "hello", "loop", "where"])
        self.assertTrue(tops["hello"].runs and not tops["hello"].op)
        self.assertFalse(tops["where"].op, "hasPermission(0) is everyone")
        self.assertTrue(tops["boss"].op)
        self.assertEqual([c.name for c in tops["boss"].children], ["summon", "expect"])
        self.assertEqual(g.usage(tops["boss"]), "boss (summon|expect)")
        expect = tops["boss"].children[1]
        self.assertEqual(g.usage(expect), "expect <target> <field>")

    def test_loops_and_comments(self):
        root = parse(FIXTURE)
        loop = {c.name: c for c in root.children}["loop"]
        self.assertEqual(g.usage(loop), "loop <v> (a|b)")
        self.assertNotIn("ghost", g.usage(root))

    def test_other_roots(self):
        locate = parse(FIXTURE, "locate")
        self.assertEqual([c.name for c in locate.children], ["place"])
        self.assertTrue(locate.children[0].op)
        self.assertEqual(g.usage(locate.children[0]), "place <id>")


class RealSource(unittest.TestCase):
    def test_every_registration_parses(self):
        root = g.build_tree()
        names = {c.name for c in root.children}
        self.assertGreaterEqual(len(names), 60)
        for known in ("wish", "absorb", "boss", "world", "guild", "necro", "artifice"):
            self.assertIn(known, names)
        for c in root.children:
            self.assertTrue(c.runs or c.children, f"/ttl {c.name} has neither an executor nor subcommands")
        self.assertEqual({c.name for c in g.build_tree("locate").children}, {"place"})

    def test_permissions_read_from_requires(self):
        tops = {c.name: c for c in g.build_tree().children}
        self.assertFalse(tops["wish"].op)
        self.assertTrue(tops["inspect"].op)


if __name__ == "__main__":
    unittest.main()
