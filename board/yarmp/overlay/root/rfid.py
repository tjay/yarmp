import serial, re, time

last = {}
startbyte = "\x02"
rescan_timeout = 1.5

with serial.Serial("/dev/ttyAMA0", 9600) as serial:
  while True:
    if serial.read() == startbyte:
      d = map(lambda x: int(x,16), re.findall('..',serial.read(12)))
      chcksm = d[0]
      for pos in range(1, 5):
        chcksm = chcksm ^ d[pos]
      assert chcksm == d[5]
      id = ''.join('{:02X}'.format(x) for x in d[:5])
      read_time = time.time()
      if (id in last and read_time > last[id]) or id not in last:
         print id
         last[id] = read_time + rescan_timeout
