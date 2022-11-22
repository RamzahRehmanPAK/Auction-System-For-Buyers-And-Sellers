import matplotlib.pyplot as plt
  
tct = []
at = []
plp = [0.1, 0.2, 0.3, 0.4, 0.5]

f = open('testLog.txt','r')
for row in f:
    row = row.split('=')
    tct.append(row[0])
    at.append(float(row[1].strip('\n')))


f = plt.figure(figsize=(11,4))

#plt.yticks(tct)
plt.subplot(1, 2, 1)
plt.plot(plp, tct, marker = 'o', c = 'g', label="lossVSTCT")
plt.title("Packet Loss vs Time to Receive Bytes (TCT)")
plt.xlabel('Packet Loss Rate')
plt.ylabel('Time taken to Receive')
#plt.legend(['lossVSTCT'], ['ltct'])
plt.legend()
plt.legend(loc='upper left')
#plt.show()

plt.subplot(1, 2, 2)
plt.plot(plp, at, marker = 'o', c = 'g', label="lossVSAT")
plt.title("Packet Loss vs Average Throughput (AT)")
plt.xlabel('Packet Loss Rate')
plt.ylabel('Average Throughput')
#plt.legend(['lossVSAT'], ['lat'])
plt.legend()
plt.legend(loc='upper left')

plt.tight_layout()
plt.show()