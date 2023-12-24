# 本地部署
## 模型下载

src/local_llm/down_model.py 文件提供了huggingface镜像站https://hf-mirror.com和阿里系的魔塔社区modelscope的下载方法.



## GLM3 6B模型
### 模型下载 
请通过src/local_llm/down_model.py下载模型,推荐使用modelscope下载,会快很多

### 模型加载
#### 基础模型加载
在src/local_llm/ChatGLM3/openai_api_demo/openai_api.py文件中,修改以下内容
```python
MODEL_PATH = "我们的模型绝对或者相对地址" #例如 r'E:\python_code\finetune_llm\ChatGLM3\model\THUDM\chatglm3-6b'
TOKENIZER_PATH = os.environ.get("TOKENIZER_PATH", MODEL_PATH)#保持原样
```
#### 微调模型加载(不合并权重,直接加载lora和原模型)在src/local_llm/ChatGLM3/openai_api_demo/openai_api_qlora.py问中,需要调整我们的--pt-checkpoint这个参数为训练好的lora check point
```python
    parser = argparse.ArgumentParser()
    parser.add_argument("--pt-checkpoint", type=str,
                        default=r"E:\python_code\finetune_llm\ChatGLM3\finetune_chatmodel_demo\output\textsc2-20231213121007-128-2e-2\checkpoint-300",
                        help="训练好的lora checkpoint")
    parser.add_argument("--model", type=str, default=r'E:\python_code\finetune_llm\ChatGLM3\model\THUDM\chatglm3-6b',
                        help="主模型权重")
    parser.add_argument("--tokenizer", type=str,
                        default=r'E:\python_code\finetune_llm\ChatGLM3\model\THUDM\chatglm3-6b',
                        help="主模型权重")
    parser.add_argument("--max-new-tokens,生成的token数", type=int, default=512)
```

### 模型量化

默认情况下，模型以 FP16 精度加载，运行上述代码需要大概 13GB 显存。如果你的 GPU 显存有限，可以尝试以量化方式加载模型，使用方法如下：
```python
model = AutoModel.from_pretrained("THUDM/chatglm3-6b",trust_remote_code=True).quantize(4).cuda()
```
#### 基础模型
在src/local_llm/ChatGLM3/openai_api_demo/openai_api.py文件夹下你需要在这里添加.quantize(4).cuda(),保证量化载入,下面为量化载入的示例

```python
if __name__ == "__main__":

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH, trust_remote_code=True)
    if 'cuda' in DEVICE:  # AMD, NVIDIA GPU can use Half Precision
        model = AutoModel.from_pretrained(MODEL_PATH, trust_remote_code=True).to(DEVICE).eval().quantize(4).cuda()
    else:  # CPU, Intel GPU and other GPU can use Float16 Precision Only
        model = AutoModel.from_pretrained(MODEL_PATH, trust_remote_code=True).float().to(DEVICE).eval().quantize(4).cuda()
    uvicorn.run(app, host='0.0.0.0', port=8000, workers=1)
```
#### 微调模型

微调模型的量化载入需要使用src/local_llm/ChatGLM3/openai_api_demo/openai_api_request_qlora.py文件,与之前一样,也需要添加.quantize(4).cuda()后缀即可

```python
if __name__ == "__main__":
...
...

    if args.pt_checkpoint:
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=True)
        config = AutoConfig.from_pretrained(args.model, trust_remote_code=True, pre_seq_len=args.pt_pre_seq_len)
        model = AutoModel.from_pretrained(args.model, config=config, trust_remote_code=True).quantize(4).cuda()

        prefix_state_dict = torch.load(os.path.join(args.pt_checkpoint, "pytorch_model.bin"))
...
...
    else:
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, trust_remote_code=True)
        model = AutoModel.from_pretrained(args.model, trust_remote_code=True).quantize(4).cuda()

    model = model.to(args.device)
```

模型量化会带来一定的性能损失，经过测试，ChatGLM3-6B 在 4-bit 量化下仍然能够进行自然流畅的生成。

### CPU 部署
非常不建议,会直接占用cpu的全部计算资源,尤其是NPC engine需要再启动一个游戏进程.
```python
model = AutoModel.from_pretrained("THUDM/chatglm3-6b", trust_remote_code=True).float()
```

### Mac 部署
参照glm3源文档

