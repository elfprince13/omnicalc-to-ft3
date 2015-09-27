#!/usr/bin/env python


import csv, re

notemap = {
	"C" : 0,
	"D" : 2,
	"E" : 4,
	"F" : 5,
	"G" : 7,
	"A" : 9,
	"B" : 11
}

mmap = {
	"N" : 0.875,
	"S" : 0.75,
	"L" : 1
}

def bpmToSeconds(bpm, divisor, default = 4):
	return (60. / bpm) * default / divisor



def main(argv):
	with open("octave-note-hl-de-table.csv", 'rU') as freqh:
		freqreader = csv.reader(freqh)
		
		ofmap = {}
		fcpairs = []
		for row, (octave, note, freq, cycles) in enumerate(freqreader):
			ofmap[(int(octave) if octave != 'R' else octave, note)] = row
			fcpairs.append((int(freq),int(cycles)))
		maxfreqindex = len(fcpairs) - 2
		
		instr = argv[1]
		T = 120 # bpm (in quarter notes)
		M = "N"
		O = 2
		L = 4 # note divisor
		o_ofs = -1
		
		pow2 = [2 ** i for i in range(7)]
		def s_X(scanner, token):
			return None
		def s_T(scanner, token):
			tval = int(token[1:])
			if tval >= 32 and tval <= 255:
				T = tval
			else:
				raise IndexError("T can only be in 32 -> 255")
			return None
		def s_M(scanner, token):
			if token[1] in mmap:
				M = token[1]
			else:
				raise IndexError("M can only be in [%s]" %  ", ".join(mmap.keys()))
		def s_L(scanner, token):
			lval = int(token[1:])
			if lval in pow2:
				L = lval
			else:
				raise IndexError("L can only be in %s" % str(pow2))
			return None
		def s_O(scanner, token):
			oval = int(token[1:])
			if oval >= 0 and oval <= 6:
				O = oval
			else:
				raise IndexError("O can only be in 0 -> 6")
			return None
		def s_UpDown(scanner, token):
			if token == "<":
				O -= 1
			elif token == ">":
				O += 1
			else:
				raise IndexError("Whattttt")
			return None
		
		rest_f, rest_c = fcpairs[ofmap[('R','R')]]
		def note_gen(index, dur, dot = False):
			rest =  index > maxfreqindex
			f, c = fcpairs[index]
			duration = bpmToSeconds(T, dur) * (1 + 0.5 * dot)
			if rest:
				return [(f, c * duration)]
			else:
				return [(f, c * duration * mmap[M]), (rest_f, rest_c * duration * (1 - mmap[M]))]
		
		def s_P(scanner, token):
			l_index = -1 if token[-1] == '.' else len(token)
			pval = int(token[1:l_index])
			if pval in pow2:
				return note_gen(ofmap[('R','R')], pval, l_index < 0)
			else:
				raise IndexError("P can only be in %s" % str(pow2))
			
		def s_N(scanner, token):
			nval = int(token[1:])
			if nval == 0:
				return s_P(scanner, "P%d" % L) # lol hax
			elif nval >= 1 and nval <= 84:
				return note_gen(nval - 13, L)
			else:
				raise IndexError("N can only be in 0 -> 84")
			
		def s_AG(scanner, token):
			note = token[0]
			modifier = len(token) > 1 and token[1] in "+-"
			dot = token[-1] == '.'
			dur = int(token[1 + modifier : -1 if dot else len(token)]) if len(token) > (1 + modifier + dot) else L # LOL EXTRA HAX
			modifier = (1 if modifier == "+" else -1) if modifier else 0
			note_index = ofmap[(O,note)] - 12 + modifier
			if note_index < 0:
				raise IndexError("your octave was too low or you took a bad flat: %s / %d" % (token, O))
			elif note_index > maxfreqindex:
				raise IndexError("your octave was too high or you took a bad sharp: %s / %d" % (token, O))
			elif dur not in pow2:
				raise IndexError("A-G can only be in %s" % str(pow2))
			else:
				return note_gen(note_index, dur, dot)
		
		
		scanner = re.Scanner([
			(r"X", s_X),
			(r"T[0-9]{2,3}", s_T),
			(r"M[NSL]", s_M),
			(r"L[0-9]{1,2}", s_L),
			(r"<|>", s_UpDown),
			(r"P[0-9]{1,2}\.?", s_P),
			(r"N[0-9]{1,2}", s_N),
			(r"[A-G][+-]?[0-9]{0,2}\.?", s_AG)])
		print scanner.scan(instr)
		
if __name__ == '__main__':
	import sys
	main(sys.argv)