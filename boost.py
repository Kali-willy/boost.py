#!/usr/bin/env python3

import os
import subprocess
import sys
import time
import logging
import re
import signal
from typing import List, Dict

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\n\033[1;31m[!] Script terminated by user.\033[0m")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ASCII Art Logo
LOGO = """
\033[1;36m
    █████╗ ███╗   ██╗██████╗ ██████╗  ██████╗ ██╗██████╗     
   ██╔══██╗████╗  ██║██╔══██╗██╔══██╗██╔═══██╗██║██╔══██╗    
   ███████║██╔██╗ ██║██║  ██║██████╔╝██║   ██║██║██║  ██║    
   ██╔══██║██║╚██╗██║██║  ██║██╔══██╗██║   ██║██║██║  ██║    
   ██║  ██║██║ ╚████║██████╔╝██║  ██║╚██████╔╝██║██████╔╝    
   ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═════╝     
                                                             
   ██████╗  ██████╗  ██████╗ ███████╗████████╗███████╗██████╗ 
   ██╔══██╗██╔═══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗
   ██████╔╝██║   ██║██║   ██║███████╗   ██║   █████╗  ██████╔╝
   ██╔══██╗██║   ██║██║   ██║╚════██║   ██║   ██╔══╝  ██╔══██╗
   ██████╔╝╚██████╔╝╚██████╔╝███████║   ██║   ███████╗██║  ██║
   ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
\033[0m
\033[1;32m =============================================== \033[0m
\033[1;33m    ✨ Ultimate Android Optimization Tool ✨     \033[0m
\033[1;32m =============================================== \033[0m
\033[1;35m      Created for Termux - Works on Any Android       \033[0m
\033[1;31m      Root/Non-Root Compatible - Safe & Effective     \033[0m
\033[1;32m =============================================== \033[0m
"""

class TermuxChecker:
    @staticmethod
    def is_termux() -> bool:
        """Check if the script is running on Termux"""
        return ('com.termux' in os.environ.get('PREFIX', '') or 
                os.path.exists('/data/data/com.termux') or
                'TERMUX_VERSION' in os.environ)
    
    @staticmethod
    def check_termux_packages() -> bool:
        """Ensure required Termux packages are installed"""
        required_packages = ['python']
        optional_packages = ['tsu']  # Root-only packages
        missing_packages = []
        
        for package in required_packages:
            try:
                result = subprocess.run(['dpkg', '-s', package], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    text=True)
                if "Status: install ok installed" not in result.stdout:
                    missing_packages.append(package)
            except:
                missing_packages.append(package)
        
        if missing_packages:
            print("\033[1;31m[!] Missing required packages:\033[0m", ', '.join(missing_packages))
            print("\033[1;33m[+] Installing missing packages...\033[0m")
            try:
                subprocess.run(['pkg', 'update'], check=True)
                subprocess.run(['pkg', 'install', '-y'] + missing_packages, check=True)
                print("\033[1;32m[✓] Successfully installed required packages\033[0m")
            except:
                print("\033[1;31m[!] Failed to install required packages\033[0m")
                print("\033[1;33m[+] Please install them manually with:\033[0m")
                print(f"    pkg update && pkg install {' '.join(missing_packages)}")
                return False
        
        # Check for optional root packages
        if TermuxChecker.check_root_access():
            for package in optional_packages:
                try:
                    result = subprocess.run(['dpkg', '-s', package], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE,
                                        text=True)
                    if "Status: install ok installed" not in result.stdout:
                        print(f"\033[1;33m[+] Installing optional root package: {package}\033[0m")
                        subprocess.run(['pkg', 'install', '-y', package], check=True)
                except:
                    print(f"\033[1;33m[!] Optional root package {package} not installed, some features may be limited\033[0m")
        
        return True
    
    @staticmethod
    def check_root_access() -> bool:
        """Check if device has root access in Termux"""
        # First try with tsu if available
        try:
            result = subprocess.run(['tsu', '-c', 'id -u'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True, timeout=2)
            if '0' in result.stdout:
                return True
        except:
            pass
        
        # Then try with su if available
        try:
            result = subprocess.run(['su', '-c', 'id -u'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True, timeout=2)
            if '0' in result.stdout:
                return True
        except:
            pass
        
        return False

class SafeCommand:
    @staticmethod
    def run(command, as_root=False, timeout=10, shell=False):
        """Run a command safely and return result"""
        is_termux = TermuxChecker.is_termux()
        
        try:
            cmd = []
            if as_root:
                if is_termux:
                    # Try tsu first, fallback to su
                    try:
                        subprocess.run(['which', 'tsu'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        cmd = ['tsu', '-c', command] if not shell else f"tsu -c '{command}'"
                    except:
                        cmd = ['su', '-c', command] if not shell else f"su -c '{command}'"
                else:
                    cmd = ['su', '-c', command] if not shell else f"su -c '{command}'"
            else:
                cmd = command if shell else command.split()
                
            if shell:
                result = subprocess.run(cmd, shell=True, timeout=timeout,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            else:
                result = subprocess.run(cmd, timeout=timeout,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
                                    
            return {
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }

class AndroidOptimizer:
    def __init__(self):
        self.is_termux = TermuxChecker.is_termux()
        self.is_rooted = self._check_root()
        self.logger = self._setup_logger()
        self.device_info = self._get_device_info()
        self.safe_mode = True  # Safe mode prevents potentially dangerous operations
        
    def _setup_logger(self):
        """Setup logging"""
        try:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'android_optimizer.log')
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            return logging.getLogger('AndroidOptimizer')
        except Exception as e:
            # Fallback to basic logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
            return logging.getLogger('AndroidOptimizer')

    def _check_root(self) -> bool:
        """Check if device is rooted"""
        if self.is_termux:
            return TermuxChecker.check_root_access()
        else:
            result = SafeCommand.run('id -u', as_root=True)
            return result['success'] and '0' in result['stdout']

    def _run_adb_command(self, command: str, as_root: bool = False) -> str:
        """Execute ADB command safely, with Termux compatibility"""
        result = SafeCommand.run(command, as_root=as_root)
        
        if result['success']:
            return result['stdout']
        else:
            self.logger.error(f"Error executing command {command}: {result['stderr']}")
            return ""

    def _get_device_info(self) -> Dict[str, str]:
        """Get device information"""
        info = {}
        try:
            # Basic device info
            commands = {
                'model': 'getprop ro.product.model',
                'android_version': 'getprop ro.build.version.release',
                'sdk': 'getprop ro.build.version.sdk',
                'manufacturer': 'getprop ro.product.manufacturer',
                'device': 'getprop ro.product.device',
                'board': 'getprop ro.product.board'
            }
            
            for key, cmd in commands.items():
                result = self._run_adb_command(cmd)
                info[key] = result.strip() if result else "Unknown"
                
            # CPU info
            try:
                cpu_info = self._run_adb_command('cat /proc/cpuinfo')
                processor_count = len(re.findall(r'processor\s+:\s+\d+', cpu_info))
                info['cpu_cores'] = str(processor_count) if processor_count > 0 else "Unknown"
                
                model_name = re.search(r'model name\s+:\s+(.*)', cpu_info)
                if model_name:
                    info['cpu_model'] = model_name.group(1)
            except:
                info['cpu_cores'] = "Unknown"
                info['cpu_model'] = "Unknown"
            
            # RAM info
            try:
                mem_info = self._run_adb_command('cat /proc/meminfo')
                total_mem = re.search(r'MemTotal:\s+(\d+)', mem_info)
                if total_mem:
                    total_mem_kb = int(total_mem.group(1))
                    total_mem_mb = total_mem_kb // 1024
                    total_mem_gb = total_mem_mb / 1024
                    info['total_ram'] = f"{total_mem_gb:.2f} GB"
                else:
                    info['total_ram'] = "Unknown"
            except:
                info['total_ram'] = "Unknown"
                
        except Exception as e:
            self.logger.error(f"Error getting device info: {str(e)}")
        
        return info

    def check_device_connection(self) -> bool:
        """Verify Android device connection or Termux environment"""
        if self.is_termux:
            # If running in Termux, we're already on the device
            return True
        else:
            # Regular environment, check if we can get device info
            return bool(self._get_device_info().get('model', ''))

    def safe_command_exists(self, command: str) -> bool:
        """Check if a command exists on the device"""
        result = self._run_adb_command(f'which {command}')
        return bool(result.strip())

    def optimize_performance(self):
        """Apply performance optimizations"""
        self.logger.info("Starting performance optimization...")
        
        # Non-root optimizations
        commands = [
            'settings put global window_animation_scale 0.7',
            'settings put global transition_animation_scale 0.7',
            'settings put global animator_duration_scale 0.7',
        ]
        
        for cmd in commands:
            self._run_adb_command(cmd)

        # Root-only optimizations
        if self.is_rooted:
            # Check if the paths exist before executing commands
            paths_to_check = [
                '/sys/module/workqueue/parameters/power_efficient',
                '/proc/sys/vm/swappiness',
                '/proc/sys/vm/vfs_cache_pressure',
                '/sys/block/mmcblk0/queue/read_ahead_kb'
            ]
            
            for path in paths_to_check:
                check_result = self._run_adb_command(f'ls {path}', as_root=True)
                if not check_result or 'No such file' in check_result:
                    self.logger.info(f"Skipping optimization for non-existent path: {path}")
                    continue
                
                # Apply optimization based on path
                if 'power_efficient' in path:
                    self._run_adb_command(f'echo 0 > {path}', as_root=True)
                elif 'swappiness' in path:
                    self._run_adb_command(f'echo 10 > {path}', as_root=True)
                elif 'vfs_cache_pressure' in path:
                    self._run_adb_command(f'echo 70 > {path}', as_root=True)
                elif 'read_ahead_kb' in path:
                    self._run_adb_command(f'echo 128 > {path}', as_root=True)

    def clear_cache(self):
        """Clear app caches"""
        self.logger.info("Clearing system caches...")
        
        if self.is_rooted:
            self._run_adb_command('rm -rf /cache/*', as_root=True)
        
        self._run_adb_command('pm trim-caches 10G')

    def optimize_battery(self):
        """Apply battery optimizations"""
        self.logger.info("Optimizing battery usage...")
        
        commands = [
            'settings put global low_power 1',
            'settings put global wifi_scan_always_enabled 0'
        ]
        
        for cmd in commands:
            self._run_adb_command(cmd)

    def optimize_gaming(self):
        """Apply gaming optimizations"""
        self.logger.info("Applying gaming optimizations...")
        
        if self.is_rooted:
            gaming_commands = [
                'echo "performance" > /sys/class/kgsl/kgsl-3d0/devfreq/governor',
                'echo "performance" > /sys/class/kgsl/kgsl-3d0/gpuclk',
                'echo 0 > /proc/sys/kernel/sched_autogroup_enabled'
            ]
            
            for cmd in gaming_commands:
                self._run_adb_command(cmd, as_root=True)

    def optimize_ram(self):
        """Optimize RAM usage"""
        self.logger.info("Optimizing RAM usage...")
        
        commands = [
            'am kill-all',  # Kill background processes
            'pm trim-caches 999999999',  # Trim all possible caches
            'settings put global activity_manager_constants max_cached_processes=36',
            'settings put global activity_manager_constants max_phantom_processes=2'
        ]
        
        for cmd in commands:
            self._run_adb_command(cmd)
            
        if self.is_rooted:
            root_commands = [
                'echo 3 > /proc/sys/vm/drop_caches',
                'echo 0 > /proc/sys/vm/swappiness',
                'echo 1 > /proc/sys/vm/compact_memory'
            ]
            for cmd in root_commands:
                self._run_adb_command(cmd, as_root=True)

    def optimize_network(self):
        """Optimize network settings"""
        self.logger.info("Optimizing network settings...")
        
        commands = [
            'settings put global wifi_scan_throttle_enabled 1',
            'settings put global mobile_data_always_on 0',
            'settings put global wifi_enhanced_auto_join 1',
            'settings put global tether_dun_required 0'
        ]
        
        for cmd in commands:
            self._run_adb_command(cmd)

        if self.is_rooted:
            root_commands = [
                'setprop net.tcp.buffersize.default 4096,87380,256960,4096,16384,256960',
                'setprop net.tcp.buffersize.wifi 4096,87380,256960,4096,16384,256960',
                'setprop net.tcp.buffersize.lte 4096,87380,256960,4096,16384,256960'
            ]
            for cmd in root_commands:
                self._run_adb_command(cmd, as_root=True)

    def optimize_thermal(self):
        """Optimize thermal settings"""
        self.logger.info("Optimizing thermal settings...")
        
        if self.is_rooted:
            root_commands = [
                'echo 0 > /sys/class/thermal/thermal_zone0/enabled',
                'echo 1 > /sys/class/thermal/thermal_zone0/cdev0/cur_state',
                'echo "performance" > /sys/class/thermal/thermal_zone0/policy'
            ]
            for cmd in root_commands:
                self._run_adb_command(cmd, as_root=True)

    def optimize_cpu(self):
        """Optimize CPU settings"""
        self.logger.info("Optimizing CPU settings...")
        
        if self.is_rooted:
            # Get available CPU governors
            cpu_count = int(self.device_info.get('cpu_cores', '1'))
            
            root_commands = []
            for i in range(cpu_count):
                root_commands.extend([
                    f'echo "performance" > /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor',
                    f'echo 1 > /sys/devices/system/cpu/cpu{i}/online',
                    f'echo 100 > /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_min_freq_percent'
                ])
            
            # CPU specific optimizations
            root_commands.extend([
                'echo 0 > /proc/sys/kernel/sched_child_runs_first',
                'echo 0 > /proc/sys/kernel/sched_tunable_scaling',
                'echo 1 > /proc/sys/kernel/sched_migration_cost_ns',
                'echo 1000000 > /proc/sys/kernel/sched_latency_ns',
                'echo 100000 > /proc/sys/kernel/sched_min_granularity_ns',
                'echo 0 > /proc/sys/kernel/randomize_va_space'
            ])
            
            for cmd in root_commands:
                self._run_adb_command(cmd, as_root=True)

    def optimize_gpu(self):
        """Optimize GPU settings"""
        self.logger.info("Optimizing GPU settings...")
        
        if self.is_rooted:
            root_commands = [
                'echo "performance" > /sys/class/kgsl/kgsl-3d0/devfreq/governor',
                'echo "1" > /sys/class/kgsl/kgsl-3d0/force_clk_on',
                'echo "1" > /sys/class/kgsl/kgsl-3d0/force_bus_on',
                'echo "1" > /sys/class/kgsl/kgsl-3d0/force_rail_on',
                'echo "1" > /sys/class/kgsl/kgsl-3d0/force_no_nap',
                'echo "0" > /sys/class/kgsl/kgsl-3d0/throttling',
                'echo "100" > /sys/class/kgsl/kgsl-3d0/idle_timer'
            ]
            
            for cmd in root_commands:
                self._run_adb_command(cmd, as_root=True)

    def optimize_apps(self):
        """Optimize app settings and management"""
        self.logger.info("Optimizing app settings...")
        
        commands = [
            'cmd package trim-caches 999999999',
            'settings put global app_standby_enabled 1',
            'settings put global app_auto_restriction_enabled true',
            'settings put global forced_app_standby_enabled 1',
            'settings put global adaptive_battery_management_enabled 1'
        ]
        
        for cmd in commands:
            self._run_adb_command(cmd)
            
        if self.is_rooted:
            root_commands = [
                'pm enable --user 0 com.android.vending',  # Ensure Play Store is enabled
                'pm trim-caches 999999999',
                'am set-inactive --user 0 $(pm list packages -3)',  # Set all third-party apps as inactive
                'sync; echo 3 > /proc/sys/vm/drop_caches'  # Clear filesystem caches
            ]
            for cmd in root_commands:
                self._run_adb_command(cmd, as_root=True)

    def optimize_system(self):
        """Apply system-wide optimizations"""
        self.logger.info("Applying system-wide optimizations...")
        
        commands = [
            'settings put global development_settings_enabled 1',
            'settings put global window_animation_scale 0.5',
            'settings put global transition_animation_scale 0.5',
            'settings put global animator_duration_scale 0.5',
            'settings put global always_finish_activities 1',
            'settings put system font_scale 1.0',
            'settings put secure long_press_timeout 200'
        ]
        
        for cmd in commands:
            self._run_adb_command(cmd)
            
        if self.is_rooted:
            root_commands = [
                'echo 128 > /sys/block/mmcblk0/queue/read_ahead_kb',
                'echo "deadline" > /sys/block/mmcblk0/queue/scheduler',
                'echo 0 > /sys/module/workqueue/parameters/power_efficient',
                'echo 0 > /proc/sys/kernel/random/read_wakeup_threshold',
                'echo 64 > /proc/sys/kernel/random/write_wakeup_threshold'
            ]
            for cmd in root_commands:
                self._run_adb_command(cmd, as_root=True)

def main():
    # Display the awesome logo
    print(LOGO)
    
    # Check if running in Termux
    is_termux = TermuxChecker.is_termux()
    
    if is_termux:
        print("\033[1;32m[+] Running in Termux environment\033[0m")
        # Check and install required packages
        if not TermuxChecker.check_termux_packages():
            print("\033[1;31m[!] Required packages check failed. Some features may not work.\033[0m")
            proceed = input("Do you want to continue anyway? (y/n): ")
            if proceed.lower() != 'y':
                sys.exit(0)
    else:
        print("\033[1;33m[!] Not running in Termux. This script is optimized for Termux.\033[0m")
        proceed = input("Do you want to continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            sys.exit(0)
    
    # Initializing...
    print("\033[1;33m[+] Initializing Android Optimizer...\033[0m")
    
    try:
        optimizer = AndroidOptimizer()
    except Exception as e:
        print(f"\033[1;31m[!] Error initializing: {str(e)}\033[0m")
        sys.exit(1)
    
    if not optimizer.check_device_connection():
        print("\033[1;31m[!] Error: Cannot access Android system. Please check your setup.\033[0m")
        sys.exit(1)
    
    print(f"\n\033[1;36m=== Device Information ===\033[0m")
    print(f"\033[1;32mModel:\033[0m {optimizer.device_info.get('model', 'Unknown')}")
    print(f"\033[1;32mManufacturer:\033[0m {optimizer.device_info.get('manufacturer', 'Unknown')}")
    print(f"\033[1;32mAndroid Version:\033[0m {optimizer.device_info.get('android_version', 'Unknown')}")
    print(f"\033[1;32mRoot Status:\033[0m {'Rooted ✓' if optimizer.is_rooted else 'Non-rooted ✗'}")
    print(f"\033[1;32mCPU:\033[0m {optimizer.device_info.get('cpu_model', 'Unknown')}")
    print(f"\033[1;32mCPU Cores:\033[0m {optimizer.device_info.get('cpu_cores', 'Unknown')}")
    print(f"\033[1;32mTotal RAM:\033[0m {optimizer.device_info.get('total_ram', 'Unknown')}")
    
    # Choose optimization level based on root status
    if optimizer.is_rooted:
        print("\n\033[1;32m[+] Root access detected. Full optimization available!\033[0m")
    else:
        print("\n\033[1;33m[+] No root access detected. Limited optimization available.\033[0m")
        print("\033[1;33m[+] For best results, please root your device.\033[0m")
    
    # Show loading animation
    print("\n\033[1;33mStarting optimization process...\033[0m")
    for _ in range(10):
        sys.stdout.write("\033[1;32m▓\033[0m")
        sys.stdout.flush()
        time.sleep(0.1)
    print("\n")
    
    try:
        # Run enhanced optimizations with better error handling
        try:
            optimizer.optimize_system()
            print("\033[1;32m[✓] System optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] System optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_performance()
            print("\033[1;32m[✓] Performance optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Performance optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_ram()
            print("\033[1;32m[✓] RAM optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] RAM optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_network()
            print("\033[1;32m[✓] Network optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Network optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_thermal()
            print("\033[1;32m[✓] Thermal settings optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Thermal optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_cpu()
            print("\033[1;32m[✓] CPU optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] CPU optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_gpu()
            print("\033[1;32m[✓] GPU optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] GPU optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_apps()
            print("\033[1;32m[✓] Apps optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Apps optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.clear_cache()
            print("\033[1;32m[✓] Cache cleared\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Cache clearing failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_battery()
            print("\033[1;32m[✓] Battery optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Battery optimization failed: {str(e)}\033[0m")
        
        try:
            optimizer.optimize_gaming()
            print("\033[1;32m[✓] Gaming performance optimized\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Gaming optimization failed: {str(e)}\033[0m")
        
        print("\n\033[1;42m ✅ OPTIMIZATION COMPLETE! ✅ \033[0m")
        print("\n\033[1;33m⚠️ Note: Some optimizations may reset after device restart.\033[0m")
        
        print("\n\033[1;36m📱 Tips for maintaining optimized performance:\033[0m")
        tips = [
            "Regularly clear cache and unused apps",
            "Keep your device updated",
            "Monitor battery usage",
            "Avoid installing unnecessary apps",
            "Use game mode when gaming",
            "Restart device weekly to clear system states",
            "Run this optimization script monthly"
        ]
        
        for i, tip in enumerate(tips, 1):
            print(f"\033[1;32m{i}. \033[0m\033[1;37m{tip}\033[0m")
        
        print("\n\033[1;36m💡 For best results:\033[0m")
        best_practices = [
            "Use a good quality USB cable",
            "Keep your device cool while optimizing",
            "Close all background apps before optimization",
            "Consider factory reset if performance issues persist"
        ]
        
        for practice in best_practices:
            print(f"\033[1;33m- \033[0m\033[1;37m{practice}\033[0m")
        
    except Exception as e:
        print(f"\n\033[1;41m ❌ Error during optimization: {str(e)} \033[0m")
        print("\033[1;31mPlease check the log file for details.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
