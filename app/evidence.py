"""Deterministic summaries shared by tutoring and PDF reports."""
def explanation(r):
 if not r or not r['stats']: return 'No valid trend inference is available. Record the data limitation; do not infer a trend from missing evidence.'
 s=r['stats']; lo,hi=s['ci95_year']
 return f"Estimated {s['direction']} trend: {s['slope_decade']:.3g} {r['unit']} per decade; 95% CI [{lo*10:.3g}, {hi*10:.3g}]; p={s['p_value']:.4g}; n={s['n']}. "+('Evidence against a zero linear slope at the 0.05 threshold. ' if s['significant'] else 'The evidence does not distinguish the slope from zero at the 0.05 threshold; this is not proof of no change. ')+'This observational analysis cannot establish a cause.'

