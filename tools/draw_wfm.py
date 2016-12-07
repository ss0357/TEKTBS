import numpy as np
import matplotlib.pyplot as plt
import os
import sys
os.chdir(r'D:\SQA\Cornerstone\funcTests')

filename = sys.argv[1]
x, y = [], []


with open(filename, mode='r') as report:
    content = report.read()

content2 = content.split('\n')
rec_length = int(content2[8].split(',')[-1])
print('rec_length: %d' % rec_length)


hor_scale = float(content2[5].split(',')[-1])
vert_scale = float(content2[13].split(',')[-1])

print('hor_scale: %f' % hor_scale)
print('vert_scale: %f' % vert_scale)

for i in range(17, rec_length+17):
    xi = content2[i-1].split(',')[0]
    yi = content2[i-1].split(',')[1]
    x.append(xi)
    y.append(yi)
    #print(i,xi,yi)



fig, ax = plt.subplots()
ax.plot(x, y, linewidth=2)

#x_divs = int((float(x[-1]) - float(x[0]))/hor_scale) + 2
ax.set_xlim((float(x[0])-hor_scale, float(x[-1])+hor_scale))
ax.set_xticks([x*hor_scale  for x in range(-8, 9)])
#ax.set_xticklabels([x for x in range(-25, 25, 5)])
ax.set_ylim((-5*vert_scale,5*vert_scale))
ax.set_yticks([x*vert_scale for x in range(-5,6)])


ax.axhline(0, color='black', lw=2)
ax.axvline(0, color='black', lw=2)


plt.grid(True)
plt.show()