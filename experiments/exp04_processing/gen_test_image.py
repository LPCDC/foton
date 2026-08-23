"""EXP-04 helper — gera um JPEG sintetico ~24MP (proxy do full-res da Canon R8).

Nao e uma foto real (cameras indisponiveis). Serve so para medir latencia de
processamento (decode/resize/watermark/encode), que depende de resolucao e
encode, nao do conteudo. Marcado como PROXY nos resultados.
"""
import os
from PIL import Image

W, H = 6000, 4000  # Canon R8 = 24.2 MP (6000x4000)
OUT = os.path.join(os.path.dirname(__file__), "data", "camera_r8_synth.jpg")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    print("gerando ruido RGB...")
    r = Image.effect_noise((W, H), 64)
    g = Image.effect_noise((W, H), 64)
    b = Image.effect_noise((W, H), 64)
    noise = Image.merge("RGB", (r, g, b))

    # gradiente suave para baixar a entropia -> tamanho de arquivo mais "foto-like"
    small = Image.new("RGB", (2, 2))
    small.putpixel((0, 0), (30, 60, 120))
    small.putpixel((1, 0), (200, 120, 60))
    small.putpixel((0, 1), (90, 140, 90))
    small.putpixel((1, 1), (220, 200, 120))
    grad = small.resize((W, H), Image.BILINEAR)

    img = Image.blend(noise, grad, 0.55)
    img.save(OUT, format="JPEG", quality=92)
    print(f"salvo: {OUT}  {os.path.getsize(OUT)} bytes  {img.size}")


if __name__ == "__main__":
    main()
