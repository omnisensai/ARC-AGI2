# T-Signature Catalog

Clustering of **740 canonical puzzles** by their T-GRID PATTERN (input → output diff), not by solver code style.

**Same operation = same T-signature**, regardless of code, colors, grid size, or positions. Invariants (`.`) are ignored by construction.

Signature schema: `(size_change, density, polarity, topology, n_components)`

- **size_change**: SAME / DIFF_SIZE  (output dims same as input or different)
- **density**: % of cells changed — NO_CHANGE / TINY / SPARSE / MEDIUM / DENSE / TOTAL
- **polarity**: ADD (bg→colour) / REMOVE (colour→bg) / RECOLOR / MOVE (add+remove) / MIXED
- **topology**: connected-component shape of changed cells — ONE_BLOB / FEW_BLOBS / MULTI_BLOBS / ISOLATED_CELLS / MANY_SCATTERED / EMPTY
- **n_components**: 0 / 1 / 2-3 / 4-8 / 9+

---

## Stats

- Puzzles analyzed: **740**
- Distinct T-signatures: **100**
- Head (clusters ≥ 2):  **72** clusters covering **712** puzzles (96.2%)
- Tail (1 puzzle):      **28** puzzles (3.8%)

---

## Clusters (largest first) — each annotated with likely L1 composition

### `(SAME | MEDIUM | ADD | ONE_BLOB | 1)` — 48 puzzles

**Likely L1 primitives**:
  - fill_enclosed
  - flood_from_seed
  - u_cup_fill

