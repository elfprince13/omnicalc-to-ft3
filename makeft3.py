#!/usr/bin/env python


import csv, re, sys

mmap = {
	"N" : 0.875,
	"S" : 0.75,
	"L" : 1
}

def bpmToSeconds(bpm, divisor, default = 4):
	return (60. / bpm) * default / divisor

def cantbin(verb,arg):
	import sys
	print ""
	raise TypeError("Don't know how to %s this %s: %s" % (verb,repr(type(arg)),repr(arg)))

def db(*args):
	return "".join([chr(arg) if type(arg) == int else (arg if type(arg) == str else cantbin("db",arg)) for arg in args])
			
	
		
def dw(*args):
	# z80 is Little-Endian
	return "".join([(chr(arg % 256) + chr(arg / 256)) if type(arg) == int and not arg / 65536 else cantbin("dw",arg) for arg in args])


def header(title, artist, album):
	return	db(0xBB,0x6D)+\
			db(0xC9)+\
			db(0x31,0x80)+\
			db(0,2,4)+\
			db(title,0)+\
			db(artist,0)+\
			db(album,0)
	
def footer(): 
	return dw(0,0)

def main(argv):
	global T, M, O, L, DEBUG
	with open("octave-note-hl-de-table.csv", 'rU') as wvlenh:
		wvlenreader = csv.reader(wvlenh)
		
		ofmap = {}
		fcpairs = []
		for row, (octave, note, wvlen, cycles) in enumerate(wvlenreader):
			ofmap[(int(octave) if octave != 'R' else octave, note)] = row
			fcpairs.append((int(wvlen),int(cycles)))
		maxwvlenindex = len(fcpairs) - 2
		
		instr = argv[1]
		T = 120 # bpm (in quarter notes)
		M = "N"
		O = 2
		L = 4 # note divisor
		o_ofs = -1
		
		DEBUG = False
		def print_token(token):
			global DEBUG, T,M,O,L
			if DEBUG: print T,M,O,L, token
		
		pow2 = [2 ** i for i in range(7)]
		def s_X(scanner, token):
			print_token(token)
			return None
		def s_T(scanner, token):
			global T
			print_token(token)
			tval = int(token[1:])
			if tval >= 32 and tval <= 255:
				T = tval
			else:
				raise IndexError("T can only be in 32 -> 255")
			return None
		def s_M(scanner, token):
			global M
			print_token(token)
			if token[1] in mmap:
				M = token[1]
			else:
				raise IndexError("M can only be in [%s]" %  ", ".join(mmap.keys()))
		def s_L(scanner, token):
			global L
			print_token(token)
			lval = int(token[1:])
			if lval in pow2:
				L = lval
			else:
				raise IndexError("L can only be in %s" % str(pow2))
			return None
		def s_O(scanner, token):
			global O
			print_token(token)
			oval = int(token[1:])
			if oval >= 0 and oval <= 6:
				O = oval
			else:
				raise IndexError("O can only be in 0 -> 6")
			return None
		def s_UpDown(scanner, token):
			global O
			print_token(token)
			if token == "<":
				O -= 1
			elif token == ">":
				O += 1
			else:
				raise IndexError("Whattttt")
			return None
		
		rest_f, rest_c = fcpairs[ofmap[('R','R')]]
		def note_gen(index, dur, dot = 0):
			rest =  index > maxwvlenindex
			f, c = fcpairs[index]
			duration = bpmToSeconds(T, dur) * (1.5 ** dot)
			if rest:
				#print "Explicit rest", c*duration, c, duration
				cdur = int(round(c*duration,0))
				if cdur > 65535:
					reps = [(f,65535)] * (cdur / 65535)
					if cdur % 65535:
						reps += [(f,cdur % 65535)]
					return reps
				else:
					return [(f, cdur)]
			else:
				#print "Implicit rest", rest_c*duration*(1 - mmap[M]), rest_c, duration, (1 - mmap[M])
				# we probably should have some warning here if it's too long
				return [(f, c * duration * mmap[M])]  + ([(rest_f, rest_c * duration * (1 - mmap[M]))] if (1 - mmap[M]) else [])
		
		def s_P(scanner, token, suppress_debug = False):
			if not suppress_debug: print_token(token)
			l_index = token.find(".") if token[-1] == '.' else len(token)
			pval = int(token[1:l_index])
			if pval in pow2:
				return note_gen(ofmap[('R','R')], pval, l_index < 0)
			else:
				raise IndexError("P can only be in %s" % str(pow2))
			
		def s_N(scanner, token):
			print_token(token)
			nval = int(token[1:])
			if nval == 0:
				return s_P(scanner, "P%d" % L, True) # lol hax
			elif nval >= 1 and nval <= 84:
				return note_gen(nval - 13, L)
			else:
				raise IndexError("N can only be in 0 -> 84")
			
		def s_AG(scanner, token):
			print_token(token)
			note = token[0]
			modifier = len(token) > 1 and token[1] in "+-"
			dot = token.count(".")
			dur = int(token[1 + modifier : -1 if dot else len(token)]) if len(token) > (1 + modifier + dot) else L # LOL EXTRA HAX
			modifier = (1 if modifier == "+" else -1) if modifier else 0
			note_index = ofmap[(O,note)] - 12 + modifier
			if note_index < 0:
				raise IndexError("your octave was too low or you took a bad flat: %s / %d" % (token, O))
			elif note_index > maxwvlenindex:
				raise IndexError("your octave was too high or you took a bad sharp: %s / %d" % (token, O))
			elif dur not in pow2:
				raise IndexError("A-G can only be in %s" % str(pow2))
			else:
				return note_gen(note_index, dur, dot)
		
		def panic(cycles):
			cycles = int(round(cycles, 0))
			if cycles:
				return cycles
			else:
				raise ValueError("panic (0)")
		
		scanner = re.Scanner([
			(r"X", s_X),
			(r"T[0-9]{2,3}", s_T),
			(r"M[NSL]", s_M),
			(r"L[0-9]{1,2}", s_L),
			(r"<|>", s_UpDown),
			(r"P[0-9]{1,2}\.*", s_P),
			(r"N[0-9]{1,2}", s_N),
			(r"[A-G][+-]?[0-9]{0,2}\.*", s_AG)])
		output = "".join([header(*argv[2:])] + [dw(wvlen,panic(cycles)) for wvlen, cycles in reduce(lambda a,b:a+b,scanner.scan(instr)[0],[])] + [footer()])
		sys.stdout.write(output)
		sys.stdout.flush()
		
if __name__ == '__main__':
	main(sys.argv)