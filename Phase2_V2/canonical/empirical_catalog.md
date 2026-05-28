# Empirical Primitive Catalog

Derived from static analysis of **739 canonical solvers** in `canonical/solvers/`.

Each cluster groups solvers that share a structural feature signature (BFS, 4- vs 8-connectivity, flood-from-border, ray tracing, bbox, period, flip, fractal, etc.). Clusters approximate the **empirical primitives real ARC uses** — no assumption about what should exist, derived from the code.

Detection is by substring/regex match. Approximate but stable; mis-matches should be rare and self-flagging (puzzles in the tail).

---

## Stats

- Total solvers analyzed:           **739**
- Distinct feature signatures:      **109**
- HEAD primitive clusters (≥2):     **54** covering **462** puzzles (62.5%)
- UNCLUSTERED (no detected struct): **223** puzzles (30.2%) — hand-crafted or analyzer-missed
- TAIL (unique signature, 1 puzzle):**54** puzzles (7.3%) — candidate new primitives or rare patterns

---

## HEAD — shared primitives

_54 clusters covering 462 puzzles._

### `BG_COUNTER`  —  **98** puzzles
**Features**: `BG_COUNTER`

**Puzzles**: 06df4c85, 0962bcdd, 0f63c0b9, 11dc524f, 11e1fe23, 1a07d186, 1a244afd, 1bfc4729, 1c56ad9f, 1caeab9d, 1e0a9b12, 1f876c06, 22eb0ac0, 25ff71a9, 2601afb7, 29700607, 29c11459, 2a28add5, 30f42897, 32e9702f, 332202d5, 332efdb3, 342dd610, 37ce87bb, 3a301edc … (+73 more)

### `CONN4_TUPLE+STACK_DFS`  —  **44** puzzles
**Features**: `CONN4_TUPLE, STACK_DFS`

**Puzzles**: 09c534e7, 22a4bbc2, 2f767503, 33b52de3, 36a08778, 3aa6fb7a, 3bd292e8, 3d588dc9, 40f6cd08, 4364c1c4, 50cb2852, 516b51b7, 52fd389e, 54d9e175, 5ffb2104, 639f5a19, 6455b5f5, 67385a82, 694f12f3, 6ad5bdfd, 84f2aca1, 868de0fa, 890034e9, 8a371977, 95990924 … (+19 more)

### `BG_COUNTER+COUNTER_LIB`  —  **37** puzzles
**Features**: `BG_COUNTER, COUNTER_LIB`

**Puzzles**: 0607ce86, 195c6913, 1e97544e, 4093f84a, 5a719d11, 5b37cb25, 5b692c0f, 60d73be6, 66ac4c3b, 73251a56, 7d7772cc, 7e576d6e, 7ec998c9, 84ba50d3, 92e50de0, 95a58926, 981add89, 984d8a3e, 9b30e358, 9bbf930d, 9def23fe, a096bf4d, ac0c2ac3, b5ca7ac4, b99e7126 … (+12 more)

### `STACK_DFS`  —  **35** puzzles
**Features**: `STACK_DFS`

**Puzzles**: 14754a24, 15663ba9, 17829a00, 18419cfa, 20981f0e, 256b0a75, 2b9ef948, 2c737e39, 305b1341, 3e980e27, 42a50994, 444801d8, 44d8ac46, 47996f11, 4e469f39, 60b61512, 64a7c07e, 72322fa7, 7acdf6d3, 810b9b61, 8fbca751, 929ab4e9, 963c33f8, a04b2602, a834deea … (+10 more)

### `BG_COUNTER+CONN4_TUPLE+STACK_DFS`  —  **29** puzzles
**Features**: `BG_COUNTER, CONN4_TUPLE, STACK_DFS`

**Puzzles**: 00dbd492, 08ed6ac7, 12eac192, 1efba499, 41e4d17e, 4347f46a, 45737921, 46c35fc7, 52364a65, 543a7ed5, 54d82841, 5521c0d9, 5623160b, 6ca952ad, 6e82a1ae, 7447852a, 8cb8642d, 985ae207, 9f669b64, ad38a9d0, b27ca6d3, b2bc3ffd, b7256dcd, d93c6891, d968ffd4 … (+4 more)