**Puzzles**: [`12422b43`](https://arcprize.org/tasks/12422b43), [`1478ab18`](https://arcprize.org/tasks/1478ab18), [`1b60fb0c`](https://arcprize.org/tasks/1b60fb0c), [`1c02dbbe`](https://arcprize.org/tasks/1c02dbbe), [`1f0c79e5`](https://arcprize.org/tasks/1f0c79e5), [`29700607`](https://arcprize.org/tasks/29700607), [`29c11459`](https://arcprize.org/tasks/29c11459), [`2bee17df`](https://arcprize.org/tasks/2bee17df), [`3a301edc`](https://arcprize.org/tasks/3a301edc), [`3ad05f52`](https://arcprize.org/tasks/3ad05f52), [`3eda0437`](https://arcprize.org/tasks/3eda0437), [`3f23242b`](https://arcprize.org/tasks/3f23242b), [`447fd412`](https://arcprize.org/tasks/447fd412), [`496994bd`](https://arcprize.org/tasks/496994bd), [`4a1cacc2`](https://arcprize.org/tasks/4a1cacc2), [`4e469f39`](https://arcprize.org/tasks/4e469f39), [`56ff96f3`](https://arcprize.org/tasks/56ff96f3), [`692cd3b6`](https://arcprize.org/tasks/692cd3b6), [`69889d6e`](https://arcprize.org/tasks/69889d6e), [`6bcdb01e`](https://arcprize.org/tasks/6bcdb01e), [`770cc55f`](https://arcprize.org/tasks/770cc55f), [`79fb03f4`](https://arcprize.org/tasks/79fb03f4), [`913fb3ed`](https://arcprize.org/tasks/913fb3ed), [`928ad970`](https://arcprize.org/tasks/928ad970), [`94414823`](https://arcprize.org/tasks/94414823) … (+23 more)

### `(SAME | MEDIUM | MOVE | MULTI_BLOBS | 4-8)` — 38 puzzles

**Likely L1 primitives**:
  - gravity_water (per-column)
  - ball_roll
  - move_to_marker × many

**Puzzles**: [`16b78196`](https://arcprize.org/tasks/16b78196), [`1caeab9d`](https://arcprize.org/tasks/1caeab9d), [`22208ba4`](https://arcprize.org/tasks/22208ba4), [`228f6490`](https://arcprize.org/tasks/228f6490), [`230f2e48`](https://arcprize.org/tasks/230f2e48), [`2601afb7`](https://arcprize.org/tasks/2601afb7), [`2faf500b`](https://arcprize.org/tasks/2faf500b), [`320afe60`](https://arcprize.org/tasks/320afe60), [`3391f8c0`](https://arcprize.org/tasks/3391f8c0), [`423a55dc`](https://arcprize.org/tasks/423a55dc), [`4364c1c4`](https://arcprize.org/tasks/4364c1c4), [`5034a0b5`](https://arcprize.org/tasks/5034a0b5), [`5623160b`](https://arcprize.org/tasks/5623160b), [`6a1e5592`](https://arcprize.org/tasks/6a1e5592), [`6ca952ad`](https://arcprize.org/tasks/6ca952ad), [`6e453dd6`](https://arcprize.org/tasks/6e453dd6), [`6e4f6532`](https://arcprize.org/tasks/6e4f6532), [`84551f4c`](https://arcprize.org/tasks/84551f4c), [`84ba50d3`](https://arcprize.org/tasks/84ba50d3), [`8e301a54`](https://arcprize.org/tasks/8e301a54), [`902510d5`](https://arcprize.org/tasks/902510d5), [`984d8a3e`](https://arcprize.org/tasks/984d8a3e), [`9b4c17c4`](https://arcprize.org/tasks/9b4c17c4), [`9bebae7a`](https://arcprize.org/tasks/9bebae7a), [`a1570a43`](https://arcprize.org/tasks/a1570a43) … (+13 more)

### `(SAME | MEDIUM | ADD | FEW_BLOBS | 2-3)` — 36 puzzles

**Likely L1 primitives**:
  - copy_to_markers (2-3 markers)
  - frame_around_seed × few
  - cross_from_seed × few
  - sandwich_fill (few pairs)

**Puzzles**: [`00dbd492`](https://arcprize.org/tasks/00dbd492), [`08573cc6`](https://arcprize.org/tasks/08573cc6), [`0e671a1a`](https://arcprize.org/tasks/0e671a1a), [`22168020`](https://arcprize.org/tasks/22168020), [`22eb0ac0`](https://arcprize.org/tasks/22eb0ac0), [`292dd178`](https://arcprize.org/tasks/292dd178), [`30f42897`](https://arcprize.org/tasks/30f42897), [`34cfa167`](https://arcprize.org/tasks/34cfa167), [`52fd389e`](https://arcprize.org/tasks/52fd389e), [`5adee1b2`](https://arcprize.org/tasks/5adee1b2), [`62ab2642`](https://arcprize.org/tasks/62ab2642), [`6d75e8bb`](https://arcprize.org/tasks/6d75e8bb), [`712bf12e`](https://arcprize.org/tasks/712bf12e), [`73c3b0d8`](https://arcprize.org/tasks/73c3b0d8), [`7447852a`](https://arcprize.org/tasks/7447852a), [`7ec998c9`](https://arcprize.org/tasks/7ec998c9), [`82819916`](https://arcprize.org/tasks/82819916), [`868de0fa`](https://arcprize.org/tasks/868de0fa), [`90f3ed37`](https://arcprize.org/tasks/90f3ed37), [`97999447`](https://arcprize.org/tasks/97999447), [`985ae207`](https://arcprize.org/tasks/985ae207), [`9ddd00f0`](https://arcprize.org/tasks/9ddd00f0), [`a65b410d`](https://arcprize.org/tasks/a65b410d), [`b527c5c6`](https://arcprize.org/tasks/b527c5c6), [`b782dc8a`](https://arcprize.org/tasks/b782dc8a) … (+11 more)

### `(SAME | MEDIUM | ADD | MULTI_BLOBS | 4-8)` — 32 puzzles

**Likely L1 primitives**:
  - copy_to_markers × many
  - frame_around_seed × many
  - cross/star_from_seed × many

**Puzzles**: [`05a7bcf2`](https://arcprize.org/tasks/05a7bcf2), [`13f06aa5`](https://arcprize.org/tasks/13f06aa5), [`17b80ad2`](https://arcprize.org/tasks/17b80ad2), [`31adaf00`](https://arcprize.org/tasks/31adaf00), [`3490cc26`](https://arcprize.org/tasks/3490cc26), [`41e4d17e`](https://arcprize.org/tasks/41e4d17e), [`444801d8`](https://arcprize.org/tasks/444801d8), [`45bbe264`](https://arcprize.org/tasks/45bbe264), [`4938f0c2`](https://arcprize.org/tasks/4938f0c2), [`4b6b68e5`](https://arcprize.org/tasks/4b6b68e5), [`538b439f`](https://arcprize.org/tasks/538b439f), [`551d5bf1`](https://arcprize.org/tasks/551d5bf1), [`5b526a93`](https://arcprize.org/tasks/5b526a93), [`5c2c9af4`](https://arcprize.org/tasks/5c2c9af4), [`673ef223`](https://arcprize.org/tasks/673ef223), [`6ffe8f07`](https://arcprize.org/tasks/6ffe8f07), [`753ea09b`](https://arcprize.org/tasks/753ea09b), [`95755ff2`](https://arcprize.org/tasks/95755ff2), [`97239e3d`](https://arcprize.org/tasks/97239e3d), [`9def23fe`](https://arcprize.org/tasks/9def23fe), [`a04b2602`](https://arcprize.org/tasks/a04b2602), [`a406ac07`](https://arcprize.org/tasks/a406ac07), [`ba26e723`](https://arcprize.org/tasks/ba26e723), [`c62e2108`](https://arcprize.org/tasks/c62e2108), [`c97c0139`](https://arcprize.org/tasks/c97c0139) … (+7 more)

### `(SAME | SPARSE | ADD | FEW_BLOBS | 2-3)` — 30 puzzles

**Likely L1 primitives**:
  - copy_to_markers (2-3 markers)
  - frame_around_seed × few
  - cross_from_seed × few
  - sandwich_fill (few pairs)

**Puzzles**: [`00d62c1b`](https://arcprize.org/tasks/00d62c1b), [`070dd51e`](https://arcprize.org/tasks/070dd51e), [`1e5d6875`](https://arcprize.org/tasks/1e5d6875), [`22233c11`](https://arcprize.org/tasks/22233c11), [`2685904e`](https://arcprize.org/tasks/2685904e), [`2c608aff`](https://arcprize.org/tasks/2c608aff), [`40853293`](https://arcprize.org/tasks/40853293), [`57aa92db`](https://arcprize.org/tasks/57aa92db), [`60a26a3e`](https://arcprize.org/tasks/60a26a3e), [`60b61512`](https://arcprize.org/tasks/60b61512), [`6aa20dc0`](https://arcprize.org/tasks/6aa20dc0), [`6d58a25d`](https://arcprize.org/tasks/6d58a25d), [`760b3cac`](https://arcprize.org/tasks/760b3cac), [`7df24a62`](https://arcprize.org/tasks/7df24a62), [`963f59bc`](https://arcprize.org/tasks/963f59bc), [`9b2a60aa`](https://arcprize.org/tasks/9b2a60aa), [`a2d730bd`](https://arcprize.org/tasks/a2d730bd), [`ac3e2b04`](https://arcprize.org/tasks/ac3e2b04), [`ac605cbb`](https://arcprize.org/tasks/ac605cbb), [`ad3b40cf`](https://arcprize.org/tasks/ad3b40cf), [`b27ca6d3`](https://arcprize.org/tasks/b27ca6d3), [`c0f76784`](https://arcprize.org/tasks/c0f76784), [`d6542281`](https://arcprize.org/tasks/d6542281), [`dc2e9a9d`](https://arcprize.org/tasks/dc2e9a9d), [`ded97339`](https://arcprize.org/tasks/ded97339) … (+5 more)

### `(SAME | SPARSE | ADD | MULTI_BLOBS | 4-8)` — 27 puzzles

**Likely L1 primitives**:
  - copy_to_markers × many
  - frame_around_seed × many
  - cross/star_from_seed × many

**Puzzles**: [`045e512c`](https://arcprize.org/tasks/045e512c), [`2546ccf6`](https://arcprize.org/tasks/2546ccf6), [`36d67576`](https://arcprize.org/tasks/36d67576), [`39e1d7f9`](https://arcprize.org/tasks/39e1d7f9), [`3e6067c3`](https://arcprize.org/tasks/3e6067c3), [`3e980e27`](https://arcprize.org/tasks/3e980e27), [`42918530`](https://arcprize.org/tasks/42918530), [`4612dd53`](https://arcprize.org/tasks/4612dd53), [`4c416de3`](https://arcprize.org/tasks/4c416de3), [`50846271`](https://arcprize.org/tasks/50846271), [`5af49b42`](https://arcprize.org/tasks/5af49b42), [`5b37cb25`](https://arcprize.org/tasks/5b37cb25), [`705a3229`](https://arcprize.org/tasks/705a3229), [`855e0971`](https://arcprize.org/tasks/855e0971), [`88207623`](https://arcprize.org/tasks/88207623), [`9772c176`](https://arcprize.org/tasks/9772c176), [`9841fdad`](https://arcprize.org/tasks/9841fdad), [`992798f6`](https://arcprize.org/tasks/992798f6), [`9caba7c3`](https://arcprize.org/tasks/9caba7c3), [`ac0c5833`](https://arcprize.org/tasks/ac0c5833), [`c444b776`](https://arcprize.org/tasks/c444b776), [`c4d067a0`](https://arcprize.org/tasks/c4d067a0), [`d43fd935`](https://arcprize.org/tasks/d43fd935), [`e40b9e2f`](https://arcprize.org/tasks/e40b9e2f), [`e734a0e8`](https://arcprize.org/tasks/e734a0e8) … (+2 more)

### `(SAME | MEDIUM | RECOLOR | MULTI_BLOBS | 4-8)` — 23 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`08ed6ac7`](https://arcprize.org/tasks/08ed6ac7), [`0dfd9992`](https://arcprize.org/tasks/0dfd9992), [`12eac192`](https://arcprize.org/tasks/12eac192), [`1d0a4b61`](https://arcprize.org/tasks/1d0a4b61), [`1da012fc`](https://arcprize.org/tasks/1da012fc), [`1e97544e`](https://arcprize.org/tasks/1e97544e), [`22a4bbc2`](https://arcprize.org/tasks/22a4bbc2), [`319f2597`](https://arcprize.org/tasks/319f2597), [`321b1fc6`](https://arcprize.org/tasks/321b1fc6), [`6e82a1ae`](https://arcprize.org/tasks/6e82a1ae), [`800d221b`](https://arcprize.org/tasks/800d221b), [`a09f6c25`](https://arcprize.org/tasks/a09f6c25), [`a57f2f04`](https://arcprize.org/tasks/a57f2f04), [`b20f7c8b`](https://arcprize.org/tasks/b20f7c8b), [`bd14c3bf`](https://arcprize.org/tasks/bd14c3bf), [`ce9e57f2`](https://arcprize.org/tasks/ce9e57f2), [`d2abd087`](https://arcprize.org/tasks/d2abd087), [`d6e50e54`](https://arcprize.org/tasks/d6e50e54), [`e0fb7511`](https://arcprize.org/tasks/e0fb7511), [`e509e548`](https://arcprize.org/tasks/e509e548), [`e95e3d8e`](https://arcprize.org/tasks/e95e3d8e), [`e9ac8c9e`](https://arcprize.org/tasks/e9ac8c9e), [`ef26cbf6`](https://arcprize.org/tasks/ef26cbf6)

### `(SAME | MEDIUM | ADD | MANY_SCATTERED | 9+)` — 23 puzzles

**Likely L1 primitives**:
  - ray_to_edge / ray_until_blocker
  - cross/star_from_seed
  - periodic_extension
  - flood_from_seed (large region)

**Puzzles**: [`1d398264`](https://arcprize.org/tasks/1d398264), [`1e32b0e9`](https://arcprize.org/tasks/1e32b0e9), [`212895b5`](https://arcprize.org/tasks/212895b5), [`2281f1f4`](https://arcprize.org/tasks/2281f1f4), [`2e65ae53`](https://arcprize.org/tasks/2e65ae53), [`35ab12c3`](https://arcprize.org/tasks/35ab12c3), [`4c5c2cf0`](https://arcprize.org/tasks/4c5c2cf0), [`58e15b12`](https://arcprize.org/tasks/58e15b12), [`5a5a2103`](https://arcprize.org/tasks/5a5a2103), [`60d73be6`](https://arcprize.org/tasks/60d73be6), [`8d510a79`](https://arcprize.org/tasks/8d510a79), [`8f2ea7aa`](https://arcprize.org/tasks/8f2ea7aa), [`8fbca751`](https://arcprize.org/tasks/8fbca751), [`b745798f`](https://arcprize.org/tasks/b745798f), [`d304284e`](https://arcprize.org/tasks/d304284e), [`db0c5428`](https://arcprize.org/tasks/db0c5428), [`e12f9a14`](https://arcprize.org/tasks/e12f9a14), [`e619ca6e`](https://arcprize.org/tasks/e619ca6e), [`e9bb6954`](https://arcprize.org/tasks/e9bb6954), [`f35d900a`](https://arcprize.org/tasks/f35d900a), [`f8be4b64`](https://arcprize.org/tasks/f8be4b64), [`fd4b2b02`](https://arcprize.org/tasks/fd4b2b02), [`fe9372f3`](https://arcprize.org/tasks/fe9372f3)

### `(SAME | MEDIUM | RECOLOR | FEW_BLOBS | 2-3)` — 22 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`009d5c81`](https://arcprize.org/tasks/009d5c81), [`103eff5b`](https://arcprize.org/tasks/103eff5b), [`2a5f8217`](https://arcprize.org/tasks/2a5f8217), [`46c35fc7`](https://arcprize.org/tasks/46c35fc7), [`4aab4007`](https://arcprize.org/tasks/4aab4007), [`50cb2852`](https://arcprize.org/tasks/50cb2852), [`516b51b7`](https://arcprize.org/tasks/516b51b7), [`604001fa`](https://arcprize.org/tasks/604001fa), [`694f12f3`](https://arcprize.org/tasks/694f12f3), [`7d1f7ee8`](https://arcprize.org/tasks/7d1f7ee8), [`817e6c09`](https://arcprize.org/tasks/817e6c09), [`941d9a10`](https://arcprize.org/tasks/941d9a10), [`981571dc`](https://arcprize.org/tasks/981571dc), [`aabf363d`](https://arcprize.org/tasks/aabf363d), [`ae58858e`](https://arcprize.org/tasks/ae58858e), [`b230c067`](https://arcprize.org/tasks/b230c067), [`b2862040`](https://arcprize.org/tasks/b2862040), [`bb43febb`](https://arcprize.org/tasks/bb43febb), [`e76a88a6`](https://arcprize.org/tasks/e76a88a6), [`ea32f347`](https://arcprize.org/tasks/ea32f347), [`ecb67b6d`](https://arcprize.org/tasks/ecb67b6d), [`fea12743`](https://arcprize.org/tasks/fea12743)

### `(SAME | DENSE | ADD | FEW_BLOBS | 2-3)` — 22 puzzles

**Likely L1 primitives**:
  - copy_to_markers (2-3 markers)
  - frame_around_seed × few
  - cross_from_seed × few
  - sandwich_fill (few pairs)

**Puzzles**: [`13713586`](https://arcprize.org/tasks/13713586), [`305b1341`](https://arcprize.org/tasks/305b1341), [`363442ee`](https://arcprize.org/tasks/363442ee), [`3bd292e8`](https://arcprize.org/tasks/3bd292e8), [`3bd67248`](https://arcprize.org/tasks/3bd67248), [`4cd1b7b2`](https://arcprize.org/tasks/4cd1b7b2), [`5207a7b5`](https://arcprize.org/tasks/5207a7b5), [`543a7ed5`](https://arcprize.org/tasks/543a7ed5), [`6455b5f5`](https://arcprize.org/tasks/6455b5f5), [`67385a82`](https://arcprize.org/tasks/67385a82), [`834ec97d`](https://arcprize.org/tasks/834ec97d), [`8e5a5113`](https://arcprize.org/tasks/8e5a5113), [`8eb1be9a`](https://arcprize.org/tasks/8eb1be9a), [`9356391f`](https://arcprize.org/tasks/9356391f), [`a3f84088`](https://arcprize.org/tasks/a3f84088), [`b6afb2da`](https://arcprize.org/tasks/b6afb2da), [`c8f0f002`](https://arcprize.org/tasks/c8f0f002), [`c9f8e694`](https://arcprize.org/tasks/c9f8e694), [`d931c21c`](https://arcprize.org/tasks/d931c21c), [`d968ffd4`](https://arcprize.org/tasks/d968ffd4), [`db3e9e38`](https://arcprize.org/tasks/db3e9e38), [`fc754716`](https://arcprize.org/tasks/fc754716)

### `(SAME | SPARSE | ADD | ONE_BLOB | 1)` — 21 puzzles

**Likely L1 primitives**:
  - frame_around_seed (3x3 halo)
  - draw_bbox
  - boundary_mask (outline)

**Puzzles**: [`253bf280`](https://arcprize.org/tasks/253bf280), [`25d487eb`](https://arcprize.org/tasks/25d487eb), [`27a77e38`](https://arcprize.org/tasks/27a77e38), [`2c737e39`](https://arcprize.org/tasks/2c737e39), [`2dd70a9a`](https://arcprize.org/tasks/2dd70a9a), [`37ce87bb`](https://arcprize.org/tasks/37ce87bb), [`44d8ac46`](https://arcprize.org/tasks/44d8ac46), [`53fb4810`](https://arcprize.org/tasks/53fb4810), [`66ac4c3b`](https://arcprize.org/tasks/66ac4c3b), [`72a961c9`](https://arcprize.org/tasks/72a961c9), [`7e576d6e`](https://arcprize.org/tasks/7e576d6e), [`84f2aca1`](https://arcprize.org/tasks/84f2aca1), [`88a10436`](https://arcprize.org/tasks/88a10436), [`891232d6`](https://arcprize.org/tasks/891232d6), [`a2fd1cf0`](https://arcprize.org/tasks/a2fd1cf0), [`b5bb5719`](https://arcprize.org/tasks/b5bb5719), [`b775ac94`](https://arcprize.org/tasks/b775ac94), [`bf89d739`](https://arcprize.org/tasks/bf89d739), [`d6ad076f`](https://arcprize.org/tasks/d6ad076f), [`e2092e0c`](https://arcprize.org/tasks/e2092e0c), [`e9614598`](https://arcprize.org/tasks/e9614598)

### `(SAME | DENSE | ADD | ONE_BLOB | 1)` — 20 puzzles

**Likely L1 primitives**:
  - fill_enclosed
  - flood_from_seed
  - u_cup_fill

**Puzzles**: [`0f63c0b9`](https://arcprize.org/tasks/0f63c0b9), [`1190bc91`](https://arcprize.org/tasks/1190bc91), [`137f0df0`](https://arcprize.org/tasks/137f0df0), [`140c817e`](https://arcprize.org/tasks/140c817e), [`1bfc4729`](https://arcprize.org/tasks/1bfc4729), [`256b0a75`](https://arcprize.org/tasks/256b0a75), [`28e73c20`](https://arcprize.org/tasks/28e73c20), [`36a08778`](https://arcprize.org/tasks/36a08778), [`762cd429`](https://arcprize.org/tasks/762cd429), [`78e78cff`](https://arcprize.org/tasks/78e78cff), [`8403a5d5`](https://arcprize.org/tasks/8403a5d5), [`9c1e755f`](https://arcprize.org/tasks/9c1e755f), [`b15fca0b`](https://arcprize.org/tasks/b15fca0b), [`b942fd60`](https://arcprize.org/tasks/b942fd60), [`ce22a75a`](https://arcprize.org/tasks/ce22a75a), [`cfb2ce5a`](https://arcprize.org/tasks/cfb2ce5a), [`d037b0a7`](https://arcprize.org/tasks/d037b0a7), [`db93a21d`](https://arcprize.org/tasks/db93a21d), [`dc1df850`](https://arcprize.org/tasks/dc1df850), [`e5c44e8f`](https://arcprize.org/tasks/e5c44e8f)

### `(SAME | MEDIUM | MOVE | FEW_BLOBS | 2-3)` — 19 puzzles

**Likely L1 primitives**:
  - move_to_marker × 2-3
  - ball_roll (snake trail)
  - gravity_water (few cells)

**Puzzles**: [`025d127b`](https://arcprize.org/tasks/025d127b), [`3906de3d`](https://arcprize.org/tasks/3906de3d), [`465b7d93`](https://arcprize.org/tasks/465b7d93), [`5168d44c`](https://arcprize.org/tasks/5168d44c), [`54dc2872`](https://arcprize.org/tasks/54dc2872), [`5521c0d9`](https://arcprize.org/tasks/5521c0d9), [`56dc2b01`](https://arcprize.org/tasks/56dc2b01), [`64a7c07e`](https://arcprize.org/tasks/64a7c07e), [`67c52801`](https://arcprize.org/tasks/67c52801), [`6c434453`](https://arcprize.org/tasks/6c434453), [`90347967`](https://arcprize.org/tasks/90347967), [`94be5b80`](https://arcprize.org/tasks/94be5b80), [`98c475bf`](https://arcprize.org/tasks/98c475bf), [`9f669b64`](https://arcprize.org/tasks/9f669b64), [`d5d6de2d`](https://arcprize.org/tasks/d5d6de2d), [`dd2401ed`](https://arcprize.org/tasks/dd2401ed), [`f3e62deb`](https://arcprize.org/tasks/f3e62deb), [`f5c89df1`](https://arcprize.org/tasks/f5c89df1), [`fe45cba4`](https://arcprize.org/tasks/fe45cba4)

### `(SAME | DENSE | MOVE | MULTI_BLOBS | 4-8)` — 16 puzzles

**Likely L1 primitives**:
  - gravity_water (per-column)
  - ball_roll
  - move_to_marker × many

**Puzzles**: [`03560426`](https://arcprize.org/tasks/03560426), [`18447a8d`](https://arcprize.org/tasks/18447a8d), [`1c0d0a4b`](https://arcprize.org/tasks/1c0d0a4b), [`446ef5d2`](https://arcprize.org/tasks/446ef5d2), [`470c91de`](https://arcprize.org/tasks/470c91de), [`5ffb2104`](https://arcprize.org/tasks/5ffb2104), [`66e6c45b`](https://arcprize.org/tasks/66e6c45b), [`6ad5bdfd`](https://arcprize.org/tasks/6ad5bdfd), [`87ab05b8`](https://arcprize.org/tasks/87ab05b8), [`99caaf76`](https://arcprize.org/tasks/99caaf76), [`9dfd6313`](https://arcprize.org/tasks/9dfd6313), [`ac2e8ecf`](https://arcprize.org/tasks/ac2e8ecf), [`b25e450b`](https://arcprize.org/tasks/b25e450b), [`b5ca7ac4`](https://arcprize.org/tasks/b5ca7ac4), [`bd283c4a`](https://arcprize.org/tasks/bd283c4a), [`e48d4e1a`](https://arcprize.org/tasks/e48d4e1a)

### `(SAME | MEDIUM | MOVE | MANY_SCATTERED | 9+)` — 16 puzzles

**Likely L1 primitives**:
  - gravity_water (many cells)
  - scatter translations

**Puzzles**: [`17829a00`](https://arcprize.org/tasks/17829a00), [`184a9768`](https://arcprize.org/tasks/184a9768), [`1b8318e3`](https://arcprize.org/tasks/1b8318e3), [`1efba499`](https://arcprize.org/tasks/1efba499), [`29623171`](https://arcprize.org/tasks/29623171), [`31aa019c`](https://arcprize.org/tasks/31aa019c), [`4e45f183`](https://arcprize.org/tasks/4e45f183), [`62593bfd`](https://arcprize.org/tasks/62593bfd), [`6cdd2623`](https://arcprize.org/tasks/6cdd2623), [`917bccba`](https://arcprize.org/tasks/917bccba), [`9f41bd9c`](https://arcprize.org/tasks/9f41bd9c), [`a78176bb`](https://arcprize.org/tasks/a78176bb), [`e26a3af2`](https://arcprize.org/tasks/e26a3af2), [`f0f8a26d`](https://arcprize.org/tasks/f0f8a26d), [`f28a3cbb`](https://arcprize.org/tasks/f28a3cbb), [`f83cb3f6`](https://arcprize.org/tasks/f83cb3f6)

### `(SAME | DENSE | ADD | MULTI_BLOBS | 4-8)` — 15 puzzles

**Likely L1 primitives**:
  - copy_to_markers × many
  - frame_around_seed × many
  - cross/star_from_seed × many

**Puzzles**: [`178fcbfb`](https://arcprize.org/tasks/178fcbfb), [`21f83797`](https://arcprize.org/tasks/21f83797), [`23581191`](https://arcprize.org/tasks/23581191), [`272f95fa`](https://arcprize.org/tasks/272f95fa), [`4258a5f9`](https://arcprize.org/tasks/4258a5f9), [`522fdd07`](https://arcprize.org/tasks/522fdd07), [`7c8af763`](https://arcprize.org/tasks/7c8af763), [`9344f635`](https://arcprize.org/tasks/9344f635), [`93b581b8`](https://arcprize.org/tasks/93b581b8), [`a8610ef7`](https://arcprize.org/tasks/a8610ef7), [`aba27056`](https://arcprize.org/tasks/aba27056), [`b60334d2`](https://arcprize.org/tasks/b60334d2), [`bae5c565`](https://arcprize.org/tasks/bae5c565), [`da515329`](https://arcprize.org/tasks/da515329), [`e9c9d9a1`](https://arcprize.org/tasks/e9c9d9a1)

### `(SAME | SPARSE | ADD | ISOLATED_CELLS | 4-8)` — 14 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`0ca9ddb6`](https://arcprize.org/tasks/0ca9ddb6), [`11e1fe23`](https://arcprize.org/tasks/11e1fe23), [`14b8e18c`](https://arcprize.org/tasks/14b8e18c), [`55059096`](https://arcprize.org/tasks/55059096), [`55783887`](https://arcprize.org/tasks/55783887), [`5c0a986e`](https://arcprize.org/tasks/5c0a986e), [`642248e4`](https://arcprize.org/tasks/642248e4), [`6e19193c`](https://arcprize.org/tasks/6e19193c), [`72207abc`](https://arcprize.org/tasks/72207abc), [`72322fa7`](https://arcprize.org/tasks/72322fa7), [`7ddcd7ec`](https://arcprize.org/tasks/7ddcd7ec), [`95990924`](https://arcprize.org/tasks/95990924), [`a699fb00`](https://arcprize.org/tasks/a699fb00), [`e048c9ed`](https://arcprize.org/tasks/e048c9ed)

### `(SAME | SPARSE | MOVE | MULTI_BLOBS | 4-8)` — 14 puzzles

**Likely L1 primitives**:
  - gravity_water (per-column)
  - ball_roll
  - move_to_marker × many

**Puzzles**: [`0e206a2e`](https://arcprize.org/tasks/0e206a2e), [`11dc524f`](https://arcprize.org/tasks/11dc524f), [`20981f0e`](https://arcprize.org/tasks/20981f0e), [`31f7f899`](https://arcprize.org/tasks/31f7f899), [`3d6c6e23`](https://arcprize.org/tasks/3d6c6e23), [`494ef9d7`](https://arcprize.org/tasks/494ef9d7), [`5b692c0f`](https://arcprize.org/tasks/5b692c0f), [`6855a6e4`](https://arcprize.org/tasks/6855a6e4), [`758abdf0`](https://arcprize.org/tasks/758abdf0), [`88bcf3b4`](https://arcprize.org/tasks/88bcf3b4), [`df978a02`](https://arcprize.org/tasks/df978a02), [`f21745ec`](https://arcprize.org/tasks/f21745ec), [`f8a8fe49`](https://arcprize.org/tasks/f8a8fe49), [`fc10701f`](https://arcprize.org/tasks/fc10701f)

### `(SAME | SPARSE | RECOLOR | ONE_BLOB | 1)` — 13 puzzles

**Likely L1 primitives**:
  - extract_largest_recolor
  - recolor_one_object

**Puzzles**: [`1818057f`](https://arcprize.org/tasks/1818057f), [`52df9849`](https://arcprize.org/tasks/52df9849), [`5792cb4d`](https://arcprize.org/tasks/5792cb4d), [`63613498`](https://arcprize.org/tasks/63613498), [`6cf79266`](https://arcprize.org/tasks/6cf79266), [`7e02026e`](https://arcprize.org/tasks/7e02026e), [`810b9b61`](https://arcprize.org/tasks/810b9b61), [`890034e9`](https://arcprize.org/tasks/890034e9), [`97d7923e`](https://arcprize.org/tasks/97d7923e), [`aedd82e4`](https://arcprize.org/tasks/aedd82e4), [`ba97ae07`](https://arcprize.org/tasks/ba97ae07), [`e5062a87`](https://arcprize.org/tasks/e5062a87), [`e88171ec`](https://arcprize.org/tasks/e88171ec)

### `(SAME | SPARSE | RECOLOR | FEW_BLOBS | 2-3)` — 13 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`1acc24af`](https://arcprize.org/tasks/1acc24af), [`25094a63`](https://arcprize.org/tasks/25094a63), [`32597951`](https://arcprize.org/tasks/32597951), [`40f6cd08`](https://arcprize.org/tasks/40f6cd08), [`50f325b5`](https://arcprize.org/tasks/50f325b5), [`776ffc46`](https://arcprize.org/tasks/776ffc46), [`7b0280bc`](https://arcprize.org/tasks/7b0280bc), [`a834deea`](https://arcprize.org/tasks/a834deea), [`af22c60d`](https://arcprize.org/tasks/af22c60d), [`c7f57c3e`](https://arcprize.org/tasks/c7f57c3e), [`f341894c`](https://arcprize.org/tasks/f341894c), [`f9d67f8b`](https://arcprize.org/tasks/f9d67f8b), [`fafd9572`](https://arcprize.org/tasks/fafd9572)

### `(SAME | DENSE | MOVE | FEW_BLOBS | 2-3)` — 12 puzzles

**Likely L1 primitives**:
  - move_to_marker × 2-3
  - ball_roll (snake trail)
  - gravity_water (few cells)

**Puzzles**: [`25ff71a9`](https://arcprize.org/tasks/25ff71a9), [`2a28add5`](https://arcprize.org/tasks/2a28add5), [`3c9b0459`](https://arcprize.org/tasks/3c9b0459), [`4acc7107`](https://arcprize.org/tasks/4acc7107), [`74dd1130`](https://arcprize.org/tasks/74dd1130), [`794b24be`](https://arcprize.org/tasks/794b24be), [`7ee1c6ea`](https://arcprize.org/tasks/7ee1c6ea), [`9968a131`](https://arcprize.org/tasks/9968a131), [`beb8660c`](https://arcprize.org/tasks/beb8660c), [`e9afcf9a`](https://arcprize.org/tasks/e9afcf9a), [`ed36ccf7`](https://arcprize.org/tasks/ed36ccf7), [`f3e14006`](https://arcprize.org/tasks/f3e14006)

### `(SAME | TOTAL | ADD | ONE_BLOB | 1)` — 12 puzzles

**Likely L1 primitives**:
  - flip_horizontal / flip_vertical
  - rotate_90 (square)
  - transpose / color_permute (whole-grid)

**Puzzles**: [`2b9ef948`](https://arcprize.org/tasks/2b9ef948), [`2bcee788`](https://arcprize.org/tasks/2bcee788), [`32e9702f`](https://arcprize.org/tasks/32e9702f), [`332202d5`](https://arcprize.org/tasks/332202d5), [`332efdb3`](https://arcprize.org/tasks/332efdb3), [`477d2879`](https://arcprize.org/tasks/477d2879), [`62b74c02`](https://arcprize.org/tasks/62b74c02), [`6f8cd79b`](https://arcprize.org/tasks/6f8cd79b), [`aaef0977`](https://arcprize.org/tasks/aaef0977), [`ac0c2ac3`](https://arcprize.org/tasks/ac0c2ac3), [`bd4472b8`](https://arcprize.org/tasks/bd4472b8), [`e179c5f4`](https://arcprize.org/tasks/e179c5f4)

### `(SAME | MEDIUM | RECOLOR | ONE_BLOB | 1)` — 10 puzzles

**Likely L1 primitives**:
  - extract_largest_recolor
  - recolor_one_object

**Puzzles**: [`0becf7df`](https://arcprize.org/tasks/0becf7df), [`0d87d2a6`](https://arcprize.org/tasks/0d87d2a6), [`150deff5`](https://arcprize.org/tasks/150deff5), [`45737921`](https://arcprize.org/tasks/45737921), [`9f27f097`](https://arcprize.org/tasks/9f27f097), [`b457fec5`](https://arcprize.org/tasks/b457fec5), [`c1d99e64`](https://arcprize.org/tasks/c1d99e64), [`c7d4e6ad`](https://arcprize.org/tasks/c7d4e6ad), [`cc9053aa`](https://arcprize.org/tasks/cc9053aa), [`e7dd8335`](https://arcprize.org/tasks/e7dd8335)

### `(SAME | SPARSE | RECOLOR | MULTI_BLOBS | 4-8)` — 10 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`14754a24`](https://arcprize.org/tasks/14754a24), [`15113be4`](https://arcprize.org/tasks/15113be4), [`1f642eb9`](https://arcprize.org/tasks/1f642eb9), [`36fdfd69`](https://arcprize.org/tasks/36fdfd69), [`689c358e`](https://arcprize.org/tasks/689c358e), [`9b5080bb`](https://arcprize.org/tasks/9b5080bb), [`a8d7556c`](https://arcprize.org/tasks/a8d7556c), [`ad173014`](https://arcprize.org/tasks/ad173014), [`b99e7126`](https://arcprize.org/tasks/b99e7126), [`c3fa4749`](https://arcprize.org/tasks/c3fa4749)

### `(SAME | SPARSE | MIXED | MULTI_BLOBS | 4-8)` — 10 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`17b866bd`](https://arcprize.org/tasks/17b866bd), [`29ec7d0e`](https://arcprize.org/tasks/29ec7d0e), [`3631a71a`](https://arcprize.org/tasks/3631a71a), [`47996f11`](https://arcprize.org/tasks/47996f11), [`484b58aa`](https://arcprize.org/tasks/484b58aa), [`696d4842`](https://arcprize.org/tasks/696d4842), [`b7955b3c`](https://arcprize.org/tasks/b7955b3c), [`ca8f78db`](https://arcprize.org/tasks/ca8f78db), [`d89b689b`](https://arcprize.org/tasks/d89b689b), [`edcc2ff0`](https://arcprize.org/tasks/edcc2ff0)

### `(SAME | MEDIUM | RECOLOR | MANY_SCATTERED | 9+)` — 9 puzzles

**Likely L1 primitives**:
  - color_palette_mapping
  - per-cell recolor by rule

**Puzzles**: [`15663ba9`](https://arcprize.org/tasks/15663ba9), [`33b52de3`](https://arcprize.org/tasks/33b52de3), [`4f537728`](https://arcprize.org/tasks/4f537728), [`7d419a02`](https://arcprize.org/tasks/7d419a02), [`845d6e51`](https://arcprize.org/tasks/845d6e51), [`ce039d91`](https://arcprize.org/tasks/ce039d91), [`d94c3b52`](https://arcprize.org/tasks/d94c3b52), [`e760a62e`](https://arcprize.org/tasks/e760a62e), [`e8593010`](https://arcprize.org/tasks/e8593010)

### `(SAME | SPARSE | MOVE | ISOLATED_CELLS | 4-8)` — 9 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`1a244afd`](https://arcprize.org/tasks/1a244afd), [`342dd610`](https://arcprize.org/tasks/342dd610), [`42a15761`](https://arcprize.org/tasks/42a15761), [`825aa9e9`](https://arcprize.org/tasks/825aa9e9), [`952a094c`](https://arcprize.org/tasks/952a094c), [`9bbf930d`](https://arcprize.org/tasks/9bbf930d), [`9c56f360`](https://arcprize.org/tasks/9c56f360), [`a48eeaf7`](https://arcprize.org/tasks/a48eeaf7), [`ecaa0ec1`](https://arcprize.org/tasks/ecaa0ec1)

### `(SAME | TOTAL | MOVE | ONE_BLOB | 1)` — 9 puzzles

**Likely L1 primitives**:
  - flip_horizontal / flip_vertical
  - rotate_90 (square)
  - transpose / color_permute (whole-grid)

**Puzzles**: [`2de01db2`](https://arcprize.org/tasks/2de01db2), [`50a16a69`](https://arcprize.org/tasks/50a16a69), [`6150a2bd`](https://arcprize.org/tasks/6150a2bd), [`67a3c6ac`](https://arcprize.org/tasks/67a3c6ac), [`6ea4a07e`](https://arcprize.org/tasks/6ea4a07e), [`bd5af378`](https://arcprize.org/tasks/bd5af378), [`bda2d7a6`](https://arcprize.org/tasks/bda2d7a6), [`caa06a1f`](https://arcprize.org/tasks/caa06a1f), [`f76d97a5`](https://arcprize.org/tasks/f76d97a5)

### `(SAME | DENSE | ADD | MANY_SCATTERED | 9+)` — 8 puzzles

**Likely L1 primitives**:
  - ray_to_edge / ray_until_blocker
  - cross/star_from_seed
  - periodic_extension
  - flood_from_seed (large region)

**Puzzles**: [`0a938d79`](https://arcprize.org/tasks/0a938d79), [`5751f35e`](https://arcprize.org/tasks/5751f35e), [`58c02a16`](https://arcprize.org/tasks/58c02a16), [`759f3fd3`](https://arcprize.org/tasks/759f3fd3), [`84db8fc4`](https://arcprize.org/tasks/84db8fc4), [`9edfc990`](https://arcprize.org/tasks/9edfc990), [`c4d1a9ae`](https://arcprize.org/tasks/c4d1a9ae), [`d22278a0`](https://arcprize.org/tasks/d22278a0)

### `(SAME | SPARSE | MOVE | MANY_SCATTERED | 9+)` — 8 puzzles

**Likely L1 primitives**:
  - gravity_water (many cells)
  - scatter translations

**Puzzles**: [`1a07d186`](https://arcprize.org/tasks/1a07d186), [`1b59e163`](https://arcprize.org/tasks/1b59e163), [`1c56ad9f`](https://arcprize.org/tasks/1c56ad9f), [`4093f84a`](https://arcprize.org/tasks/4093f84a), [`93c31fbe`](https://arcprize.org/tasks/93c31fbe), [`b9630600`](https://arcprize.org/tasks/b9630600), [`d687bc17`](https://arcprize.org/tasks/d687bc17), [`db615bd4`](https://arcprize.org/tasks/db615bd4)

### `(SAME | DENSE | RECOLOR | MULTI_BLOBS | 4-8)` — 7 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`0a2355a6`](https://arcprize.org/tasks/0a2355a6), [`37d3e8b2`](https://arcprize.org/tasks/37d3e8b2), [`4e7e0eb9`](https://arcprize.org/tasks/4e7e0eb9), [`880c1354`](https://arcprize.org/tasks/880c1354), [`9caf5b84`](https://arcprize.org/tasks/9caf5b84), [`ad38a9d0`](https://arcprize.org/tasks/ad38a9d0), [`b1948b0a`](https://arcprize.org/tasks/b1948b0a)

### `(SAME | SPARSE | ADD | ISOLATED_CELLS | 9+)` — 7 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`142ca369`](https://arcprize.org/tasks/142ca369), [`508bd3b6`](https://arcprize.org/tasks/508bd3b6), [`623ea044`](https://arcprize.org/tasks/623ea044), [`7e2bad24`](https://arcprize.org/tasks/7e2bad24), [`92e50de0`](https://arcprize.org/tasks/92e50de0), [`9d9215db`](https://arcprize.org/tasks/9d9215db), [`af726779`](https://arcprize.org/tasks/af726779)

### `(SAME | SPARSE | ADD | MANY_SCATTERED | 9+)` — 7 puzzles

**Likely L1 primitives**:
  - ray_to_edge / ray_until_blocker
  - cross/star_from_seed
  - periodic_extension
  - flood_from_seed (large region)

**Puzzles**: [`342ae2ed`](https://arcprize.org/tasks/342ae2ed), [`396d80d7`](https://arcprize.org/tasks/396d80d7), [`3ed85e70`](https://arcprize.org/tasks/3ed85e70), [`a395ee82`](https://arcprize.org/tasks/a395ee82), [`b7f8a4d8`](https://arcprize.org/tasks/b7f8a4d8), [`cb227835`](https://arcprize.org/tasks/cb227835), [`fd096ab6`](https://arcprize.org/tasks/fd096ab6)

### `(SAME | SPARSE | MIXED | FEW_BLOBS | 2-3)` — 7 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`3d588dc9`](https://arcprize.org/tasks/3d588dc9), [`896d5239`](https://arcprize.org/tasks/896d5239), [`903d1b4a`](https://arcprize.org/tasks/903d1b4a), [`b8825c91`](https://arcprize.org/tasks/b8825c91), [`d90796e8`](https://arcprize.org/tasks/d90796e8), [`d93c6891`](https://arcprize.org/tasks/d93c6891), [`dd6b8c4b`](https://arcprize.org/tasks/dd6b8c4b)

### `(SAME | TOTAL | MIXED | ONE_BLOB | 1)` — 6 puzzles

**Likely L1 primitives**:
  - flip_horizontal / flip_vertical
  - rotate_90 (square)
  - transpose / color_permute (whole-grid)

**Puzzles**: [`0d3d703e`](https://arcprize.org/tasks/0d3d703e), [`17cae0c1`](https://arcprize.org/tasks/17cae0c1), [`25d8a9c8`](https://arcprize.org/tasks/25d8a9c8), [`6e02f1e3`](https://arcprize.org/tasks/6e02f1e3), [`85c4e7cd`](https://arcprize.org/tasks/85c4e7cd), [`a85d4709`](https://arcprize.org/tasks/a85d4709)

### `(SAME | SPARSE | ADD | ISOLATED_CELLS | 2-3)` — 6 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`11852cab`](https://arcprize.org/tasks/11852cab), [`3aa6fb7a`](https://arcprize.org/tasks/3aa6fb7a), [`54d82841`](https://arcprize.org/tasks/54d82841), [`b8cdaf2b`](https://arcprize.org/tasks/b8cdaf2b), [`cbded52d`](https://arcprize.org/tasks/cbded52d), [`ec883f72`](https://arcprize.org/tasks/ec883f72)

### `(SAME | MEDIUM | MIXED | MULTI_BLOBS | 4-8)` — 6 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`195c6913`](https://arcprize.org/tasks/195c6913), [`5a719d11`](https://arcprize.org/tasks/5a719d11), [`a61f2674`](https://arcprize.org/tasks/a61f2674), [`bc93ec48`](https://arcprize.org/tasks/bc93ec48), [`c663677b`](https://arcprize.org/tasks/c663677b), [`f1cefba8`](https://arcprize.org/tasks/f1cefba8)

### `(SAME | DENSE | MOVE | MANY_SCATTERED | 9+)` — 6 puzzles

**Likely L1 primitives**:
  - gravity_water (many cells)
  - scatter translations

**Puzzles**: [`5e6bbc0b`](https://arcprize.org/tasks/5e6bbc0b), [`6a980be1`](https://arcprize.org/tasks/6a980be1), [`782b5218`](https://arcprize.org/tasks/782b5218), [`8ee62060`](https://arcprize.org/tasks/8ee62060), [`dc2aa30b`](https://arcprize.org/tasks/dc2aa30b), [`f3cdc58f`](https://arcprize.org/tasks/f3cdc58f)

### `(SAME | MEDIUM | ADD | ISOLATED_CELLS | 9+)` — 5 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`0962bcdd`](https://arcprize.org/tasks/0962bcdd), [`1f876c06`](https://arcprize.org/tasks/1f876c06), [`d364b489`](https://arcprize.org/tasks/d364b489), [`d492a647`](https://arcprize.org/tasks/d492a647), [`db695cfb`](https://arcprize.org/tasks/db695cfb)

### `(SAME | MEDIUM | MIXED | FEW_BLOBS | 2-3)` — 5 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`2b01abd0`](https://arcprize.org/tasks/2b01abd0), [`929ab4e9`](https://arcprize.org/tasks/929ab4e9), [`aa4ec2a5`](https://arcprize.org/tasks/aa4ec2a5), [`c074846d`](https://arcprize.org/tasks/c074846d), [`d2acf2cb`](https://arcprize.org/tasks/d2acf2cb)

### `(SAME | DENSE | MOVE | ONE_BLOB | 1)` — 5 puzzles

**Likely L1 primitives**:
  - drop_to_floor
  - move_to_marker (1 object)

**Puzzles**: [`abc82100`](https://arcprize.org/tasks/abc82100), [`bf32578f`](https://arcprize.org/tasks/bf32578f), [`c61be7dc`](https://arcprize.org/tasks/c61be7dc), [`d511f180`](https://arcprize.org/tasks/d511f180), [`e7b06bea`](https://arcprize.org/tasks/e7b06bea)

### `(SAME | TOTAL | ADD | FEW_BLOBS | 2-3)` — 4 puzzles

**Likely L1 primitives**:
  - flip_horizontal / flip_vertical
  - rotate_90 (square)
  - transpose / color_permute (whole-grid)

**Puzzles**: [`05269061`](https://arcprize.org/tasks/05269061), [`13e47133`](https://arcprize.org/tasks/13e47133), [`54d9e175`](https://arcprize.org/tasks/54d9e175), [`f8c80d96`](https://arcprize.org/tasks/f8c80d96)

### `(SAME | SPARSE | RECOLOR | MANY_SCATTERED | 9+)` — 4 puzzles

**Likely L1 primitives**:
  - color_palette_mapping
  - per-cell recolor by rule

**Puzzles**: [`06df4c85`](https://arcprize.org/tasks/06df4c85), [`09c534e7`](https://arcprize.org/tasks/09c534e7), [`264363fd`](https://arcprize.org/tasks/264363fd), [`58743b76`](https://arcprize.org/tasks/58743b76)

### `(SAME | TINY | ADD | ONE_BLOB | 1)` — 4 puzzles

**Likely L1 primitives**:
  - frame_around_seed (3x3 halo)
  - draw_bbox
  - boundary_mask (outline)

**Puzzles**: [`0b17323b`](https://arcprize.org/tasks/0b17323b), [`135a2760`](https://arcprize.org/tasks/135a2760), [`18419cfa`](https://arcprize.org/tasks/18419cfa), [`9f5f939b`](https://arcprize.org/tasks/9f5f939b)

### `(SAME | SPARSE | RECOLOR | ISOLATED_CELLS | 4-8)` — 4 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`2204b7a8`](https://arcprize.org/tasks/2204b7a8), [`575b1a71`](https://arcprize.org/tasks/575b1a71), [`a5f85a15`](https://arcprize.org/tasks/a5f85a15), [`aa300dc3`](https://arcprize.org/tasks/aa300dc3)

### `(SAME | SPARSE | REMOVE | FEW_BLOBS | 2-3)` — 4 puzzles

**Likely L1 primitives**:
  - component_4/8conn keep_largest
  - delete_by_marker

**Puzzles**: [`22806e14`](https://arcprize.org/tasks/22806e14), [`2f767503`](https://arcprize.org/tasks/2f767503), [`9720b24f`](https://arcprize.org/tasks/9720b24f), [`c35c1b4c`](https://arcprize.org/tasks/c35c1b4c)

### `(SAME | SPARSE | MOVE | FEW_BLOBS | 2-3)` — 4 puzzles

**Likely L1 primitives**:
  - move_to_marker × 2-3
  - ball_roll (snake trail)
  - gravity_water (few cells)

**Puzzles**: [`28a6681f`](https://arcprize.org/tasks/28a6681f), [`963c33f8`](https://arcprize.org/tasks/963c33f8), [`981add89`](https://arcprize.org/tasks/981add89), [`df9fd884`](https://arcprize.org/tasks/df9fd884)

### `(SAME | DENSE | MIXED | MULTI_BLOBS | 4-8)` — 4 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`41ace6b5`](https://arcprize.org/tasks/41ace6b5), [`9b365c51`](https://arcprize.org/tasks/9b365c51), [`f18ec8cc`](https://arcprize.org/tasks/f18ec8cc), [`ff2825db`](https://arcprize.org/tasks/ff2825db)

### `(SAME | MEDIUM | REMOVE | MULTI_BLOBS | 4-8)` — 4 puzzles

**Likely L1 primitives**:
  - component_4/8conn keep_largest
  - delete_by_marker

**Puzzles**: [`52364a65`](https://arcprize.org/tasks/52364a65), [`6350f1f4`](https://arcprize.org/tasks/6350f1f4), [`73251a56`](https://arcprize.org/tasks/73251a56), [`e39e9282`](https://arcprize.org/tasks/e39e9282)

### `(SAME | DENSE | RECOLOR | FEW_BLOBS | 2-3)` — 4 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`626c0bcc`](https://arcprize.org/tasks/626c0bcc), [`639f5a19`](https://arcprize.org/tasks/639f5a19), [`8dae5dfc`](https://arcprize.org/tasks/8dae5dfc), [`ddf7fa4f`](https://arcprize.org/tasks/ddf7fa4f)

### `(SAME | MEDIUM | REMOVE | MANY_SCATTERED | 9+)` — 4 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`6d0160f0`](https://arcprize.org/tasks/6d0160f0), [`6df30ad6`](https://arcprize.org/tasks/6df30ad6), [`95a58926`](https://arcprize.org/tasks/95a58926), [`f823c43c`](https://arcprize.org/tasks/f823c43c)

### `(SAME | SPARSE | MOVE | ISOLATED_CELLS | 9+)` — 4 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`7d7772cc`](https://arcprize.org/tasks/7d7772cc), [`85b81ff1`](https://arcprize.org/tasks/85b81ff1), [`ae3edfdc`](https://arcprize.org/tasks/ae3edfdc), [`df8cc377`](https://arcprize.org/tasks/df8cc377)

### `(SAME | MEDIUM | MOVE | ONE_BLOB | 1)` — 3 puzzles

**Likely L1 primitives**:
  - drop_to_floor
  - move_to_marker (1 object)

**Puzzles**: [`05f2a901`](https://arcprize.org/tasks/05f2a901), [`a79310a0`](https://arcprize.org/tasks/a79310a0), [`fc4aaf52`](https://arcprize.org/tasks/fc4aaf52)

### `(SAME | SPARSE | REMOVE | ISOLATED_CELLS | 9+)` — 3 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`3bdb4ada`](https://arcprize.org/tasks/3bdb4ada), [`42a50994`](https://arcprize.org/tasks/42a50994), [`7f4411dc`](https://arcprize.org/tasks/7f4411dc)

### `(SAME | SPARSE | MIXED | MANY_SCATTERED | 9+)` — 2 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`0607ce86`](https://arcprize.org/tasks/0607ce86), [`b74ca5d1`](https://arcprize.org/tasks/b74ca5d1)

### `(SAME | MEDIUM | REMOVE | FEW_BLOBS | 2-3)` — 2 puzzles

**Likely L1 primitives**:
  - component_4/8conn keep_largest
  - delete_by_marker

**Puzzles**: [`182e5d0f`](https://arcprize.org/tasks/182e5d0f), [`a934301b`](https://arcprize.org/tasks/a934301b)

### `(SAME | SPARSE | RECOLOR | ISOLATED_CELLS | 9+)` — 2 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`1d61978c`](https://arcprize.org/tasks/1d61978c), [`e681b708`](https://arcprize.org/tasks/e681b708)

### `(SAME | DENSE | REMOVE | MANY_SCATTERED | 9+)` — 2 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`252143c9`](https://arcprize.org/tasks/252143c9), [`91714a58`](https://arcprize.org/tasks/91714a58)

### `(SAME | SPARSE | MIXED | ONE_BLOB | 1)` — 2 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`3345333e`](https://arcprize.org/tasks/3345333e), [`bcb3040b`](https://arcprize.org/tasks/bcb3040b)

### `(SAME | MEDIUM | ADD | ISOLATED_CELLS | 4-8)` — 2 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`3ac3eb23`](https://arcprize.org/tasks/3ac3eb23), [`e3fe1151`](https://arcprize.org/tasks/e3fe1151)

### `(SAME | MEDIUM | REMOVE | ONE_BLOB | 1)` — 2 puzzles

**Likely L1 primitives**:
  - delete_one_object
  - boundary_mask (hollow interior)

**Puzzles**: [`4347f46a`](https://arcprize.org/tasks/4347f46a), [`aa62e3f4`](https://arcprize.org/tasks/aa62e3f4)

### `(SAME | DENSE | REMOVE | MULTI_BLOBS | 4-8)` — 2 puzzles

**Likely L1 primitives**:
  - component_4/8conn keep_largest
  - delete_by_marker

**Puzzles**: [`456873bc`](https://arcprize.org/tasks/456873bc), [`d23f8c26`](https://arcprize.org/tasks/d23f8c26)

### `(SAME | TINY | RECOLOR | FEW_BLOBS | 2-3)` — 2 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`48634b99`](https://arcprize.org/tasks/48634b99), [`79369cc6`](https://arcprize.org/tasks/79369cc6)

### `(SAME | DENSE | REMOVE | FEW_BLOBS | 2-3)` — 2 puzzles

**Likely L1 primitives**:
  - component_4/8conn keep_largest
  - delete_by_marker

**Puzzles**: [`4df5b0ae`](https://arcprize.org/tasks/4df5b0ae), [`d255d7a7`](https://arcprize.org/tasks/d255d7a7)

### `(SAME | DENSE | REMOVE | ONE_BLOB | 1)` — 2 puzzles

**Likely L1 primitives**:
  - delete_one_object
  - boundary_mask (hollow interior)

**Puzzles**: [`5582e5ca`](https://arcprize.org/tasks/5582e5ca), [`8cb8642d`](https://arcprize.org/tasks/8cb8642d)

### `(SAME | TOTAL | MIXED | FEW_BLOBS | 2-3)` — 2 puzzles

**Likely L1 primitives**:
  - flip_horizontal / flip_vertical
  - rotate_90 (square)
  - transpose / color_permute (whole-grid)

**Puzzles**: [`68b16354`](https://arcprize.org/tasks/68b16354), [`833966f4`](https://arcprize.org/tasks/833966f4)

### `(SAME | TINY | MOVE | ISOLATED_CELLS | 2-3)` — 2 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`7acdf6d3`](https://arcprize.org/tasks/7acdf6d3), [`8dab14c2`](https://arcprize.org/tasks/8dab14c2)

### `(SAME | SPARSE | MIXED | ISOLATED_CELLS | 9+)` — 2 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`7e0986d6`](https://arcprize.org/tasks/7e0986d6), [`8886d717`](https://arcprize.org/tasks/8886d717)

### `(SAME | MEDIUM | RECOLOR | ISOLATED_CELLS | 4-8)` — 2 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`9473c6fb`](https://arcprize.org/tasks/9473c6fb), [`d406998b`](https://arcprize.org/tasks/d406998b)

### `(SAME | DENSE | RECOLOR | ONE_BLOB | 1)` — 2 puzzles

**Likely L1 primitives**:
  - extract_largest_recolor
  - recolor_one_object

**Puzzles**: [`9565186b`](https://arcprize.org/tasks/9565186b), [`b7256dcd`](https://arcprize.org/tasks/b7256dcd)

### `(SAME | SPARSE | MOVE | ISOLATED_CELLS | 2-3)` — 2 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`97c75046`](https://arcprize.org/tasks/97c75046), [`e4941b18`](https://arcprize.org/tasks/e4941b18)

### `(SAME | SPARSE | MOVE | ONE_BLOB | 1)` — 2 puzzles

**Likely L1 primitives**:
  - drop_to_floor
  - move_to_marker (1 object)

**Puzzles**: [`98cf29f8`](https://arcprize.org/tasks/98cf29f8), [`dc433765`](https://arcprize.org/tasks/dc433765)

### `(SAME | DENSE | RECOLOR | MANY_SCATTERED | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - color_palette_mapping
  - per-cell recolor by rule

**Puzzles**: [`09629e4f`](https://arcprize.org/tasks/09629e4f)

### `(SAME | SPARSE | RECOLOR | ISOLATED_CELLS | 2-3)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`18286ef8`](https://arcprize.org/tasks/18286ef8)

### `(SAME | MEDIUM | MOVE | ISOLATED_CELLS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`1e0a9b12`](https://arcprize.org/tasks/1e0a9b12)

### `(SAME | SPARSE | REMOVE | ISOLATED_CELLS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`1e81d6f9`](https://arcprize.org/tasks/1e81d6f9)

### `(SAME | MEDIUM | MIXED | ISOLATED_CELLS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`3618c87e`](https://arcprize.org/tasks/3618c87e)

### `(SAME | DENSE | MIXED | ONE_BLOB | 1)` — 1 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`3befdf3e`](https://arcprize.org/tasks/3befdf3e)

### `(SAME | TINY | RECOLOR | MULTI_BLOBS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - recolor_by_marker
  - recolor_by_size / by_topology

**Puzzles**: [`4ff4c9da`](https://arcprize.org/tasks/4ff4c9da)

### `(SAME | TINY | MOVE | ISOLATED_CELLS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`50c07299`](https://arcprize.org/tasks/50c07299)

### `(SAME | SPARSE | REMOVE | ONE_BLOB | 1)` — 1 puzzles

**Likely L1 primitives**:
  - delete_one_object
  - boundary_mask (hollow interior)

**Puzzles**: [`54db823b`](https://arcprize.org/tasks/54db823b)

### `(SAME | NO_CHANGE | MIXED | EMPTY | 0)` — 1 puzzles

**Likely L1 primitives**:
  - identity / no-op

**Puzzles**: [`5ad8a7c0`](https://arcprize.org/tasks/5ad8a7c0)

### `(SAME | MEDIUM | MIXED | ONE_BLOB | 1)` — 1 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`67a423a3`](https://arcprize.org/tasks/67a423a3)

### `(SAME | TOTAL | ADD | MULTI_BLOBS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - flip_horizontal / flip_vertical
  - rotate_90 (square)
  - transpose / color_permute (whole-grid)

**Puzzles**: [`7b6016b9`](https://arcprize.org/tasks/7b6016b9)

### `(SAME | TOTAL | ADD | MANY_SCATTERED | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - flip_horizontal / flip_vertical
  - rotate_90 (square)
  - transpose / color_permute (whole-grid)

**Puzzles**: [`83302e8f`](https://arcprize.org/tasks/83302e8f)

### `(SAME | MEDIUM | MIXED | MANY_SCATTERED | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`85fa5666`](https://arcprize.org/tasks/85fa5666)

### `(SAME | MEDIUM | RECOLOR | ISOLATED_CELLS | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`8a371977`](https://arcprize.org/tasks/8a371977)

### `(SAME | TINY | REMOVE | MULTI_BLOBS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - component_4/8conn keep_largest
  - delete_by_marker

**Puzzles**: [`8e5c0c38`](https://arcprize.org/tasks/8e5c0c38)

### `(SAME | SPARSE | REMOVE | MANY_SCATTERED | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`8f215267`](https://arcprize.org/tasks/8f215267)

### `(SAME | TINY | REMOVE | ONE_BLOB | 1)` — 1 puzzles

**Likely L1 primitives**:
  - delete_one_object
  - boundary_mask (hollow interior)

**Puzzles**: [`9f8de559`](https://arcprize.org/tasks/9f8de559)

### `(SAME | TINY | RECOLOR | ISOLATED_CELLS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`a096bf4d`](https://arcprize.org/tasks/a096bf4d)

### `(SAME | DENSE | ADD | ISOLATED_CELLS | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`a3df8b1e`](https://arcprize.org/tasks/a3df8b1e)

### `(SAME | MEDIUM | MOVE | ISOLATED_CELLS | 2-3)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`a9f96cdd`](https://arcprize.org/tasks/a9f96cdd)

### `(SAME | MEDIUM | REMOVE | ISOLATED_CELLS | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`ba9d41b8`](https://arcprize.org/tasks/ba9d41b8)

### `(SAME | TINY | ADD | ISOLATED_CELLS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`bb52a14b`](https://arcprize.org/tasks/bb52a14b)

### `(SAME | MEDIUM | MIXED | ISOLATED_CELLS | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`d07ae81c`](https://arcprize.org/tasks/d07ae81c)

### `(SAME | TINY | MOVE | MANY_SCATTERED | 9+)` — 1 puzzles

**Likely L1 primitives**:
  - gravity_water (many cells)
  - scatter translations

**Puzzles**: [`e1d2900e`](https://arcprize.org/tasks/e1d2900e)

### `(SAME | DENSE | MIXED | FEW_BLOBS | 2-3)` — 1 puzzles

**Likely L1 primitives**:
  - COMPOSITION — multiple primitives
  - (likely ADD + RECOLOR, or MOVE + RECOLOR)

**Puzzles**: [`e21a174a`](https://arcprize.org/tasks/e21a174a)

### `(SAME | TINY | RECOLOR | ISOLATED_CELLS | 2-3)` — 1 puzzles

**Likely L1 primitives**:
  - (unrecognised — open and review)

**Puzzles**: [`e4888269`](https://arcprize.org/tasks/e4888269)

### `(SAME | DENSE | ADD | ISOLATED_CELLS | 4-8)` — 1 puzzles

**Likely L1 primitives**:
  - mark_corners
  - scatter point ops
  - periodic_extension (periodic dots)

**Puzzles**: [`ea786f4a`](https://arcprize.org/tasks/ea786f4a)

