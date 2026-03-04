### NCM 解密工具
Python 实现的网易云音乐 NCM 加密音频解密工具，包含核心解密算法、批量处理脚本、GUI 可视化界面三个核心文件。

#### 源代码说明
##### 1. ncmdump.py（核心算法文件）
- 核心功能：实现 NCM 文件的 AES 解密逻辑，完成加密密钥解析、音频数据解密、原生音频格式还原；
- 关键逻辑：校验 NCM 文件头、解密音频密钥、逐块解密音频数据并写入本地文件；
- 依赖：`pycryptodome`（AES 加密算法）。

##### 2. batch_convert_ncm.py（批量处理脚本）
- 核心功能：调用 `ncmdump.py` 的解密方法，批量扫描指定目录下的所有 NCM 文件并自动解密；
- 关键逻辑：递归遍历文件夹、过滤 .ncm 后缀文件、批量调用解密函数、输出处理结果；
- 依赖：`ncmdump.py`、`os` 模块（路径处理）。

##### 3. ncm_gui.py（GUI 可视化界面）
- 核心功能：基于 tkinter 实现可视化操作界面，支持单文件/文件夹选择、自定义输出目录、实时日志输出；
- 关键逻辑：GUI 布局搭建、文件/文件夹选择交互、调用 `ncmdump.py` 完成解密、日志实时打印；
- 依赖：`ncmdump.py`、`tkinter`（Python 内置）。

#### 快速使用
1. 安装依赖：`pip install pycryptodome`
2. 运行方式：
   - GUI 版（推荐）：`python ncm_gui.py`
   - 批量版：`python batch_convert_ncm.py`

#### 注意事项
仅用于解密个人合法获取的 NCM 音频文件。
