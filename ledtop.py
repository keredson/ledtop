import os, sys, time

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
    else:
      self.size = len(zone.leds)
      
    if 'leds' in config:
      if '-' in config['leds']:
        led_start, led_end = [int(s) for s in config['leds'].split('-')]
        if led_start > led_end:
          self.leds = slice(led_end-1, led_start, -1)
        else:
          self.leds = slice(led_start-1, led_end)
      elif config['leds'].isnumeric():
        self.leds = slice(int(config['leds'])-1, int(config['leds']))
    elif 'led' in config:
      self.leds = slice(config['led']-1, config['led'])
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


class Temp(Display):

  def __init__(self, client, config):
    super().__init__(client, config)
    self.component = config.get('component')
    self.sensor = config.get('sensor')
    self.low = config.get('low')
    self.high = config.get('high')
    
  def show(self, temps):
    if self.component:
      component = temps[self.component]
    else:
      component = temps.items()[0][1]
    if self.sensor:
      sensor = [s for s in component if s.label==self.sensor][0]
    else:
      sensor = component[0]
    low = self.low or 20
    high = self.high or sensor.high or 90
    temp = (sensor.current - low) / (high - low) # [0-1]
    temp = max(temp,0)
    temp = min(temp,1)
    color = openrgb.utils.RGBColor(
      int(round((255 * temp))),
      int(round(128*(1-temp))),
      0
    )
    num_leds = abs(self.leds.stop - self.leds.start)
    self.zone.colors[self.leds] = [color] * num_leds
    



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

    self.temps = []
    if 'temp' in self.config:
      if isinstance(self.config['temp'].get('device'), str):
        self.temps.append(Temp(self.client, self.config['temp']))
      for k,v in self.config['temp'].items():
        if isinstance(v, dict):
          self.temps.append(Temp(self.client, v))

    
  def reset_leds(self):
    seen = set()
    for cpu in self.cpus + self.mems + self.temps:
      if cpu.zone in seen: continue
      seen.add(cpu.zone)
      cpu.zone.colors = [openrgb.utils.RGBColor(0,0,0)] * cpu.size
        
  def show_all(self):
    seen = set()
    for cpu in self.cpus + self.mems + self.temps:
      if cpu.zone in seen: continue
      seen.add(cpu.zone)
      cpu.zone.show()
    
  def run(self):
    self.client.clear()
    while True:
      cpu_times = psutil.cpu_times_percent(interval=1, percpu=False)
      svmem = psutil.virtual_memory()
      temps = psutil.sensors_temperatures()
      self.reset_leds()
      for cpu in self.cpus:
        cpu.show(cpu_times)
      for mem in self.mems:
        mem.show(svmem)
      for temp in self.temps:
        temp.show(temps)
      self.show_all()
    
  

def main(config:str=None, info:bool=False):
  '''
    https://github.com/keredson/ledtop
  '''
  
  if info:
  
    print('--------------')
    print(' LED Displays')
    print('--------------')
    client = openrgb.OpenRGBClient()
    for device in client.devices:
      print(f'Device: {repr(device.name)} (id:{device.id})')
      for zone in device.zones:
        print(f' - zone: {repr(zone.name)} (id:{zone.id})')
        
      
  
    print()
    print('---------------------')
    print(' Temperature Sensors')
    print('---------------------')
    for dev, sensors in psutil.sensors_temperatures().items():
      print(f'Device: {repr(dev)}')
      for sensor in sensors:
        print(f' - sensor: {repr(sensor.label)} ({int(round(sensor.current))}°C)')
    print('\n[https://github.com/keredson/ledtop]')
    sys.exit(0)
  
  if not config:
    config = os.path.join(appdirs.user_config_dir('ledtop'), 'config.toml')
  if os.path.isfile(config):
    top = LEDTop(config)
    top.run()
  else:
    print(f'cannot find: {config}')
    print('Please create the file or set --config=<path>.')
    print('See documentation at: https://github.com/keredson/ledtop')


if __name__=='__main__':
  darp.prep(main).run()
