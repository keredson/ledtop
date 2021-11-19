# ledtop

Like `htop` (CPU and memory usage), but for your case LEDs. 😄

![Demo](demo.gif)

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

Example: 
```
[cpu]
device = 'B550I AORUS PRO AX'
zone = 'D_LED1'
size = 42
leds = '1-21'

[memory]
device = 'B550I AORUS PRO AX'
zone = 'D_LED1'
leds = '42-22'
brightness = 20
```

It has two section types, `cpu` and `memory` with the following options:

| Option | Details | Required |
|--------|---------|----------|
|`device`|A string or an integer, corresponding to OpenRGB's device name or ID.|✓|
|`zone`  |A string or an integer, corresponding to OpenRGB's zone name or ID.|✓|
|`size`  |The number of LEDs in your zone.|No, but recommended at least once.|
|`leds`  |Which LEDs to use (a range), inclusive starting at 1.  If the first number is larger than the second, the displayed order will be reversed.  (Say if your strip is mounted upside-down.)  Example: `1-21`|✓|
|`brightness`  |The brightness of your LEDs, an integer 0-100.||
|custom cpu colors|A hex RGB string like `#0000ff`. Options: `nice_color`, `user_color`, `system_color`, `iowait_color`, `irq_color`, `softirq_color`, `idle_color` |
|custom memory colors|A hex RGB string like `#ff4400`. Options: `used_color`, `buffers_color`, `cached_color`, `unused_color` |

If you want more than one display of each type, name them like:
```
[cpu.1]
...
[cpu.2]
...
```