### `RAY_STEP`  —  **15** puzzles
**Features**: `RAY_STEP`

**Puzzles**: 08573cc6, 1d398264, 212895b5, 5c0a986e, 692cd3b6, 6ffe8f07, 95755ff2, 9f8de559, ae3edfdc, bcb3040b, c074846d, d06dbe63, da515329, e5c44e8f, f8be4b64

### `BBOX`  —  **12** puzzles
**Features**: `BBOX`

**Puzzles**: 05f2a901, 11852cab, 4938f0c2, 56dc2b01, 60a26a3e, 6d75e8bb, 760b3cac, 94414823, a1570a43, a48eeaf7, bb52a14b, d6e50e54

### `CONN4_TUPLE+QUEUE_BFS`  —  **10** puzzles
**Features**: `CONN4_TUPLE, QUEUE_BFS`

**Puzzles**: 0a2355a6, 0d87d2a6, 28a6681f, 6e453dd6, 9edfc990, aa4ec2a5, c3fa4749, cbebaa4b, cc9053aa, e69241bd

### `COUNTER_LIB`  —  **10** puzzles
**Features**: `COUNTER_LIB`

**Puzzles**: 2de01db2, 31aa019c, 3345333e, 4e7e0eb9, 52df9849, 6cdd2623, 9caf5b84, ad3b40cf, bd283c4a, e3fe1151

### `BG_COUNTER+CONN4_TUPLE+COUNTER_LIB+STACK_DFS`  —  **9** puzzles
**Features**: `BG_COUNTER, CONN4_TUPLE, COUNTER_LIB, STACK_DFS`

**Puzzles**: 22806e14, 31f7f899, 4b6b68e5, 53fb4810, 78e78cff, 83302e8f, a2d730bd, c4d067a0, edcc2ff0

### `BBOX+BG_COUNTER`  —  **8** puzzles
**Features**: `BBOX, BG_COUNTER`

**Puzzles**: 4a1cacc2, 952a094c, 9caba7c3, 9f27f097, aba27056, b548a754, cfb2ce5a, e7639916

### `CONN4_TUPLE`  —  **7** puzzles
**Features**: `CONN4_TUPLE`

**Puzzles**: 1818057f, 22233c11, 230f2e48, 55059096, 7e02026e, 8886d717, d90796e8

### `BG_COUNTER+STACK_DFS`  —  **7** puzzles
**Features**: `BG_COUNTER, STACK_DFS`

**Puzzles**: 22168020, 4df5b0ae, c6141b15, d43fd935, d5d6de2d, d753a70b, fd096ab6

### `COL_SETTLE+STACK_DFS`  —  **7** puzzles
**Features**: `COL_SETTLE, STACK_DFS`

**Puzzles**: 3490cc26, 3ad05f52, 4ff4c9da, 99caaf76, ac2e8ecf, f1bcbc2c, f341894c

### `CONN4_TUPLE+CONN8_TUPLE+STACK_DFS`  —  **6** puzzles
**Features**: `CONN4_TUPLE, CONN8_TUPLE, STACK_DFS`

**Puzzles**: 025d127b, 1e5d6875, 37d3e8b2, 54db823b, e509e548, f3e62deb

### `BG_COUNTER+COUNTER_LIB+STACK_DFS`  —  **6** puzzles
**Features**: `BG_COUNTER, COUNTER_LIB, STACK_DFS`

**Puzzles**: 13f06aa5, 34cfa167, 79fb03f4, 8f215267, 981571dc, a09f6c25

### `BG_COUNTER+COUNTER_LIB+QUEUE_BFS`  —  **6** puzzles
**Features**: `BG_COUNTER, COUNTER_LIB, QUEUE_BFS`

**Puzzles**: 184a9768, 1b59e163, 50846271, 6e4f6532, 7b0280bc, b7955b3c

### `QUEUE_BFS`  —  **6** puzzles
**Features**: `QUEUE_BFS`

**Puzzles**: 3391f8c0, 36d67576, 447fd412, bc93ec48, c62e2108, dc2e9a9d

### `COL_SETTLE+CONN4_TUPLE+STACK_DFS`  —  **5** puzzles
**Features**: `COL_SETTLE, CONN4_TUPLE, STACK_DFS`

