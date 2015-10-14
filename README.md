Omnicalc to FloppyTunes Music Converter:
----------------------------------------

This python script takes 4 command line arguments and outputs binary data to standard out.
The binary data can be converted to an 8xp with any standard toolchain (e.g. WabbitSign).

The first argument is a string containing the song to be converted, in [Omnicalc play() format](http://www.detachedsolutions.com/omnicalc/manual/functions.php#play) (note: Omnicalc merely reimplements the QBasic version of the same function).
The following three arguments are the song title, album, and artist, as they will be displayed in FloppyTunes (at most 16 chars each).

Example usage:

`./makeft3.py "T180P2P8L8GGGL2E-P32.P8L8FFFL2D" "5th Symphony" "Omnicalc Manual" "Beethoven" > beethvn5.bin && wabbit beethvn5.bin beethvn5.8xp`
