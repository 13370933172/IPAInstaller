import argparse
import asyncio
import os
import sys
import zipfile
import plistlib
import posixpath
from datetime import datetime
from pathlib import Path

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.usbmux import list_devices


async def list_connected_devices():
    devices = await list_devices()
    if not devices:
        print("未检测到已连接的 iOS 设备。")
        print("请确保：")
        print("  1. iOS 设备已通过 USB 连接到电脑")
        print("  2. 设备已解锁并信任此电脑")
        print("  3. 已安装 iTunes 或 Apple 设备驱动程序")
        return []

    print(f"检测到 {len(devices)} 台设备：")
    device_list = []
    for i, device in enumerate(devices):
        try:
            lockdown = await create_using_usbmux(serial=device.serial)
            device_name = lockdown.all_values.get("DeviceName", "未知设备")
            ios_version = lockdown.all_values.get("ProductVersion", "未知")
            device_type = lockdown.all_values.get("ProductType", "未知")
            print(f"  [{i}] {device_name} ({device_type}) - iOS {ios_version}")
            print(f"      UDID: {device.serial}")
            device_list.append({
                "serial": device.serial,
                "name": device_name,
                "version": ios_version,
                "type": device_type,
                "connection_type": device.connection_type,
            })
        except Exception as e:
            print(f"  [{i}] 无法获取设备信息: {e}")
            device_list.append({
                "serial": device.serial,
                "name": "未知",
                "version": "未知",
                "type": "未知",
                "connection_type": device.connection_type,
            })
    return device_list


def extract_ipa_info(ipa_path):
    if not os.path.exists(ipa_path):
        raise FileNotFoundError(f"IPA 文件不存在: {ipa_path}")

    if not ipa_path.lower().endswith(".ipa"):
        raise ValueError(f"文件不是 IPA 格式: {ipa_path}")

    info = {
        "bundle_id": None,
        "app_name": None,
        "version": None,
        "file_size": os.path.getsize(ipa_path),
    }

    try:
        with zipfile.ZipFile(ipa_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".app/Info.plist") and "/" in name.rstrip("/"):
                    payload_path = name
                    break
            else:
                for name in zf.namelist():
                    if "Info.plist" in name and name.endswith(".app/Info.plist"):
                        payload_path = name
                        break
                else:
                    print("警告: 无法在 IPA 中找到 Info.plist")
                    return info

            with zf.open(payload_path) as plist_file:
                plist_data = plistlib.load(plist_file)
                info["bundle_id"] = plist_data.get("CFBundleIdentifier")
                info["app_name"] = plist_data.get("CFBundleDisplayName") or plist_data.get("CFBundleName")
                info["version"] = plist_data.get("CFBundleShortVersionString") or plist_data.get("CFBundleVersion")
    except Exception as e:
        print(f"警告: 解析 IPA 信息时出错: {e}")

    return info


async def install_ipa(ipa_path, device_serial=None, uninstall_existing=False):
    devices = await list_devices()
    if not devices:
        print("错误: 未检测到已连接的 iOS 设备。")
        return False

    if device_serial:
        target_device = None
        for d in devices:
            if d.serial == device_serial:
                target_device = d
                break
        if not target_device:
            print(f"错误: 未找到 UDID 为 {device_serial} 的设备。")
            return False
    else:
        if len(devices) == 1:
            target_device = devices[0]
        else:
            print("错误: 检测到多台设备，请使用 --udid 参数指定目标设备。")
            await list_connected_devices()
            return False

    print(f"\n正在连接到设备: {target_device.serial}")

    try:
        lockdown = await create_using_usbmux(serial=target_device.serial)
        device_name = lockdown.all_values.get("DeviceName", "未知设备")
        ios_version = lockdown.all_values.get("ProductVersion", "未知")
        print(f"设备名称: {device_name}")
        print(f"系统版本: iOS {ios_version}")
    except Exception as e:
        print(f"错误: 无法连接到设备: {e}")
        return False

    ipa_info = extract_ipa_info(ipa_path)
    print(f"\nIPA 信息:")
    print(f"  应用名称: {ipa_info['app_name'] or '未知'}")
    print(f"  Bundle ID: {ipa_info['bundle_id'] or '未知'}")
    print(f"  版本: {ipa_info['version'] or '未知'}")
    print(f"  文件大小: {ipa_info['file_size'] / 1024 / 1024:.2f} MB")

    if not ipa_info["bundle_id"]:
        print("错误: 无法获取 Bundle ID，安装无法继续。")
        return False

    try:
        installation_proxy = InstallationProxyService(lockdown=lockdown)

        if uninstall_existing:
            print(f"正在卸载已存在的应用: {ipa_info['bundle_id']}")
            try:
                await installation_proxy.uninstall(ipa_info["bundle_id"])
                print("卸载完成。")
            except Exception as e:
                print(f"卸载失败（可能应用未安装）: {e}")

        print(f"\n正在安装应用到设备...")
        print("这可能需要几分钟时间，请耐心等待...")

        await installation_proxy.install_from_local(Path(ipa_path))

        print(f"\n✓ 安装成功！")
        print(f"应用 '{ipa_info['app_name'] or ipa_info['bundle_id']}' 已安装到设备。")

        return True

    except Exception as e:
        print(f"\n✗ 安装失败: {e}")
        print("\n常见问题排查：")
        print("  1. 确保设备已解锁并信任此电脑")
        print("  2. 确保 IPA 文件完整且未损坏")
        print("  3. 确保设备上有足够的存储空间")
        print("  4. 尝试重启设备和电脑后重试")
        return False


