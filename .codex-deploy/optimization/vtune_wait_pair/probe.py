import math
import time

deadline = time.monotonic() + 2.5
value = 1.0
while time.monotonic() < deadline:
    value += math.sqrt(value % 113 + 0.5)
print(value)
