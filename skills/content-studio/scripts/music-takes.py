#!/usr/bin/env python3
"""Music takes to pick by ear: ACE-Step 1.5 (MIT, local), under a memory cap, SFT model and steps.

Usage (with ACE-Step's own Python, e.g. <ACE-Step>/.venv/bin/python):
  music-takes.py --acestep <ACE-Step dir> --out <dir> --caption "rock, bar, friends dancing, instrumental" --bpm 124
      [--seconds 20] [--takes 3] [--seed 7] [--model acestep-v15-sft] [--steps 50] [--name bed] [--plan]
      [--max-gb 20] [--min-free-gb 30]

⛔ Memory. Left alone, ACE-Step sizes itself for the whole unified memory of an Apple Silicon Mac (no quantization,
no offload) and on a 64 GB Mac reached 54 GB in two minutes and reset the computer, three times in two days
(Nov 2026). So this script always runs the model under `memory_guard.py` (beside it): it refuses to start with less
than --min-free-gb available or a nearly full disk, and kills the run above --max-gb (default 20). Before ACE-Step
loads it sets MAX_MPS_VRAM=16 (ACE-Step's own override: the 16 GB tier), ACESTEP_MLX_VAE_CHUNK=256 (the VAE decode
is where memory peaks) and ACESTEP_SAVE_MEMORY=1, and caps MLX's own allocator. Takes are at most 90 s: make a
60–90 s take and loop or extend it, never one long render. The 1.7B planning model ("thinking") is off for
instrumentals; --plan turns it on (it adds about 4 GB). The cap cannot be lifted above 24 GB, and nothing here runs
the model without the guard.

Writes <name>-<seed>.m4a (and .wav) per take and prints one JSON line per take with what can be measured: peak and
clipped samples, loudness, near-silent holes (the rule a film renderer refuses a bed by), and spectral flatness
(noise is flat, music is not). A measurement never picks a take: every take is listened to whole, and the person
picks by ear. Then the pick is made at full length with the same caption, bpm and seed (`--takes 1 --seed <its seed>
--seconds <up to 90>`). The guard's last line (stderr) gives the run's peak memory.

Why the SFT model at 50 steps: beds made with the turbo model in 8 steps, picked by waveform, were heard as
"weird clipped noise, not music" (Nov 2026).
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time

MAX_SECONDS = 90.0
GUARDED = "MUSIC_TAKES_GUARDED"


def args():
    a = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    a.add_argument("--acestep", default=os.environ.get("ACESTEP_DIR", ""), help="ACE-Step 1.5 checkout (or ACESTEP_DIR)")
    a.add_argument("--out", required=True)
    a.add_argument("--caption", required=True, help="style words, e.g. 'rock, bar, friends dancing, instrumental'")
    a.add_argument("--bpm", type=int, default=None)
    a.add_argument("--seconds", type=float, default=20.0, help=f"at most {MAX_SECONDS:g}; loop or extend for longer")
    a.add_argument("--takes", type=int, default=3)
    a.add_argument("--seed", type=int, default=7, help="first seed; each next take adds 1000")
    a.add_argument("--model", default="acestep-v15-sft", help="DiT model under checkpoints/ (sft or base: 50 steps)")
    a.add_argument("--steps", type=int, default=None, help="default 50, or 8 for a turbo model")
    a.add_argument("--plan", action="store_true", help="turn on the planning model (off for instrumentals)")
    a.add_argument("--lm", default="acestep-5Hz-lm-1.7B", help="the planning model under checkpoints/, with --plan")
    a.add_argument("--name", default="take")
    a.add_argument("--fade", type=float, default=1.6, help="fade-out seconds (ACE-Step's endings are cut, not composed)")
    a.add_argument("--max-gb", type=float, default=20.0, help="kill the run above this memory footprint (at most 24)")
    a.add_argument("--min-free-gb", type=float, default=30.0, help="refuse to start under this much available memory")
    o = a.parse_args()
    if o.seconds > MAX_SECONDS:
        a.error(f"--seconds {o.seconds:g} is over {MAX_SECONDS:g}: make a 60-90 s take and loop or extend it")
    if o.max_gb > 24:
        a.error("--max-gb above 24 is refused: the uncapped model is what reset the computer")
    return o


def ffmpeg():
    return shutil.which("ffmpeg") or sys.exit("ffmpeg is needed on PATH")


def pcm(path):
    """The take as mono float samples at 48 kHz, through ffmpeg."""
    import numpy as np
    raw = subprocess.run([ffmpeg(), "-v", "error", "-i", path, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def holes(levels, step):
    """Near-silent holes inside the bed (not in the first 1.5 s or the last 2 s): what a film renderer refuses."""
    if not levels:
        return []
    median = sorted(levels)[len(levels) // 2]
    quiet = min(median - 25.0, -40.0)
    end = len(levels) * step
    out, i = [], 0
    while i < len(levels):
        if levels[i] < quiet:
            j = next((k for k in range(i, len(levels)) if levels[k] >= quiet), len(levels))
            a, b = i * step, j * step
            if b - a >= 0.4 and a >= 1.5 and b <= end - 2.0:
                out.append([round(a, 2), round(b, 2)])
            i = j
        else:
            i += 1
    return out


def measure(path):
    import numpy as np
    stereo = subprocess.run([ffmpeg(), "-v", "error", "-i", path, "-ar", "48000", "-f", "f32le", "-"],
                            capture_output=True, check=True).stdout
    s = np.frombuffer(stereo, dtype=np.float32)
    x = pcm(path)
    peak = float(np.max(np.abs(s))) if s.size else 0.0
    # Clipping: samples at full scale, and flat tops (3+ equal samples in a row at the peak).
    at_full = int(np.sum(np.abs(s) >= 0.999))
    top = np.abs(s) >= peak * 0.999 if peak > 0 else np.zeros_like(s, dtype=bool)
    flat_tops = int(np.sum(top[:-2] & top[1:-1] & top[2:])) if s.size > 2 else 0
    step = 0.025
    n = int(48000 * step)
    frames = x[: len(x) // n * n].reshape(-1, n)
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    levels = [float(20 * math.log10(r)) if r > 1e-6 else -120.0 for r in rms]
    # Spectral flatness per 4096-sample window (geometric over arithmetic mean of power): white noise is about 0.5 to
    # 1, music sits well under 0.2. And the share of windows that are noise-like.
    w = 4096
    win = np.hanning(w)
    flat, cent = [], []
    for i in range(0, len(x) - w, w):
        p = np.abs(np.fft.rfft(x[i:i + w] * win)) ** 2 + 1e-12
        if np.mean(p) < 1e-8:
            continue
        flat.append(float(np.exp(np.mean(np.log(p))) / np.mean(p)))
        f = np.fft.rfftfreq(w, 1 / 48000)
        cent.append(float(np.sum(f * p) / np.sum(p)))
    loud = subprocess.run([ffmpeg(), "-v", "info", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    lufs = next((float(l.split(":")[1].split()[0]) for l in reversed(loud.splitlines()) if l.strip().startswith("I:")), None)
    flat.sort(); cent.sort()
    return {
        "seconds": round(len(x) / 48000, 2),
        "peak_db": round(20 * math.log10(peak), 2) if peak > 0 else None,
        "samples_at_full_scale": at_full,
        "flat_top_runs": flat_tops,
        "lufs": lufs,
        "holes": holes(levels, step),
        "quietest_25ms_db_inside": round(min(levels[int(1.5 / step):-int(2 / step)] or [0.0]), 1),
        "flatness_median": round(flat[len(flat) // 2], 4) if flat else None,
        "noise_like_windows": round(sum(1 for v in flat if v > 0.3) / len(flat), 3) if flat else None,
        "centroid_hz_median": round(cent[len(cent) // 2]) if cent else None,
    }


def capped_env():
    """ACE-Step's own memory switches, read when it loads: set before any acestep import."""
    env = dict(os.environ)
    env.update({GUARDED: "1", "MAX_MPS_VRAM": "16", "ACESTEP_MLX_VAE_CHUNK": "256", "ACESTEP_SAVE_MEMORY": "1",
                "TOKENIZERS_PARALLELISM": "false"})
    return env


