#!/usr/bin/env python3
"""
Interfaz gráfica para generar subtítulos SRT y LRC usando Whisper,
con subdivisión automática de segmentos largos en trozos breves
y que aparezcan por partes mientras habla la persona.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import whisper
import datetime
import threading
import os

# Número máximo de palabras por subtítulo
CHUNK_WORDS = 6

def secs_to_srt(t: float) -> str:
    """
    Convierte segundos (float) a formato SRT: HH:MM:SS,mmm
    """
    hours   = int(t // 3600)
    minutes = int((t % 3600) // 60)
    seconds = int(t % 60)
    millis  = int((t - int(t)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def split_segment(seg):
    """
    Divide un segmento en trozos más pequeños según CHUNK_WORDS.
    Devuelve lista de (start, end, text) para cada subsegmento.
    """
    words = seg['text'].strip().split()
    total = len(words)
    if total <= CHUNK_WORDS:
        return [(seg['start'], seg['end'], seg['text'].strip())]
    dur = seg['end'] - seg['start']
    chunks = []
    num_chunks = (total + CHUNK_WORDS - 1) // CHUNK_WORDS
    for i in range(num_chunks):
        w_chunk = words[i*CHUNK_WORDS : (i+1)*CHUNK_WORDS]
        start = seg['start'] + (dur * i / num_chunks)
        end   = seg['start'] + (dur * (i+1) / num_chunks)
        text  = ' '.join(w_chunk)
        chunks.append((start, end, text))
    return chunks


def generate_files(audio_path: str, output_dir: str, model_size: str="base"):
    """
    Transcribe el audio y genera archivos SRT y LRC subdivididos.
    """
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)

    # Generar subtitulos.srt
    srt_path = os.path.join(output_dir, "subtitulos.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        index = 1
        for seg in result["segments"]:
            for (st, ed, txt) in split_segment(seg):
                start = secs_to_srt(st)
                end   = secs_to_srt(ed)
                f.write(f"{index}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{txt}\n\n")
                index += 1

    # Generar subtitulos.lrc
    lrc_path = os.path.join(output_dir, "subtitulos.lrc")
    with open(lrc_path, "w", encoding="utf-8") as f:
        for seg in result["segments"]:
            for (st, _, txt) in split_segment(seg):
                mm = int(st // 60)
                ss = int(st % 60)
                xx = int((st - int(st)) * 100)
                timestamp = f"[{mm:02d}:{ss:02d}.{xx:02d}]"
                f.write(f"{timestamp}{txt}\n")

    return srt_path, lrc_path


def start_generation():
    audio_path = entry_audio.get()
    output_dir = entry_output.get()
    if not audio_path or not output_dir:
        messagebox.showwarning("Atención", "Por favor, selecciona el archivo de audio y la carpeta de destino.")
        return

    btn_generate.config(state=tk.DISABLED)
    label_status.config(text="Generando subtítulos, espera un momento...")

    def task():
        try:
            srt_path, lrc_path = generate_files(audio_path, output_dir)
            messagebox.showinfo("¡Hecho!", f"Subtítulos creados:\n{srt_path}\n{lrc_path}")
            label_status.config(text="Subtítulos generados con éxito.")
        except Exception as e:
            messagebox.showerror("¡Error!", f"Ocurrió un problema:\n{e}")
            label_status.config(text="Error durante la generación.")
        finally:
            btn_generate.config(state=tk.NORMAL)

    threading.Thread(target=task, daemon=True).start()

# --- Interfaz Tkinter ---
root = tk.Tk()
root.title("Generador de subtítulos con Whisper")
root.geometry("550x230")

# Archivo de audio
lbl_audio = tk.Label(root, text="Archivo de audio:")
lbl_audio.pack(anchor="w", padx=10, pady=(10,0))
entry_audio = tk.Entry(root, width=60)
entry_audio.pack(padx=10, pady=5, fill="x")
btn_browse_audio = tk.Button(
    root, text="Examinar audio…",
    command=lambda: (entry_audio.delete(0, tk.END), entry_audio.insert(0, filedialog.askopenfilename(filetypes=[("Archivos de audio", "*.mp3 *.wav *.m4a")])))
)
btn_browse_audio.pack(padx=10)

# Carpeta de destino
lbl_output = tk.Label(root, text="Carpeta de destino:")
lbl_output.pack(anchor="w", padx=10, pady=(10,0))
entry_output = tk.Entry(root, width=60)
entry_output.pack(padx=10, pady=5, fill="x")
btn_browse_output = tk.Button(
    root, text="Examinar carpeta…",
    command=lambda: (entry_output.delete(0, tk.END), entry_output.insert(0, filedialog.askdirectory()))
)
btn_browse_output.pack(padx=10)

# Botón de generar
btn_generate = tk.Button(root, text="Generar subtítulos", command=start_generation)
btn_generate.pack(pady=15)

# Estado
label_status = tk.Label(root, text="Listo")
label_status.pack()

root.mainloop()
