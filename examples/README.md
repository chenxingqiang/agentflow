# Image Processing Example

这个示例展示了如何使用 ImageProcessingInstruction 来处理图像。示例包含以下功能：

1. **单张图片处理**
   - 加载单张图片
   - 自动调整大小
   - 使用 ViT 模型进行图像分类

2. **批量处理**
   - 同时处理多张图片
   - 使用批处理提高效率
   - 返回每张图片的分类结果

3. **自动优化**
   - 自动检测大图片并调整大小
   - 智能批处理
   - 资源优化

## 运行示例

1. 确保已安装所需依赖：
```bash
pip install torch torchvision transformers pillow
```

2. 准备测试图片：
   - 将测试图片放在适当的目录中
   - 修改代码中的图片路径

3. 运行示例：
```bash
python image_processing_example.py
```

## 示例输出说明

1. 单张图片处理结果：
   - 包含图片的分类标签
   - 分类的置信度分数

2. 批量处理结果：
   - 所有图片的处理结果列表
   - 处理的总图片数
   - 使用的批次数量

3. 优化结果：
   - 显示优化前后的上下文变化
   - 展示自动优化的效果