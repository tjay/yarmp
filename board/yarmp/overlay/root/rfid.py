import serial, re

with serial.Serial("/dev/ttyAMA0", 9600) as serial:
  while True:
    if "\x02" == serial.read():
      d =  map(lambda x: int(x,16), re.findall('..',serial.read(12)))
      chcksm = d[0]
      for pos in range(1, 5):
        chcksm = chcksm ^ d[pos]
      assert chcksm == d[5]
      print ''.join('{:02X}'.format(x) for x in d[:5])

