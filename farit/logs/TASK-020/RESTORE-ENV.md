# RESTORE — как восстановить окружение хаба за 1 команду (если vnedu снесли, worst case)

Проверенная конфигурация (рабочая на драйвере CUDA 12.5 / 555.42.06, A100 MIG):

    python3 -m venv /home/jovyan/persistent_volume/sds-hub/venv
    source /home/jovyan/persistent_volume/sds-hub/venv/bin/activate
    pip install "vllm==0.19.1"

    # Если torch окажется cu13-вариантом по умолчанию (так проще гарант):
    pip install "torch==2.10.0+cu128" --index-url https://download.pytorch.org/whl/cu128
    # недостающий cudnn, если import torch ругается на libcudnn.so.9:
    pip install --force-reinstall --no-deps "nvidia-cudnn-cu12==9.10.2.21" "nvidia-cublas-cu12==12.8.4.1" \
        nvidia-cuda-cupti-cu12==12.8.90 nvidia-cuda-nvrtc-cu12==12.8.93 nvidia-cuda-runtime-cu12==12.8.90 \
        nvidia-cufft-cu12 nvidia-cufile-cu12 nvidia-curand-cu12 nvidia-cusolver-cu12 nvidia-cusparse-cu12 \
        nvidia-cusparselt-cu12 nvidia-nccl-cu12==2.27.5 nvidia-nvjitlink-cu12 nvidia-nvshmem-cu12 nvidia-nvtx-cu12
    # (версии nvidia-*-cu12 в freeze-файле рядом)

Проверка:

    python -c "import torch, vllm; print(torch.__version__, vllm.__version__); torch.cuda.is_available()"

Сверка пакетов: `out/pip-freeze-2026-10-26.txt` (как было в момент работающего прогона).

Обретённые уроки (не повторять битые пути):
- НЕ ставить пейп-дефолтное "pip install vllm" — возьмёт torch 2.13/CUDA 13, драйвер 12.5 отвергнет.
- НЕ ставить vllm 0.26–0.31 — бинарники слинкованы с CUDA 13 (ImportError libcudart.so.13).
- НЕ ставить vllm 0.16 — не знает архитектуру Qwen3_5*ForConditionalGeneration.
- Прежде чем чинить «битые cu13/cu12 библиотеки»: при uninstall pip удаляет содержимое
  общих поддеревьев `nvidia/<lib>` — после force-reinstall основных НЕ забывать
  `nvidia-cudnn-cu12` и прочие cu12 пакеты, иначе ImportError ибо дист-инфо жив, а либ нет的诗.

Сонтекст: OLD logs в out/snapshots/vllm-*.log показывают успешный рабочий ран на этой связке.
