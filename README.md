# IPAInstaller 使用教程

## 简介

IPAInstaller 是一个 Windows 端的 IPA 安装工具，可以将 `.ipa` 文件直接安装到 iOS 设备上。它是一个**单文件绿色软件**，无需安装 Python 或任何依赖，下载即用。

---

## 一、准备工作

### 1.1 安装 Apple 驱动程序

Windows 需要 Apple 的 USB 驱动才能与 iOS 设备通信。选择以下任一方式：

| 方式 | 说明 |
|------|------|
| **Apple Devices 应用**（推荐） | 从 Microsoft Store 搜索「Apple Devices」安装，仅包含驱动，体积小 |
| **iTunes** | 从 [Apple 官网](https://www.apple.com.cn/itunes/) 下载安装，功能完整但体积较大 |

> 安装完成后**不需要打开** iTunes 或 Apple Devices，驱动会在后台自动运行。

### 1.2 连接 iOS 设备

1. 用 **USB 数据线** 将 iPhone/iPad 连接到电脑
2. 解锁设备屏幕
3. 如果弹出「要信任此电脑吗？」，点击 **「信任」** 并输入设备密码

> 如果之前点过「不信任」，需要在设备上进入 **设置 → 通用 → 传输或还原 → 还原 → 还原位置与隐私**，然后重新连接。

---

## 二、下载工具

从 `dist` 目录中获取 `IPAInstaller.exe`，放到任意文件夹即可使用。

---

## 三、基本使用

### 3.1 打开命令行

在 `IPAInstaller.exe` 所在文件夹的地址栏中输入 `cmd` 然后回车：

```
C:\Users\xxx\Desktop\IPAInstaller> _
```

### 3.2 列出已连接的设备

```bash
IPAInstaller.exe list
```

输出示例：

```
检测到 1 台设备：
  [0] 我的 iPhone (iPhone11,8) - iOS 18.7.2
      UDID: 00008020-0015503826D2002E
```

> **UDID** 是设备的唯一标识符，多设备时需要用它来指定目标。

### 3.3 查看 IPA 包信息

在安装前，可以先查看 IPA 包的基本信息：

```bash
IPAInstaller.exe info C:\Users\xxx\Downloads\app.ipa
```

输出示例：

```
IPA 文件: C:\Users\xxx\Downloads\app.ipa
  应用名称: 微信
  Bundle ID: com.tencent.xin
  版本: 8.0.50
  文件大小: 350.25 MB
```

### 3.4 安装 IPA 到设备

**单设备（自动识别）：**

```bash
IPAInstaller.exe install C:\Users\xxx\Downloads\app.ipa
```

**多设备（指定 UDID）：**

```bash
IPAInstaller.exe install C:\Users\xxx\Downloads\app.ipa --udid 00008020-0015503826D2002E
```

**先卸载旧版本再安装：**

```bash
IPAInstaller.exe install C:\Users\xxx\Downloads\app.ipa --uninstall
```

安装过程输出示例：

```
正在连接到设备: 00008020-0015503826D2002E
设备名称: 我的 iPhone
系统版本: iOS 18.7.2

IPA 信息:
  应用名称: 微信
  Bundle ID: com.tencent.xin
  版本: 8.0.50
  文件大小: 350.25 MB

正在安装应用到设备...
这可能需要几分钟时间，请耐心等待...

✓ 安装成功！
应用 '微信' 已安装到设备。
```

---

## 四、命令速查

| 命令 | 说明 |
|------|------|
| `IPAInstaller.exe list` | 列出所有已连接的 iOS 设备 |
| `IPAInstaller.exe info <ipa路径>` | 查看 IPA 包信息（不安装） |
| `IPAInstaller.exe install <ipa路径>` | 安装 IPA 到唯一连接的设备 |
| `IPAInstaller.exe install <ipa路径> -u <UDID>` | 安装到指定设备 |
| `IPAInstaller.exe install <ipa路径> -r` | 先卸载再安装 |
| `IPAInstaller.exe --help` | 查看帮助信息 |

---

## 五、常见问题

### Q1: 提示「未检测到已连接的 iOS 设备」

**排查步骤：**

1. 确认设备已通过 **USB 数据线** 连接（不支持无线连接）
2. 确认设备已 **解锁屏幕**
3. 确认已点击 **「信任此电脑」**
4. 确认已安装 **iTunes 或 Apple Devices 应用**
5. 尝试 **重新拔插 USB 线**
6. 尝试 **重启电脑和设备**

### Q2: 安装失败

**常见原因：**

- IPA 文件损坏或不完整 → 重新下载 IPA
- 设备存储空间不足 → 清理设备空间
- 设备上已安装更高版本 → 使用 `--uninstall` 参数先卸载
- 设备连接中断 → 保持设备屏幕常亮，关闭自动锁屏

### Q3: 安装后应用打不开 / 闪退

这通常与 IPA 包本身有关，而非安装工具的问题：

- IPA 可能没有正确的签名（需要企业证书或个人签名）
- 应用可能不兼容当前 iOS 版本
- 建议使用已签名或已脱壳的 IPA 包

### Q4: 支持哪些 iOS 版本？

理论上支持 **iOS 3.0 ~ iOS 18.x** 的所有版本，实际测试过 iOS 15/16/17/18。

### Q5: 支持 iPad 吗？

支持。iPhone 和 iPad 均可使用。

### Q6: 需要手机越狱吗？

**不需要。** 本工具通过苹果官方的 USB 通信协议与设备交互，无需越狱。

---

## 六、进阶技巧

### 6.1 拖拽安装

将 IPA 文件直接拖到命令行窗口中，会自动填入文件路径，省去手动输入的麻烦。

### 6.2 批量安装

创建一个 `.bat` 批处理文件，内容如下：

```batch
@echo off
IPAInstaller.exe install "C:\IPA\app1.ipa"
IPAInstaller.exe install "C:\IPA\app2.ipa"
IPAInstaller.exe install "C:\IPA\app3.ipa"
pause
```

### 6.3 发送到桌面快捷方式

右键 `IPAInstaller.exe` → 发送到 → 桌面快捷方式，方便快速使用。

### 6.4 配置环境变量（全局使用）

将 `IPAInstaller.exe` 所在目录添加到系统环境变量 `Path` 中，即可在任意位置通过 `cmd` 直接使用。

**步骤：**

1. 按 `Win + R`，输入 `sysdm.cpl` 并回车，打开 **系统属性**
2. 点击 **高级** 选项卡 → **环境变量**
3. 在 **系统变量** 中找到 `Path`，选中后点击 **编辑**
4. 点击 **新建**，填入 `IPAInstaller.exe` 所在的文件夹路径（例如 `C:\Tools\IPAInstaller`）
5. 依次点击 **确定** 保存所有窗口

配置完成后，**重新打开 `cmd`**，即可在任何目录下直接使用：

```bash
IPAInstaller list
IPAInstaller install C:\Users\xxx\Downloads\app.ipa
IPAInstaller info C:\Users\xxx\Downloads\app.ipa
```

> **提示**：如果觉得 `IPAInstaller` 名称太长，可以将 `IPAInstaller.exe` 重命名为 `ipa.exe`，之后用 `ipa list`、`ipa install` 等命令操作。

---

## 七、注意事项

1. 安装过程中请 **保持设备屏幕常亮**，不要锁屏
2. 安装大体积 IPA（>1GB）时请耐心等待，可能需要 5-10 分钟
3. 安装完成后，设备上会出现新应用的图标，可能需要等待几秒钟
4. 首次打开安装的应用时，如果提示「未受信任的开发者」，需要去 **设置 → 通用 → VPN 与设备管理** 中手动信任
