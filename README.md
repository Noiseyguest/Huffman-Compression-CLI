# Huffman-Compression-CLI
A python script which uses the concepts of huffman encoding to compress simple text files

# Huffman File Compressor

![Python](https://img.shields.io/badge/python-3.x-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![No Dependencies](https://img.shields.io/badge/dependencies-none-lightgrey)

A command-line tool that compresses and decompresses files using Huffman coding, a lossless data compression algorithm. Works on any file type (text, images, binaries, etc.) since it operates directly on raw bytes.

## Table of Contents

- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Worked Example](#worked-example)
- [File Format](#file-format)
- [Things I Learned Building This](#things-i-learned-building-this)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## How It Works

Huffman coding assigns shorter binary codes to frequently occurring bytes and longer codes to rare ones, reducing the average number of bits needed per byte compared to a fixed 8-bit encoding.

The process:

1. Count how often each byte value appears in the file.
2. Build a binary tree by repeatedly merging the two least frequent nodes.
3. Generate a bit code for each byte based on its path from the root of the tree (left = `0`, right = `1`).
4. Replace every byte in the file with its code and pack the resulting bits into a compressed output file.

Decompression reverses this: it rebuilds the same tree from the stored frequency table, then walks the tree bit by bit to recover the original bytes.

## Requirements

- Python 3
- No external dependencies (standard library only)

## Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

No `pip install` needed — just run the script directly with Python.

## Usage

**Compress a file:**
```bash
python huffman.py compress <input_file> [output_file]
```
If no output file is given, it defaults to `<input_file>.huff`.

**Decompress a file:**
```bash
python huffman.py decompress <input_file> [output_file]
```
If no output file is given, it strips the `.huff` extension, or appends `.out` if the input doesn't end in `.huff`.

### Example

```bash
python huffman.py compress notes.txt
# -> Compressed notes.txt (522 bytes) -> notes.txt.huff (463 bytes), 11.3% smaller

python huffman.py decompress notes.txt.huff restored.txt
# -> Decompressed notes.txt.huff -> restored.txt (522 bytes)
```

## Worked Example

Take the string `AAABBC` (6 bytes: A×3, B×2, C×1).

1. **Frequencies:** `{A: 3, B: 2, C: 1}`
2. **Build the tree:** merge the two smallest first — C(1) and B(2) combine into a node of weight 3. That node then merges with A(3) to form the root (weight 6).
3. **Codes from root to leaf:** `A = 0`, `B = 11`, `C = 10`. Notice A, the most frequent byte, gets the shortest code.
4. **Encode:** `A A A B B C` → `0 0 0 11 11 10` → the bitstring `000111110` (9 bits).
5. **Pad to a full byte:** 9 bits needs 7 zero bits of padding to reach 16 bits (2 bytes).
6. **Result:** the payload shrinks from 6 bytes to 2 bytes — though for a file this small, the stored frequency-table header adds more overhead than that saves, which is why compression only pays off on larger files with real repetition.

| File | Original Size | Compressed Size | Reduction |
|---|---|---|---|
| Small text sample | 522 bytes | 463 bytes | 11.3% |
| Larger, repetitive text | 105,410 bytes | 57,306 bytes | 45.6% |

The gain scales with how skewed the byte-frequency distribution is.

## File Format

A `.huff` file consists of:

| Section | Size | Description |
|---|---|---|
| Header length | 4 bytes | Length of the pickled frequency table that follows |
| Header | variable | Pickled `{byte: frequency}` table, used to rebuild the tree during decompression |
| Padding count | 1 byte | Number of padding bits appended to the final byte |
| Packed data | remaining bytes | The Huffman-encoded file contents |

## Things I Learned Building This

- **Prefix codes only work because data lives at leaves.** Every symbol sits at a leaf of the tree, and a leaf's root-to-leaf path can never be a prefix of another leaf's path — so the tree structure itself guarantees unambiguous decoding, with no separators needed between codes.
- **`heapq` needs a strict way to compare nodes, even when frequencies tie.** Pushing plain `Node` objects onto the heap breaks the moment two nodes share a frequency, since Python doesn't know how to order them. The fix was pushing `(frequency, insertion_counter, node)` tuples instead — tuples compare element by element, so the unique counter guarantees a tie is always resolved before Python ever has to compare two `Node` objects directly.
- **Bits don't divide evenly into bytes.** Encoded data is rarely a multiple of 8 bits long, so it has to be padded with zeros before it can be packed into whole bytes — and that padding count has to be stored somewhere, or decompression can't tell where real data ends and padding begins.
- **The decoder needs the exact same tree, not just "a valid" tree.** Storing the frequency table (rather than the tree structure itself) works because tree-building is deterministic: feeding the same frequencies into the same algorithm always produces the identical tree.
- **Small files can get bigger, not smaller.** This felt like a bug at first, but it's inherent to the algorithm — the frequency-table header has a fixed cost, and on a small file that overhead can outweigh whatever bits were saved by shorter codes.
- **Edge cases matter more than the "normal" path.** A file with only one distinct byte value produces a tree with just one leaf, which breaks normal root-to-leaf code generation (the path would be empty). Handling this required an explicit check to wrap that single leaf under an artificial root so it still gets a valid 1-bit code.

## Limitations

- Small or already-compressed files may end up *larger* after compression, since the stored frequency table adds overhead that can outweigh the savings.
- Compression ratio depends entirely on how skewed the byte frequency distribution is — highly repetitive files compress well, while high-entropy files (e.g. already-compressed or encrypted data) compress little or not at all.

## Contributing

Issues and pull requests are welcome. If you spot a bug or want to extend this (e.g. canonical Huffman codes to shrink the header, or adaptive Huffman coding), feel free to open a PR.
