import matplotlib.pyplot as plt

packetLossProb = []
fileSize = []  
tct = []
at = []


f = open('performance.txt','r')
for row in f:
    row = row.split(',')
    packetLossProb.append(row[0])
    fileSize.append(row[1])
    tct.append(row[2])
    at.append(float(row[3].strip('\n')))

f = plt.figure(figsize=(11,4))

#plt.yticks(tct)
plt.subplot(1, 2, 1)
plt.plot(packetLossProb, tct, marker = 'o', c = 'g', label="lossVSTCT")
plt.title("Packet Loss vs Time to Receive Bytes (TCT)")
plt.xlabel('Packet Loss Rate')
plt.ylabel('Time taken to Receive')
#plt.legend(['lossVSTCT'], ['ltct'])
plt.legend()
plt.legend(loc='upper left')
#plt.show()

plt.subplot(1, 2, 2)
plt.plot(packetLossProb, at, marker = 'o', c = 'g', label="lossVSAT")
plt.title("Packet Loss vs Average Throughput (AT)")
plt.xlabel('Packet Loss Rate')
plt.ylabel('Average Throughput')
#plt.legend(['lossVSAT'], ['lat'])
plt.legend()
plt.legend(loc='upper left')

plt.tight_layout()
plt.show()