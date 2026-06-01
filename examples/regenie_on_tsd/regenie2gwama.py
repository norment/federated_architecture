import numpy as np
import pandas as pd


def _first_present(df: pd.DataFrame, candidates):
    for name in candidates:
        if name in df.columns:
            return name
    return None


def regenie2gwama(input_path: str, output_path: str, mode: str = "or") -> None:
    """Convert a REGENIE step2 result file into GWAMA input format.

    The output includes OR-based columns for GWAMA execution and also keeps
    BETA/SE columns used by downstream local summary checks.
    """
    if mode.lower() != "or":
        raise ValueError(f"Unsupported mode: {mode}. Only 'or' is supported.")

    df = pd.read_csv(input_path, sep=r"\s+", engine="python")

    marker_col = _first_present(df, ["ID", "SNP", "MARKERNAME"])
    ea_col = _first_present(df, ["ALLELE1", "A1", "EA"])
    nea_col = _first_present(df, ["ALLELE0", "A2", "NEA"])
    beta_col = _first_present(df, ["BETA", "LOG_OR", "LOGOR"])
    se_col = _first_present(df, ["SE", "SE_LOG_OR", "SELOGOR"])
    or_col = _first_present(df, ["OR"])
    or_l_col = _first_present(df, ["OR_95L"])
    or_u_col = _first_present(df, ["OR_95U"])
    n_col = _first_present(df, ["N", "NMISS"])
    p_col = _first_present(df, ["P"])
    log10p_col = _first_present(df, ["LOG10P"])

    required = {
        "marker": marker_col,
        "effect allele": ea_col,
        "non-effect allele": nea_col,
    }
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise ValueError(f"Missing required REGENIE columns: {', '.join(missing)}")

    out = pd.DataFrame()
    out["MARKERNAME"] = df[marker_col]
    out["EA"] = df[ea_col]
    out["NEA"] = df[nea_col]

    if beta_col is not None:
        beta = pd.to_numeric(df[beta_col], errors="coerce")
    elif or_col is not None:
        beta = np.log(pd.to_numeric(df[or_col], errors="coerce"))
    else:
        raise ValueError("Missing BETA/OR information required for GWAMA conversion")

    if se_col is not None:
        se = pd.to_numeric(df[se_col], errors="coerce")
    else:
        # If SE is unavailable, downstream simple meta-analysis cannot be done.
        # Keep NaN to make the issue explicit.
        se = pd.Series(np.nan, index=df.index)

    if or_col is not None:
        odds_ratio = pd.to_numeric(df[or_col], errors="coerce")
    else:
        odds_ratio = np.exp(beta)

    if or_l_col is not None and or_u_col is not None:
        or_95l = pd.to_numeric(df[or_l_col], errors="coerce")
        or_95u = pd.to_numeric(df[or_u_col], errors="coerce")
    else:
        or_95l = np.exp(beta - 1.96 * se)
        or_95u = np.exp(beta + 1.96 * se)

    out["OR"] = odds_ratio
    out["OR_95L"] = or_95l
    out["OR_95U"] = or_95u
    out["BETA"] = beta
    out["SE"] = se

    if p_col is not None:
        out["P"] = pd.to_numeric(df[p_col], errors="coerce")
    elif log10p_col is not None:
        out["P"] = 10.0 ** (-pd.to_numeric(df[log10p_col], errors="coerce"))

    if n_col is not None:
        out["N"] = pd.to_numeric(df[n_col], errors="coerce")

    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=["MARKERNAME", "EA", "NEA", "OR"])

    out.to_csv(output_path, sep="\t", index=False)
