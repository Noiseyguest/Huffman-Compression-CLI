import sys
import os
import heapq
import pickle
from collections import Counter

# node class used for the tree
class Node:
    __slots__ = ("freq", "byte", "left", "right")

    def __init__(self, freq, byte=None, left=None, right=None):
        self.freq = freq
        self.byte = byte
        self.left = left
        self.right = right

    # required so heapq can compare nodes when frequencies are equal
    def __lt__(self, other):
        return self.freq < other.freq


# builds the huffman tree from a dictionary of byte frequencies
def build_tree(freq_table):
    heap = []
    counter = 0  # used to break ties when two frequencies are equal
    for byte, freq in freq_table.items():
        heap.append((freq, counter, Node(freq, byte=byte)))
        counter = counter + 1
    heapq.heapify(heap)  # arranges the list into a valid heap

    # edge case: only one distinct byte value in the file
    if len(heap) == 1:
        freq, _, node = heap[0]
        return Node(freq, left=node)

    # repeatedly merge the two smallest nodes until one tree remains
    while len(heap) > 1:
        f1, _, n1 = heapq.heappop(heap)
        f2, _, n2 = heapq.heappop(heap)
        merged = Node(f1 + f2, left=n1, right=n2)
        heapq.heappush(heap, (merged.freq, counter, merged))
        counter = counter + 1

    return heap[0][2]  # remaining node is the root of the tree


# walks the tree and returns a dictionary of byte -> bit code
def build_codes(root):
    codes = {}

    def walk(node, path):
        if node == None:
            return
        if node.byte != None:
            # if the tree only has one leaf, path will be empty
            if path == "":
                codes[node.byte] = "0"
            else:
                codes[node.byte] = path
            return
        walk(node.left, path + "0")
        walk(node.right, path + "1")

    walk(root, "")
    return codes


# compresses a file using huffman coding
def compress(input_path, output_path):
    f = open(input_path, "rb")
    data = f.read()
    f.close()

    if len(data) == 0:
        # edge case: empty input file
        f = open(output_path, "wb")
        pickle.dump({}, f)
        f.write((0).to_bytes(4, "big"))
        f.close()
        print(input_path + " is empty, wrote an empty archive")
        return

    freq_table = Counter(data)
    tree = build_tree(freq_table)
    codes = build_codes(tree)

    # convert the file into one long string of 0s and 1s
    bitstring = ""
    for b in data:
        bitstring = bitstring + codes[b]

    # pad the bitstring so its length is a multiple of 8
    padding = (8 - len(bitstring) % 8) % 8
    bitstring = bitstring + "0" * padding

    # convert the bitstring into actual bytes
    packed = bytearray()
    i = 0
    while i < len(bitstring):
        chunk = bitstring[i:i+8]
        packed.append(int(chunk, 2))
        i = i + 8

    out = open(output_path, "wb")
    header = pickle.dumps(freq_table)  # stored so the file can be decoded later
    out.write(len(header).to_bytes(4, "big"))
    out.write(header)
    out.write(bytes([padding]))
    out.write(bytes(packed))
    out.close()

    original_size = len(data)
    compressed_size = os.path.getsize(output_path)
    ratio = (1 - compressed_size / original_size) * 100
    print("Compressed " + input_path + " (" + str(original_size) + " bytes) -> " + output_path + " (" + str(compressed_size) + " bytes), " + str(round(ratio, 1)) + "% smaller")


# reverses the compression process
def decompress(input_path, output_path):
    f = open(input_path, "rb")
    header_len_bytes = f.read(4)
    if len(header_len_bytes) < 4:
        raise ValueError("file is corrupt or empty")
    header_len = int.from_bytes(header_len_bytes, "big")
    header = f.read(header_len)
    freq_table = pickle.loads(header)

    if not freq_table:
        # original file was empty
        f.read(4)
        f.close()
        open(output_path, "wb").close()
        print("Restored empty file to " + output_path)
        return

    padding = f.read(1)[0]
    packed = f.read()
    f.close()

    # convert the bytes back into a string of 0s and 1s
    bitstring = ""
    for byte in packed:
        bitstring = bitstring + format(byte, '08b')

    if padding > 0:
        bitstring = bitstring[:-padding]  # remove the padding bits added during compression

    tree = build_tree(freq_table)  # rebuilds the same tree used during compression
    total_bytes = sum(freq_table.values())

    output = bytearray()
    node = tree
    for bit in bitstring:
        if bit == "0":
            node = node.left
        else:
            node = node.right
        if node.byte != None:
            output.append(node.byte)
            node = tree  # return to the root to decode the next byte
            if len(output) == total_bytes:
                break  # stop once all original bytes have been recovered

    out = open(output_path, "wb")
    out.write(bytes(output))
    out.close()

    print("Decompressed " + input_path + " -> " + output_path + " (" + str(len(output)) + " bytes)")


# entry point for running the script from the command line
def main():
    if len(sys.argv) < 3:
        print("Usage: python huffman.py compress/decompress <file>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    input_path = sys.argv[2]

    if mode == "compress":
        if len(sys.argv) > 3:
            output_path = sys.argv[3]
        else:
            output_path = input_path + ".huff"
        compress(input_path, output_path)
    elif mode == "decompress":
        if len(sys.argv) > 3:
            output_path = sys.argv[3]
        else:
            if input_path.endswith(".huff"):
                output_path = input_path[:-5]  # remove the .huff extension
            else:
                output_path = input_path + ".out"
        decompress(input_path, output_path)
    else:
        print("Unknown mode: " + mode + ". Use compress or decompress.")
        sys.exit(1)


if __name__ == "__main__":
    main()
