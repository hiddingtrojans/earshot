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
