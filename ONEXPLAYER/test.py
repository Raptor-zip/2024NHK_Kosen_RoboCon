import psutil
print(f"{psutil.sensors_battery().percent}%")