def cap_mlx(max_gb):
    """MLX's allocator limit, under the guard's kill line, so MLX frees and waits before the guard has to kill."""
    try:
        import mlx.core as mx
        limit = int(max_gb * 0.8 * 1024 ** 3)
        (getattr(mx, "set_memory_limit", None) or mx.metal.set_memory_limit)(limit)
    except Exception:
        pass


def main():
    o = args()
    repo = os.path.abspath(os.path.expanduser(o.acestep))
    if not os.path.isdir(os.path.join(repo, "acestep")):
        sys.exit("--acestep must point at an ACE-Step 1.5 checkout (or set ACESTEP_DIR)")
    if os.environ.get(GUARDED) != "1":
        # The outer process starts this same script again as the guarded job and waits. It never loads the model.
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from memory_guard import run_guarded
        sys.exit(run_guarded([sys.executable, os.path.abspath(__file__), *sys.argv[1:]], max_gb=o.max_gb,
                             min_free_gb=o.min_free_gb, env=capped_env()))
    out = os.path.abspath(o.out)
    os.makedirs(out, exist_ok=True)
    steps = o.steps or (8 if "turbo" in o.model else 50)
    sys.path.insert(0, repo)
    os.chdir(repo)
    cap_mlx(o.max_gb)
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music

    ckpt = os.path.join(repo, "checkpoints")
    if not os.path.isdir(os.path.join(ckpt, o.model)):
        sys.exit(f"{o.model} is not under {ckpt}: `acestep-download --model {o.model} --skip-main` first")
    dit = AceStepHandler()
    print(dit.initialize_service(project_root=repo, config_path=o.model, device="auto"), file=sys.stderr, flush=True)
    llm = None
    if o.plan:
        from acestep.llm_inference import LLMHandler
        llm = LLMHandler()
        backend = "mlx" if sys.platform == "darwin" else "pt"
        msg, ok = llm.initialize(checkpoint_dir=ckpt, lm_model_path=o.lm, backend=backend, device="auto")
        if not ok:
            sys.exit(f"the planning model {o.lm} did not load ({msg}); run without --plan")
    for k in range(o.takes):
        seed = o.seed + 1000 * k
        base = os.path.join(out, f"{o.name}-{seed}")
        tmp = f"{base}.tmp"
        os.makedirs(tmp, exist_ok=True)
        p = GenerationParams(caption=o.caption, lyrics="[Instrumental]", instrumental=True, bpm=o.bpm,
                             duration=o.seconds, seed=seed, thinking=o.plan, inference_steps=steps,
                             guidance_scale=7.0, fade_out_duration=min(o.fade, o.seconds / 4))
        t = time.time()
        r = generate_music(dit, llm, p, GenerationConfig(batch_size=1, audio_format="wav"), save_dir=tmp)
        if not (r.success and r.audios):
            shutil.rmtree(tmp, ignore_errors=True)
            print(json.dumps({"seed": seed, "error": str(r.error)}), flush=True)
            continue
        shutil.move(r.audios[0]["path"], f"{base}.wav")
        shutil.rmtree(tmp, ignore_errors=True)
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", f"{base}.wav", "-c:a", "aac", "-b:a", "256k",
                        "-movflags", "+faststart", f"{base}.m4a"], check=True)
        m = measure(f"{base}.wav")
        m.update({"seed": seed, "file": f"{base}.m4a", "model": o.model, "steps": steps, "planned": o.plan,
                  "caption": o.caption, "bpm": o.bpm, "made_in_s": round(time.time() - t)})
        print(json.dumps(m), flush=True)


if __name__ == "__main__":
    main()
