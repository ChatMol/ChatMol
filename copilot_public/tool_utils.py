import os

class StructPair:
    def __init__(self, p1, p2) -> None:
        self.p1 = p1
        self.p2 = p2

    def tmalign(self):
        # print(os.popen(f"TMalign {self.p1} {self.p2}").read())
        self._tmalign_out_parser(os.popen(f"TMalign {self.p1} {self.p2}").read())

    def _tmalign_out_parser(self, tmalign_outstring):
        lst = tmalign_outstring.splitlines()[1:]
        _, _, aligned_length, _, rmsd, _, identity = lst[15].split()
        self.aligned_length = int(aligned_length[:-1])
        self.rmsd = float(rmsd[:-1])
        self.identity = float(identity)
        self.tmscore_p1 = float(lst[16].split()[1])
        self.tmscore_p2 = float(lst[17].split()[1])
        self.aligned_seq1 = lst[21]
        self.aligned_seq2 = lst[23]