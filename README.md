# Huffman-Compression-CLI

A Python command-line tool that compresses and decompresses files using Huffman coding, a lossless data compression algorithm.

# Huffman File Compressor

A command-line tool that compresses and decompresses files using Huffman coding. The implementation operates directly on raw bytes rather than text characters, so it can process any file type, including text files, images, and binary data.

## Table of Contents

* [How It Works](#how-it-works)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [Worked Example](#worked-example)
* [File Format](#file-format)
* [Things I Learned Building This](#things-i-learned-building-this)
* [Limitations](#limitations)

## How It Works

Huffman coding assigns shorter binary codes to frequently occurring bytes and longer codes to less frequent ones. This reduces the average number of bits required to represent the data compared with a fixed 8-bit representation.

The process:

1. Count how often each byte value appears in the file.
2. Build a binary tree by repeatedly merging the two least frequent nodes.
3. Generate a bit code for each byte based on its path from the root of the tree (left = `0`, right = `1`).
4. Replace every byte in the file with its corresponding Huffman code and pack the resulting bit sequence into bytes for the compressed output.

Decompression reverses this process. It reconstructs the Huffman tree from the stored frequency table, then walks the tree bit by bit to recover the original byte sequence.

## Requirements

* Python 3
* No external dependencies (standard library only)

## Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

No `pip install` is required — the script can be run directly with Python.

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

If no output file is given, the program strips the `.huff` extension, or appends `.out` if the input file does not end in `.huff`.

### Example

```bash
python huffman.py compress notes.txt
# -> Compressed notes.txt (522 bytes) -> notes.txt.huff (463 bytes), 11.3% smaller

python huffman.py decompress notes.txt.huff restored.txt
# -> Decompressed notes.txt.huff -> restored.txt (522 bytes)
```

## Worked Example

Consider the byte sequence `AAABBC` (6 bytes: A×3, B×2, C×1).

1. **Frequencies:** `{A: 3, B: 2, C: 1}`
2. **Build the tree:** merge the two smallest nodes first — C(1) and B(2) combine into a node with weight 3. That node then merges with A(3) to form the root with weight 6.
3. **Codes from root to leaf:** `A = 0`, `B = 11`, `C = 10`. A, the most frequent byte, receives the shortest code.
4. **Encode:** `A A A B B C` → `0 0 0 11 11 10` → the bitstring `000111110` (9 bits).
5. **Pad to a full byte:** 9 bits requires 7 zero-padding bits to reach 16 bits (2 bytes).
6. **Result:** the encoded payload is 2 bytes instead of the original 6 bytes. However, for a file this small, the stored frequency-table header adds significantly more overhead than the payload saves, so compression only becomes useful when the file is large enough and contains enough repetition.

| File                    | Original Size | Compressed Size | Reduction |
| ----------------------- | ------------- | --------------- | --------- |
| Small text sample       | 522 bytes     | 463 bytes       | 11.3%     |
| Larger, repetitive text | 105,410 bytes | 57,306 bytes    | 45.6%     |

The compression ratio depends heavily on the distribution of byte frequencies. The more uneven the distribution, the more opportunity Huffman coding has to assign shorter codes to common bytes and reduce the overall size.

## File Format

A `.huff` file consists of:

| Section       | Size            | Description                                                                                  |
| ------------- | --------------- | -------------------------------------------------------------------------------------------- |
| Header length | 4 bytes         | Length of the pickled frequency table that follows                                           |
| Header        | variable        | Pickled `{byte: frequency}` table, used to reconstruct the Huffman tree during decompression |
| Padding count | 1 byte          | Number of padding bits appended to the final byte                                            |
| Packed data   | remaining bytes | The Huffman-encoded file contents                                                            |

## Things I Learned Building This

* **Prefix codes make the encoded data unambiguous.** Every symbol is stored at a leaf of the Huffman tree, so no symbol's root-to-leaf path can be a prefix of another symbol's path. This means the decoder can determine where one code ends and the next begins without needing separators between codes.

* **`heapq` needs a way to break ties between nodes.** When two nodes have the same frequency, Python cannot directly compare two plain `Node` objects. I solved this by storing `(frequency, insertion_counter, node)` tuples in the heap. The counter is unique for each entry, so it provides a deterministic tie-breaker before Python ever needs to compare the `Node` objects themselves.

* **Bits do not always line up neatly into bytes.** The encoded bitstream will usually not contain a number of bits divisible by 8, so the final byte has to be padded with zeros. I also need to store the number of padding bits because the decoder otherwise cannot distinguish actual encoded data from the padding.

* **The decoder needs to reconstruct the same coding tree.** Storing the entire tree would work, but it is unnecessary here. The frequency table contains enough information to reconstruct the tree, provided that the same tie-breaking rules are used when building it. This is why the implementation also needs deterministic heap ordering when multiple nodes have equal frequencies.

* **Small files can become larger after compression.** This is expected rather than a bug. The frequency table adds a fixed amount of metadata to every compressed file, and for a small input, that overhead can be larger than the space saved by Huffman coding.

* **Edge cases matter more than the normal path.** A file containing only one distinct byte value produces a tree with a single leaf. Normally, its root-to-leaf path would be empty, which would result in an invalid zero-bit code. I handle this explicitly by giving the single symbol a 1-bit code instead.

## Limitations

* Small or already-compressed files may become larger after compression because the stored frequency table adds overhead that can outweigh the space saved by Huffman coding.
* Compression effectiveness depends on the distribution of byte frequencies. Highly repetitive files generally compress well, while high-entropy data — such as already-compressed or encrypted data — typically provides little opportunity for Huffman coding to reduce its size.
