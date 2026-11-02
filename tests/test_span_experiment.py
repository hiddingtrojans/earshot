import numpy as np

from tools.span_prompt_experiment import matrix


def test_matrix_computes_diagonal_and_correct_voice_rate():
    time = np.arange(96_000) / 48_000
    first = (0.2 + 0.8 * (np.sin(2 * np.pi * 3 * time) > 0)) * np.sin(2 * np.pi * 220 * time)
    second = (0.2 + 0.8 * (np.sin(2 * np.pi * 7 * time) > 0)) * np.sin(2 * np.pi * 330 * time)
    result = matrix([first, second], [first, second], first + second)
    assert result["correct_voice_rate"] == 1.0
    assert result["diagonal_mean"] == 1.0
    assert abs(result["off_diagonal_mean"]) < 0.2
    assert len(result["matrix"]) == len(result["mixture_baseline"]) == 2


def test_clean_mic_ab_cli_starts():
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).parent.parent / "tools" / "clean_mic_ab.py"
    result = subprocess.run([sys.executable, str(script), "--help"], check=True, capture_output=True, text=True)
    assert "clean mixed-down mic" in result.stdout