对于搭载了 Apple Silicon 或者 AMD GPU 的 Mac，可以使用 MPS 后端来在 GPU 上运行 ChatGLM3-6B。需要参考 Apple 的 [官方说明](https://developer.apple.com/metal/pytorch) 安装 PyTorch-Nightly（正确的版本号应该是2.x.x.dev2023xxxx，而不是 2.x.x）。

目前在 MacOS 上只支持[从本地加载模型](README.md#从本地加载模型)。将代码中的模型加载改为从本地加载，并使用 mps 后端：
```python
model = AutoModel.from_pretrained("your local path", trust_remote_code=True).to('mps')
```

加载半精度的 ChatGLM3-6B 模型需要大概 13GB 内存。内存较小的机器（比如 16GB 内存的 MacBook Pro），在空余内存不足的情况下会使用硬盘上的虚拟内存，导致推理速度严重变慢。

### lora微调 chat模型

#### 数据格式
由于glm3的文档过于混乱,在这里我们直接给出微调需要的数据格式:
```json
{"conversations":[{"role":"user","content":"昨天的日期"},{"role":"assistant","content":"昨天的日期，等于今天的日期减去1天"}]}
{"conversations":[{"role":"user","content":"昨天是几号？"},{"role":"assistant","content":"先查出今天的日期，再用今天的日期减去1天，结果就是昨天的日期"}]}
{"conversations":[{"role":"user","content":"这两天是哪两天"},{"role":"assistant","content":"这两天指的是昨天和今天，也就是开始时间是昨天，结束时间是今天"}]}
{"conversations":[{"role":"user","content":"近一周是什么时间范围"},{"role":"assistant","content":"先算出来今天的日期，开始时间就是今天减去7天，结束时间是今天"}]}
{"conversations":[{"role":"user","content":"什么是重点人员"},{"role":"assistant","content":"重点人员是库管理中创建的一个特殊的库，库的名称叫做重点人员库，里面的数据都是重点人员"}]}
{"conversations":[{"role":"user","content":"南京到北京有多远"},{"role":"assistant","content":"北京到南京约1100公里，高铁大约4~6个小时，开车需要10小时以上"}]}
{"conversations":[{"role":"user","content":"世界上最好的跳远成绩是多少米"},{"role":"assistant","content":"在助跑跳远比赛中，美国选手迈克·鲍威尔在1991年第三届世界田径锦标赛上创造了男子跳远世界纪录，成绩为8.95米，这一纪录至今无人打破。女子跳远世界纪录是由前苏联选手加琳娜·奇斯佳科娃在1988年创造的，成绩为7.52米"}]}
{"conversations":[{"role":"user","content":"特斯拉开多少公里需要加一次油？"},{"role":"assistant","content":"特斯拉是新能源电车，不需要加油。但是如果长途旅行的话，需要注意电量和沿途是否有充电桩。"}]}
```
具体可以参照src/local_llm/ChatGLM3/data/zxyc_interface.jsonl文件.格式转换请使用gpt4写一个脚本来完成

#### 训练
由于计算资源不足,我在windows上实现了qlora微调.该文件可以实现微调src/local_llm/ChatGLM3/finetune_chatmodel_demo/训练.bat,内容如下

注意最后这里的--quantization_bit 4代表4 bit量化训练
```text
@echo off 
chcp 65001 >null
echo 启动中，请耐心等待

set DATASET_PATH=数据集路径
set BASE_MODEL_PATH=基础模型路径
set RUN_NAME=项目名称
set PRE_SEQ_LEN=128
set LR=2e-2
set NUM_GPUS=gpu个数
set MAX_SEQ_LEN=最长输入长度
set DEV_BATCH_SIZE=batch size
set GRAD_ACCUMULARION_STEPS=16
set MAX_STEP=训练轮数
set SAVE_INTERVAL=100
set DATESTR=%Date:~3,4%%Date:~8,2%%Date:~11,2%%time:~0,2%%time:~3,2%%time:~6,2%
set OUTPUT_DIR=output\%RUN_NAME%-%DATESTR%-%PRE_SEQ_LEN%-%LR%

set PYTHON=F:\ide\anaconda\envs\llmenv\python.exe #你的python路径
set MY_PATH=f:\ide\anaconda\envs\llmenv\lib #你的包路径
set PATH=%MY_PATH%;%PATH%

mkdir %OUTPUT_DIR%

%PYTHON% finetune.py --train_format multi-turn --train_file %DATASET_PATH% --max_seq_length %MAX_SEQ_LEN% --preprocessing_num_workers 1 --model_name_or_path %BASE_MODEL_PATH% --output_dir %OUTPUT_DIR% --per_device_train_batch_size %DEV_BATCH_SIZE% --gradient_accumulation_steps %GRAD_ACCUMULARION_STEPS% --max_steps %MAX_STEP% --logging_steps 1 --save_steps %SAVE_INTERVAL% --learning_rate %LR% --pre_seq_len %PRE_SEQ_LEN% --quantization_bit 4

pause
```
#### windows微调需要的特殊包

1. 先把ChatGLM3路径下的requirement 安装好.
2. 如果需要安装flash-attention,请在这个https://github.com/bdashore3/flash-attention/releases/tag/2.3.3,它提供了windows可用的flash attention
3. bitsandbytes 请在https://github.com/jllllll/bitsandbytes-windows-webui 这里安装

## Qwen

### 模型下载
请通过`src/local_llm/down_model.py`下载模型,推荐使用modelscope下载,会快很多

### 模型加载
在`npc_engine/src/local_llm/Qwen/openai_api.py`的507行开始有多种加载模型,经过测试,int4量化下的qwen1.8b占用4g显存.所以我们选择它.在541行选择量化的模型加载方式


注意我们需要安装auto-gptq,`pip install auto-gptq optimum`.
### 参数说明
```python
    parser = ArgumentParser()
    parser.add_argument(
        default=r"E:\python_code\finetune_llm\llm_model\qwen\Qwen-1_8B-Chat-Int4",
        help="Checkpoint name or path, default to %(default)r",#模型地址
    )
    parser.add_argument(
        "--server-port", type=int, default=5001, help="Demo server port." #端口号
    )
    args = parser.parse_args()
    return args
```