**Puzzles**: 03560426, 2e65ae53, 54dc2872, 88207623, c6e1b8da

### `MOD_PERIOD`  —  **5** puzzles
**Features**: `MOD_PERIOD`

**Puzzles**: 0dfd9992, 29ec7d0e, c663677b, ca8f78db, e95e3d8e

### `BG_COUNTER+COL_SETTLE+CONN4_TUPLE+COUNTER_LIB+STACK_DFS`  —  **5** puzzles
**Features**: `BG_COUNTER, COL_SETTLE, CONN4_TUPLE, COUNTER_LIB, STACK_DFS`

**Puzzles**: 135a2760, 3e6067c3, 446ef5d2, b7f8a4d8, e681b708

### `BG_COUNTER+CONN4_TUPLE+COUNTER_LIB+QUEUE_BFS`  —  **5** puzzles
**Features**: `BG_COUNTER, CONN4_TUPLE, COUNTER_LIB, QUEUE_BFS`

**Puzzles**: 13e47133, 67c52801, 800d221b, 9b5080bb, e4888269

### `ray_tracing`  —  **5** puzzles
**Features**: `BG_COUNTER, RAY_STEP`

**Puzzles**: 1478ab18, 252143c9, 25d487eb, 623ea044, db695cfb

### `BG_COUNTER+CONN4_TUPLE+CONN8_TUPLE+STACK_DFS`  —  **5** puzzles
**Features**: `BG_COUNTER, CONN4_TUPLE, CONN8_TUPLE, STACK_DFS`

**Puzzles**: 22208ba4, 7f4411dc, 8e301a54, f21745ec, fe45cba4

### `CONN8_TUPLE`  —  **4** puzzles
**Features**: `CONN8_TUPLE`

**Puzzles**: 0ca9ddb6, 57aa92db, a9f96cdd, fd4b2b02

### `BG_COUNTER+CONN4_TUPLE`  —  **4** puzzles
**Features**: `BG_COUNTER, CONN4_TUPLE`

**Puzzles**: 14b8e18c, 5792cb4d, 97c75046, e73095fd

### `BG_COUNTER+COUNTER_LIB+MOD_PERIOD`  —  **4** puzzles
**Features**: `BG_COUNTER, COUNTER_LIB, MOD_PERIOD`

**Puzzles**: 1d0a4b61, 484b58aa, ea959feb, f823c43c

### `FROZENSET_KEY+STACK_DFS`  —  **4** puzzles
**Features**: `FROZENSET_KEY, STACK_DFS`

**Puzzles**: 2a5f8217, 604001fa, 776ffc46, 845d6e51

### `BBOX+BG_COUNTER+CONN4_TUPLE+STACK_DFS`  —  **4** puzzles
**Features**: `BBOX, BG_COUNTER, CONN4_TUPLE, STACK_DFS`

**Puzzles**: 2c608aff, 465b7d93, 8dae5dfc, df9fd884

### `CONN4_TUPLE+CONN8_TUPLE+QUEUE_BFS`  —  **4** puzzles
**Features**: `CONN4_TUPLE, CONN8_TUPLE, QUEUE_BFS`

**Puzzles**: 2faf500b, 477d2879, 6855a6e4, 880c1354

### `DIAG_RESIDUE`  —  **3** puzzles
**Features**: `DIAG_RESIDUE`

**Puzzles**: 05269061, c3f564a4, e9afcf9a

### `BG_COUNTER+CONN8_TUPLE`  —  **3** puzzles
**Features**: `BG_COUNTER, CONN8_TUPLE`

**Puzzles**: 140c817e, 396d80d7, e12f9a14

### `COL_SETTLE+CONN4_TUPLE+CONN8_TUPLE+STACK_DFS`  —  **3** puzzles
**Features**: `COL_SETTLE, CONN4_TUPLE, CONN8_TUPLE, STACK_DFS`

**Puzzles**: 182e5d0f, 9772c176, a57f2f04

### `CONN4_TUPLE+RAY_STEP+STACK_DFS`  —  **3** puzzles
**Features**: `CONN4_TUPLE, RAY_STEP, STACK_DFS`

**Puzzles**: 292dd178, 551d5bf1, 696d4842

