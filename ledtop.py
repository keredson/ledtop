import os, time

import psutil
import darp
import toml
import openrgb
import appdirs



class Display:

  def __init__(self, client, config):
  
    if 'device' not in config:
      raise Exception('device not defined in [cpu]')
    if isinstance(config['device'], int):
      device = client.devices[config['device']]
    elif isinstance(config['device'], str):
      device = client.get_devices_by_name(config['device'])[0]
    else:
      raise Exception('device must be a str or an int')
    device.set_mode('direct')
      
    for zone in device.zones:
      if isinstance(config['zone'], int) and config['zone']==zone.id:
        break
      if isinstance(config['zone'], str) and config['zone']==zone.name:
        break
    else:
      raise Exception(f"zone {config['zone']} not found")
    self.zone = zone
      
    if 'size' in config:
      self.size = config['size']
      zone.resize(config['size'])
      
    if 'leds' in config:
      led_start, led_end = [int(s) for s in config['leds'].split('-')]
      if led_start > led_end:
        self.leds = slice(led_end-1, led_start, -1)
      else:
        self.leds = slice(led_start-1, led_end)
    else:
      self.leds = slice(0, self.size)
    
    self.brightness = config.get('brightness', 100)
  
  def adjust_brightness(self, color):
    if self.brightness < 100:
      color = openrgb.utils.RGBColor(
        int(round(color.red*self.brightness/100)),
        int(round(color.green*self.brightness/100)),
        int(round(color.blue*self.brightness/100))
      )
    return color
    

class CPU(Display):

  def __init__(self, client, config):
    super().__init__(client, config)
    self.nice_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('nice_color', '#0000ff')))
    self.user_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('user_color', '#00ff00')))
    self.system_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('system_color', '#ff0000')))
    self.iowait_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('iowait_color', '#888888')))
    self.irq_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('irq_color', '#ffff00')))
    self.softirq_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('softirq_color', '#ff00ff')))
    self.idle_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('idle_color', '#000000')))
    
  def show(self, cpu_times):
    colors = []
    num_leds = abs(self.leds.stop - self.leds.start)
    cumulative = 0
    for kind in ['user','nice','system','iowait','irq','softirq']:
      colors[int(round(cumulative)):num_leds] = [getattr(self, kind+'_color')] * (num_leds - int(round(cumulative)))
      cumulative += num_leds * getattr(cpu_times, kind) / 100
    colors[int(round(cumulative)):num_leds] = [self.idle_color] * (num_leds - int(round(cumulative)))

    if self.leds.step == -1:
      self.zone.colors[self.leds.start:self.leds.stop] = reversed(colors)
    else:
      self.zone.colors[self.leds] = colors


class Memory(Display):

  def __init__(self, client, config):
    super().__init__(client, config)
    self.used_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('used_color', '#00ff00')))
    self.buffers_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('buffers_color', '#0000ff')))
    self.cached_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('cached_color', '#ff4400')))
    self.unused_color = self.adjust_brightness(openrgb.utils.RGBColor.fromHEX(config.get('unused_color', '#888888')))

  def show(self, svmem):
    colors = []
    num_leds = abs(self.leds.stop - self.leds.start)
    cumulative = 0
    for kind in ['used','buffers','cached']:
      colors[int(round(cumulative)):num_leds] = [getattr(self, kind+'_color')] * (num_leds - int(round(cumulative)))
      cumulative += num_leds * getattr(svmem, kind) / svmem.total
    colors[int(round(cumulative)):num_leds] = [self.unused_color] * (num_leds - int(round(cumulative)))

    if self.leds.step == -1:
      self.zone.colors[self.leds.start:self.leds.stop] = reversed(colors)
    else:
      self.zone.colors[self.leds] = colors



class LEDTop:

  def __init__(self, conf_fn):
    self.config = toml.load(conf_fn)
    print(self.config)
    self.client = openrgb.OpenRGBClient()
    self.cpus = []
    if 'cpu' in self.config:
      if isinstance(self.config['cpu'].get('device'), str):
        self.cpus.append(CPU(self.client, self.config['cpu']))
      for k,v in self.config['cpu'].items():
        if isinstance(v, dict):
          self.cpus.append(CPU(self.client, v))

    self.mems = []
    if 'memory' in self.config:
      if isinstance(self.config['memory'].get('device'), str):
        self.mems.append(Memory(self.client, self.config['memory']))
      for k,v in self.config['memory'].items():
        if isinstance(v, dict):
          self.mems.append(Memory(self.client, v))

    
  def reset_leds(self):
    seen = set()
    for cpu in self.cpus:
      if cpu.zone in seen: continue
      seen.add(cpu.zone)
      cpu.zone.colors = [cpu.idle_color] * cpu.size
        
  def show_all(self):
    seen = set()
    for cpu in self.cpus:
      if cpu.zone in seen: continue
      seen.add(cpu.zone)
      cpu.zone.show()
    
  def run(self):
    self.client.clear()
    while True:
      cpu_times = psutil.cpu_times_percent(interval=1, percpu=False)
      svmem = psutil.virtual_memory()
      self.reset_leds()
      for cpu in self.cpus:
        cpu.show(cpu_times)
      for mem in self.mems:
        mem.show(svmem)
      self.show_all()
    
  

def main(config:str=None):
  '''
    LEDTop
    https://github.com/keredson/ledtop
  '''
  if not config:
    config = os.path.join(appdirs.user_config_dir('LEDTop'), 'config.toml')
  if os.path.isfile(config):
    top = LEDTop(config)
    top.run()
  else:
    print(f'cannot find: {config}')
    print('Please create the file or set --config=<path>.')
    print('See documentation at: https://github.com/keredson/ledtop')


if __name__=='__main__':
  darp.prep(main).run()
