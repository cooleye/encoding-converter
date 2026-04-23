# 编码转换器 (Encoding Converter)

一个简洁高效的文本文件编码转换工具，支持批量转换、自动编码检测和实时预览。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 功能特性

- **批量文件转换**: 支持同时转换多个文件
- **自动编码检测**: 自动识别文件编码，支持 UTF-8、GBK、GB2312、GB18030、Big5 等
- **实时预览**: 转换前可预览原始内容和转换后的效果
- **智能导出**: 自动按时间戳组织导出目录，方便管理
- **错误处理**: 多种错误处理策略，确保转换过程稳定
- **BOM 处理**: 支持添加或去除字节顺序标记 (BOM)

## 支持的编码格式

- UTF-8 / UTF-8-SIG
- GBK / GB2312 / GB18030
- Big5
- Latin-1 / ISO-8859-1
- ASCII
- 以及更多...

## 安装与运行

### 环境要求

- Python 3.8+
- PyQt5
- chardet
- charset-normalizer

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python run.py
```

## 打包成可执行文件

### Windows

```bash
python packaging/windows/build_exe.py
```

打包后的可执行文件位于 `dist/EncodingConverter/EncodingConverter.exe`

## 使用说明

### 基本操作

1. **添加文件**: 点击"添加文件"或"添加文件夹"按钮选择要转换的文件
2. **选择编码**: 选择源编码（可选自动检测）和目标编码
3. **设置导出目录**: 默认导出到软件目录下的 `导出目录/yyyy-MM-dd-HH-mm-ss/`
4. **开始转换**: 点击"开始转换"按钮，等待完成

### 导出目录

- **默认位置**: 软件所在目录下的 `导出目录/yyyy-MM-dd-HH-mm-ss/`
- **自定义**: 可在主界面或设置中修改导出目录
- **自动组织**: 每次转换自动创建时间戳子目录，避免文件覆盖

### 转换完成

转换完成后会弹出提示框，显示：
- 成功转换的文件数
- 跳过的文件数（编码相同）
- 失败的文件数
- **打开导出目录**按钮，一键查看转换结果

### 选项说明

- **去除 BOM**: 从源文件中移除字节顺序标记
- **添加 BOM**: 向目标文件添加字节顺序标记
- **错误处理**: 选择遇到无效字符时的处理方式

## 项目结构

```
encoding-converter/
├── src/
│   ├── core/           # 核心转换逻辑
│   │   ├── converter.py    # 编码转换器
│   │   ├── detector.py     # 编码检测器
│   │   ├── models.py       # 数据模型
│   │   └── worker.py       # 后台工作线程
│   ├── ui/             # 用户界面
│   │   ├── main_window.py      # 主窗口
│   │   ├── dialogs/            # 对话框
│   │   └── widgets/            # 自定义组件
│   ├── utils/          # 工具函数
│   └── app.py          # 应用入口
├── packaging/          # 打包配置
│   └── windows/
│       └── build_exe.py    # Windows 打包脚本
├── requirements.txt    # 依赖列表
├── run.py             # 程序入口
└── README.md          # 本文件
```

## 技术栈

- **GUI**: PyQt5
- **编码检测**: chardet, charset-normalizer
- **打包**: PyInstaller

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- ✨ 初始版本发布
- 支持批量文件编码转换
- 自动编码检测
- 实时预览功能
- 智能导出目录管理
