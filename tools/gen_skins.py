"""Draw the pack’s original Tensura NPC skins on the Minecraft 64×64 player atlas.

Run with Pillow installed: python tools/gen_skins.py
Edit a character’s palette and face maps below. Each letter paints one texel;
a dot keeps the underlying material (transparent on the optional outer layer).
Base materials use s (skin), h (hair), c (coat), t (trousers) and b (boots).
Additional letters belong to the individual palette. Right and left are the wearer's. See design/lore/skins.md for the art references.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageColor

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "pack/kubejs/assets/ttl/textures/entity/npc"

# Original pixel designs after the official character sheets at ten-sura.com/character/.
# Reading the body from the front, a character's right shoulder is on the viewer's left.
GUILD = {
    "fuze": dict(
        slim=False,
        colors=dict(s="#d99f76", h="#302a28", e="#484147", c="#843e49", t="#344465",
                    b="#382f35", a="#deb264", w="#e7dfd3", g="#b7aa9f", d="#59313b",
                    k="#393339", u="#a47766", l="#ad545c", n="#716051"),
        faces={
            "head.front": """hhhnhhhh hnhhhhhg hhshssgg hssussgs swesweus ssssussu suusssus sushhsus""",
            "head.right": """hhnhnhhh hhhhhhhh hhhhhhhh hhgghhhs hhgggsus hhggssus hhgsssss hhususss""",
            "head.left": """hhhnhhhh hhnhhhhg hhhhhhgg hhhhgghg sssggggg susgghhg susshhhh ssushhhh""",
            "hat.front": """..h.hh.. .hhnnhh. hh..h..g h......g ........ ........ ........ ........""",
            "body.front": """clwwwwlc clgwwglc cdcwwcdc clcwgwlc cllwwllc cldwgdlc ccdwwdcc cdkkkkdc ckkggkkc ckkgkkkc cldwwdlc clwwwwlc""",
            "body.back": """cllllllc cddddddc clcccllc cllccclc clcclclc clcclclc clcclclc cddccddc cccddccc clcddclc clcddclc aaaddaac""",
            "jacket.front": """l......l .l....l. .d....d. ..l..l.. ........ ........ ........ ........ ...gg... ...kg... ........ a......a""",
            "right_arm.front": """llcc ccll cclc acac aaca wwww wggw gwwg ddll cclc ckck bbbb""",
            "left_arm.front": """ccll llcc clcc caca acaa wwww gwgw gwwg llcd lccc bkbk bbbb""",
            "right_leg.front": """ccdt cldt cldt altt tatt tttt ttkt tkkt bbbb lclc cclc kkbb""",
            "left_leg.front": """tdcc tdlc tdlc ttla ttat tttt tktt tkkt bbbb clcl clcc bbkk""",
        }),
    "kaijin": dict(
        slim=False,
        scale=0.8,
        colors=dict(s="#d9a17b", h="#79563f", e="#463521", c="#574054", t="#302933",
                    b="#704634", a="#b4ac71", w="#ede0c7", d="#382936", r="#934e47",
                    m="#677978", i="#afc8bc", f="#b08a61", k="#453628", p="#695046"),
        faces={
            "head.front": """rrrrrrkr rmiirmir rmimrmim fhhsfhhs fwesswef shfsshfs hfhhhffh ffhhhffh""",
            "head.back": """rrkrrrkr rrrrkrrr rkkrrrkr mmmmmmmm hhfhfhfh fhfhfhff fhhhffhh hffffhhh""",
            "head.top": """rrkkrrrr rrkkkkrr rrkrrkrr rkkrrrkr rkrrkrrr rrrkrrkr rrrrkrrr krrrrkrr""",
            "hat.front": """..rrrr.. .mi..mi. .mm..mm. ........ ........ ........ .ff..ff. .ffhhff.""",
            "hat.back": """..rrk... ..rrrk.. ....rr.. ........ ........ ........ ........ ........""",
            "body.front": """wwwhhwww fwwhfwwf cwwffwwc cwpkkpwc ccppppcc ccpkppcc ccppppcc aaaaaaaa aaffaafa cppapppc cppapppc cpkpkkpc""",
            "body.back": """wwfwwfww fwwwwwwf cfwffwfc cfccccfc cpfccfpc ccfppfcc ccppppcc aaaaaaaa afffaaaf cccapccc cccapccc cccapccc""",
            "jacket.front": """ww....ww .ww..ww. ..w..w.. ........ ........ ........ ........ ........ ...aa... ...af... ..a..a.. ..a..a..""",
            "right_arm.front": """wwfw wwww fwfw ccwc ccdc dccd cddc dddd ssss fsss bbbk bbkb""",
            "left_arm.front": """wfww wwww wfwf cwcc cdcc dccd cddc dddd ssss sssf kbbb bkbb""",
            "right_leg.front": """cppp pppp kpkp dddd tttt tttt wfwf wwww fbwb bbbb bpbb kkkk""",
            "left_leg.front": """pppc pppp pkpk dddd tttt tttt fwfw wwww bwbf bbbb bbpb kkkk""",
        }),
    "kabal": dict(
        slim=False,
        colors=dict(s="#e0ac82", h="#a78341", e="#544435", c="#37383b", t="#847f7e",
                    b="#555156", a="#ceab69", w="#e3dcc6", d="#53412e", g="#999ba4",
                    k="#393237", p="#a77c4d", f="#cdaa6a", u="#bd855c"),
        faces={
            "head.front": """hffhhffh hffhffhh hfssshfh hsssssff hweswefh hsssussf hfsssufh hfsssshf""",
            "head.back": """hhfhffhh hfhffhhf hfhhfhhf fhfhhfhf fhfhfhhf hhfhffhf hhfhffhf fhffhhfh""",
            "hat.front": """..fhh... .fh..hf. .h....f. h......h f......h h......f h......f f......h""",
            "body.front": """ccassacc ccaaaaac ccadadac caaaadac cdaaaaac cdpaapdc ccddapcc ccwpddcc cccwpddc kppppppk wfwwwwwf ppwppwpp""",
            "body.back": """cchfffcc cchhhfcc ccffhfcc ccffhfcc cchfhhcc cddhffcc ccpddccc cccpddcc ccccpddc kppppppk wfwwwwwf pppwwppp""",
            "jacket.front": """.......c g......c gg...... ........ .d...... ..d..... ...a.... ....dd.. ........ ........ w..w...w ........""",
            "right_arm.front": """ggwg ggww kgwg gggg kggg aaaa cccc bbbb ggkg gggg kggk bbbb""",
            "left_arm.front": """cccc cccc cckc cccc cccc aaaa cccc bbbb gkgk gggg gkkg bbbb""",
            "right_leg.front": """pppp papp pppp pddp wwtt twwt tkkt tttt wwww wbww bbbb bbkk""",
            "left_leg.front": """pppp ppap pppp pddp ttww twwt tkkt tttt wwww wwbw bbbb kkbb""",
        }),
    "elen": dict(
        slim=True,
        colors=dict(s="#f4c1ac", h="#e8b954", e="#389080", c="#c64c59", t="#48424b",
                    b="#49414a", a="#283e70", w="#faf0df", d="#99394c", f="#ffe192",
                    p="#df819c", k="#62483a", g="#ba9357", u="#dda48d"),
        faces={
            "head.front": """fhhhhffh hfhffhfh hhfhshhf hfssssfs fweswefh fsssssfs hfssusfh hffssfhf""",
            "head.back": """hffhhhfh fhhffhhf hhfhffhh fhhhfhff hffhhfhf ffhhffhh hffhffhh fhhhfhhf""",
            "hat.front": """.a...... aa...... .aa..... aaf..... .a.....f .......h f......f .f....h.""",
            "body.front": """hccssccf cddwwddc ccsssscc cccccccc cdccccdc dcddddcd wccccccw wwwccwww wwwwwwww kkggkkkk pwwppwwp pppppppp""",
            "body.back": """hfhffhfh chhfhhfc chfhffhc cffhhfhc cchffhcc cchhhfcc wdccccdw wwwwwwww wwwwwwww kkkgkkkk ppwwwwpp pppdpppp""",
            "jacket.front": """f......f hf....fh ........ ........ c......c .d....d. ..d..d.. ........ ........ ...gg... ........ .p....p.""",
            "right_arm.front": """cdd ccc ccc wcc www ccc dcc cdc www kkk sss ssu""",
            "left_arm.front": """ddc ccc ccc ccw www ccc ccd cdc www kkk sss uss""",
            "right_leg.front": """pppp pdpp pdpp pddp ssss tttt tttt tttt tttt bbkb bbbb kkbb""",
            "left_leg.front": """pppp ppdp ppdp pddp ssss tttt tttt tttt tttt tttt bbbb bbkk""",
        }),
    "gido": dict(
        slim=False,
        colors=dict(s="#d69c71", h="#896c4f", e="#4b4234", c="#69503c", t="#77786a",
                    b="#503c2f", a="#964c43", w="#dacfb5", g="#8caa71", d="#493a32",
                    f="#af9771", k="#39363c", u="#af7458"),
        faces={
            "head.front": """hffhhffh fhhffhfh aaaaaaaa aaaaaaaa swesswes sussussu sssuuuss usshhssu""",
            "head.back": """hffhhfhf fhhfhhfh aaaaaaaa aaadaaaa hhffhfhf fhfhfhhf hhfhffhh hffhfhfh""",
            "hat.front": """..h.f... .fhfhh.. a......a ........ ........ ........ ........ ........""",
            "hat.back": """........ ........ aaa..aaa ....a... ...aa... ....a... ....aa.. ........""",
            "body.front": """cggssggc ccggggcc cdcggcdc ccddgdcc cccddccc cddcdccc cccddccc cdddcdcc cccccccc wwwwwwww bbggbbbb tcwttttt""",
            "body.back": """cggggggc ccggggcc cccggccc cdccccdc cdccccdc cdccccdc cdccccdc cdccccdc cccccccc wwwwwwww bbbgbbbb tttwtttt""",
            "jacket.front": """c......c .d....d. ..d..d.. ...d.... ........ ........ ........ ........ ........ ........ ..gg.... ..w.....""",
            "right_arm.front": """cggg gcgg gggg ggfg gggg gffg gggg ssss ssss kkkk kkdk kkkk""",
            "left_arm.front": """gggc ggcg gggg gfgg gggg gffg gggg ssss ssss kkkk kdkk kkkk""",
            "right_leg.front": """ttww ttwf ttwf ttww tttt tttt dttd wwww fwww wwfw bbbb ddbb""",
            "left_leg.front": """tttt tftt tttt tttt tttt tttt dttd wwww wwwf wfww bbbb bbdd""",
        }),
    "receptionist": dict(
        slim=True,
        colors=dict(s="#d9aa87", h="#543c36", e="#536658", c="#35506b", t="#344458",
                    b="#453d3c", a="#cba669", w="#eee4d2", d="#263752", g="#827065",
                    u="#be8969", f="#77534a", l="#496783"),
        faces={
            "head.front": """hhffhhfh fhhhffhh hhfhfhss hfhsssss hweswesh sssssssh ssssussf hssssssh""",
            "head.back": """hhhffhhh hhffhhhh hfhhfhhh hhhhhfhh fhhhffhh hffhhffh hhfffhhh hhgggghh""",
            "hat.front": """cccccccc ccllllcc dddadaad .d...... ........ ........ ........ ........""",
            "hat.back": """cccccccc ccllllcc dddddddd ........ ........ ........ ...hh... ..hffh..""",
            "hat.top": """ddccccdd dccllccd ccllllcc cllllllc cllllllc ccllllcc dccllccd ddccccdd""",
            "body.front": """ccwsswcc clwwwwlc cclaalcc ccwaawcc ccwawccc clwwwalc clwwwllc clwwwwlc cclwwlcc dddagddd cclddlcc cclddlcc""",
            "body.back": """ccffhhcc cclhhflc ccchhfcc cllffllc clcggclc clcccclc clcccclc clcccclc cccllccc dddagddd cclddlcc cclddlcc""",
            "jacket.front": """l......l .l....l. ........ ......a. ..w...a. ........ ........ ........ ........ ...a.... ........ ........""",
            "right_arm.front": """clc ccc cac ccc clc clc clc ccc ddd www sss ssu""",
            "left_arm.front": """clc ccc cac ccc clc clc clc ccc ddd www sss uss""",
            "right_leg.front": """cclc cllc tttt tttt tttt tttt dtdt tttt bbbb bbbb bbgb ddbb""",
            "left_leg.front": """clcc cllc tttt tttt tttt tttt tdtd tttt bbbb bbbb bgbb bbdd""",
        }),
}
# The portal's character turnarounds informed these original UV pixel drawings.
# Each head design, including the horns, fits the eight-pixel face of a player skin.
KIJIN = {
    "benimaru": dict(
        slim=False,
        colors=dict(s="#e9b593", h="#af2939", e="#9b1c31", c="#bd3740", t="#49283c",
                    b="#eee7d8", a="#e5b44f", k="#30262c", r="#f06055", d="#71283c",
                    w="#faf3de", g="#9b672f", f="#765362"),
        faces={
            "hat.top": "........ ........ ........ ........ ........ ........ .k....k. .kk..kk.",
            "head.front": """
                hrhhrhrh hhhhrhhh hrhshhsh hhssshhs
                skeessks swesswes hssssssh ssssssss
            """,
            "hat.front": """
                .k....k. .k....k. ..k..k.. ....r...
                h......h ........ ........ ........
            """,
            "hat.back": """
                ..rr.hh. .r....h. .......h h....r..
                h....hh. ...h..h. .hh...h. ..h.....
            """,
            "body.front": """
                wwksskwk cwksstwc cktttkdc cktaatdc
                kgaaaagk kgaagagk cktggtdc cktttdcc
                cktttdcc aaggggaa aaagaaga ckttttdc
            """,
            "body.back": """
                wwwwwwww awccccwa caccccac cccrrccc
                ccrccrcc cccrrccc cccccccc cccddccc
                ccddcdcc aaagaaaa ggagggag cccttccc
            """,
            "jacket.front": """
                w......w .w....w. ..k..k.. ........
                ...a.... ..a.a... ...g.... ........
                ........ a......a ..ggg... ........
            """,
            "right_arm.front": """
                gaaa awaa gaag cggc cccc ccdc dccc cdcc
                cccc kkkk ssss ssss
            """,
            "left_arm.front": """
                cwwc ccwc cccc cccd ccdc dccc cccc ccdc
                cccc kkkk ssss ssss
            """,
            "right_leg.front": """
                acct acct acct acct acct bwct bwct bwct
                btft wwbw kbkk kkkk
            """,
            "left_leg.front": """
                tcca tcca tcca tcca tcca tcwb tcwb tcwb
                tftb wbww kkbk kkkk
            """,
        },
    ),
    "shuna": dict(
        slim=True,
        colors=dict(s="#f1c4aa", h="#e9a0b9", e="#a3345b", c="#faf3e7", t="#dd4a44",
                    b="#eee7e4", a="#992c48", k="#4c3545", r="#fbd1dd", d="#b86b8a",
                    w="#fffdee", f="#b83239", g="#c9b5c7"),
        faces={
            "hat.top": "........ ........ ........ ........ ........ ........ .w....w. .ww..ww.",
            "head.front": """
                hrhrrhrh hrrhhrhh hhrhhshr rhhsshhh
                hkksskdh hwessweh hssssssh hdssssdh
            """,
            "hat.front": """
                .w....w. .g....g. ..w..w.. r......r
                h......h h......h h......h d......d
            """,
            "body.front": """
                hdssssdh hhcwwchh hhrcachh hccccach
                hccaccca ccaaccac cwaaawwc cccaffcc
                aaafaaaa fffaffff ttfftttt tfttttft
            """,
            "body.back": """
                dhrhhhrd hrrhrdhd hrhdhrhh hrdhhrrh
                hrhdhhhd hrdhhrhd hdrhhhdd ddhhrhdc
                adhhrdda afhhddaa tfhdhtft ttdhthtt
            """,
            "hat.back": """
                .r....r. .rhr..r. ..h...r. ..h..r..
                .r...h.. .h...h.. .d..h..r d..dh..h
            """,
            "jacket.front": """
                ........ ........ ..a..... ...a....
                ....a... .....a.. ........ ........
                ..a..a.. ...aa... ..a..a.. .a....a.
            """,
            "right_arm.front": """
                cgc ccg ccc ccc acc cac cca ccc cgc aaa cgc sss
            """,
            "left_arm.front": """
                cgc gcc ccc ccc cca cac acc ccc cgc aaa cgc sss
            """,
            "right_leg.front": """
                fttt tftt tftt tftt tftt tftt tftt tftt
                tftt bbbb bfab kfkk
            """,
            "left_leg.front": """
                tttf ttft ttft ttft ttft ttft ttft ttft
                ttft bbbb bafb kkfk
            """,
        },
    ),
    "shion": dict(
        slim=True,
        colors=dict(s="#edc2ac", h="#ab85cc", e="#654495", c="#4e365f", t="#604579",
                    b="#302c36", a="#c8ab64", k="#342840", r="#d6b2e9", d="#785b98",
                    w="#faf1e8", f="#332b42", v="#785787"),
        faces={
            "head.front": """
                hrrhhrrh hrhhhhrh rhhsdhhh hhssshrh
                hkesskkh hwessweh hssssssh dhsssssh
            """,
            "hat.front": """
                .....k.. ....kk.. ....k... rr......
                h......h h......h d......h .......d
            """,
            "body.front": """
                vhssssrv cvssssvc cvssssvc ccvssvcc
                ccvsvccc cccvcccc cccvcccc cccacacc
                cccvcccc cccacacc ccfccfcc cfcffcfc
            """,
            "body.back": """
                ccchhrhc ccchrrhc ccchrhdc ccchrhdc
                cchhrhdc cchrhddc cchhddcc cchhdccc
                cchdcccc ccdfcccc cccffccc ccfccfcc
            """,
            "hat.back": """
                ...dd... ..hhhd.. ..hrhd.. ..drhd..
                ...hh... ..hhdd.. ..hrhd.. ..hrhd..
            """,
            "jacket.front": """
                .v....v. ..v..v.. ..v..v.. ...vv...
                ...v.... ........ ........ ...a.a..
                ........ ...a.a.. ........ ........
            """,
            "right_arm.front": """
                vcc cvc ccc ccc ccf ccf ccc ccc ccc cfc sss sss
            """,
            "left_arm.front": """
                ccv cvc ccc ccc fcc fcc ccc ccc ccc cfc sss sss
            """,
            "right_leg.front": """
                cttt vttf vttf vttf tttf tttf tttf tttf
                ttff tffb bbbb bfbb
            """,
            "left_leg.front": """
                tttc fttv fttv fttv fttt fttt fttt fttt
                fftt bfft bbbb bbfb
            """,
        },
    ),
    "souei": dict(
        slim=False,
        colors=dict(s="#cdaa92", h="#344867", e="#a27c40", c="#37446b", t="#d2d5d9",
                    b="#393943", a="#d9dce1", k="#282b37", r="#586d90", d="#242e49",
                    w="#fff4dc", f="#8794a7", m="#56606d"),
        faces={
            "head.front": """
                hrhhrrhh hhrhhrrh hhrhhhrs hhhrhhss
                hhhdsekh hhdssweh hdsssssh dssssssh
            """,
            "hat.front": """
                ......w. .....ww. .....a.. hh......
                .h...... .h...... h....... ........
            """,
            "body.front": """
                aaaafaaa faaaafaa cffaaaaf cccfffcc
                cccccccd ccdccccc dcccccdd cccdcccd
                aaaaafff ffaaaaaa aaaaafff ccdccdcc
            """,
            "body.back": """
                daaaafdd afaaaafa aaaafffa ccaafacd
                ccdafadc ccdafdcc cccadccc ccdcdccd
                aaaaffff fffaaaaa aaaffffa ccdccdcc
            """,
            "hat.back": """
                ..r....h .r..r..h .h..h... .......d
                h....d.. .h...d.. .d..d..h d...h..d
            """,
            "jacket.front": """
                aa...... .aa..... ..faa... ....ff..
                ........ ........ ........ ........
                a....... .....aaa ........ ........
            """,
            "right_arm.front": """
                ccrd cccc dccc cccd cccc dddd
                mkmk kmkm mkmk kmkm mkmk ssss
            """,
            "left_arm.front": """
                drcc cccc cccd dccc cccc dddd
                kmkm mkmk kmkm mkmk kmkm ssss
            """,
            "right_leg.front": """
                ccdc ccdc ccdc cdtf cttt cftt ttft fftf
                bbbb bmbb bbkb kkkk
            """,
            "left_leg.front": """
                cdcc cdcc cdcc ftdc tttc ttfc tftt ftff
                bbbb bbmb bkbb kkkk
            """,
        },
    ),
    "hakurou": dict(
        slim=False,
        colors=dict(s="#d5b59c", h="#ebeae5", e="#797164", c="#eae9dd", t="#deded3",
                    b="#9c9353", a="#9d9947", k="#4a4b43", r="#fffdf3", d="#aaaab0",
                    w="#fffaf0", f="#b9bbae", g="#726d39"),
        faces={
            "head.front": """
                hdhrhhrh rhhrhhrr hhshhshh hdddssdh
                hesssseh dssssdsh sdshhsds sshhhsss
            """,
            "hat.front": """
                ..r..r.. ..d..d.. .h....r. .d....d.
                .dd..dd. ........ ..h..h.. ...h....
            """,
            "body.front": """
                agssssga aagssgaa caagaaac ccaagacc
                cccgaccc ccgacccc cgacccfc cgccccfc
                cccccfcc cffccfcc fffffffc ccccfccc
            """,
            "body.back": """
                aahhhhaa agghhdga caghrdgc ccaahhcc
                cccahdcc cccahdcc cccahdcc cccahdcc
                ccccdhcc ccccdhcc ffffdcff cccccccc
            """,
            "hat.back": """
                ..rh.... .hhrh... .hrhh... ..hhd...
                ...gg... ...hh... ...rh... ...hd...
            """,
            "jacket.front": """
                .a....a. .g....g. ..a..a.. ...aa...
                ...g.... ..g..... ........ ........
                ........ ........ ........ ........
            """,
            "right_arm.front": """
                accc cccc cccf cccf ccfc ccfc cfcc fccc
                cccf cfff fffc ssss
            """,
            "left_arm.front": """
                ccca cccc fccc fccc cfcc cfcc ccfc cccf
                fccc fffc cfff ssss
            """,
            "right_leg.front": """
                ccfc ccfc ccfc cffc ttft tftt fftf kkgg
                gbbg bgbb bgbb gggg
            """,
            "left_leg.front": """
                cfcc cfcc cfcc cffc tftt ttft ftff ggkk
                gbbg bbgb bbgb gggg
            """,
        },
    ),
}
# Original pixel maps drawn from the official anime character profiles.
TEMPEST = {
    "treyni": dict(
        slim=True,
        colors=dict(s="#ffe1cb", h="#9acc92", e="#528c57", c="#bbefdd",
                    t="#8ed8cd", b="#8cd2c5", a="#669d70", w="#f0fff5", d="#71b1a6"),
        faces={
            "head.front": """hhhhhhhh hhhhhwhh hhwhhhsh hhshhssh hwessewh hssssssh hssssssh hhsssshh""",
            "hat.front": """..ahh... .ah..wh. .h.....h h....... ........ ........ ........ ........""",
            "hat.back": """hhwhhhwh hhwhhhwh hhhwhhhh hhhwhhwh hhwhhhwh hwhhhwhh hwhhhhhh hhwhhwhh""",
            "body.front": """wwssssww cwsssswc cwwsswwc cccwwccc dccccccd ddccccdd cddccddc ccddddcc aaacccaa ccaacacc ccwcaaac cdwccwcd""",
            "body.back": """hhwhhwhh hhwhhwhh hhwhhhwh hhwhhwhh hhhwhhwh hhwhhwhh chhhhdhc cchhchcc aacccaaa ccaaaccc cdwccwdc cdwccwdd""",
            "jacket.front": """........ ........ ........ ........ ........ ........ ........ ......a. ....aa.. ..aa.... .a.a.... a.......""",
            "right_arm.front": """www cww ccs wcs wss wss dws sss ass sas sss sss""",
            "left_arm.front": """www wwc scc scw ssw ssw swd sss ssa sas sss sss""",
            "right_leg.front": """dcwc dcwc dcwc cdwc cdwc cdwc ccwd ccwd ccwd ccwd cdww dwwc""",
            "left_leg.front": """cwcd cwcd cwcd cwdc cwdc cwdc dwcc dwcc dwcc dwcc wwdc cwwd""",
        }),
    "milim": dict(
        slim=True,
        colors=dict(s="#ffdec7", h="#ef93ad", e="#46a9d4", c="#29243a",
                    t="#373046", b="#8e354a", a="#c59a53", w="#f1eef5",
                    p="#bc617f", v="#76618d", r="#c34b56"),
        faces={
            "jacket.back": "hp....ph ph....hp hp....ph ph....hp hp....ph hp....ph .h....h. .p....p. ........ ........ ........ ........",
            "hat.right": ".....phh ....phhp ....aaah ....hphh ....phhp .....php .....hph ......hp",
            "hat.left": "hhp..... phhp.... haaa.... hhph.... phhp.... php..... hph..... ph......",
            "head.front": """phhhphhh hhhhhhph hshhhshh hsshsssh swessews ssssssss sssppsss shsssshs""",
            "hat.front": """phh..hhp hh....hh h.....ph h......h ........ ........ ........ ........""",
            "hat.back": """phhhhhhp aahhhhaa phhhhhhp hphhhhph ph....hp ph....hp hp....ph ph....hp""",
            "body.front": """ccassacc ccccaccc vccaccvv wwccccww cwwccwwc sscwwcss sssccsss ssssssss ssssssss vccssccv cvvaavvc tttvvttt""",
            "body.back": """pccccccp hpccccph hpvccvph hpswwsph phswsshp phsssshp hpssssph .pssssp. ssssssss vccssccv ccvvvvcc tttvvttt""",
            "right_arm.front": """acc vcc ccc vwc sss sss sss aas sas ccc vcc ccc""",
            "left_arm.front": """cca ccv ccc cwv sss sss sss saa sas ccc ccv ccc""",
            "right_leg.front": """tttt cvvc ssss saas aswa ssss ssss rrrs brrb brbb brbb bbbr""",
            "left_leg.front": """tttt cvvc wwww pppp wwww pppp wwww rrrr brrb bbrb bbrb rbbb""",
        }),
    "yuuki": dict(
        slim=False,
        colors=dict(s="#efcaaa", h="#383234", e="#514438", c="#f2f0e9",
                    t="#e3e1db", b="#343439", a="#504f6e", w="#fffdf4", d="#c8c7c4", k="#544744"),
        faces={
            "head.front": """hhkhhhkh hhhkhhhh khhhhkhh hshhhshh .weshesh ssssssss ssskksss hssssssh""",
            "hat.front": """..hhkh.. .hh..hk. h.h...hh ..h..h.. ........ ........ ........ ........""",
            "body.front": """ccwsswcc ccwwwwcc cccwwccc cccwwccc ccaaaacc ccccccac ccccccac ccccccac ccccccac ccccccac ccccccac ddcccdad""",
            "body.back": """ccwddwcc ccwwwwcc cccccccc wccccccw wccccccw wccccccw cccccccc cccccccc cccccccc cccdcccc cccdcccc ddddcddd""",
            "right_arm.front": """cwcc cwcc cwcc cwcc cccc cccc cccc cdcc cdcc dada ssss ssss""",
            "left_arm.front": """ccwc ccwc ccwc ccwc cccc cccc cccc ccdc ccdc adad ssss ssss""",
            "right_leg.front": """twtd twtd twtd twtd twtd twtd tttd tttd tttd ddtd bbbb bbab""",
            "left_leg.front": """dtwt dtwt dtwt dtwt dtwt dtwt dttt dttt dttt dtdd bbbb babb""",
        }),
    "rigurd": dict(
        slim=False,
        colors=dict(s="#8d9b66", h="#c4bdca", e="#3f362c", c="#413a3a",
                    t="#96734d", b="#58483a", a="#e7d9b3", d="#747079",
                    l="#a8a2a5", w="#f5edda", k="#6b774a"),
        faces={
            "head.back": "hhhhlhhh hhlhhhlh llhhhllh khhlhhsk skhhksss sskkssss ssssssss ssssssss",
            "head.right": "hhlhhhhh lhhhhllh hhhlhhks khhhksss skkssskk ssksksks ssksssss ssssssss",
            "head.left": "hhhhhlhh hllhhhhl skhhlhhh ssskhhhk kkssskks skskskss ssssskss ssssssss",
            "head.front": """hhlhhhlh hhhshhhh hskssksk skksskks swessews skskksks skwsswks sskkkkss""",
            "hat.front": """hh.hhlhh .hh..hh. h......h ........ ........ ........ ........ ........""",
            "body.front": """aassssaa caskksac cadlldac cadlldac cadlldac cadlldac cadlldac cadlldac caattaac cattatac caabbaac caatttac""",
            "body.back": """aaassaaa caaaaaac cccccccc cccccccc dccccccd cdccccdc cdccccdc ccdccdcc ccdccdcc cccccccc cccccccc aaaaaaaa""",
            "right_arm.front": """cccc ccdc ccdc ccdc cccc cccc aaaa awaa tttt btbt ssks ssss""",
            "left_arm.front": """cccc cdcc cdcc cdcc cccc cccc aaaa aawa tttt tbtb skss ssss""",
            "right_leg.front": """ttbt ttbt ttbt tttt tttb tttb tttb bttb tbtb bbbb bbab bbbb""",
            "left_leg.front": """tbtt tbtt tbtt tttt bttt bttt bttt bttb btbt bbbb babb bbbb""",
        }),
    "gobta": dict(
        slim=False,
        colors=dict(s="#a2ad72", h="#ccc0d2", e="#383737", c="#5a4437",
                    t="#af925e", b="#413a34", a="#e1cfa9", w="#fff8e9",
                    v="#99919f", k="#79824f", r="#864f42"),
        faces={
            "head.back": "ssvhvhss svhhhhvs svhvhvss ssvhvsss sssvssss ssssssss ssssssss ssssssss",
            "head.top": "ssvhvhss svhhhhvs svhvvhvs sshhhvss svhhhvvs svhhhhvs svhvhvhs shhhhhhs",
            "head.left": "hhhhvsss vhvhvsss shvvssss ssvssssk ssssskks sskkksss ssssssss ssssssss",
            "head.right": "sssvhhhh sssvhvhv ssssvvhs kssssvss skksssss ssskkkss ssssssss ssssssss",
            "head.front": """hhvhhhhh vhhvhshh skssskss swesswes swesswes ssskksss sswrrwss skssssks""",
            "hat.front": """..h.hh.. .vh.hhv. .h....h. ........ ........ ........ ........ ........""",
            "body.front": """aaassaaa caawwaac cawwwwac cawwwwac cawwwwac cawwwwac cawwwwac cawwwwac cawwwwac caarraac catbbtac aatbttaa""",
            "body.back": """aaassaaa ccaaaacc cccccccc ccvccvcc ccccvcvc cccccccc ccvccccc cccccccc cccccccc ccaaaaac aatbbtaa aattbtaa""",
            "right_arm.front": """cccc ccvv cccc aaaa ssss ssss tttt btbt bttb bttb ssss ssss""",
            "left_arm.front": """cccc vvcc cccc aaaa ssss ssss tttt tbtb bttb bttb ssss ssss""",
            "right_leg.front": """ttbt ttbt tttt tttt tttb tttb tttb tttb btbb bbbb btbb bbbb""",
            "left_leg.front": """tbtt tbtt tttt tttt bttt bttt bttt bttt bbtb bbbb bbtb bbbb""",
        }),
}
# The three Dwargon artisans, with separately drawn crowns, profiles and beard edges.
# The colour choices and workshop details are interpretations of their trade and silhouette.
DWARVES = {
    "garm": dict(
        slim=False,
        colors=dict(s="#ce946a", h="#514034", e="#443430", c="#414248", t="#655448",
                    b="#4b3933", a="#c4a06b", w="#e1d9c7", d="#302e32", f="#856447",
                    g="#a39888", k="#3c302b", u="#b57a53", l="#5a595b", p="#88664d"),
        faces={
            "head.front": """hhfhfhhh fhffhfhh hfhssshh hsssshhs lweeswes sssfufss fhhsshff hhfhhfhh""",
            "head.top": """hfffhhhf fhfhfhfh hfhffhff hhffhfhf hhhfhhfh fhffhfff hffhhfhh hfhhfhhh""",
            "head.back": """hhfhhfhf hfhffhfh hffhhffh hfhffhhh hhhfhhfh fhfhhfhh uhhhhhhs ssshhsss""",
            "head.right": """hfhhfhff fhfhhffh hhffhfhf hfhfhshh hhhhsush hhhssush hfhssuhh hhhhhhfh""",
            "head.left": """ffhfhfhh fhffhhfh hfhfhhff hhshfhhh hsusfhfh hsusshhh hfusshfh hhhhfhhh""",
            "head.bottom": """hhfhhfhh hhhfhhfh hhfhfhfh hhhhhhfh uhhhhuss ussssusu sssusuus ssssuuus""",
            "hat.front": """..fh.f.. .hffhfh. hf.....h ........ ........ .hf..fh. fhh..hhf .hhffhh.""",
            "hat.back": """..fhh... .hfhfh.. ........ .......h h....... ........ ........ ........""",
            "hat.left": """..fhh... ....hfh. .......h ........ ........ h....... hh...... hhf.....""",
            "hat.right": """...hfh.. .fh..... h....... ........ ........ .......h ......hh .....fhh""",
            "body.front": """schhhfcs scuhhucs sclsscls sccllccs ucccccdu ccllccdc cccldccd cccldclc ccccllcc pppppppp bbgagbbb ttpptttt""",
            "body.back": """scuuuscs sclsscls sccllccs ucclcccu uccclcdu clccclcc cdclcllc cdcccllc ccdccccd pppppppp bpppbbbb ttpptttt""",
            "body.right": """ssss ssss ssus ssus uccu cccc clcc ccdc cccc pppp bbbb ttpt""",
            "body.left": """ssss ssss suss suss uccu cccc cclc cdcc cccc pppp bbbb tptt""",
            "jacket.front": """..hffh.. ...hh... ........ ........ ........ ........ ........ ........ ........ .p...... .b.aa... .b......""",
            "right_arm.front": """ssus ssss suss ssss suus usss gwww wwgw gwww wgwg bbbd ssss""",
            "left_arm.front": """suss ssss ssus ssss suus sssu wggw wwww wwgw gwgw dbbb ssss""",
            "right_leg.front": """ttpb ttpb tttp ttpt tppt ttpt ttpt ddtt bppb bbbb bpbb kkkk""",
            "left_leg.front": """bptt bptt pttt tptt tptt pptt tptt ttdd bppb bbbb bbpb kkkk""",
        }),
    "dold": dict(
        slim=False,
        colors=dict(s="#d9a481", h="#645451", e="#51413c", c="#ded9cb", t="#766252",
                    b="#554237", a="#c69b63", d="#37343a", f="#918482", w="#f0eadc",
                    k="#453d40", u="#b7856e", l="#acaa9f", p="#8a7461", g="#b4a994"),
        faces={
            "head.front": """fhhfhfff fhfhfhhs hfssusss hssuussu seeusees usssussu hfhhhffh hhhhhfhh""",
            "head.top": """fhfhhfff hhhffhff hfffhhfh hfhfffhh fhffhhhf hhfhffhh fhhfffhh hffhhfhf""",
            "head.back": """ffhfhhff hhffhhfh hfhffhff hhfhhfhh fhfhfhhh hhhhhhhh uhhfhhhu suuuuuss""",
            "head.right": """hhfhffhh hfhffhfs hhhfhhss hhfhsuss hhhusush hhhsuush hhhfshhh hhhhffhh""",
            "head.left": """ffhhfhfh sshhhhhf sshfhfhf sssuhhhh suusfhhh hussfhhh hhhshhfh hhhfhhhh""",
            "head.bottom": """fhhffhhh hhfhhhhf hhhffhhh hhfhhhhf ushhhfuu uusssuus ssusuuss ssssssss""",
            "hat.front": """..fhff.. .fh..fh. h....... ........ ........ .......h fhh..hhf hhffhhfh""",
            "hat.right": """...hh... ....hh.. ........ ........ ........ ......hh .....fhh ....hhfh""",
            "hat.left": """..ffh... .hh..... ........ ........ ........ hh...... hhf..... hfhh....""",
            "hat.back": """...hhf.. ..h..hf. ........ ........ h....... ........ ........ ........""",
            "body.front": """ddhfhfdd ddkhhkdd kdkddkdk cdkddkdc wcwllwcw wccwlccw cwwlwcwc ccclwccc cllwlclc cccwlccc bbbgagbb wwwccwww""",
            "body.back": """dkdkdkdk kdkdddkd dkdkddkd cdkddkdc wcwccwcw cwcllwcw ccclwccc cccwlccc cllwlclc cccwlccc bbbpbbbb wwwccwww""",
            "jacket.front": """dd....dd kd....dk .kd..dk. .d....d. ........ ........ ........ ........ ........ ........ ...ga... ........""",
            "jacket.back": """dkkddkkd .dkddkd. .dk..kd. ..d..d.. ........ ........ ........ ........ ........ ........ ........ ........""",
            "right_arm.front": """wwlc tptt ttpt tptt tppt ptpt pppt gggg gllg gggg glgg suss""",
            "left_arm.front": """clww ttpt tptt ttpt tppt tptp tppp gggg gllg gggg gglg ssus""",
            "right_leg.front": """wwwc pttt tptt ptpt tptt tptt pttp bbpb bppb bbbb bpbb kkkk""",
            "left_leg.front": """cwww tttp ttpt tptp ttpt ttpt pttp bpbb bppb bbbb bbpb kkkk""",
        }),
    "mildo": dict(
        slim=False,
        colors=dict(s="#ddad85", h="#897043", e="#554941", c="#b59a64", t="#7e7160",
                    b="#594a3b", a="#d4b97e", w="#eee8db", l="#cec7b6", u="#c49572",
                    f="#ae905b", k="#6c573b", p="#aa8357", v="#e8bd96", d="#685844"),
        faces={
            "head.front": """ssvvvvss svvvvsss ssvsssss suusssus sweuswes usssussu sfsfsffs hffhhffh""",
            "head.top": """ussssssu sssvvsss ssvvvvss svvvvvvs svvvvvvs ssvvvvss ssvvvsss ssssssss""",
            "head.back": """ussssssu sssvvsss ssssvsss ssssssss ussssssu uussusuu huuuuush hhhuuhhh""",
            "head.right": """usssssss sssssvvs sssssvss sssussss ussuusus usuususu hsuussuf hhuhffhh""",
            "head.left": """sssssssu svvsssss svssssss ssssusss susuusss ususuuus fusssush hhffhuhh""",
            "head.bottom": """hhfhffhh hhhfhhfh hhhhhhfh uhfhhfhu usuhhusu ssuususs ssssssuu ssssssuu""",
            "hat.front": """........ ........ ........ ........ ........ ........ f......f .hhffhh.""",
            "hat.left": """........ ........ ........ ........ ........ ........ f....... hf......""",
            "hat.right": """........ ........ ........ ........ ........ ........ .......f ......fh""",
            "body.front": """wwwffwww wwlfflww lwwwwwwl cllwwllc ccalwlac ccawwacc ccalwacc caacwccc caaclccc caacccac pppapppp ccpaapcc""",
            "body.back": """lwwwwwwl wwwllwww lwwwwwwl cllwwllc cccllccc ccaccacc ccaccacc caaccaac caaccaac ccccccac pppapppp cccaaccc""",
            "body.right": """lwww wwww lwww ccll accc ccca cccc cccc accc ccca pppp caac""",
            "body.left": """wwwl wwww wwwl llcc ccca accc cccc cccc ccca accc pppp caac""",
            "jacket.front": """ww....ww .ww..ww. ..wwww.. ...lw... ...ww... ...wl... ....w... ....l... ........ ........ ...a.... ........""",
            "jacket.back": """lwwwwwwl .wwllww. ..wwww.. ...ll... ........ ........ ........ ........ ........ ........ ........ ........""",
            "right_arm.front": """acca ccca accc caac cacc accc caac cccc pppp aapa ssss ssus""",
            "left_arm.front": """acca accc ccca caac ccac ccca caac cccc pppp apaa ssss suss""",
            "right_leg.front": """ccca tttt tptt ttpt tptt tttt tppt dttd ppbp bbbb bbpb dddd""",
            "left_leg.front": """accc tttt ttpt tptt ttpt tttt tppt dttd pbpp bbbb bpbb dddd""",
        }),
}

# Court dress. The crown's band follows Edmaris's head around all four sides.
# Razen uses Shogo's vessel. Louis wears the Holy Emperor's white-and-gold vestment.
COURT = {
    "edmaris": dict(
        slim=False,
        colors=dict(s="#d7a987", h="#97868a", e="#5b504b", c="#903843",
                    t="#47312e", b="#523e37", a="#dea844", k="#594442",
                    w="#e1c7a6", l="#ffe197", d="#70545a", f="#b8997d",
                    g="#996925", j="#454678", m="#ad8d71"),
        faces={
            "head.front": """
                hdhhdhhh dhhhhhhd hssssssh hhhsshhd
                seessees hsskkssh hhhdhhhd hhhhddhh
            """,
            "hat.front": """
                a..aa..a gaajjaag aaaajaaa .g....g.
                ........ ........ .hd..dh. ..d..h..
            """,
            "hat.top": """
                aagjjgaa a......a g......g j......j
                j......j g......g a......a aagjjgaa
            """,
            "hat.back": """
                a..aa..a aagaagaa gaaaalag ........
                .....d.. .h.....h .h..hd.h h..h...d
            """,
            "hat.left": """
                a..aa..a aggaagga aaaaaaaa ........ ........ ........ ........ ........
            """,
            "hat.right": """
                a..aa..a aggaagga aaaaaaaa ........ ........ ........ ........ ........
            """,
            "body.front": """
                fwfddfwf wfwhhfwf fwfhhwfw fwahhafw
                cwaaaawc cctggtcc cctattcc cctgtacc
                cctagtcc cttgattc cttagttc cttgattc
            """,
            "body.back": """
                fwfwwfwf wfwfwwfw wwfwffwf fwwffwwf
                mfwfffwm cmmwfmmc ccmmfmcc ccdccdcc
                ccdccdcc ccdccdcc ccdccdcc ccdccdcc
            """,
            "jacket.front": """
                .w....w. wfw..wfw .f....f. ..a..a..
                ...aa... ........ ........ ........
                ........ ........ ........ ........
            """,
            "right_arm.front": """
                wfwf fwwf wfwf mfmm cccc cccd cccd cccd
                ccad agaa ssss ssss
            """,
            "left_arm.front": """
                fwfw fwwf fwfw mmfm cccc dccc dccc dccc
                dacc aaga ssss ssss
            """,
            "right_leg.front": """
                cctg cctg cctg cctg cctg cctg cttg cttg
                aatt aatt bbbb bgbb
            """,
            "left_leg.front": """
                attc attc attc attc attc attc attc attc
                ttaa ttaa bbbb bbgb
            """,
            "right_leg.back": """
                cdcc cdcc ccdc ccdc ccdc ccdc ccdc ccdc
                gcag agaa bbbb bbbb
            """,
            "left_leg.back": """
                ccdc ccdc cdcc cdcc cdcc cdcc cdcc cdcc
                gacg aaga bbbb bbbb
            """,
        },
    ),
    "razen": dict(
        slim=False,
        colors=dict(s="#d7b396", h="#24252d", e="#513d34", c="#695476",
                    t="#4a4351", b="#39353f", a="#a28eaa", k="#302d39",
                    w="#eae1d8", r="#464650", d="#40384a", p="#85718f",
                    g="#ac9472"),
        faces={
            "head.front": """
                hhrhhrhh rhhrhhrh hshhsshh hssshssh
                skksskks swesswes ssssssss ssssssss
            """,
            "hat.top": """
                .rh..h.. h...r..h ..hh..r. .r..h...
                h..r...h ..hr.hh. h...rh.. ..r..h..
            """,
            "hat.front": """
                hrhhhhrh .h..h..h ..h..h.. ..h.....
                ........ ........ ........ ........
            """,
            "hat.back": """
                ...hr..h .rh..... h...rh.. ..hr...h
                ..h..rh. h....h.. .h..h... ..rh..h.
            """,
            "body.front": """
                kkdssdkk dkpwwpkd ddpwwpdd cddppddc
                ccdggdcc cccwwccc cccwtccc cccwwccc
                dddggddd kkkggkkk cccttccc ccpttpcc
            """,
            "body.back": """
                dkkkkkkd dpkddkpd cdpddpdc ccdppdcc
                cccddccc cccccccc ccccpccc cccppccc
                ccpcppcc ccpccpcc cdcccpcc cdcccpdc
            """,
            "jacket.front": """
                kk....kk .d....d. ..p..p.. ...pp...
                ...gg... ........ ........ ........
                ........ ........ ........ ........
            """,
            "right_arm.front": """
                kdcc ddpc cccp cccc cccd cccd cccd cccd
                pppd dpdd ssss ssss
            """,
            "left_arm.front": """
                ccdk cpdd pccc cccc dccc dccc dccc dccc
                dppp ddpd ssss ssss
            """,
            "right_leg.front": """
                ccpt ccpt ccpt ccpt ccpt ccpt ccpt cdpt
                cdpt pdtt tttt bbbb
            """,
            "left_leg.front": """
                tpcc tpcc tpcc tpcc tpcc tpcc tpcc tpdc
                tpdc ttdp tttt bbbb
            """,
            "right_leg.back": """
                cdcc cdcc cdcc cdcc cdcc cdcc cdcc cdcc
                pdpp cddc tttt bbbb
            """,
            "left_leg.back": """
                ccdc ccdc ccdc ccdc ccdc ccdc ccdc ccdc
                ppdp cddc tttt bbbb
            """,
        },
    ),
    "louis": dict(
        slim=False,
        colors=dict(s="#e4c8ad", h="#d7c69d", e="#747c6c", c="#f5f0e6",
                    t="#514a5b", b="#c8a151", a="#d7aa57", k="#797165",
                    w="#fffaf1", r="#eee1bf", d="#a59074", f="#d6d1ca",
                    g="#ad8134", j="#f3d584"),
        faces={
            "head.front": """
                hrrhrhrh rhhrhrhh hhshhssh dssssssh
                dkksskks swesswes ssssssss ssssssss
            """,
            "hat.top": """
                .r..r... .rr..r.. ..rh.r.. h..h..r.
                hr..hr.. .rh..r.. ..r..rh. ...r..r.
            """,
            "hat.front": """
                rh..r..r .rh..rh. ..h...d. ........
                ........ ........ ........ ........
            """,
            "hat.back": """
                ..r.h..r .r..hr.. .rh..r.. ..h..r..
                .rh...h. ..d..h.. .d....h. ...d.d..
            """,
            "body.front": """
                cacsscac caaccaac ccaaaacc caccccac
                caccccac cajccjac caaccaac caccccac
                caccccac caccccac acccccca acccccca
            """,
            "body.back": """
                fcaaaacf fcaacacf ccaaccac ccaaaacc
                cccccccc ccccfccc ccccfccc ccccfccc
                cccaaccc cccaaccc ccaafacc caccffac
            """,
            "jacket.front": """
                .a....a. ..a..a.. ...aa... ........
                ........ ..j..j.. ..g..g.. ........
                ........ ........ ........ ........
            """,
            "right_arm.front": """
                aaac aaac cccc cccf cccf cccf cccf cccf
                tttt tttt wwww wffw
            """,
            "left_arm.front": """
                caaa caaa cccc fccc fccc fccc fccc fccc
                tttt tttt wwww wffw
            """,
            "right_leg.front": """
                accc accc acca acca acac acga accg acca
                tttt caac wwww bjjb
            """,
            "left_leg.front": """
                ccca ccca acca acca caca agca gcca acca
                tttt caac wwww bjjb
            """,
            "right_leg.back": """
                cacc cacc cacc cacc cacc cacc cacc cacc
                tttt caac wwww bbbb
            """,
            "left_leg.back": """
                ccac ccac ccac ccac ccac ccac ccac ccac
                tttt caac wwww bbbb
            """,
        },
    ),
}

# Limestone effigies. The pauldron, wings and chain bib identify the seats at a distance.
WALPURGIS = {
    "carrion": dict(
        slim=False,
        colors=dict(s="#b5b1a4", h="#c7bfaa", e="#565960", c="#717276", t="#a49f94",
                    b="#666870", a="#b5a78b", w="#dad2bd", d="#87857f", k="#96918b"),
        faces={
            "head.front": """whwhhwhw hwhhwhwh hwhhdhwh hssddssh sdewweds sssddsss sdssssds ssddddss""",
            "hat.front": """w.h.wh.h hhwhhwhw .wh..wh. .h....h. ........ ........ ........ ........""",
            "hat.back": """hw.hw.wh whwhwhwh hwhhwhhh hddhhdhh .h.hd.h. ..h..h.. ........ ........""",
            "body.front": """cassssac cassssac casdssac cakssaac casdaadc casaaadc caaaadac caaadacc awwawwaa waawaawa awawawaw cawawawc""",
            "body.back": """ccdccdcc cccddccc cccccccc dccccccd cdccccdc cddccddc ccdccdcc cccccccc awwawwaa waawaawa awawawaw cawawawc""",
            "jacket.front": """a....... wa...... aw...... .aw..... ..aw.... ...a.... ........ ........ ........ ........ ........ ........""",
            "right_arm.front": """aaww waaa ddaw awaa aaww ccca ccss ssss awaw waaw sssd ssds""",
            "right_sleeve.front": """w... ww.. aww. .a.. ww.. .ww. ..a. .... .... .... .... ....""",
            "right_sleeve.right": """...w ..ww .wwa ..a. ..ww .ww. .a.. .... .... .... .... ....""",
            "left_arm.front": """cccc cdcc ccdc cdcc cccc ccdd ssss ssss awaw waaw sssd sdss""",
            "right_leg.front": """catt catt catt catt catt catt catt cadt ttdd dddd bbab bwbb""",
            "left_leg.front": """ttac ttac ttac ttac ttac ttac ttac tdac ddtt dddd babb bbwb""",
        }),
    "frey": dict(
        slim=False,
        colors=dict(s="#bbb7b1", h="#d4cfd0", e="#67636b", c="#938284", t="#77757b",
                    b="#aaa18c", a="#b6b3b2", w="#e0dbd2", d="#928f97", k="#77767e"),
        faces={
            "head.front": """hhwhhwhh hwhddhwh whdssdhw hdssssdh hwessewh hssssssh hssddssh hdssssdh""",
            "hat.front": """hwh..hwh wh....hw h......h h......h h......h h......h h......h .h....h.""",
            "body.front": """kksssskk dkkkkkkd ssdkkdss ssssssss cssssssc ccsssscc ccdssdcc cccddccc ccdccdcc cdccccdc dccccccd sdccccds""",
            "body.back": """ahhddhha whhhhhhw awhhhhwa hawddwah whawdahw hwhwwhwh ahwhhwha dahwwhad cdahhadc ccdwwdcc sccddccs ssccccss""",
            "jacket.back": """wh....hw hwh..hwh dhwhhwhd .dhwwhd. w.dhhd.w hw.dd.wh dhw..whd .dhwwhd. ..dhhd.. ...ww... ........ ........""",
            "right_arm.front": """ssss sssd ssss sssc cccd ccdc cdcc dccc cccd ccdc cdds ssds""",
            "left_arm.front": """ssss dsss ssss csss dccc cdcc ccdc cccd dccc cdcc sddc sdss""",
            "right_arm.back": """wwah haww whha hwhh dhww wdhw hwdh dhwd wdhw hwdh .hwd ..hd""",
            "left_arm.back": """haww wwah ahhw hhwh wwhd whdw hdwh dwhd whdw hdwh dwh. dh..""",
            "right_sleeve.right": """..ww .whw whhw hhwh hwhd whdh hdhw dhwh hwhd whd. hd.. d...""",
            "left_sleeve.left": """ww.. whw. whhw hwhh dhwh hdhw whdh hwhd dhwh .dhw ..dh ...d""",
            "right_leg.front": """sssc ssss ssss dsss ttdd tttt ttkt bbtt bbbd bwbd kkbb wkdk""",
            "left_leg.front": """csss ssss ssss sssd ddtt tttt tktt ttbb dbbb dbwb bbkk kdkw""",
        }),
    "guy": dict(
        slim=False,
        colors=dict(s="#b9b1a5", h="#9a8684", e="#5b575a", c="#676972", t="#77737a",
                    b="#b9b7b2", a="#998781", w="#d8cfc0", d="#858185", k="#aea09d"),
        faces={
            "head.front": """hhkhkhhk hkhhhkhh hhshhhsh hssehssh swehsews hsssdssh hssddssh hssssssh""",
            "hat.front": """h.kh..hh hk.hhkk. .h.h.hh. ..h..h.h .....h.. ........ ........ ........""",
            "hat.back": """hkhhkhhk khhkhhkh hhhkhkhh hkhhhkhk hhkhkhhh hkhhhkhh khhkhhkh hhhkhhkh""",
            "body.front": """kcssssck ccdwwdcc ccwsswcc cdwdwddc cdwwwwdc csdssdsc cssddssc cssssssc sssddsss bbwwwwbb aakaaakk kaakaaak""",
            "body.back": """chkhhkhc chhkhhhc chkhhkhc cdhkhhdc cdchhcdc ccchhccc ccchcccc cccdccdc cccccccc bbwwwwbb aakaaakk kaakaaak""",
            "jacket.front": """cc....cc .c....c. .cd..dc. ..c..c.. .c....c. c......c ........ ........ ........ ........ ......ak ......ka""",
            "jacket.back": """........ ........ ........ ........ ........ ........ ........ ........ ........ ........ k......k .kk..kk.""",
            "right_arm.front": """cccc ccdc ccdc cccc cdcc ccdd kkkk dkdk kkkk ddkk ssss ssss""",
            "left_arm.front": """cccc cdcc cdcc cccc ccdc ddcc kkkk kdkd kkkk kkdd ssss ssss""",
            "right_leg.front": """attt ttdt ttdt ttdt tdtt tdtt dttd tddt bwwb bwwb bbwb dddb""",
            "left_leg.front": """aaka ttak ttda ttdt ttdt tttd dttd tddt bwwb bwwb bwbb bddd""",
        }),
    "leon": dict(
        slim=False,
        colors=dict(s="#c5beb0", h="#b2ac9c", e="#535963", c="#787b80", t="#88898a",
                    b="#74767a", w="#e8e2d4", l="#d2cbbb", d="#60656d", k="#4f5560",
                    f="#a09d94", g="#a8a394", v="#dad2c0"),
        faces={
            "head.front": "lhhllhlh lhlhhlhl hlhlhlhh lshlshlh svessves lssssssl hssffssl hfsllsfh",
            "head.back": "lhllhhlh hlhllhlh lhhlhlhl hlhlhlhl hlhlhhlh hhhlhlhl fhflhlhf fffhffhf",
            "head.top": "fhhhhlhh hllhhllh hlhlhllh hlhhhlhl lhhhlhhl hhlhlhhl lhlhhlhl lhhlhlhl",
            "hat.front": ".lhhlhh. lh..h.hl h...h..h h......h l......l h......h f......f ........",
            "hat.back": ".hl..h.. .hl..lh. .hh..lh. .hh..hh. ..h...h. .fh..ff. .ff...f. ..f.....",
            "body.front": "dvvwwvvd cdlwwldc cdlwwldc cdlgggdc cdlffldc cdvggvdc cdvgfvdc cdvggvdc clgffglc clgddglc lggddggl ggdttdgg",
            "body.back": "ddhhhhdd clhhhlhc cdhhhlhc cdfhfhfc cddhffdc cddffddc cdddcddc cdcddcdc cdcddcdc cdcdcdcc cdcddcdc ddcddcdd",
            "jacket.front": ".d.vv.d. ..wwww.. ..wllw.. ...ww... ..v..v.. ..v..v.. ........ ........ .v....v. .v....v. v......v v......v",
            "jacket.back": ".d....d. ..d..d.. ........ d......d dc....cd dc....cd dc....cd dc....cd dc....cd dc....cd dd....dd dd....dd",
            "right_arm.front": "ccdc cdcc ccdc cddc cddc cddc cdcc ggvg gvvg kkkk ssss sfsf",
            "left_arm.front": "cdcc ccdc cdcc cddc cddc cddc ccdc gvgg gvvg kkkk ssss fsfs",
            "right_leg.front": "ggdt ggtt gdtt tdtt tdtt kdtt kttt kdtt gvvg fgvg bbgb kbbk",
            "left_leg.front": "tdgg ttgg ttdg ttdt ttdt ttdk tttk ttdk gvvg gvgf bgbb kbbk",
        }),
    "ramiris": dict(
        slim=False,
        colors=dict(s="#cbc4b7", h="#b4ac98", e="#5b6066", c="#77777b", t="#999899",
                    b="#b7b5ac", w="#ece5d7", l="#ded6c2", d="#666972", k="#565b64",
                    f="#9e978b", g="#aaa69b", v="#c7c6bf"),
        faces={
            "head.front": "lhlhlhll hhlhlhlh lhlhshlh hlhssslh slkssklh swesswes hssssssh ssfsllfs",
            "head.back": "hlhllhhl lhlhlhlh hhlhlhlh hlhllhlh lhfhhlhl hfhhlhfh hhhffhhh hffhhffh",
            "hat.front": ".l..lh.. ..lhlh.l lh.h..h. .h.....l h......h f......h ........ ........",
            "hat.right": "..lh..l. .lh.hl.. .hhl.... ..lh.... .hl..... .lh..... .hf..... hf......",
            "hat.left": ".l..hl.. ..lh.hl. ....lhh. ....hl.. .....lh. .....hl. .....fh. ......fh",
            "body.front": "hsskkssh lssssssl fssccssf sccccccs cdccccdc cdccccdc ccdccdcc ccdccdcc gvccccvg dgvvvvgd ckdggdkc dcckkccd",
            "body.back": "hsssccsh hccccsch cccccccc cdccccdc ccdccdcc cccddccc cccddccc ccdccdcc gccccccg dgccccgd ckdggdkc dcckkccd",
            "jacket.back": "w......w lw....wl lvw..wvl .lvwwvl. ..vwwv.. ...vv... ..wvvw.. .wvvvvw. wvvllvvw vlv..vlv lw....wl w......w",
            "right_arm.back": "ccss ccss ccss csss csss ccss csss ssss csss ccss cccc kkkk",
            "left_arm.back": "sscc sscc sscc sssc sssc sscc sssc ssss sssc sscc cccc kkkk",
            "right_sleeve.back": "..wl .wvl wvvl vvvl vvl. vl.. l... ..vl .vv. wv.. v... ....",
            "left_sleeve.back": "lw.. lvw. lvvw lvvv .lvv ..lv ...l lv.. .vv. ..vw ...v ....",
            "right_arm.front": "hssl lhhf ssfs ssss dgsg ggvg cccc cdcc ccdc cdcc dcdc kcck",
            "left_arm.front": "lssh fhhl sfss ssss gsgd gvgg cccc ccdc cdcc ccdc cdcd kcck",
            "jacket.front": "h......h .l....l. .f....f. ........ ........ ........ ........ ........ v......v .v....v. ..v..v.. ........",
            "right_leg.front": "cdcc dcdc cddc lssc ssss vvvs vwvv vvwl vllv vvwv ddbb kbbk",
            "left_leg.front": "ccdc cdcd cddc cssl ssss svvv vvwv lwvv vllv vwvv bbdd kbbk",
        }),
    "dagruel": dict(
        slim=False,
        colors=dict(s="#b8b0a2", h="#78797b", e="#494f59", c="#c9c4b9", t="#85858a",
                    b="#b3b0a9", w="#e6dfce", l="#cfc6b2", d="#676b73", k="#565c64",
                    f="#9e9687", g="#969489", v="#dcd6c6"),
        faces={
            "head.front": "hddhdhdh dhhsshdd hhssdfsh sslfdfss fedssdef svessves fsfslsfs sfslflfs",
            "head.back": "dhdhhdhd hdhhhdhh hdhhhdhd hhhdhhhd dddhhhdh fdhddhdf sfhffhfs ssfssffs",
            "hat.front": ".h...dh. hh..hd.. .d..h..h ........ ........ ........ ........ ........",
            "hat.back": ".h.dhh.. h.dh.h.d .dhh..dh ...hd.h. ..d...dh ....h... ........ ........",
            "body.front": "wssffssw wslsslsw vslsslsv vsffsfsv vffssffv vssffsww wsfssvwc wvffvwcv cvvwwcvc cwwccvvc ggvgvggv gffggffg",
            "body.back": "wssffssw wlsffslw vssffssv cvfssfvc cvcffcvv vcvcvvcv vvcvvcvc cvwvcvcc vwvcwcvv wvcvvcwc ggvggvgg gffggffg",
            "jacket.front": "w......w w......w ........ ........ .......w ......w. .....w.. ....w... ...w.... ..w..... .l..l..l .f..f..f",
            "right_arm.front": "slss llss ssff sffs ddds kkdk dddk vccv vvcc cvvc ssss sffl",
            "left_arm.front": "ssls ssll ffss sffs sddd kdkk kddd vccv ccvv cvvc ssss lffs",
            "right_leg.front": "cvcv vcvw cwcv vvcv cvcv cdtt ttft tdtt ttdt gfgg bvvb bbdb",
            "left_leg.front": "vcwc cvvc wvcc vcvc tccv tttc tftt ttdt tdtt ggfg bvvb bdbb",
        }),
}

SKINS = {**GUILD, **KIJIN, **TEMPEST, **DWARVES, **COURT, **WALPURGIS}

# Standard player cube nets. The two limbs have distinct UV islands in the 64px format.
# Dimensions are width, height, depth. Slim arms are one texel narrower on four faces.
PARTS = {
    "head": ((0, 0), (32, 0), "hat", (8, 8, 8)),
    "body": ((16, 16), (16, 32), "jacket", (8, 12, 4)),
    "right_arm": ((40, 16), (40, 32), "right_sleeve", (4, 12, 4)),
    "left_arm": ((32, 48), (48, 48), "left_sleeve", (4, 12, 4)),
    "right_leg": ((0, 16), (0, 32), "right_pants", (4, 12, 4)),
    "left_leg": ((16, 48), (0, 48), "left_pants", (4, 12, 4)),
}


def face_boxes(origin, width, height, depth):
    """Pillow rectangles in the order of the six faces in a Minecraft cube net."""
    u, v = origin
    side_y = v + depth
    return {
        "top": (u + depth, v, u + depth + width, side_y),
        "bottom": (u + depth + width, v, u + depth + 2*width, side_y),
        "right": (u, side_y, u + depth, side_y + height),
        "front": (u + depth, side_y, u + depth + width, side_y + height),
        "left": (u + depth + width, side_y, u + 2*depth + width, side_y + height),
        "back": (u + 2*depth + width, side_y, u + 2*(depth + width), side_y + height),
    }


def material(part, face, x, y, width):
    """Paint the continuous base underneath the hand-drawn features."""
    if part == "head":
        if face == "bottom":
            return "s"
        if face in ("top", "back"):
            return "h"
        if face in ("left", "right"):
            # Both ears open toward the face, around a stepped hairline.
            front_distance = x if face == "left" else width - x - 1
            return "s" if y >= 4 and front_distance <= 4 and (y >= 6 or front_distance in (2, 3)) else "h"
        return "h" if y < 2 else "s"
    if part == "body":
        return "c"
    if part.endswith("_arm"):
        if face == "bottom" or face != "top" and y >= 9:
            return "s"
        return "c"
    if face == "bottom" or face != "top" and y >= 8:
        return "b"
    return "t"


def fabric_edge(patterns, part, face, x, y, width):
    """Carry the cut of a sleeve, stocking or hem around sides and across the back."""
    front = patterns.get(f"{part}.front")
    if part == "head" or not front or face == "front":
        return None
    if face in ("top", "bottom"):
        row = front[0 if face == "top" else -1]
        return row[x]
    row = front[y]
    back = patterns.get(f"{part}.back")
    if face == "back":
        # A front crease or badge belongs on the front. Wrap just the edge colours.
        return row[-1 if x < width/2 else 0]
    edge = row[0 if face == "right" else -1]
    if back and (face == "right" and x < width//2 or face == "left" and x >= width//2):
        edge = back[y][-1 if face == "right" else 0]
    return edge


def shade(color, face, x, y):
    # A slight value change gives the unpatterned texels a woven surface and the
    # under-faces a shadow. The hand-drawn motifs keep their authored palette.
    light = {"top": 6, "bottom": -10, "back": -3, "left": -4, "right": -2}.get(face, 0)
    grain = (3*x + 7*y + (x//2)*(y//3)) % 9 - 4
    return tuple(max(0, min(255, channel + light + grain)) for channel in color)


def draw_skin(npc_id, spec):
    image = Image.new("RGBA", (64, 64))
    palette = {key: ImageColor.getrgb(value) for key, value in spec["colors"].items()}
    patterns = {key: value.split() if isinstance(value, str) else value
                for key, value in spec["faces"].items()}
    maps = dict(patterns)
    for part, (base, outer, outer_name, (width, height, depth)) in PARTS.items():
        if spec["slim"] and part.endswith("_arm"):
            width = 3
        for origin, name in ((base, part), (outer, outer_name)):
            for face, (u, v, end_u, end_v) in face_boxes(origin, width, height, depth).items():
                key = f"{name}.{face}"
                pattern = maps.pop(key, None)
                w, h = end_u-u, end_v-v
                if pattern is not None and (len(pattern) != h or any(len(row) != w for row in pattern)):
                    raise ValueError(f"{npc_id} {key}: expected {h} rows of {w} texels")
                if pattern is not None:
                    unknown = set("".join(pattern)).difference(palette, ".")
                    if unknown:
                        raise ValueError(f"{npc_id} {key}: undefined palette keys {sorted(unknown)}")
                for y in range(h):
                    for x in range(w):
                        mark = pattern[y][x] if pattern is not None else "."
                        if mark != ".":
                            rgb = palette[mark]
                        elif name == part:
                            edge = fabric_edge(patterns, part, face, x, y, w)
                            color = material(part, face, x, y, w) if edge in (None, ".") else edge
                            rgb = shade(palette[color], face, x, y)
                        else:
                            continue
                        image.putpixel((u+x, v+y), (*rgb, 255))
    if maps:
        raise ValueError(f"{npc_id}: unknown face maps {sorted(maps)}")
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check committed PNG pixels without writing")
    args = parser.parse_args()
    if not args.check:
        TARGET.mkdir(parents=True, exist_ok=True)
    for npc_id, spec in SKINS.items():
        fresh = draw_skin(npc_id, spec)
        target = TARGET / f"{npc_id}.png"
        if args.check:
            if not target.is_file():
                parser.exit(1, f"Missing skin: {target}\n")
            with Image.open(target) as saved:
                if saved.mode != "RGBA" or saved.size != fresh.size or saved.tobytes() != fresh.tobytes():
                    parser.exit(1, f"Stale skin: {target}\n")
        else:
            fresh.save(target)
    action = "Checked" if args.check else "Wrote"
    print(f"{action} {len(SKINS)} skins in {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
