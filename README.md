# ledtop

Like `htop` (CPU and memory usage), but for your case LEDs. 😄

![Demo](demo.gif)

In this setup, memory is the left strip, CPU is the right strip.

## Install

```
$ pip install ledtop
```

## Configure

Example (`~/.config/ledtop/config.toml`):
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
