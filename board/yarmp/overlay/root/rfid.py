import serial, re

serialport = serial.Serial("/dev/ttyAMA0", 9600)

while True:
  if "\x02" == serialport.read():
    d =  map(lambda x: int(x,16), re.findall('..',serialport.read(12)))
    chcksm = d[0]
    for pos in range(1, 5):
      chcksm = chcksm ^ d[pos]
    assert chcksm == d[5]
    print ''.join('{:02X}'.format(x) for x in d[:5])