### `BG_COUNTER+COL_SETTLE+STACK_DFS`  —  **3** puzzles
**Features**: `BG_COUNTER, COL_SETTLE, STACK_DFS`

**Puzzles**: 3befdf3e, 93c31fbe, df978a02

### `BBOX+BG_COUNTER+COUNTER_LIB`  —  **3** puzzles
**Features**: `BBOX, BG_COUNTER, COUNTER_LIB`

**Puzzles**: 58c02a16, 917bccba, f8cc533f

### `BG_COUNTER+COL_SETTLE+COUNTER_LIB+FROZENSET_KEY+STACK_DFS`  —  **3** puzzles
**Features**: `BG_COUNTER, COL_SETTLE, COUNTER_LIB, FROZENSET_KEY, STACK_DFS`

**Puzzles**: 62593bfd, c7f57c3e, d6542281

### `CONN4_TUPLE+RAY_STEP`  —  **3** puzzles
**Features**: `CONN4_TUPLE, RAY_STEP`

**Puzzles**: 9bebae7a, b527c5c6, c9680e90

### `TUPLE_NORMALIZE`  —  **2** puzzles
**Features**: `TUPLE_NORMALIZE`

**Puzzles**: 009d5c81, 142ca369

### `BG_COUNTER+BORDER_LOOP+CONN4_TUPLE+STACK_DFS`  —  **2** puzzles
**Features**: `BG_COUNTER, BORDER_LOOP, CONN4_TUPLE, STACK_DFS`

**Puzzles**: 00d62c1b, a5313dff

### `FROZENSET_KEY`  —  **2** puzzles
**Features**: `FROZENSET_KEY`

**Puzzles**: 150deff5, 17cae0c1

### `CONN8_TUPLE+STACK_DFS`  —  **2** puzzles
**Features**: `CONN8_TUPLE, STACK_DFS`

**Puzzles**: 1d61978c, 896d5239

### `BG_COUNTER+MAX_BY_LEN+STACK_DFS`  —  **2** puzzles
**Features**: `BG_COUNTER, MAX_BY_LEN, STACK_DFS`

**Puzzles**: 1da012fc, 90f3ed37

### `BBOX+CONN4_TUPLE+STACK_DFS`  —  **2** puzzles
**Features**: `BBOX, CONN4_TUPLE, STACK_DFS`

**Puzzles**: 1e81d6f9, 3bdb4ada

### `COL_SETTLE+CONN4_TUPLE+RAY_STEP+STACK_DFS`  —  **2** puzzles
**Features**: `COL_SETTLE, CONN4_TUPLE, RAY_STEP, STACK_DFS`

**Puzzles**: 342ae2ed, 689c358e

### `HFLIP_IDX+VFLIP_IDX`  —  **2** puzzles
**Features**: `HFLIP_IDX, VFLIP_IDX`

**Puzzles**: 3c9b0459, 6150a2bd

### `BBOX+FROZENSET_KEY`  —  **2** puzzles
**Features**: `BBOX, FROZENSET_KEY`

**Puzzles**: 50f325b5, 7df24a62

### `BG_COUNTER+CONN4_TUPLE+COUNTER_LIB`  —  **2** puzzles
**Features**: `BG_COUNTER, CONN4_TUPLE, COUNTER_LIB`

**Puzzles**: 538b439f, 88bcf3b4

### `ROT90_IDX+VFLIP_IDX`  —  **2** puzzles
**Features**: `ROT90_IDX, VFLIP_IDX`

**Puzzles**: 68b16354, a8610ef7

### `BORDER_LOOP+CONN4_TUPLE+STACK_DFS`  —  **2** puzzles
**Features**: `BORDER_LOOP, CONN4_TUPLE, STACK_DFS`

**Puzzles**: 7b6016b9, 84db8fc4

### `BG_COUNTER+COL_SETTLE+CONN4_TUPLE+CONN8_TUPLE+STACK_DFS`  —  **2** puzzles
**Features**: `BG_COUNTER, COL_SETTLE, CONN4_TUPLE, CONN8_TUPLE, STACK_DFS`

**Puzzles**: 7d1f7ee8, b745798f