def format_log_line(entry):
    timestamp = entry.timestamp
    pid = entry.pid
    level = entry.level.name
    filename = entry.filename
    image_name = posixpath.basename(entry.image_name) if entry.image_name else ""
    message = entry.message
    process_name = posixpath.basename(filename) if filename else ""

    if image_name:
        return f"{timestamp} {process_name}({image_name})[{pid}] <{level}>: {message}"
    else:
        return f"{timestamp} {process_name}[{pid}] <{level}>: {message}"


async def log_device(device_serial=None, output_file=None, filter_text=None):
    from pymobiledevice3.services.os_trace import OsTraceService

    devices = await list_devices()
    if not devices:
        print("错误: 未检测到已连接的 iOS 设备。")
        return

    if device_serial:
        target_device = None
        for d in devices:
            if d.serial == device_serial:
                target_device = d
                break
        if not target_device:
            print(f"错误: 未找到 UDID 为 {device_serial} 的设备。")
            return
    else:
        target_device = devices[0]
        if len(devices) > 1:
            print(f"检测到多台设备，默认使用第一台: {target_device.serial}")
            print("可使用 --udid 参数指定设备")

    try:
        lockdown = await create_using_usbmux(serial=target_device.serial)
    except Exception as e:
        print(f"错误: 无法连接到设备: {e}")
        return

    device_name = lockdown.all_values.get("DeviceName", "未知设备")
    ios_version = lockdown.all_values.get("ProductVersion", "未知")
    print(f"\n设备名称: {device_name}")
    print(f"系统版本: iOS {ios_version}")

    if output_file is None:
        output_file = f"iOS_{datetime.now().strftime('%Y%m%d')}/iOS_{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    line_count = 0
    out_file = None

    try:
        out_file = open(output_file, 'a', encoding='utf-8')

        separator = f"\n{'=' * 60}\n# iOS Log session started at {datetime.now()}\n# Device: {target_device.serial}\n{'=' * 60}\n"
        out_file.write(separator)
        out_file.flush()
        print(separator, end='')

        os_trace = OsTraceService(lockdown=lockdown)
        print(f"开始捕获实时日志... (过滤: {filter_text or '无'})")
        print("按 Ctrl+C 停止\n")

        async for entry in os_trace.syslog():
            line_str = format_log_line(entry)
            if not line_str.endswith('\n'):
                line_str += '\n'
            if filter_text and filter_text.lower() not in line_str.lower():
                continue
            line_count += 1
            sys.stdout.write(line_str)
            sys.stdout.flush()
            out_file.write(line_str)
            out_file.flush()

    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n错误: {e}")
    finally:
        end_mark = f"\n# iOS Log session ended at {datetime.now()}\n{'=' * 60}\n"
        if out_file:
            out_file.write(end_mark)
            out_file.flush()
            out_file.close()
        print(f"\n已捕获 {line_count} 行日志。")
        print(f"日志文件: {os.path.abspath(output_file)}")


def main():
    parser = argparse.ArgumentParser(
        description="Windows iOS IPA 安装工具 - 在 Windows 上将 IPA 包安装到 iOS 设备",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  IPAInstaller.exe list                    列出已连接的设备
  IPAInstaller.exe install app.ipa         安装 IPA 到唯一连接的设备
  IPAInstaller.exe install app.ipa --udid <UDID>  安装到指定设备
  IPAInstaller.exe install app.ipa --uninstall    先卸载再安装
  IPAInstaller.exe info app.ipa            查看 IPA 包信息
  IPAInstaller.exe log                     实时查看 iOS 设备系统日志
  IPAInstaller.exe log -f "MyApp"          过滤包含 "MyApp" 的日志
  IPAInstaller.exe log -o mylog.log        将日志保存到指定文件
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    list_parser = subparsers.add_parser("list", help="列出已连接的 iOS 设备")

    info_parser = subparsers.add_parser("info", help="查看 IPA 包信息")
    info_parser.add_argument("ipa_path", help="IPA 文件路径")

    install_parser = subparsers.add_parser("install", help="安装 IPA 到 iOS 设备")
    install_parser.add_argument("ipa_path", help="IPA 文件路径")
    install_parser.add_argument("--udid", "-u", help="目标设备的 UDID（多设备时必须指定）")
    install_parser.add_argument("--uninstall", "-r", action="store_true",
                                help="安装前先卸载已存在的应用")

    log_parser = subparsers.add_parser("log", help="实时查看 iOS 设备系统日志")
    log_parser.add_argument("--udid", "-u", help="目标设备的 UDID（多设备时可选）")
    log_parser.add_argument("--output", "-o", help="输出日志文件路径（默认自动生成）")
    log_parser.add_argument("--filter", "-f", help="只显示包含该字符串的日志行（不区分大小写）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "list":
        asyncio.run(list_connected_devices())

    elif args.command == "info":
        try:
            info = extract_ipa_info(args.ipa_path)
            print(f"IPA 文件: {args.ipa_path}")
            print(f"  应用名称: {info['app_name'] or '未知'}")
            print(f"  Bundle ID: {info['bundle_id'] or '未知'}")
            print(f"  版本: {info['version'] or '未知'}")
            print(f"  文件大小: {info['file_size'] / 1024 / 1024:.2f} MB")
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)

    elif args.command == "install":
        success = asyncio.run(install_ipa(
            args.ipa_path,
            device_serial=args.udid,
            uninstall_existing=args.uninstall,
        ))
        if not success:
            sys.exit(1)

    elif args.command == "log":
        try:
            asyncio.run(log_device(
                device_serial=args.udid,
                output_file=args.output,
                filter_text=args.filter,
            ))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
