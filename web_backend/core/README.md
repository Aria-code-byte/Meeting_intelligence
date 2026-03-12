# Jinni 核心引擎 (C++)

## 编译说明

### 依赖
- C++17 或更高版本
- FFmpeg 库 (libavformat, libavcodec)
- nlohmann/json
- libcurl (用于 API 调用)

### 编译命令
```bash
g++ -std=c++17 -O3 \
    -I/usr/include/ffmpeg \
    -lavformat -lavcodec -lavutil -lswresample \
    -lcurl \
    jinni_engine.cpp \
    -o jinni_engine
```

### 测试运行
```bash
./jinni_engine --help
```

## Python 调用方式

后端通过 subprocess 调用：
```bash
./jinni_engine --input video.mp4 --output result.json --llm deepseek
```