### `COL_SETTLE+FROZENSET_KEY+STACK_DFS`  —  **2** puzzles
**Features**: `COL_SETTLE, FROZENSET_KEY, STACK_DFS`

**Puzzles**: 94be5b80, b20f7c8b

### `BG_COUNTER+CONN8_TUPLE+STACK_DFS`  —  **2** puzzles
**Features**: `BG_COUNTER, CONN8_TUPLE, STACK_DFS`

**Puzzles**: aa18de87, f0100645

### `BG_COUNTER+CONN8_TUPLE+COUNTER_LIB+RAY_STEP`  —  **2** puzzles
**Features**: `BG_COUNTER, CONN8_TUPLE, COUNTER_LIB, RAY_STEP`

**Puzzles**: d07ae81c, ec883f72

---

## UNCLUSTERED — no structural features detected

_223 puzzles. These solvers don't use the patterns the analyzer recognizes (BFS, ray, bbox, mirror, period, fractal, etc.). Could be:_
_- bespoke per-puzzle rules (real tail of the substrate)_
_- patterns the analyzer missed (refine features and re-run)_

<details><summary>223 puzzles</summary>

- `045e512c`
- `05a7bcf2`
- `070dd51e`
- `09629e4f`
- `0a938d79`
- `0b17323b`
- `0becf7df`
- `0d3d703e`
- `0e671a1a`
- `103eff5b`
- `12422b43`
- `13713586`
- `137f0df0`
- `15113be4`
- `178fcbfb`
- `17b80ad2`
- `17b866bd`
- `18286ef8`
- `1b60fb0c`
- `1c02dbbe`
- `1c0d0a4b`
- `1e32b0e9`
- `1f0c79e5`
- `1f642eb9`
- `21f83797`
- `2204b7a8`
- `2281f1f4`
- `23581191`
- `25094a63`
- `253bf280`
- `2546ccf6`
- `25d8a9c8`
- `2685904e`
- `272f95fa`
- `27a77e38`
- `28e73c20`
- `29623171`
- `2b01abd0`
- `2bcee788`
- `2dd70a9a`
- `319f2597`
- `31adaf00`
- `32597951`
- `35ab12c3`
- `3618c87e`
- `3631a71a`
- `363442ee`
- `36fdfd69`
- `3906de3d`
- `3ac3eb23`
- `3bd67248`
- `3d6c6e23`
- `3eda0437`
- `3f23242b`
- `41ace6b5`
- `423a55dc`
- `4258a5f9`
- `42918530`
- `42a15761`
- `456873bc`
- `45bbe264`
- `4612dd53`
- `470c91de`
- `48634b99`
- `494ef9d7`
- `4aab4007`
- `4cd1b7b2`
- `4e45f183`
- `508bd3b6`
- `50a16a69`
- `5168d44c`
- `5207a7b5`
- `5582e5ca`
- `575b1a71`
- `58e15b12`
- `5a5a2103`
- `5b526a93`
- `5c2c9af4`
- `5e6bbc0b`
- `626c0bcc`
- `62b74c02`
- `6350f1f4`
- `642248e4`
- `673ef223`
- `69889d6e`
- `6a980be1`
- `6bcdb01e`
- `6c434453`
- `6cf79266`
- `6d0160f0`
- `6df30ad6`
- `6e02f1e3`
- `6ea4a07e`
- `6f8cd79b`
- `712bf12e`
- `72207abc`
- `72a961c9`
- `73c3b0d8`
- `74dd1130`
- `758abdf0`
- `759f3fd3`
- `762cd429`
- `770cc55f`
- `782b5218`
- `79369cc6`
- `7c8af763`
- `7d419a02`
- `7e2bad24`
- `7ee1c6ea`
- `817e6c09`
- `833966f4`
- `834ec97d`
- `8403a5d5`
- `84551f4c`
- `855e0971`
- `85c4e7cd`
- `891232d6`
- `8d510a79`
- `8dab14c2`
- `8e5a5113`
- `8eb1be9a`
- `8ee62060`
- `8f2ea7aa`
- `903d1b4a`
- `913fb3ed`
- `91714a58`
- `928ad970`
- `9356391f`
- `93b581b8`
- `941d9a10`
- `963f59bc`
- `96a8c0cd`
- `97239e3d`
- `97999447`
- `97d7923e`
- `98c475bf`
- `992798f6`
- `9b365c51`
- `9c56f360`
- `9d9215db`
- `9ddd00f0`
- `9f41bd9c`
- `9f5f939b`
- `a2fd1cf0`
- `a3df8b1e`
- `a3f84088`
- `a406ac07`
- `a5f85a15`
- `a61f2674`
- `a64e4611`
- `a65b410d`
- `a699fb00`
- `a78176bb`
- `a79310a0`
- `a8d7556c`
- `aa300dc3`
- `ac3e2b04`
- `ac605cbb`
- `ad173014`
- `af22c60d`
- `af902bf9`
- `b1948b0a`
- `b60334d2`
- `b7249182`
- `b7fb29bc`
- `b8825c91`
- `ba97ae07`
- `baf41dbf`
- `bd4472b8`
- `bda2d7a6`
- `bdad9b1f`
- `bf89d739`
- `c444b776`
- `c87289bb`
- `c8f0f002`
- `c9f8e694`
- `caa06a1f`
- `ce039d91`
- `ce9e57f2`
- `cf133acc`
- `d037b0a7`
- `d23f8c26`
- `d2acf2cb`
- `d364b489`
- `d406998b`
- `d492a647`
- `d4a91cb9`
- `d511f180`
- `d94c3b52`
- `d9f24cd1`
- `db0c5428`
- `db3e9e38`
- `db7260a4`
- `dbc1a6ce`
- `dc1df850`
- `dd2401ed`
- `e048c9ed`
- `e179c5f4`
- `e2092e0c`
- `e21a174a`
- `e40b9e2f`
- `e45ef808`
- `e5790162`
- `e74e1818`
- `e7b06bea`
- `e9bb6954`
- `e9c9d9a1`
- `ecdecbb3`
- `ed36ccf7`
- `ef26cbf6`
- `f0df5ff0`
- `f15e1fac`
- `f1cefba8`
- `f35d900a`
- `f3cdc58f`
- `f5c89df1`
- `f76d97a5`
- `f8a8fe49`
- `f9a67cb5`
- `f9d67f8b`
- `fcc82909`
- `ff2825db`
- `ff72ca3e`

