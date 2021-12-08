# ledtop

Like `htop` (CPU and memory usage), but for your case LEDs. 😄

![Demo](https://github.com/keredson/ledtop/raw/main/demo.gif)

In this setup, memory is the left strip, CPU is the right strip.

## Install

1. Install [OpenRGB](https://openrgb.org/).
2. Run: `$ pip install ledtop`


## Run
1. Launch OpenRGB.
2. Click the tab `SDK Server` and the button `Start Server`.
3. Run: `$ python -m ledtop`

## Configuration

The config file location is defined by [appdirs](https://pypi.org/project/appdirs/) (ex: `~/.config/ledtop/config.toml`) based on your OS, in [TOML](https://toml.io/en/) format.  If no config file exists, running `python -m ledtop` will tell you where it should be.

To see your detected devices, zones and sensors, run `python -m ledtop --info`.  Example:
```
$ python ledtop.py --info
--------------
 LED Displays
--------------
Device: 'B550I AORUS PRO AX' (id:0)
 - zone: 'D_LED1' (id:0)
 - zone: 'Motherboard' (id:1)

---------------------
 Temperature Sensors
---------------------
Device: 'acpitz'
 - sensor: '' (17°C)
Device: 'nvme'
 - sensor: 'Composite' (44°C)
Device: 'k10temp'
 - sensor: 'Tctl' (34°C)
 - sensor: 'Tdie' (34°C)
 - sensor: 'Tccd1' (45°C)
 - sensor: 'Tccd2' (42°C)
Device: 'iwlwifi_1'
 - sensor: '' (36°C)
```


Example configuration file: 
```
[cpu]
device = 'B550I AORUS PRO AX'
zone = 'D_LED1'
leds = '1-21'

[memory]
device = 'B550I AORUS PRO AX'
zone = 'D_LED1'
leds = '42-22'
brightness = 20

[temp.ssd]
device = 'B550I AORUS PRO AX'
zone = 'Motherboard'
component = 'nvme'
leds = '1-2'

[temp.cpu]
device = 'B550I AORUS PRO AX'
zone = 'Motherboard'
component = 'k10temp'
sensor = 'Tctl'
leds = '3-5'
```

There are three section types with the following options:

### Section: `cpu`

| Option | Details | Required |
|--------|---------|----------|
|`device`|A string or an integer, corresponding to OpenRGB's device name or ID.|✓|
|`zone`  |A string or an integer, corresponding to OpenRGB's zone name or ID.|✓|
|`size`  |The number of LEDs in your zone.  Will call `zone.resize()` in OpenRGB.|✓ (If not set by OpenRGB config.)|
|`leds` |Which LEDs to use (a range), inclusive starting at 1.  If the first number is larger than the second, the displayed order will be reversed.  (Say if your strip is mounted upside-down.)  Example: `1-21`|✓|
|`brightness`  |The brightness of your LEDs, an integer 0-100.||
|custom cpu colors|A hex RGB string like `#0000ff`. Options: `nice_color`, `user_color`, `system_color`, `iowait_color`, `irq_color`, `softirq_color`, `idle_color` |

### Section: `memory`

| Option | Details | Required |
|--------|---------|----------|
|`device`|A string or an integer, corresponding to OpenRGB's device name or ID.|✓|
|`zone`  |A string or an integer, corresponding to OpenRGB's zone name or ID.|✓|
|`size`  |The number of LEDs in your zone.  Will call `zone.resize()` in OpenRGB.||
|`leds` |Which LEDs to use (a range), inclusive starting at 1.  If the first number is larger than the second, the displayed order will be reversed.  (Say if your strip is mounted upside-down.)  Example: `41-22`|✓|
|`brightness`  |The brightness of your LEDs, an integer 0-100.||
|custom memory colors|A hex RGB string like `#ff4400`. Options: `used_color`, `buffers_color`, `cached_color`, `unused_color` |

### Section: `temp`

| Option | Details | Required |
|--------|---------|----------|
|`device`|A string or an integer, corresponding to OpenRGB's device name or ID.|✓|
|`zone`  |A string or an integer, corresponding to OpenRGB's zone name or ID.|✓|
|`size`  |The number of LEDs in your zone.  Will call `zone.resize()` in OpenRGB.||
|`leds` |Which LEDs to use (a range), inclusive starting at 1.  If the first number is larger than the second, the displayed order will be reversed.  (Say if your strip is mounted upside-down.)  Example: `1-4`|✓|
|`component` |The component (motherboard, CPU, SSD, etc.) to measure the temp of.  Run `python -m ledtop --info` to see what's detected.|✓|
|`sensor` |Some components have multiple sensors.  Run `python -m ledtop --info` to see your options.||
|`low` |Low temperature - integer in °C.  (Default: 20)||
|`high` |High temperature - integer in °C.  (Default: 90 or self-reported by the sensor.)||

If you want more than one display of each type, name them like:
```
[cpu.1]
...
[cpu.2]
...
```

## Colors

Default LED colors are the same as `htop`.  For CPU usage the color key is:
- Blue: low priority processes (nice > 0)
- Green: normal (user) processes.
- Red: kernel processes.
- Yellow: IRQ time.
- Magenta: Soft IRQ time.
- Grey: IO Wait time.

Memory:
- Green: Used memory pages.
- Blue: Buffer pages.
- Orange: Cache pages.
- Grey: Free (unused)