</details>

---

## TAIL — unique signatures (your review queue)

_54 puzzles with a structural signature unique to them. Each is a candidate new primitive, or a rare composition. Review each, decide._

- `0e206a2e` — features: `BG_COUNTER, COUNTER_LIB, FROZENSET_KEY, STACK_DFS`
- `1190bc91` — features: `COL_SETTLE, CONN4_TUPLE, MAX_BY_LEN, QUEUE_BFS, ROT90_IDX, STACK_DFS`
- `16b78196` — features: `BBOX, CONN4_TUPLE, FROZENSET_KEY, ROT90_IDX, VFLIP_IDX`
- `18447a8d` — features: `BG_COUNTER, FROZENSET_KEY`
- `1acc24af` — features: `BBOX, CONN4_TUPLE, FROZENSET_KEY, STACK_DFS`
- `228f6490` — features: `CONN4_TUPLE, COUNTER_LIB, FROZENSET_KEY, STACK_DFS`
- `264363fd` — features: `BG_COUNTER, COL_SETTLE, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, STACK_DFS`
- `2bee17df` — features: `ROT90_IDX`
- `320afe60` — features: `BG_COUNTER, CONN4_TUPLE, QUEUE_BFS, STACK_DFS`
- `321b1fc6` — features: `BG_COUNTER, CONN4_TUPLE, FROZENSET_KEY, STACK_DFS`
- `39e1d7f9` — features: `MAX_BY_LEN, STACK_DFS`
- `3ed85e70` — features: `BBOX, STACK_DFS`
- `4acc7107` — features: `BBOX, QUEUE_BFS`
- `4c416de3` — features: `BG_COUNTER, COL_SETTLE, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, MAX_BY_LEN, STACK_DFS`
- `4c5c2cf0` — features: `CONN8_TUPLE, FROZENSET_KEY`
- `522fdd07` — features: `BG_COUNTER, COL_SETTLE, CONN4_TUPLE, STACK_DFS`
- `55783887` — features: `BG_COUNTER, COUNTER_LIB, RAY_STEP`
- `5adee1b2` — features: `CONN4_TUPLE, CONN8_TUPLE, QUEUE_BFS, STACK_DFS`
- `5af49b42` — features: `BORDER_LOOP`
- `62ab2642` — features: `CONN4_TUPLE, MAX_BY_LEN, STACK_DFS`
- `63613498` — features: `COUNTER_LIB, FROZENSET_KEY, STACK_DFS`
- `67a3c6ac` — features: `HFLIP_IDX`
- `6a1e5592` — features: `BBOX, FROZENSET_KEY, STACK_DFS`
- `6aa20dc0` — features: `BG_COUNTER, COL_SETTLE, COUNTER_LIB, STACK_DFS`
- `6d58a25d` — features: `COUNTER_LIB, STACK_DFS`
- `6e19193c` — features: `CONN4_TUPLE, CONN8_TUPLE, RAY_STEP, STACK_DFS`
- `753ea09b` — features: `BG_COUNTER, CONN4_TUPLE, MAX_BY_LEN, QUEUE_BFS`
- `7ddcd7ec` — features: `BBOX, BG_COUNTER, CONN8_TUPLE, RAY_STEP`
- `825aa9e9` — features: `CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, STACK_DFS`
- `85fa5666` — features: `CONN8_TUPLE, RAY_STEP`
- `8e5c0c38` — features: `BG_COUNTER, CONN8_TUPLE, COUNTER_LIB, FROZENSET_KEY, STACK_DFS`
- `902510d5` — features: `BG_COUNTER, COUNTER_LIB, MAX_BY_LEN, STACK_DFS`
- `9720b24f` — features: `BG_COUNTER, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, QUEUE_BFS`
- `9b2a60aa` — features: `CONN4_TUPLE, CONN8_TUPLE, MAX_BY_LEN, STACK_DFS`
- `9b4c17c4` — features: `CONN4_TUPLE, QUEUE_BFS, STACK_DFS`
- `a395ee82` — features: `BG_COUNTER, COUNTER_LIB, GCD, MAX_BY_LEN, STACK_DFS`
- `aa62e3f4` — features: `BORDER_LOOP, CONN4_TUPLE, QUEUE_BFS`
- `ac0c5833` — features: `BBOX, COL_SETTLE, STACK_DFS`
- `b15fca0b` — features: `BG_COUNTER, CONN4_TUPLE, QUEUE_BFS`
- `b230c067` — features: `CONN4_TUPLE, CONN8_TUPLE, FROZENSET_KEY, STACK_DFS, TUPLE_NORMALIZE`
- `b74ca5d1` — features: `BG_COUNTER, COUNTER_LIB, FROZENSET_KEY`
- `b782dc8a` — features: `CONN4_TUPLE, DIAG_RESIDUE, QUEUE_BFS`
- `b942fd60` — features: `QUEUE_BFS, RAY_STEP`
- `b9630600` — features: `CONN4_TUPLE, CONN8_TUPLE, TUPLE_NORMALIZE`
- `d4f3cd78` — features: `BBOX, BG_COUNTER, RAY_STEP`
- `dd6b8c4b` — features: `BG_COUNTER, BORDER_LOOP, CONN4_TUPLE, COUNTER_LIB, QUEUE_BFS, STACK_DFS`
- `df8cc377` — features: `BG_COUNTER, CONN4_TUPLE, CONN8_TUPLE, COUNTER_LIB, STACK_DFS`
- `e5062a87` — features: `BG_COUNTER, CONN4_TUPLE, FROZENSET_KEY`
- `e76a88a6` — features: `BG_COUNTER, CONN4_TUPLE, MAX_BY_LEN, STACK_DFS`
- `ecb67b6d` — features: `BG_COUNTER, RAY_STEP, STACK_DFS`
- `f3b10344` — features: `BG_COUNTER, FROZENSET_KEY, STACK_DFS`
- `f8f52ecc` — features: `BG_COUNTER, TUPLE_NORMALIZE`
- `fafd9572` — features: `BBOX, BG_COUNTER, CONN4_TUPLE, CONN8_TUPLE, MAX_BY_LEN, STACK_DFS`
- `fe9372f3` — features: `CONN4_TUPLE, CONN8_TUPLE`
